import json
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from easy_tenants import tenant_context

from accountability.models import Accountability, Expense, ExpenseFile
from accounts.models import User


class ExpenseDocumentWorkspaceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_root = tempfile.mkdtemp(prefix="sitts-document-tests-")
        cls.settings_override = override_settings(
            MEDIA_ROOT=cls.media_root,
            STORAGES={
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            },
        )
        cls.settings_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.settings_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        call_command("seed_dev", verbosity=0)
        cls.user = User.objects.get(email="admin@admin.com")
        with tenant_context(cls.user.organization):
            cls.accountability = Accountability.objects.filter(
                status=Accountability.ReviewStatus.WIP,
                expenses__isnull=False,
            ).first()
            cls.expense = cls.accountability.expenses.first()
            cls.other_accountability = Accountability.objects.create(
                contract=cls.accountability.contract,
                month=cls.accountability.month,
                year=cls.accountability.year + 100,
                status=Accountability.ReviewStatus.WIP,
            )

    def setUp(self):
        self.client.force_login(self.user)

    def create_document(self, name, *, accountability=None, expense=None):
        with tenant_context(self.user.organization):
            return ExpenseFile.objects.create(
                accountability=accountability or self.accountability,
                expense=expense,
                created_by=self.user,
                name=name,
                file=SimpleUploadedFile(name, b"%PDF-test"),
            )

    def create_expense(
        self, identification, *, accountability=None, favored=None, value="100.00"
    ):
        with tenant_context(self.user.organization):
            return Expense.objects.create(
                accountability=accountability or self.accountability,
                source=self.expense.source,
                favored=favored,
                identification=identification,
                value=value,
                competency=self.expense.competency,
            )

    def test_document_list_defaults_to_unassigned_and_paginates(self):
        for index in range(21):
            self.create_document(f"queue-{index:02}.pdf")
        self.create_document("assigned.pdf", expense=self.expense)

        url = reverse(
            "accountability:expense-document-list",
            args=[self.accountability.id],
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 20)
        self.assertTrue(payload["has_more"])
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["total"], 22)
        self.assertEqual(payload["unassigned_total"], 21)
        self.assertTrue(all(item["expense_id"] is None for item in payload["results"]))

        second_page = self.client.get(url, {"page": 2}).json()
        self.assertEqual(len(second_page["results"]), 1)
        self.assertFalse(second_page["has_more"])

        for index in range(30):
            self.create_document(f"extra-{index:02}.pdf")
        capped_page = self.client.get(
            url,
            {"scope": "all", "page_size": 999},
        ).json()
        self.assertEqual(len(capped_page["results"]), 50)
        self.assertTrue(capped_page["has_more"])

    def test_document_list_filters_and_stays_scoped(self):
        expected = self.create_document("target-in-scope.pdf")
        self.create_document("not-a-match.pdf")
        self.create_document(
            "target-other-accountability.pdf",
            accountability=self.other_accountability,
        )

        response = self.client.get(
            reverse(
                "accountability:expense-document-list",
                args=[self.accountability.id],
            ),
            {"scope": "all", "q": "TARGET"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item["id"] for item in payload["results"]], [str(expected.id)]
        )
        self.assertEqual(payload["results"][0]["name"], "target-in-scope.pdf")

    def test_expense_list_filters_missing_documents(self):
        with_document = self.create_expense(
            "Workspace expense with document",
            favored=self.expense.favored,
        )
        without_document = self.create_expense(
            "Workspace expense missing target",
            favored=self.expense.favored,
        )
        self.create_document("linked.pdf", expense=with_document)

        response = self.client.get(
            reverse(
                "accountability:expense-document-expense-list",
                args=[self.accountability.id],
            ),
            {"q": "missing target", "without_documents": "true"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item["id"] for item in payload["results"]],
            [str(without_document.id)],
        )
        self.assertEqual(payload["results"][0]["document_count"], 0)
        self.assertEqual(
            payload["results"][0]["favored_name"], self.expense.favored.name
        )

    def test_expense_list_searches_and_paginates(self):
        for index in range(21):
            self.create_expense(f"Pagination target {index:02}")
        self.create_expense(
            "Pagination target outside scope",
            accountability=self.other_accountability,
        )

        url = reverse(
            "accountability:expense-document-expense-list",
            args=[self.accountability.id],
        )
        response = self.client.get(url, {"q": "Pagination target"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 20)
        self.assertTrue(payload["has_more"])
        self.assertEqual(payload["page"], 1)

        second_page = self.client.get(
            url,
            {"q": "Pagination target", "page": 2},
        ).json()
        self.assertEqual(len(second_page["results"]), 1)
        self.assertFalse(second_page["has_more"])
        self.assertNotIn(
            "Pagination target outside scope",
            [item["identification"] for item in second_page["results"]],
        )

        for index in range(30):
            self.create_expense(f"Pagination target extra {index:02}")
        capped_page = self.client.get(
            url,
            {"q": "Pagination target", "page_size": 999},
        ).json()
        self.assertEqual(len(capped_page["results"]), 50)
        self.assertTrue(capped_page["has_more"])

        favored_search = self.client.get(
            url,
            {"q": self.expense.favored.name},
        ).json()
        self.assertIn(
            str(self.expense.id),
            [item["id"] for item in favored_search["results"]],
        )

    def test_expense_list_prioritizes_missing_then_value_not_document_count(self):
        missing = self.create_expense("Missing documents", value="10.00")
        one_document = self.create_expense("One document", value="100.00")
        two_documents = self.create_expense("Two documents", value="300.00")
        self.create_document("one.pdf", expense=one_document)
        self.create_document("two-a.pdf", expense=two_documents)
        self.create_document("two-b.pdf", expense=two_documents)

        response = self.client.get(
            reverse(
                "accountability:expense-document-expense-list",
                args=[self.accountability.id],
            ),
            {"q": "document"},
        )

        self.assertEqual(response.status_code, 200)
        result_ids = [item["id"] for item in response.json()["results"]]
        self.assertEqual(
            result_ids,
            [str(missing.id), str(two_documents.id), str(one_document.id)],
        )

    def test_workspace_renders_api_backed_controls(self):
        response = self.client.get(
            reverse(
                "accountability:expense-document-workspace",
                args=[self.accountability.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-documents-url="')
        self.assertContains(response, 'data-expenses-url="')
        self.assertContains(
            response,
            'data-filter="unassigned" aria-pressed="true"',
        )
        self.assertContains(response, 'id="hide-expenses-with-documents"')
        self.assertContains(response, 'id="document-sentinel"')
        self.assertContains(response, 'id="expense-sentinel"')
        self.assertContains(response, 'id="document-end"')
        self.assertContains(response, 'id="expense-end"')
        self.assertNotContains(response, 'class="doc-card__name"')

    def test_bulk_upload_creates_unassigned_documents(self):
        response = self.client.post(
            reverse(
                "accountability:expense-document-bulk-upload",
                args=[self.accountability.id],
            ),
            {
                "files": [
                    SimpleUploadedFile("nota-1.pdf", b"%PDF-test"),
                    SimpleUploadedFile("nota-2.png", b"\x89PNG\r\n\x1a\n"),
                ]
            },
        )

        self.assertEqual(response.status_code, 201)
        with tenant_context(self.user.organization):
            documents = ExpenseFile.objects.filter(accountability=self.accountability)
            self.assertEqual(documents.count(), 2)
            self.assertFalse(documents.filter(expense__isnull=False).exists())

    def test_assign_endpoint_moves_many_documents_to_one_expense(self):
        with tenant_context(self.user.organization):
            documents = [
                ExpenseFile.objects.create(
                    accountability=self.accountability,
                    created_by=self.user,
                    name=f"nota-{index}.pdf",
                    file=SimpleUploadedFile(f"nota-{index}.pdf", b"%PDF-test"),
                )
                for index in range(2)
            ]

        response = self.client.post(
            reverse(
                "accountability:expense-document-assign",
                args=[self.accountability.id],
            ),
            data=json.dumps(
                {
                    "document_ids": [str(document.id) for document in documents],
                    "expense_id": str(self.expense.id),
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        with tenant_context(self.user.organization):
            self.assertEqual(
                ExpenseFile.objects.filter(
                    id__in=[document.id for document in documents],
                    expense=self.expense,
                ).count(),
                2,
            )

    def test_upload_rejects_unsupported_files_without_partial_save(self):
        response = self.client.post(
            reverse(
                "accountability:expense-document-bulk-upload",
                args=[self.accountability.id],
            ),
            {
                "files": [
                    SimpleUploadedFile("nota.pdf", b"%PDF-valid"),
                    SimpleUploadedFile("script.exe", b"invalid"),
                ]
            },
        )

        self.assertEqual(response.status_code, 400)
        with tenant_context(self.user.organization):
            self.assertFalse(
                ExpenseFile.objects.filter(accountability=self.accountability).exists()
            )

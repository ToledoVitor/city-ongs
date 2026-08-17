import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from easy_tenants import tenant_context
from google.auth.credentials import Credentials
from google.cloud.storage.blob import Blob
from storages.backends.gcloud import GoogleCloudStorage

from accountability.models import Accountability, Expense, ExpenseFile
from accounts.models import User
from core import settings as project_settings


class TokenOnlyCredentials(Credentials):
    def refresh(self, request):
        pass

    @property
    def service_account_email(self):
        return "sitts-run@sitts-504501.iam.gserviceaccount.com"


class CloudStorageConfigurationTests(SimpleTestCase):
    def test_private_media_urls_use_iam_sign_blob_with_token_credentials(self):
        credentials = TokenOnlyCredentials()
        credentials.token = "access-token"
        storage_options = dict(
            getattr(
                project_settings,
                "GCS_MEDIA_STORAGE_OPTIONS",
                {
                    "default_acl": None,
                    "querystring_auth": True,
                },
            )
        )
        storage_options["bucket_name"] = "sitts-private-media"
        storage = GoogleCloudStorage(
            credentials=credentials,
            project_id="sitts-504501",
            **storage_options,
        )

        with patch.object(
            Blob,
            "generate_signed_url",
            return_value="https://storage.example/signed-document",
        ) as generate_signed_url:
            url = storage.url("uploads/expenses/document.pdf")

        self.assertEqual(url, "https://storage.example/signed-document")
        self.assertEqual(
            generate_signed_url.call_args.kwargs.get("service_account_email"),
            credentials.service_account_email,
        )
        self.assertEqual(
            generate_signed_url.call_args.kwargs.get("access_token"),
            "access-token",
        )


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

    def media_files(self):
        media_root = Path(self.media_root)
        return {
            path.relative_to(media_root)
            for path in media_root.rglob("*")
            if path.is_file()
        }

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
        self.assertEqual(
            payload["results"][0]["documents_url"],
            reverse(
                "accountability:expense-document-expense-documents",
                args=[self.accountability.id, without_document.id],
            ),
        )

    def test_expense_documents_endpoint_is_scoped_and_paginated(self):
        target_expense = self.create_expense("Disclosure target")
        other_expense = self.create_expense("Disclosure other expense")
        other_accountability_expense = self.create_expense(
            "Disclosure other accountability",
            accountability=self.other_accountability,
        )
        for index in range(21):
            self.create_document(f"target-{index:02}.pdf", expense=target_expense)
        self.create_document("other-expense.pdf", expense=other_expense)
        self.create_document(
            "other-accountability.pdf",
            accountability=self.other_accountability,
            expense=other_accountability_expense,
        )
        deleted = self.create_document("deleted.pdf", expense=target_expense)
        with tenant_context(self.user.organization):
            deleted.deleted_at = timezone.now()
            deleted.save(update_fields=["deleted_at", "updated_at"])

        url = reverse(
            "accountability:expense-document-expense-documents",
            args=[self.accountability.id, target_expense.id],
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 20)
        self.assertTrue(payload["has_more"])
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["total"], 21)
        self.assertTrue(
            all(item["name"].startswith("target-") for item in payload["results"])
        )

        second_page = self.client.get(url, {"page": 2}).json()
        self.assertEqual(len(second_page["results"]), 1)
        self.assertFalse(second_page["has_more"])

        for index in range(30):
            self.create_document(f"target-extra-{index:02}.pdf", expense=target_expense)
        capped_page = self.client.get(url, {"page_size": 999}).json()
        self.assertEqual(len(capped_page["results"]), 50)
        self.assertTrue(capped_page["has_more"])

        foreign_expense_url = reverse(
            "accountability:expense-document-expense-documents",
            args=[self.accountability.id, other_accountability_expense.id],
        )
        self.assertEqual(self.client.get(foreign_expense_url).status_code, 404)

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
        self.assertContains(
            response,
            "Selecione documentos vinculados em Todos ou remova abaixo",
        )
        self.assertContains(response, "expenseDisclosureStates")
        self.assertContains(response, "linkedSelectedIds")
        self.assertContains(response, "parseJsonResponse")
        self.assertContains(
            response,
            "Não foi possível enviar os documentos. Tente novamente.",
        )
        self.assertContains(response, "Vincular ")
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

    def test_bulk_upload_rolls_back_rows_and_files_when_signed_url_fails(self):
        with tenant_context(self.user.organization):
            document_count = ExpenseFile.objects.filter(
                accountability=self.accountability
            ).count()
        files_before_upload = self.media_files()

        with patch(
            "django.core.files.storage.FileSystemStorage.url",
            side_effect=RuntimeError("signed URL failed"),
        ):
            response = self.client.post(
                reverse(
                    "accountability:expense-document-bulk-upload",
                    args=[self.accountability.id],
                ),
                {
                    "files": [
                        SimpleUploadedFile("rollback-1.pdf", b"%PDF-test"),
                        SimpleUploadedFile("rollback-2.pdf", b"%PDF-test"),
                    ]
                },
            )

        self.assertEqual(response.status_code, 500)
        with tenant_context(self.user.organization):
            self.assertEqual(
                ExpenseFile.objects.filter(accountability=self.accountability).count(),
                document_count,
            )
        self.assertEqual(self.media_files(), files_before_upload)

    def test_bulk_upload_signed_url_failure_returns_json_error(self):
        with patch(
            "django.core.files.storage.FileSystemStorage.url",
            side_effect=RuntimeError("signed URL failed"),
        ):
            response = self.client.post(
                reverse(
                    "accountability:expense-document-bulk-upload",
                    args=[self.accountability.id],
                ),
                {"files": [SimpleUploadedFile("json-error.pdf", b"%PDF-test")]},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {"error": "Não foi possível enviar os documentos. Tente novamente."},
        )

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

    def test_assign_endpoint_unlinks_without_deleting(self):
        document = self.create_document("mismoved.pdf", expense=self.expense)

        response = self.client.post(
            reverse(
                "accountability:expense-document-assign",
                args=[self.accountability.id],
            ),
            data=json.dumps(
                {
                    "document_ids": [str(document.id)],
                    "expense_id": None,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["expense_id"])
        with tenant_context(self.user.organization):
            document.refresh_from_db()
            self.assertIsNone(document.expense_id)
            self.assertTrue(ExpenseFile.objects.filter(id=document.id).exists())

    def test_assign_endpoint_rejects_cross_accountability_document(self):
        foreign_document = self.create_document(
            "foreign.pdf",
            accountability=self.other_accountability,
        )

        response = self.client.post(
            reverse(
                "accountability:expense-document-assign",
                args=[self.accountability.id],
            ),
            data=json.dumps(
                {
                    "document_ids": [str(foreign_document.id)],
                    "expense_id": str(self.expense.id),
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        with tenant_context(self.user.organization):
            foreign_document.refresh_from_db()
            self.assertIsNone(foreign_document.expense_id)

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

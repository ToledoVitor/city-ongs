import json
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from easy_tenants import tenant_context

from accountability.models import Accountability, ExpenseFile
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

    def setUp(self):
        self.client.force_login(self.user)

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

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CityHall, Organization
from audesp.models import AudespCredential

User = get_user_model()


class AudespCredentialSettingsTests(TestCase):
    """Covers the city-hall-scoped AUDESP credential settings page added
    under `accounts:audesp-credentials-*` (see `accounts/views.py` and
    `accounts/forms.py`). Mocks `audesp.secrets.set_credentials` — never
    hits real GCP Secret Manager.
    """

    def setUp(self):
        self.city_hall = CityHall.objects.create(
            name="Prefeitura de Teste",
            mayor="Prefeito Teste",
            document="12345678901",
        )
        self.organization = Organization.objects.create(
            city_hall=self.city_hall,
            name="Organização Teste",
        )

        self.admin_user = User.objects.create(
            email="admin@example.com",
            username="admin@example.com",
            first_name="Admin",
            last_name="Teste",
            cpf="11111111111",
            organization=self.organization,
            access_level=User.AccessChoices.MASTER,
            password_redefined=True,
        )
        self.admin_user.set_password("strong-pass-123")
        self.admin_user.save()

        self.plain_user = User.objects.create(
            email="accountant@example.com",
            username="accountant@example.com",
            first_name="Contador",
            last_name="Teste",
            cpf="22222222222",
            organization=self.organization,
            access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT,
            password_redefined=True,
        )
        self.plain_user.set_password("strong-pass-123")
        self.plain_user.save()

    def test_list_view_requires_admin_access(self):
        self.client.force_login(self.plain_user)
        response = self.client.get(reverse("accounts:audesp-credentials-list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("contracts:contracts-list"))

    def test_list_view_renders_for_admin_with_no_credentials_configured(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("accounts:audesp-credentials-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Piloto")
        self.assertContains(response, "Produção")
        self.assertContains(response, "Não configurada")
        self.assertContains(response, "Prefeitura de Teste")

    def test_form_view_requires_admin_access(self):
        self.client.force_login(self.plain_user)
        response = self.client.get(
            reverse("accounts:audesp-credentials-form", args=["PILOTO"])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("contracts:contracts-list"))

    def test_form_view_404s_on_invalid_environment(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("accounts:audesp-credentials-form", args=["NOT_AN_ENV"])
        )
        self.assertEqual(response.status_code, 404)

    def test_development_mode_disables_credential_fields_and_never_renders_password(
        self,
    ):
        # settings.DEVELOPMENT is True in this test process (see .env) — the
        # form must disable username/password exactly like the admin form
        # does, and never pre-fill a password value.
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("accounts:audesp-credentials-form", args=["PILOTO"])
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.fields["username"].disabled)
        self.assertTrue(form.fields["password"].disabled)
        self.assertContains(response, "Ambiente de desenvolvimento")
        self.assertNotContains(response, 'value="piloto-pass"')

    @override_settings(DEVELOPMENT=False)
    @patch("audesp.secrets.set_credentials")
    def test_creating_credential_calls_set_credentials(self, mock_set_credentials):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("accounts:audesp-credentials-form", args=["PILOTO"]),
            data={"username": "tce-user", "password": "tce-pass", "is_active": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"], reverse("accounts:audesp-credentials-list")
        )

        credential = AudespCredential.objects.get(
            city_hall=self.city_hall, environment="PILOTO"
        )
        self.assertTrue(credential.is_active)
        mock_set_credentials.assert_called_once_with(
            self.city_hall, "PILOTO", "tce-user", "tce-pass"
        )

    @override_settings(DEVELOPMENT=False)
    @patch("audesp.secrets.set_credentials")
    def test_creating_credential_without_password_fails_validation(
        self, mock_set_credentials
    ):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("accounts:audesp-credentials-form", args=["PILOTO"]),
            data={"is_active": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "obrigatórios")
        mock_set_credentials.assert_not_called()
        self.assertFalse(
            AudespCredential.objects.filter(
                city_hall=self.city_hall, environment="PILOTO"
            ).exists()
        )

    @override_settings(DEVELOPMENT=False)
    @patch("audesp.secrets.set_credentials")
    def test_editing_credential_without_new_password_keeps_existing_row(
        self, mock_set_credentials
    ):
        credential = AudespCredential.objects.create(
            city_hall=self.city_hall, environment="PILOTO", is_active=True
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("accounts:audesp-credentials-form", args=["PILOTO"]),
            data={"is_active": ""},
        )
        self.assertEqual(response.status_code, 302)
        mock_set_credentials.assert_not_called()
        credential.refresh_from_db()
        self.assertFalse(credential.is_active)

    def test_toggle_status_flips_is_active(self):
        credential = AudespCredential.objects.create(
            city_hall=self.city_hall, environment="PILOTO", is_active=True
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("accounts:audesp-credentials-toggle-status", args=["PILOTO"])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"], reverse("accounts:audesp-credentials-list")
        )
        credential.refresh_from_db()
        self.assertFalse(credential.is_active)

    def test_toggle_status_requires_post(self):
        AudespCredential.objects.create(
            city_hall=self.city_hall, environment="PILOTO", is_active=True
        )
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("accounts:audesp-credentials-toggle-status", args=["PILOTO"])
        )
        self.assertEqual(response.status_code, 405)

    def test_credential_is_scoped_to_city_hall(self):
        other_city_hall = CityHall.objects.create(
            name="Outra Prefeitura",
            mayor="Outro Prefeito",
            document="99988877766",
        )
        AudespCredential.objects.create(
            city_hall=other_city_hall, environment="PILOTO", is_active=True
        )

        self.client.force_login(self.admin_user)

        # This city hall's list must not show the other city hall's row.
        response = self.client.get(reverse("accounts:audesp-credentials-list"))
        self.assertContains(response, "Não configurada")

        # Nor can this admin toggle the other city hall's credential.
        response = self.client.post(
            reverse("accounts:audesp-credentials-toggle-status", args=["PILOTO"])
        )
        self.assertEqual(response.status_code, 404)

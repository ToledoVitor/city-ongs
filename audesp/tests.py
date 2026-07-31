"""Tests for the AUDESP Fase IV trigger/status UI (audesp/views.py,
audesp/forms.py, and the contract-detail tab). Builds a minimal fixture
directly rather than the full accounts.management.commands.seed_dev
dev-seed, which is for local bootstrapping, not test isolation.

No real network call is ever made — AudespClient's HTTP layer is patched
in every test that reaches a submit path.
"""

import datetime
import uuid
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from easy_tenants import tenant_context

from accountability.models import BudgetCommitment
from accounts.models import Area, CityHall, Organization, User
from audesp.models import AudespCredential, AudespFaseIVSubmission
from contracts.choices import AudespFundingSourceTypeChoices
from contracts.models import Contract


class _FakeResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data
        self.text = str(json_data)

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected status {self.status_code}")


def _fake_request(method, url, **kwargs):
    """Stand-in for `requests.request` — no real network call in tests."""
    if url.endswith("/login"):
        return _FakeResponse(200, {"token": "fake-jwt-token"})
    if "/recepcao-fase-4/f4/enviar-ajuste" in url:
        return _FakeResponse(200, {"protocolo": "PROTO-000123", "mensagem": "Recebido"})
    raise AssertionError(f"Unexpected request in test: {method} {url}")


class AudespFaseIVViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city_hall = CityHall.objects.create(
            name="Prefeitura Teste",
            document="12345678000199",
            audesp_municipality_code=7107,
        )
        cls.organization = Organization.objects.create(
            city_hall=cls.city_hall,
            name="OSC Teste",
            document="98765432000188",
            audesp_entity_code=10048,
        )
        with tenant_context(cls.organization):
            cls.area = Area.objects.create(
                organization=cls.organization,
                city_hall=cls.city_hall,
                name="Assistência Social",
            )
            cls.contract = Contract.objects.create(
                organization=cls.organization,
                name="Convênio Teste",
                concession_type=Contract.ConcessionChoices.AGREEMENT,
                code="CV-001",
                audesp_agreement_code="20260000000001",
                internal_code=1001,
                objective="Prestação de serviços de assistência social",
                bidding="Chamamento Público 01/2026",
                original_value=Decimal("120000.00"),
                total_value=Decimal("120000.00"),
                start_of_vigency=datetime.date(2026, 1, 1),
                end_of_vigency=datetime.date(2026, 12, 31),
                signature_date=datetime.date(2025, 12, 15),
                area=cls.area,
            )
            cls.budget_commitment = BudgetCommitment.objects.create(
                organization=cls.organization,
                contract=cls.contract,
                number="123",
                issue_date=datetime.date(2026, 1, 5),
                economic_classification="33903900",
                funding_source_type=AudespFundingSourceTypeChoices.TREASURY,
                value=Decimal("120000.00"),
                description="Empenho referente ao convênio 001/2026",
                spending_authority_cpf="12345678909",
            )

        cls.user = User.objects.create(
            username="tester@example.com",
            email="tester@example.com",
            organization=cls.organization,
            access_level=User.AccessChoices.MASTER,
            cpf="85351346893",
            first_name="Test",
            last_name="User",
            is_active=True,
            password_redefined=True,
        )
        cls.user.set_password("irrelevant-in-tests")
        cls.user.save()
        cls.user.areas.set([cls.area])

        cls.credential = AudespCredential.objects.create(
            city_hall=cls.city_hall,
            environment=AudespCredential.EnvironmentChoices.PILOTO,
            is_active=True,
        )

    def setUp(self):
        # DEVELOPMENT-mode credentials (audesp/secrets.py) come from
        # settings.AUDESP_DEV_CREDENTIALS, populated once from .env at
        # import time — .env has no real AUDESP_PILOTO_USERNAME/PASSWORD,
        # so tests exercising a successful login need a valid pair here.
        # Restored after each test so the "no credential configured" test
        # can still exercise the blank-credential path independently.
        original = settings.AUDESP_DEV_CREDENTIALS["PILOTO"]
        settings.AUDESP_DEV_CREDENTIALS["PILOTO"] = {
            "username": "dev-user",
            "password": "dev-pass",
        }
        self.addCleanup(settings.AUDESP_DEV_CREDENTIALS.__setitem__, "PILOTO", original)

    # --- access control ------------------------------------------------

    def test_anonymous_get_ajuste_create_redirects_to_login(self):
        resp = self.client.get(
            reverse("audesp:fase-iv-ajuste-create", args=[self.contract.id])
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/auth/login", resp.url)

    def test_unknown_contract_id_404s(self):
        self.client.force_login(self.user)
        resp = self.client.get(
            reverse("audesp:fase-iv-ajuste-create", args=[uuid.uuid4()])
        )
        self.assertEqual(resp.status_code, 404)

    # --- contract detail tab --------------------------------------------

    def test_contract_detail_page_renders_fase_iv_tab(self):
        self.client.force_login(self.user)
        resp = self.client.get(
            reverse("contracts:contracts-detail", args=[self.contract.id])
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("audesp-fase-iv-tab", body)
        self.assertIn("AUDESP Fase IV", body)
        self.assertIn(self.budget_commitment.number, body)
        self.assertIn("Nenhuma submissão ainda", body)

    # --- Ajuste: build + validate ---------------------------------------

    def test_ajuste_create_get_shows_empty_preview(self):
        self.client.force_login(self.user)
        resp = self.client.get(
            reverse("audesp:fase-iv-ajuste-create", args=[self.contract.id])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sem documento construído", resp.content.decode())

    def test_ajuste_build_valid_creates_submission(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("audesp:fase-iv-ajuste-create", args=[self.contract.id]),
            {"codigo_edital": "CHP0012026", "itens": "1, 2, 4"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Documento válido", resp.content.decode())

        with tenant_context(self.organization):
            submission = AudespFaseIVSubmission.objects.get(
                contract=self.contract,
                document_type=AudespFaseIVSubmission.DocumentTypeChoices.AJUSTE,
            )
        self.assertEqual(submission.status, AudespFaseIVSubmission.StatusChoices.VALID)
        self.assertEqual(submission.validation_errors, [])
        self.assertEqual(submission.payload["itens"], [1, 2, 4])
        self.assertEqual(submission.payload["descritor"]["codigoEdital"], "CHP0012026")

    def test_ajuste_build_rejects_malformed_itens_without_crashing(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("audesp:fase-iv-ajuste-create", args=[self.contract.id]),
            {"codigo_edital": "CHP0012026", "itens": "abc"},
        )
        self.assertEqual(resp.status_code, 200)
        with tenant_context(self.organization):
            self.assertFalse(
                AudespFaseIVSubmission.objects.filter(contract=self.contract).exists()
            )
        self.assertContains(resp, "não é um número de item válido")

    def test_ajuste_build_without_budget_commitment_shows_form_error(self):
        # A second contract with no BudgetCommitment at all — the builder's
        # ValueError (no fonteRecursosContratacao available) must surface as
        # a form error, not a 500.
        with tenant_context(self.organization):
            bare_contract = Contract.objects.create(
                organization=self.organization,
                name="Contrato sem empenho",
                concession_type=Contract.ConcessionChoices.AGREEMENT,
                audesp_agreement_code="20260000000002",
                internal_code=1002,
                objective="Objeto de teste",
                bidding="Chamamento Público 02/2026",
                original_value=Decimal("1000.00"),
                total_value=Decimal("1000.00"),
                start_of_vigency=datetime.date(2026, 1, 1),
                end_of_vigency=datetime.date(2026, 12, 31),
                signature_date=datetime.date(2025, 12, 15),
                area=self.area,
            )
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("audesp:fase-iv-ajuste-create", args=[bare_contract.id]),
            {"codigo_edital": "CHP0022026", "itens": "1"},
        )
        self.assertEqual(resp.status_code, 200)
        with tenant_context(self.organization):
            self.assertFalse(
                AudespFaseIVSubmission.objects.filter(contract=bare_contract).exists()
            )
        self.assertContains(resp, "No fonteRecursosContratacao available")

    # --- Empenho: build + validate ---------------------------------------

    def test_empenho_build_valid_redirects_with_success_message(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("audesp:fase-iv-empenho-create", args=[self.contract.id]),
            {"budget_commitment": str(self.budget_commitment.id)},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        with tenant_context(self.organization):
            submission = AudespFaseIVSubmission.objects.get(
                budget_commitment=self.budget_commitment,
                document_type=AudespFaseIVSubmission.DocumentTypeChoices.EMPENHO,
            )
        self.assertEqual(submission.status, AudespFaseIVSubmission.StatusChoices.VALID)
        self.assertIn("Empenho registrado e válido", resp.content.decode())

    def test_empenho_create_requires_post(self):
        self.client.force_login(self.user)
        resp = self.client.get(
            reverse("audesp:fase-iv-empenho-create", args=[self.contract.id])
        )
        self.assertEqual(resp.status_code, 405)

    # --- submit -----------------------------------------------------------

    def test_submit_moves_valid_submission_to_submitted(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("audesp:fase-iv-ajuste-create", args=[self.contract.id]),
            {"codigo_edital": "CHP0012026", "itens": "1"},
        )
        with tenant_context(self.organization):
            submission = AudespFaseIVSubmission.objects.get(
                contract=self.contract,
                document_type=AudespFaseIVSubmission.DocumentTypeChoices.AJUSTE,
            )
        with patch("audesp.clients.requests.request", side_effect=_fake_request):
            resp = self.client.post(
                reverse("audesp:fase-iv-submission-submit", args=[submission.id]),
                follow=True,
            )
        self.assertEqual(resp.status_code, 200)
        with tenant_context(self.organization):
            submission.refresh_from_db()
        self.assertEqual(
            submission.status, AudespFaseIVSubmission.StatusChoices.SUBMITTED
        )
        self.assertEqual(submission.protocol_number, "PROTO-000123")
        self.assertIn("Enviado ao AUDESP", resp.content.decode())

    def test_submit_invalid_submission_is_refused_without_calling_webservice(self):
        with tenant_context(self.organization):
            submission = AudespFaseIVSubmission.objects.create(
                organization=self.organization,
                contract=self.contract,
                document_type=AudespFaseIVSubmission.DocumentTypeChoices.AJUSTE,
                status=AudespFaseIVSubmission.StatusChoices.INVALID,
                payload={},
                validation_errors=[{"message": "campo obrigatório ausente"}],
            )
        self.client.force_login(self.user)
        with patch("audesp.clients.requests.request", side_effect=_fake_request) as m:
            resp = self.client.post(
                reverse("audesp:fase-iv-submission-submit", args=[submission.id]),
                follow=True,
            )
        m.assert_not_called()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Apenas submissões válidas", resp.content.decode())

    def test_submit_without_dev_credentials_shows_friendly_message_not_500(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("audesp:fase-iv-ajuste-create", args=[self.contract.id]),
            {"codigo_edital": "CHP0012026", "itens": "1"},
        )
        with tenant_context(self.organization):
            submission = AudespFaseIVSubmission.objects.get(
                contract=self.contract,
                document_type=AudespFaseIVSubmission.DocumentTypeChoices.AJUSTE,
            )
        original = settings.AUDESP_DEV_CREDENTIALS["PILOTO"]
        settings.AUDESP_DEV_CREDENTIALS["PILOTO"] = {"username": "", "password": ""}
        try:
            resp = self.client.post(
                reverse("audesp:fase-iv-submission-submit", args=[submission.id]),
                follow=True,
            )
        finally:
            settings.AUDESP_DEV_CREDENTIALS["PILOTO"] = original
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nenhuma credencial AUDESP configurada", resp.content.decode())

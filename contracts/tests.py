import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from easy_tenants import tenant_context

from accounts.models import Area, CityHall, Organization
from activity.models import ActivityLog, Notification
from contracts.forms import ContractItemSupplementUpdateForm
from contracts.models import (
    Contract,
    ContractItem,
    ContractItemNewValueRequest,
    ContractItemSupplement,
)

User = get_user_model()


class ContractChangeApprovalWorkflowTests(TestCase):
    """The review routes are the public boundary for contract value changes."""

    @classmethod
    def setUpTestData(cls):
        cls.organization, cls.area, cls.contract = cls.create_contract_context(
            "Principal", "11111111000111", 1001
        )
        with tenant_context(cls.organization):
            cls.raise_item = ContractItem.objects.create(
                organization=cls.organization,
                contract=cls.contract,
                name="Item que recebe",
                objective="Objetivo",
                month_quantity=12,
                month_expense=Decimal("100.00"),
                anual_expense=Decimal("1200.00"),
                nature="ADMINISTRATIVE",
            )
            cls.downgrade_item = ContractItem.objects.create(
                organization=cls.organization,
                contract=cls.contract,
                name="Item que cede",
                objective="Objetivo",
                month_quantity=12,
                month_expense=Decimal("200.00"),
                anual_expense=Decimal("2400.00"),
                nature="ADMINISTRATIVE",
            )

        cls.reviewer = cls.create_user(
            "reviewer@example.com", cls.organization, User.AccessChoices.FOLDER_MANAGER
        )
        cls.reviewer.areas.add(cls.area)
        cls.reviewer.supervision_contracts.add(cls.contract)
        cls.requester = cls.create_user(
            "requester@example.com",
            cls.organization,
            User.AccessChoices.ORGANIZATION_ACCOUNTANT,
        )
        cls.requester.accountability_contracts.add(cls.contract)
        cls.unrelated_user = cls.create_user(
            "unrelated@example.com",
            cls.organization,
            User.AccessChoices.ORGANIZATION_ACCOUNTANT,
        )

        cls.other_organization, cls.other_area, cls.other_contract = (
            cls.create_contract_context("Outra", "22222222000122", 2001)
        )
        cls.cross_tenant_user = cls.create_user(
            "other@example.com",
            cls.other_organization,
            User.AccessChoices.FOLDER_MANAGER,
        )
        cls.cross_tenant_user.areas.add(cls.other_area)
        cls.cross_tenant_user.supervision_contracts.add(cls.other_contract)

    @classmethod
    def create_contract_context(cls, suffix, document, internal_code):
        city_hall = CityHall.objects.create(
            name=f"Prefeitura {suffix}", mayor="Prefeito", document=document
        )
        organization = Organization.objects.create(
            city_hall=city_hall, name=f"Organização {suffix}"
        )
        with tenant_context(organization):
            area = Area.objects.create(
                organization=organization, city_hall=city_hall, name=f"Área {suffix}"
            )
            contract = Contract.objects.create(
                organization=organization,
                name=f"Contrato {suffix}",
                concession_type=Contract.ConcessionChoices.AGREEMENT,
                internal_code=internal_code,
                objective="Objetivo de teste",
                bidding="Chamamento",
                original_value=Decimal("10000.00"),
                total_value=Decimal("10000.00"),
                start_of_vigency=datetime.date(2026, 1, 1),
                end_of_vigency=datetime.date(2026, 12, 31),
                area=area,
            )
        return organization, area, contract

    @classmethod
    def create_user(cls, email, organization, access_level):
        return User.objects.create(
            username=email,
            email=email,
            first_name="Usuário",
            last_name="Teste",
            cpf={
                "reviewer@example.com": "85351346893",
                "requester@example.com": "11144477735",
                "unrelated@example.com": "93541134780",
                "other@example.com": "12345678909",
            }[email],
            organization=organization,
            access_level=access_level,
            password_redefined=True,
        )

    def create_supplement(self):
        with tenant_context(self.organization):
            return ContractItemSupplement.objects.create(
                organization=self.organization,
                item=self.raise_item,
                suplement_value=Decimal("100.00"),
            )

    def create_reallocation_request(self):
        with tenant_context(self.organization):
            return ContractItemNewValueRequest.objects.create(
                organization=self.organization,
                requested_by=self.requester,
                downgrade_item=self.downgrade_item,
                raise_item=self.raise_item,
                month_raise=Decimal("25.00"),
                anual_raise=Decimal("300.00"),
            )

    def has_activity(self, action, target_object_id):
        with tenant_context(self.organization):
            return ActivityLog.objects.filter(
                action=action,
                target_object_id=str(target_object_id),
            ).exists()

    def test_supplement_update_persists_the_legacy_amount_field(self):
        supplement = self.create_supplement()
        self.client.force_login(self.requester)
        edit_url = reverse(
            "contracts:item-supplementations-update", args=[supplement.id]
        )

        response = self.client.get(edit_url)
        self.assertContains(response, 'value="100')

        response = self.client.post(
            edit_url,
            {"supplement_value": "250,00", "observations": "Atualizado"},
        )

        self.assertRedirects(
            response,
            reverse("contracts:item-supplementations", args=[self.contract.id]),
        )
        supplement.refresh_from_db()
        self.assertEqual(supplement.suplement_value, Decimal("250.00"))
        self.assertTrue(
            self.has_activity(
                ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM_SUPPLEMENT,
                supplement.id,
            )
        )

    def test_supplement_decisions_record_reviewer_and_are_immutable(self):
        supplement = self.create_supplement()
        self.client.force_login(self.reviewer)
        review_url = reverse(
            "contracts:item-supplementations-review", args=[supplement.id]
        )

        response = self.client.post(
            review_url,
            {"status": "APPROVED", "rejection_reason": "Não deve persistir"},
        )

        self.assertRedirects(
            response,
            reverse("contracts:item-supplementations", args=[self.contract.id]),
        )
        supplement.refresh_from_db()
        self.assertEqual(
            supplement.status, ContractItemSupplement.ReviewStatus.APPROVED
        )
        self.assertEqual(supplement.reviewed_by, self.reviewer)
        self.assertIsNotNone(supplement.reviewed_at)
        self.assertIsNone(supplement.rejection_reason)
        self.assertTrue(
            self.has_activity(
                "APPROVED_CONTRACT_ITEM_SUPPLEMENT",
                supplement.id,
            )
        )

        second_response = self.client.post(
            review_url, {"status": "REJECTED", "rejection_reason": "Tarde"}
        )
        self.assertEqual(second_response.status_code, 404)
        supplement.refresh_from_db()
        self.assertEqual(
            supplement.status, ContractItemSupplement.ReviewStatus.APPROVED
        )

    def test_supplement_rejection_requires_a_reason(self):
        supplement = self.create_supplement()
        self.client.force_login(self.reviewer)

        response = self.client.post(
            reverse("contracts:item-supplementations-review", args=[supplement.id]),
            {"status": "REJECTED", "rejection_reason": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "É necessário informar um motivo para rejeição")
        supplement.refresh_from_db()
        self.assertEqual(
            supplement.status, ContractItemSupplement.ReviewStatus.IN_REVIEW
        )

    def test_supplement_review_blocks_unrelated_and_cross_tenant_users(self):
        supplement = self.create_supplement()
        review_url = reverse(
            "contracts:item-supplementations-review", args=[supplement.id]
        )

        self.client.force_login(self.unrelated_user)
        self.assertEqual(self.client.get(review_url).status_code, 404)

        self.client.force_login(self.cross_tenant_user)
        self.assertEqual(self.client.get(review_url).status_code, 404)

    def test_supplement_review_requires_an_explicit_decision(self):
        supplement = self.create_supplement()
        self.client.force_login(self.reviewer)
        review_url = reverse(
            "contracts:item-supplementations-review", args=[supplement.id]
        )

        response = self.client.get(review_url)
        self.assertContains(response, '<option value="">Selecione…</option>', html=True)

        response = self.client.post(review_url, {"status": "", "rejection_reason": ""})
        self.assertEqual(response.status_code, 200)
        supplement.refresh_from_db()
        self.assertEqual(
            supplement.status, ContractItemSupplement.ReviewStatus.IN_REVIEW
        )

    def test_supplement_rejection_records_its_reason_and_audit_event(self):
        supplement = self.create_supplement()
        self.client.force_login(self.reviewer)

        response = self.client.post(
            reverse("contracts:item-supplementations-review", args=[supplement.id]),
            {"status": "REJECTED", "rejection_reason": "Valor sem memória de cálculo"},
        )

        self.assertRedirects(
            response,
            reverse("contracts:item-supplementations", args=[self.contract.id]),
        )
        supplement.refresh_from_db()
        self.assertEqual(
            supplement.status, ContractItemSupplement.ReviewStatus.REJECTED
        )
        self.assertEqual(supplement.rejection_reason, "Valor sem memória de cálculo")
        self.assertEqual(supplement.reviewed_by, self.reviewer)
        self.assertTrue(
            self.has_activity(
                "REJECTED_CONTRACT_ITEM_SUPPLEMENT",
                supplement.id,
            )
        )

    def test_stale_supplement_update_cannot_reopen_a_terminal_decision(self):
        supplement = self.create_supplement()
        self.client.force_login(self.requester)
        edit_url = reverse(
            "contracts:item-supplementations-update", args=[supplement.id]
        )
        original_is_valid = ContractItemSupplementUpdateForm.is_valid

        def approve_before_stale_save(form):
            ContractItemSupplement.objects.filter(id=supplement.id).update(
                status=ContractItemSupplement.ReviewStatus.APPROVED
            )
            return original_is_valid(form)

        with patch(
            "contracts.views.ContractItemSupplementUpdateForm.is_valid",
            autospec=True,
            side_effect=approve_before_stale_save,
        ):
            response = self.client.post(
                edit_url,
                {"supplement_value": "250,00", "observations": "Tentativa atrasada"},
            )

        self.assertEqual(response.status_code, 404)
        supplement.refresh_from_db()
        self.assertEqual(
            supplement.status, ContractItemSupplement.ReviewStatus.APPROVED
        )
        self.assertEqual(supplement.suplement_value, Decimal("100.00"))

    @patch("activity.services.SendGridClient.notify")
    def test_reallocation_rejection_changes_neither_item_and_logs_decision(
        self, _notify
    ):
        value_request = self.create_reallocation_request()
        self.client.force_login(self.reviewer)

        response = self.client.post(
            reverse("contracts:review-value-requests", args=[value_request.id]),
            {"status": "REJECTED", "rejection_reason": "Sem justificativa"},
        )

        self.assertRedirects(
            response, reverse("contracts:contracts-detail", args=[self.contract.id])
        )
        self.raise_item.refresh_from_db()
        self.downgrade_item.refresh_from_db()
        self.assertEqual(self.raise_item.month_expense, Decimal("100.00"))
        self.assertEqual(self.raise_item.anual_expense, Decimal("1200.00"))
        self.assertEqual(self.downgrade_item.month_expense, Decimal("200.00"))
        self.assertEqual(self.downgrade_item.anual_expense, Decimal("2400.00"))
        self.assertTrue(
            self.has_activity(
                "REJECTED_CONTRACT_ITEM_VALUE_REQUEST",
                value_request.id,
            )
        )
        with tenant_context(self.organization):
            self.assertTrue(
                Notification.objects.filter(
                    recipient=self.requester,
                    category=Notification.Category.CONTRACT_ITEM_VALUE_REVIEWED,
                ).exists()
            )

    @patch("activity.services.SendGridClient.notify")
    def test_reallocation_approval_changes_both_items_exactly_once(self, _notify):
        value_request = self.create_reallocation_request()
        self.client.force_login(self.reviewer)
        review_url = reverse("contracts:review-value-requests", args=[value_request.id])

        response = self.client.post(
            review_url,
            {"status": "APPROVED", "rejection_reason": "Não deve persistir"},
        )

        self.assertRedirects(
            response, reverse("contracts:contracts-detail", args=[self.contract.id])
        )
        self.raise_item.refresh_from_db()
        self.downgrade_item.refresh_from_db()
        self.assertEqual(self.raise_item.month_expense, Decimal("125.00"))
        self.assertEqual(self.raise_item.anual_expense, Decimal("1500.00"))
        self.assertEqual(self.downgrade_item.month_expense, Decimal("175.00"))
        self.assertEqual(self.downgrade_item.anual_expense, Decimal("2100.00"))
        value_request.refresh_from_db()
        self.assertIsNone(value_request.rejection_reason)
        self.assertTrue(
            self.has_activity(
                "APPROVED_CONTRACT_ITEM_VALUE_REQUEST",
                value_request.id,
            )
        )
        with tenant_context(self.organization):
            self.assertTrue(
                Notification.objects.filter(
                    recipient=self.requester,
                    category=Notification.Category.CONTRACT_ITEM_VALUE_REVIEWED,
                ).exists()
            )

        repeat_response = self.client.post(
            review_url, {"status": "APPROVED", "rejection_reason": ""}
        )
        self.assertEqual(repeat_response.status_code, 404)
        self.raise_item.refresh_from_db()
        self.downgrade_item.refresh_from_db()
        self.assertEqual(self.raise_item.month_expense, Decimal("125.00"))
        self.assertEqual(self.downgrade_item.month_expense, Decimal("175.00"))

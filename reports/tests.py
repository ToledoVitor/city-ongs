"""Tests for reports/exporters/commons/integral_statement.py — the shared
revenue-summary/expense-categorization logic extracted from the RP-06/08/
10/12/14 "demonstrativo integral" exporters — plus a smoke/regression test
on one of those exporters end-to-end.

Builds a minimal fixture directly (same convention as audesp/tests.py)
rather than the full accounts.management.commands.seed_dev dev-seed, which
is for local bootstrapping, not test isolation.
"""

import datetime
from decimal import Decimal

from django.test import TestCase
from easy_tenants import tenant_context

from accountability.models import (
    Accountability,
    Expense,
    Favored,
    ResourceSource,
    Revenue,
)
from accounts.models import Area, CityHall, Organization, User
from bank.models import BankAccount
from contracts.choices import NatureChoices
from contracts.models import Company, Contract
from reports.exporters.commons.integral_statement import (
    build_revenue_summary,
    categorize_expenses,
)
from reports.exporters.pass_on_3 import PassOn3PDFExporter
from reports.exporters.pass_on_5 import PassOn5PDFExporter
from reports.exporters.pass_on_6 import PassOn6PDFExporter
from reports.exporters.pass_on_7 import PassOn7PDFExporter
from reports.exporters.pass_on_9 import PassOn9PDFExporter
from reports.exporters.pass_on_11 import PassOn11PDFExporter
from reports.exporters.pass_on_13 import PassOn13PDFExporter
from reports.exporters.pass_on_14 import PassOn14PDFExporter


class IntegralStatementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city_hall = CityHall.objects.create(
            name="Prefeitura Teste",
            document="12345678000199",
        )
        cls.organization = Organization.objects.create(
            city_hall=cls.city_hall,
            name="OSC Teste",
            document="98765432000188",
        )
        with tenant_context(cls.organization):
            cls.area = Area.objects.create(
                organization=cls.organization,
                city_hall=cls.city_hall,
                name="Assistência Social",
            )
            cls.checking_account = BankAccount.objects.create(
                organization=cls.organization,
                bank_name="Banco Teste",
                bank_id=1,
                account="123456",
                account_type=BankAccount.AccountTypeChoices.CHECKING,
            )
            cls.investing_account = BankAccount.objects.create(
                organization=cls.organization,
                bank_name="Banco Teste",
                bank_id=1,
                account="987654",
                account_type=BankAccount.AccountTypeChoices.INVESTING,
            )
            cls.contract = Contract.objects.create(
                organization=cls.organization,
                area=cls.area,
                name="Convênio Teste",
                concession_type=Contract.ConcessionChoices.MANAGEMENT,
                internal_code=1001,
                objective="Prestação de serviços de assistência social",
                bidding="Chamamento Público 01/2026",
                original_value=Decimal("120000.00"),
                total_value=Decimal("120000.00"),
                start_of_vigency=datetime.date(2026, 1, 1),
                end_of_vigency=datetime.date(2026, 12, 31),
                checking_account=cls.checking_account,
                investing_account=cls.investing_account,
            )
            cls.accountability = Accountability.objects.create(
                organization=cls.organization,
                contract=cls.contract,
                month=1,
                year=2026,
            )
            cls.resource_source = ResourceSource.objects.create(
                organization=cls.organization,
                name="Fonte Teste",
            )

            # Repasse dentro do período — mais recente.
            Revenue.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Repasse municipal",
                value=Decimal("1000.00"),
                competency=datetime.date(2026, 3, 1),
                receive_date=datetime.date(2026, 3, 10),
                bank_account=cls.checking_account,
                revenue_nature=Revenue.Nature.PUBLIC_TRANSFER,
            )
            # Repasse dentro do período — mais antigo (não deve ser o
            # "latest_pass_on_info").
            Revenue.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Repasse municipal anterior",
                value=Decimal("2000.00"),
                competency=datetime.date(2026, 1, 15),
                receive_date=datetime.date(2026, 1, 20),
                bank_account=cls.checking_account,
                revenue_nature=Revenue.Nature.PUBLIC_TRANSFER,
            )
            Revenue.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Rendimento de aplicação",
                value=Decimal("50.00"),
                competency=datetime.date(2026, 3, 5),
                receive_date=datetime.date(2026, 3, 5),
                bank_account=cls.investing_account,
                revenue_nature=Revenue.Nature.INVESTMENT_INCOME,
            )
            Revenue.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Recurso próprio",
                value=Decimal("300.00"),
                competency=datetime.date(2026, 4, 1),
                receive_date=datetime.date(2026, 4, 1),
                bank_account=cls.checking_account,
                revenue_nature=Revenue.Nature.OWN_RESOURCES,
            )
            # Fora do período pedido pelo teste — não deve entrar em nenhuma
            # soma.
            Revenue.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Repasse de outro exercício",
                value=Decimal("9999.00"),
                competency=datetime.date(2025, 3, 1),
                receive_date=datetime.date(2025, 3, 1),
                bank_account=cls.checking_account,
                revenue_nature=Revenue.Nature.PUBLIC_TRANSFER,
            )

            # Dentro do período, contabilizada e paga.
            Expense.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Folha de pagamento",
                value=Decimal("400.00"),
                source=cls.resource_source,
                nature=NatureChoices.SALARIES_AND_WAGES,
                competency=datetime.date(2026, 5, 10),
                due_date=datetime.date(2026, 5, 20),
            )
            # Fora do período — não deve entrar em nenhum total.
            Expense.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Despesa do ano passado",
                value=Decimal("999.00"),
                source=cls.resource_source,
                nature=NatureChoices.SALARIES_AND_WAGES,
                competency=datetime.date(2025, 5, 10),
                due_date=datetime.date(2025, 5, 20),
            )

        cls.start_date = datetime.datetime(2026, 1, 1)
        cls.end_date = datetime.datetime(2026, 12, 31)

    def test_build_revenue_summary_splits_by_nature(self):
        with tenant_context(self.organization):
            summary = build_revenue_summary(
                self.contract, self.start_date, self.end_date
            )

        self.assertEqual(summary.all_pass_on_values, Decimal("3350.00"))
        self.assertEqual(summary.previous_balance, Decimal("0.00"))
        self.assertEqual(summary.investment_income, Decimal("50.00"))
        self.assertEqual(summary.own_resources, Decimal("300.00"))
        self.assertEqual(summary.other_revenues_value, Decimal("0.00"))

    def test_build_revenue_summary_picks_latest_pass_on(self):
        with tenant_context(self.organization):
            summary = build_revenue_summary(
                self.contract, self.start_date, self.end_date
            )

        self.assertIsNotNone(summary.latest_pass_on_info)
        self.assertEqual(
            summary.latest_pass_on_info["receive_date"], datetime.date(2026, 3, 10)
        )

    def test_categorize_expenses_only_counts_expenses_in_period(self):
        with tenant_context(self.organization):
            categorized = categorize_expenses(
                self.contract, self.start_date, self.end_date, inclusive_bounds=False
            )

        self.assertEqual(
            categorized["HUMAN_RESOURCES"]["accounted_and_paid"], Decimal("400.00")
        )
        self.assertEqual(categorized["TOTAL"]["accounted_and_paid"], Decimal("400.00"))

    def test_categorize_expenses_inclusive_vs_exclusive_bounds(self):
        # Nenhuma despesa desta fixture cai exatamente na borda do período,
        # então os dois modos devem concordar aqui — o objetivo deste teste
        # é documentar que o parâmetro existe e não quebra, não a diferença
        # de comportamento em si (ver REPORTS_TODO.md).
        with tenant_context(self.organization):
            inclusive = categorize_expenses(
                self.contract, self.start_date, self.end_date, inclusive_bounds=True
            )
            exclusive = categorize_expenses(
                self.contract, self.start_date, self.end_date, inclusive_bounds=False
            )

        self.assertEqual(inclusive["TOTAL"], exclusive["TOTAL"])


class PassOn6PDFExporterRegressionTests(TestCase):
    """Regressão do bug corrigido em pass_on_6.py/pass_on_8.py: a soma
    "(E) Total de recursos públicos" precisa incluir o item D (outras
    receitas), não só A+B+C.
    """

    @classmethod
    def setUpTestData(cls):
        cls.city_hall = CityHall.objects.create(
            name="Prefeitura Teste RP-06",
            document="11122233000144",
        )
        cls.organization = Organization.objects.create(
            city_hall=cls.city_hall,
            name="OSC Teste RP-06",
            document="55566677000188",
        )
        with tenant_context(cls.organization):
            cls.area = Area.objects.create(
                organization=cls.organization,
                city_hall=cls.city_hall,
                name="Saúde",
            )
            cls.checking_account = BankAccount.objects.create(
                organization=cls.organization,
                bank_name="Banco Teste",
                bank_id=1,
                account="111111",
            )
            cls.hired_company = Company.objects.create(
                organization=cls.organization,
                name="Fornecedora Teste LTDA",
                cnpj="11222333000181",
            )
            cls.responsible_user = User.objects.create(
                username="responsavel@example.com",
                email="responsavel@example.com",
                organization=cls.organization,
                access_level=User.AccessChoices.MASTER,
                cpf="11111111111",
                first_name="Responsável",
                last_name="Teste",
                is_active=True,
                password_redefined=True,
            )
            cls.responsible_user.set_password("irrelevant-in-tests")
            cls.responsible_user.save()
            cls.contract = Contract.objects.create(
                organization=cls.organization,
                area=cls.area,
                name="Contrato de Gestão Teste",
                concession_type=Contract.ConcessionChoices.MANAGEMENT,
                internal_code=2001,
                objective="Gestão de equipamento de saúde",
                bidding="Chamamento Público 02/2026",
                original_value=Decimal("50000.00"),
                total_value=Decimal("50000.00"),
                start_of_vigency=datetime.date(2026, 1, 1),
                end_of_vigency=datetime.date(2026, 12, 31),
                checking_account=cls.checking_account,
                hired_company=cls.hired_company,
                accountability_autority=cls.responsible_user,
                supervision_autority=cls.responsible_user,
            )
            cls.accountability = Accountability.objects.create(
                organization=cls.organization,
                contract=cls.contract,
                month=1,
                year=2026,
            )
            Revenue.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Outras receitas da execução",
                value=Decimal("777.00"),
                competency=datetime.date(2026, 2, 1),
                receive_date=datetime.date(2026, 2, 1),
                bank_account=cls.checking_account,
                revenue_nature=Revenue.Nature.OTHER_REVENUES,
            )

    def test_sum_items_a_to_d_includes_item_d(self):
        with tenant_context(self.organization):
            exporter = PassOn6PDFExporter(
                contract=self.contract,
                start_date=datetime.datetime(2026, 1, 1),
                end_date=datetime.datetime(2026, 12, 31),
            )
            pdf = exporter.handle()

        # Regressão do bug: a soma "(E) Total" chegou a omitir o item D
        # (other_revenues_value). other_revenues_value > 0 aqui (a única
        # receita da fixture tem nature=OTHER_REVENUES), então se o bug
        # reaparecer essa comparação falha.
        self.assertGreater(exporter.other_revenues_value, Decimal("0.00"))
        self.assertEqual(
            exporter.sum_items_a_to_d,
            exporter.previous_balance
            + exporter.all_pass_on_values
            + exporter.investment_income
            + exporter.other_revenues_value,
        )
        self.assertGreater(len(bytes(pdf.output())), 0)


class CertificationTermPDFExportersTests(TestCase):
    """Smoke tests for the RP-03/05/07/09/11/13 "termo de ciência e
    notificação" exporters after the rewrite that replaced their
    byte-identical (and, for RP-03/05/07/11/13, wrongly-labeled) RP-09 body
    with `commons.certification_term.CertificationTermPDFExporter` — see
    REPORTS_TODO.md.
    """

    @classmethod
    def setUpTestData(cls):
        cls.city_hall = CityHall.objects.create(
            name="Prefeitura Teste RP-Termos",
            document="22233344000155",
            mayor="Prefeito Teste",
            position="Prefeito Municipal",
        )
        cls.organization = Organization.objects.create(
            city_hall=cls.city_hall,
            name="OSC Teste RP-Termos",
            document="66677788000199",
            owner="Dirigente Teste",
            position="Presidente",
        )
        with tenant_context(cls.organization):
            cls.area = Area.objects.create(
                organization=cls.organization,
                city_hall=cls.city_hall,
                name="Educação",
            )
            cls.hired_company = Company.objects.create(
                organization=cls.organization,
                name="OSC Contratada Teste LTDA",
                cnpj="11222333000181",
                city="São Paulo",
            )
            cls.contractor_company = Company.objects.create(
                organization=cls.organization,
                name="Prefeitura Teste RP-Termos",
                cnpj="22233344000155",
                city="São Paulo",
            )
            cls.contractor_manager = Company.objects.create(
                organization=cls.organization,
                name="Secretaria Gestora Teste",
                cnpj="33344455000122",
            )
            cls.responsible_user = User.objects.create(
                username="responsavel-termo@example.com",
                email="responsavel-termo@example.com",
                organization=cls.organization,
                access_level=User.AccessChoices.MASTER,
                cpf="22222222222",
                first_name="Responsável",
                last_name="Termo",
                position="Contador",
                is_active=True,
                password_redefined=True,
            )
            cls.responsible_user.set_password("irrelevant-in-tests")
            cls.responsible_user.save()
            cls.contract = Contract.objects.create(
                organization=cls.organization,
                area=cls.area,
                name="Termo de Colaboração Teste",
                concession_type=Contract.ConcessionChoices.COLLABORATION,
                internal_code=3001,
                objective="Educação em tempo integral",
                bidding="Chamamento Público 03/2026",
                agreement_num="12/2026",
                law_num="1234/2020",
                original_value=Decimal("80000.00"),
                total_value=Decimal("80000.00"),
                start_of_vigency=datetime.date(2026, 1, 1),
                end_of_vigency=datetime.date(2026, 12, 31),
                hired_company=cls.hired_company,
                contractor_company=cls.contractor_company,
                contractor_manager=cls.contractor_manager,
                accountability_autority=cls.responsible_user,
                supervision_autority=cls.responsible_user,
            )

        cls.start_date = datetime.datetime(2026, 1, 1)
        cls.end_date = datetime.datetime(2026, 12, 31)

    def _handle(self, exporter_class):
        with tenant_context(self.organization):
            exporter = exporter_class(
                contract=self.contract,
                start_date=self.start_date,
                end_date=self.end_date,
                responsibles=[],
            )
            return exporter.handle()

    def test_pass_on_3_renders_public_bodies_labels(self):
        pdf = self._handle(PassOn3PDFExporter)
        self.assertGreater(len(bytes(pdf.output())), 0)

    def test_pass_on_5_renders_management_contract_labels(self):
        pdf = self._handle(PassOn5PDFExporter)
        self.assertGreater(len(bytes(pdf.output())), 0)

    def test_pass_on_7_renders_partnership_term_labels(self):
        pdf = self._handle(PassOn7PDFExporter)
        self.assertGreater(len(bytes(pdf.output())), 0)

    def test_pass_on_9_renders_collaboration_term_labels(self):
        pdf = self._handle(PassOn9PDFExporter)
        self.assertGreater(len(bytes(pdf.output())), 0)

    def test_pass_on_11_renders_agreement_term_labels(self):
        pdf = self._handle(PassOn11PDFExporter)
        self.assertGreater(len(bytes(pdf.output())), 0)

    def test_pass_on_13_renders_grant_term_labels(self):
        pdf = self._handle(PassOn13PDFExporter)
        self.assertGreater(len(bytes(pdf.output())), 0)

    def test_pass_on_3_uses_contractor_company_city_for_local(self):
        # RP-03 (repasses a órgãos públicos) não tem uma OSC como
        # contraparte — LOCAL usa a cidade da `contractor_company`, não da
        # `hired_company` (usada pelos outros 5, que são todos do terceiro
        # setor). Regressão do bug de copiar o corpo do RP-09 sem adaptar a
        # fonte de dado do LOCAL.
        with tenant_context(self.organization):
            exporter = PassOn3PDFExporter(
                contract=self.contract,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            self.assertEqual(exporter._local_city(), self.contractor_company.city)


class PassOn14PDFExporterTests(TestCase):
    """Smoke test for the RP-14 rewrite — the old exporter copied the
    RP-06/08/10/12 table structure (A-G/H-I-J), which does not exist in the
    official RP-14 model; it was rewritten to the simpler RP-02-style
    structure. See REPORTS_TODO.md.
    """

    @classmethod
    def setUpTestData(cls):
        cls.city_hall = CityHall.objects.create(
            name="Prefeitura Teste RP-14",
            document="44455566000133",
        )
        cls.organization = Organization.objects.create(
            city_hall=cls.city_hall,
            name="OSC Teste RP-14",
            document="77788899000111",
            owner="Dirigente Teste RP-14",
            position="Presidente",
        )
        with tenant_context(cls.organization):
            cls.area = Area.objects.create(
                organization=cls.organization,
                city_hall=cls.city_hall,
                name="Cultura",
            )
            cls.checking_account = BankAccount.objects.create(
                organization=cls.organization,
                bank_name="Banco Teste",
                bank_id=1,
                account="222222",
            )
            cls.hired_company = Company.objects.create(
                organization=cls.organization,
                name="OSC Teste RP-14 LTDA",
                cnpj="11222333000181",
                city="São Paulo",
            )
            cls.responsible_user = User.objects.create(
                username="responsavel-rp14@example.com",
                email="responsavel-rp14@example.com",
                organization=cls.organization,
                access_level=User.AccessChoices.MASTER,
                cpf="33333333333",
                first_name="Responsável",
                last_name="RP14",
                position="Contador",
                is_active=True,
                password_redefined=True,
            )
            cls.responsible_user.set_password("irrelevant-in-tests")
            cls.responsible_user.save()
            cls.contract = Contract.objects.create(
                organization=cls.organization,
                area=cls.area,
                name="Auxílio Teste",
                concession_type=Contract.ConcessionChoices.GRANT,
                internal_code=4001,
                objective="Fomento a projetos culturais",
                bidding="Chamamento Público 04/2026",
                law_num="9999/2019",
                original_value=Decimal("30000.00"),
                total_value=Decimal("30000.00"),
                start_of_vigency=datetime.date(2026, 1, 1),
                end_of_vigency=datetime.date(2026, 12, 31),
                checking_account=cls.checking_account,
                hired_company=cls.hired_company,
                accountability_autority=cls.responsible_user,
                supervision_autority=cls.responsible_user,
            )
            cls.accountability = Accountability.objects.create(
                organization=cls.organization,
                contract=cls.contract,
                month=1,
                year=2026,
            )
            cls.resource_source = ResourceSource.objects.create(
                organization=cls.organization,
                name="Fonte Teste RP-14",
            )
            cls.favored = Favored.objects.create(
                organization=cls.organization,
                name="Fornecedor Teste RP-14",
                document="55566677000144",
            )
            Revenue.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Repasse municipal",
                value=Decimal("30000.00"),
                competency=datetime.date(2026, 2, 1),
                receive_date=datetime.date(2026, 2, 1),
                bank_account=cls.checking_account,
                revenue_nature=Revenue.Nature.PUBLIC_TRANSFER,
            )
            Expense.objects.create(
                organization=cls.organization,
                accountability=cls.accountability,
                identification="Material cultural",
                value=Decimal("5000.00"),
                source=cls.resource_source,
                favored=cls.favored,
                nature=NatureChoices.OTHER_CONSUMABLES,
                competency=datetime.date(2026, 3, 1),
                due_date=datetime.date(2026, 3, 10),
                liquidation=datetime.date(2026, 3, 10),
                paid=True,
            )

        cls.start_date = datetime.datetime(2026, 1, 1)
        cls.end_date = datetime.datetime(2026, 12, 31)

    def test_handle_renders_pdf_with_simplified_structure(self):
        with tenant_context(self.organization):
            exporter = PassOn14PDFExporter(
                contract=self.contract,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            pdf = exporter.handle()

        self.assertGreater(len(bytes(pdf.output())), 0)

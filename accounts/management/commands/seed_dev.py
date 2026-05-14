"""Idempotent dev seed.

Creates a full development scenario:
  - 3 city halls
  - 2 organizations (one with rich data, one mostly empty for cross-org tests)
  - 4 areas, 2 users, 4 companies
  - 2 contracts (one in EXECUTION with full history, one in PLANNING)
  - 2 funding sources, 3 favored payees
  - Bank accounts (checking + investing) per contract, with statements + transactions
  - Monthly accountabilities with expenses and revenues across mixed statuses

Safe to run repeatedly. Every record is keyed by a natural identifier so a
second run upserts instead of duplicating. Only runs when DEVELOPMENT=True.
"""

import datetime as dt
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_cpf_cnpj.fields import CNPJ
from easy_tenants import tenant_context

from accountability.models import (
    Accountability,
    Expense,
    Favored,
    ResourceSource,
    Revenue,
)
from accounts.models import Area, CityHall, Organization, User
from bank.models import BankAccount, BankStatement, Transaction
from contracts.choices import NatureChoices
from contracts.models import Company, Contract, ContractItem
from utils.choices import MonthChoices, StatesChoices

DEV_PASSWORD = "admin"


# ---------------------------------------------------------------------------
# Generic ensure_* helpers
# ---------------------------------------------------------------------------


def _digits(value: str | None) -> str:
    return "".join(c for c in (value or "") if c.isdigit())


def _apply_updates(instance, fields: dict) -> bool:
    changed = False
    for key, value in fields.items():
        if getattr(instance, key) != value:
            setattr(instance, key, value)
            changed = True
    return changed


def ensure_city_hall(*, name, mayor, document):
    obj, _ = CityHall.objects.get_or_create(
        document=_digits(document),
        defaults={"name": name, "mayor": mayor},
    )
    if _apply_updates(obj, {"name": name, "mayor": mayor}):
        obj.save()
    return obj


def ensure_organization(*, city_hall, name, owner, document):
    org, _ = Organization.objects.get_or_create(
        city_hall=city_hall,
        document=_digits(document),
        defaults={"name": name, "owner": owner or ""},
    )
    if _apply_updates(org, {"name": name, "owner": owner or ""}):
        org.save()
    return org


def ensure_area(*, organization, city_hall, name, description):
    area, _ = Area.objects.get_or_create(
        organization=organization,
        name=name,
        defaults={"city_hall": city_hall, "description": description},
    )
    if _apply_updates(area, {"city_hall": city_hall, "description": description}):
        area.save()
    return area


def ensure_company(organization, cnpj_digits, **fields):
    cnpj_value = CNPJ(_digits(cnpj_digits))
    with tenant_context(organization):
        company, _ = Company.objects.get_or_create(
            organization=organization,
            cnpj=cnpj_value,
            defaults=fields,
        )
        if _apply_updates(company, fields):
            company.save()
    return company


def ensure_user(
    *,
    email,
    organization,
    access_level,
    cpf,
    first_name,
    last_name,
    is_superuser,
    is_staff,
    areas,
):
    user, _ = User.objects.update_or_create(
        email=email,
        defaults={
            "username": email,
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization,
            "access_level": access_level,
            "cpf": cpf,
            "cnpj": None,
            "is_superuser": is_superuser,
            "is_staff": is_staff,
            "is_active": True,
            "deactivated_at": None,
            "password_redefined": True,
        },
    )
    user.set_password(DEV_PASSWORD)
    user.save()
    user.areas.set(areas)
    return user


def ensure_resource_source(organization, document, **fields):
    digits = _digits(document)
    with tenant_context(organization):
        source, _ = ResourceSource.objects.get_or_create(
            organization=organization,
            document=digits,
            defaults=fields,
        )
        if _apply_updates(source, fields):
            source.save()
    return source


def ensure_favored(organization, document, name):
    digits = _digits(document)
    with tenant_context(organization):
        favored, _ = Favored.objects.get_or_create(
            organization=organization,
            document=digits,
            defaults={"name": name},
        )
        if _apply_updates(favored, {"name": name}):
            favored.save()
    return favored


def ensure_contract(organization, internal_code, **fields):
    with tenant_context(organization):
        contract, _ = Contract.objects.get_or_create(
            organization=organization,
            internal_code=internal_code,
            defaults=fields,
        )
        if _apply_updates(contract, fields):
            contract.save()
    return contract


def ensure_contract_item(contract, name, **fields):
    with tenant_context(contract.organization):
        item, _ = ContractItem.objects.get_or_create(
            organization=contract.organization,
            contract=contract,
            name=name,
            defaults=fields,
        )
        if _apply_updates(item, fields):
            item.save()
    return item


def ensure_bank_account(organization, bank_name, account, account_type, **fields):
    with tenant_context(organization):
        bank_account, _ = BankAccount.objects.get_or_create(
            organization=organization,
            bank_name=bank_name,
            account=account,
            account_type=account_type,
            defaults=fields,
        )
        if _apply_updates(bank_account, fields):
            bank_account.save()
    return bank_account


def link_contract_account(contract, account, *, role):
    field = "checking_account" if role == "checking" else "investing_account"
    if getattr(contract, f"{field}_id") != account.id:
        setattr(contract, field, account)
        with tenant_context(contract.organization):
            contract.save(update_fields=[field])


def ensure_bank_statement(
    bank_account, *, reference_day, reference_month, reference_year, **fields
):
    with tenant_context(bank_account.organization):
        statement, _ = BankStatement.objects.get_or_create(
            organization=bank_account.organization,
            bank_account=bank_account,
            reference_day=reference_day,
            reference_month=reference_month,
            reference_year=reference_year,
            defaults=fields,
        )
        if _apply_updates(statement, fields):
            statement.save()
    return statement


def ensure_transaction(bank_account, *, transaction_number, memo, **fields):
    with tenant_context(bank_account.organization):
        txn, _ = Transaction.objects.get_or_create(
            organization=bank_account.organization,
            bank_account=bank_account,
            transaction_number=transaction_number,
            memo=memo,
            defaults=fields,
        )
        if _apply_updates(txn, fields):
            txn.save()
    return txn


def ensure_accountability(contract, *, month, year, **fields):
    with tenant_context(contract.organization):
        accountability, _ = Accountability.objects.get_or_create(
            organization=contract.organization,
            contract=contract,
            month=month,
            year=year,
            defaults=fields,
        )
        if _apply_updates(accountability, fields):
            accountability.save()
    return accountability


def ensure_expense(accountability, *, identification, **fields):
    with tenant_context(accountability.organization):
        expense, _ = Expense.objects.get_or_create(
            organization=accountability.organization,
            accountability=accountability,
            identification=identification,
            defaults=fields,
        )
        if _apply_updates(expense, fields):
            expense.save()
    return expense


def ensure_revenue(accountability, *, identification, **fields):
    with tenant_context(accountability.organization):
        revenue, _ = Revenue.objects.get_or_create(
            organization=accountability.organization,
            accountability=accountability,
            identification=identification,
            defaults=fields,
        )
        if _apply_updates(revenue, fields):
            revenue.save()
    return revenue


# ---------------------------------------------------------------------------
# Scenario data
# ---------------------------------------------------------------------------


def seed_contracts_and_movements(*, organization, area_primary, area_secondary):
    """Build the full execution scenario for one organization.

    Fixed dates keep re-runs identical. The reference window spans
    2026-Q1 / 2026-Q2 so accountabilities at FINISHED / SENT / WIP states
    coexist for UI walk-throughs.
    """

    # --- funding sources & payees ---------------------------------------
    src_municipal = ensure_resource_source(
        organization,
        "11222333000181",
        name="Repasse Prefeitura Várzea Paulista",
        origin=ResourceSource.OriginChoices.MUNICIPAL,
        category=ResourceSource.CategoryChoices.COLLABORATION_AGREEMENT,
        contract_number="2026-001",
    )
    src_counterpart = ensure_resource_source(
        organization,
        "39053344705",
        name="Contrapartida ONG (recursos próprios)",
        origin=ResourceSource.OriginChoices.COUNTERPART_PARTNER,
        category=ResourceSource.CategoryChoices.NOT_APPLIABLE,
        contract_number=None,
    )

    favored_clinic = ensure_favored(
        organization, "24479422000150", "Clínica Comunitária Saúde Já LTDA"
    )
    favored_supplier = ensure_favored(
        organization, "49279736000130", "Distribuidora de Insumos Cidadania ME"
    )
    favored_payroll = ensure_favored(
        organization, "21135963000172", "Folha de Pagamento — Equipe Programa Saúde"
    )

    # --- Contract A (active, with full history) -------------------------
    contract_a = ensure_contract(
        organization,
        internal_code=1001,
        name="Programa Saúde Comunitária 2026",
        concession_type=Contract.ConcessionChoices.COLLABORATION,
        code="VP-2026-001",
        objective="Atendimento ambulatorial e ações preventivas nos bairros periféricos.",
        bidding="Chamamento Público 003/2025",
        law_num="Lei Municipal 4.812/2025",
        law_date=dt.date(2025, 11, 12),
        agreement_num="Convênio 2026/001",
        agreement_date=dt.date(2025, 12, 18),
        original_value=Decimal("600000.00"),
        total_value=Decimal("660000.00"),
        municipal_value=Decimal("600000.00"),
        counterpart_value=Decimal("60000.00"),
        start_of_vigency=dt.date(2026, 1, 1),
        end_of_vigency=dt.date(2026, 12, 31),
        status=Contract.ContractStatusChoices.EXECUTION,
        area=area_primary,
    )

    ensure_contract_item(
        contract_a,
        "Equipe técnica de saúde",
        source=ContractItem.ResourceSource.CITY_HALL,
        objective="Salários e encargos da equipe assistencial.",
        methodology="Folha mensal processada pela ONG.",
        month_quantity=12,
        month_expense=Decimal("32000.00"),
        anual_expense=Decimal("384000.00"),
        quantity=1,
        unit_type="equipe",
        nature=NatureChoices.SALARIES_AND_WAGES,
        start_date=dt.date(2026, 1, 1),
        end_date=dt.date(2026, 12, 31),
        is_additive=False,
    )
    ensure_contract_item(
        contract_a,
        "Insumos e materiais ambulatoriais",
        source=ContractItem.ResourceSource.CITY_HALL,
        objective="Compra mensal de insumos de consumo.",
        methodology="Pregão eletrônico, entregas mensais.",
        month_quantity=12,
        month_expense=Decimal("8500.00"),
        anual_expense=Decimal("102000.00"),
        quantity=1,
        unit_type="lote",
        nature=NatureChoices.OTHER_CONSUMABLES,
        start_date=dt.date(2026, 1, 1),
        end_date=dt.date(2026, 12, 31),
        is_additive=False,
    )
    ensure_contract_item(
        contract_a,
        "Aluguel e utilidades da unidade",
        source=ContractItem.ResourceSource.COUNTERPART,
        objective="Custos fixos do imóvel utilizado pelo programa.",
        methodology="Pagamento mensal direto ao locador.",
        month_quantity=12,
        month_expense=Decimal("5000.00"),
        anual_expense=Decimal("60000.00"),
        quantity=1,
        unit_type="imóvel",
        nature=NatureChoices.REAL_ESTATE_LEASE,
        start_date=dt.date(2026, 1, 1),
        end_date=dt.date(2026, 12, 31),
        is_additive=False,
    )

    # --- Contract B (planning only, no movements yet) -------------------
    contract_b = ensure_contract(
        organization,
        internal_code=1002,
        name="Cultura no Bairro 2026/2027",
        concession_type=Contract.ConcessionChoices.PARTNERSHIP,
        code="VP-2026-002",
        objective="Oficinas culturais e formação artística para jovens.",
        bidding="Chamamento Público 008/2026",
        law_num=None,
        law_date=None,
        agreement_num=None,
        agreement_date=None,
        original_value=Decimal("240000.00"),
        total_value=Decimal("240000.00"),
        municipal_value=Decimal("240000.00"),
        counterpart_value=Decimal("0.00"),
        start_of_vigency=dt.date(2026, 6, 1),
        end_of_vigency=dt.date(2027, 5, 31),
        status=Contract.ContractStatusChoices.PLANNING,
        area=area_secondary,
    )

    # --- bank accounts ---------------------------------------------------
    checking_a = ensure_bank_account(
        organization,
        bank_name="Banco do Brasil",
        account="123456",
        account_type=BankAccount.AccountTypeChoices.CHECKING,
        bank_id=1,
        agency="3201",
        opening_balance=Decimal("50000.00"),
        origin=BankAccount.OriginChoices.MUNICIPAL,
    )
    investing_a = ensure_bank_account(
        organization,
        bank_name="Banco do Brasil",
        account="123456001",
        account_type=BankAccount.AccountTypeChoices.INVESTING,
        bank_id=1,
        agency="3201",
        opening_balance=Decimal("10000.00"),
        origin=BankAccount.OriginChoices.MUNICIPAL,
    )
    checking_b = ensure_bank_account(
        organization,
        bank_name="Itaú",
        account="987654",
        account_type=BankAccount.AccountTypeChoices.CHECKING,
        bank_id=341,
        agency="0182",
        opening_balance=Decimal("0.00"),
        origin=BankAccount.OriginChoices.MUNICIPAL,
    )

    link_contract_account(contract_a, checking_a, role="checking")
    link_contract_account(contract_a, investing_a, role="investing")
    link_contract_account(contract_b, checking_b, role="checking")

    # --- transactions on the active contract's checking account ---------
    # Pattern: monthly municipal transfer + recurring outflows for 3 months.
    months = [(2026, 2), (2026, 3), (2026, 4)]
    for year, month in months:
        ensure_transaction(
            checking_a,
            transaction_number=f"VP{year}{month:02d}001",
            memo="Repasse municipal mensal",
            amount=Decimal("55000.00"),
            date=dt.date(year, month, 5),
            transaction_type=Transaction.TransactionTypeChoices.CREDIT,
            name="Repasse Prefeitura",
        )
        ensure_transaction(
            checking_a,
            transaction_number=f"VP{year}{month:02d}010",
            memo="Folha de pagamento",
            amount=Decimal("-32000.00"),
            date=dt.date(year, month, 7),
            transaction_type=Transaction.TransactionTypeChoices.PAYMENT,
            name="Folha — equipe técnica",
        )
        ensure_transaction(
            checking_a,
            transaction_number=f"VP{year}{month:02d}020",
            memo="Compra de insumos",
            amount=Decimal("-8500.00"),
            date=dt.date(year, month, 12),
            transaction_type=Transaction.TransactionTypeChoices.PAYMENT,
            name="Insumos ambulatoriais",
        )
        ensure_transaction(
            checking_a,
            transaction_number=f"VP{year}{month:02d}030",
            memo="Aluguel da unidade",
            amount=Decimal("-5000.00"),
            date=dt.date(year, month, 15),
            transaction_type=Transaction.TransactionTypeChoices.PAYMENT,
            name="Aluguel imóvel sede",
        )
        ensure_transaction(
            checking_a,
            transaction_number=f"VP{year}{month:02d}040",
            memo="Tarifa bancária",
            amount=Decimal("-45.00"),
            date=dt.date(year, month, 28),
            transaction_type=Transaction.TransactionTypeChoices.FEE,
            name="Tarifa de manutenção",
        )

    # Statement snapshots aligned with the bank's reported closing balance.
    # checking_a: opening 50k; per month net = +55000 -32000 -8500 -5000 -45 = +9455
    # Statements are reconciliation anchors only — current_balance is derived.
    closing_balances = {
        (2026, 2): Decimal("59455.00"),
        (2026, 3): Decimal("68910.00"),
        (2026, 4): Decimal("78365.00"),
    }
    previous_close = Decimal("50000.00")
    for (year, month), closing in closing_balances.items():
        last_day = (
            dt.date(year + (month // 12), (month % 12) + 1, 1) - dt.timedelta(days=1)
        ).day
        ensure_bank_statement(
            checking_a,
            reference_day=last_day,
            reference_month=month,
            reference_year=year,
            opening_balance=previous_close,
            closing_balance=closing,
        )
        previous_close = closing

    # investing_a: two monthly yield credits.
    for (year, month), yield_value in [
        ((2026, 3), Decimal("85.50")),
        ((2026, 4), Decimal("91.20")),
    ]:
        ensure_transaction(
            investing_a,
            transaction_number=f"INV{year}{month:02d}",
            memo="Rendimento aplicação",
            amount=yield_value,
            date=dt.date(year, month, 30),
            transaction_type=Transaction.TransactionTypeChoices.INCOME,
            name="Rendimento mensal",
        )

    # --- accountabilities: Feb (FINISHED), Mar (SENT), Apr (WIP) --------
    accountability_states = [
        (2, "FEB", Accountability.ReviewStatus.FINISHED),
        (3, "MAR", Accountability.ReviewStatus.SENT),
        (4, "APR", Accountability.ReviewStatus.WIP),
    ]

    expense_statuses_by_state = {
        Accountability.ReviewStatus.FINISHED: Expense.ReviewStatus.APPROVED,
        Accountability.ReviewStatus.SENT: Expense.ReviewStatus.IN_ANALISIS,
        Accountability.ReviewStatus.WIP: Expense.ReviewStatus.IN_ANALISIS,
    }

    for month, _name, acc_status in accountability_states:
        accountability = ensure_accountability(
            contract_a,
            month=getattr(MonthChoices, _name),
            year=2026,
            status=acc_status,
        )
        competency = dt.date(2026, month, 1)
        expense_status = expense_statuses_by_state[acc_status]
        paid = acc_status != Accountability.ReviewStatus.WIP

        ensure_expense(
            accountability,
            identification=f"Folha equipe técnica {month:02d}/2026",
            status=expense_status,
            paid=paid,
            conciled=paid,
            planned=True,
            observations="Folha mensal da equipe assistencial.",
            value=Decimal("32000.00"),
            source=src_municipal,
            favored=favored_payroll,
            nature=NatureChoices.SALARIES_AND_WAGES,
            due_date=dt.date(2026, month, 5),
            competency=competency,
            liquidation=dt.date(2026, month, 7) if paid else None,
            liquidation_form=Expense.LiquidationChoices.ELETRONIC_TRANSFER,
            document_type=Expense.DocumentChoices.PAYSLIP,
            document_number=f"FP-{2026}-{month:02d}",
        )
        ensure_expense(
            accountability,
            identification=f"Insumos ambulatoriais {month:02d}/2026",
            status=expense_status,
            paid=paid,
            conciled=paid,
            planned=True,
            observations="Compra mensal recorrente.",
            value=Decimal("8500.00"),
            source=src_municipal,
            favored=favored_supplier,
            nature=NatureChoices.OTHER_CONSUMABLES,
            due_date=dt.date(2026, month, 10),
            competency=competency,
            liquidation=dt.date(2026, month, 12) if paid else None,
            liquidation_form=Expense.LiquidationChoices.ELETRONIC_TRANSFER,
            document_type=Expense.DocumentChoices.NFE,
            document_number=f"NFE-{2026}-{month:02d}-001",
        )
        ensure_expense(
            accountability,
            identification=f"Aluguel unidade {month:02d}/2026",
            status=expense_status,
            paid=paid,
            conciled=paid,
            planned=True,
            observations="Custo fixo via contrapartida.",
            value=Decimal("5000.00"),
            source=src_counterpart,
            favored=favored_clinic,
            nature=NatureChoices.REAL_ESTATE_LEASE,
            due_date=dt.date(2026, month, 15),
            competency=competency,
            liquidation=dt.date(2026, month, 15) if paid else None,
            liquidation_form=Expense.LiquidationChoices.ELETRONIC_TRANSFER,
            document_type=Expense.DocumentChoices.RECEIPT,
            document_number=f"REC-{2026}-{month:02d}",
        )

        ensure_revenue(
            accountability,
            identification=f"Repasse municipal {month:02d}/2026",
            status=(
                Revenue.ReviewStatus.APPROVED
                if acc_status == Accountability.ReviewStatus.FINISHED
                else Revenue.ReviewStatus.IN_ANALISIS
            ),
            paid=True,
            conciled=True,
            observations="Crédito da prefeitura na conta corrente.",
            value=Decimal("55000.00"),
            competency=competency,
            receive_date=dt.date(2026, month, 5),
            source=Revenue.RevenueSource.CITY_HALL,
            bank_account=checking_a,
            revenue_nature=Revenue.Nature.PUBLIC_TRANSFER,
        )

    return {
        "contracts": [contract_a, contract_b],
        "bank_accounts": [checking_a, investing_a, checking_b],
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@transaction.atomic
def run_seed():
    varzea = ensure_city_hall(
        name="Prefeitura Municipal de Várzea Paulista",
        mayor="Jorge Prefeito",
        document="11222333000181",
    )
    ensure_city_hall(
        name="Prefeitura Municipal de Campo Limpo Paulista",
        mayor="João Prefeito",
        document="60701190000104",
    )
    ensure_city_hall(
        name="Prefeitura Municipal de Jundiaí",
        mayor="José Prefeito",
        document="00000000000191",
    )

    org_primary = ensure_organization(
        city_hall=varzea,
        name="ONG Contabilidade Vitor Toledo",
        owner="Marcos Dono",
        document="52998224725",
    )
    org_secondary = ensure_organization(
        city_hall=varzea,
        name="Fundação Social de Desenvolvimento Social",
        owner="Matheus Dono",
        document="39053344705",
    )

    a1 = ensure_area(
        organization=org_primary,
        city_hall=varzea,
        name="Desenvolvimento social",
        description="Desenvolvimento social",
    )
    a2 = ensure_area(
        organization=org_primary,
        city_hall=varzea,
        name="Desenvolvimento econômico",
        description="Desenvolvimento econômico",
    )
    a3 = ensure_area(
        organization=org_primary,
        city_hall=varzea,
        name="Gestão e Fiscalização",
        description="Gestão e Fiscalização",
    )
    ensure_area(
        organization=org_secondary,
        city_hall=varzea,
        name="Projetos transversais",
        description="Áreas compartilhadas entre programas",
    )

    primary_areas = [a1, a2, a3]

    ensure_user(
        email="admin@admin.com",
        organization=org_primary,
        access_level=User.AccessChoices.MASTER,
        cpf="85351346893",
        first_name="Admin",
        last_name="Master",
        is_superuser=True,
        is_staff=True,
        areas=primary_areas,
    )
    ensure_user(
        email="contador@dev.local",
        organization=org_primary,
        access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT,
        cpf="11144477735",
        first_name="Ana",
        last_name="Contadora",
        is_superuser=False,
        is_staff=False,
        areas=[a1, a2],
    )

    ensure_company(
        org_primary,
        "24479422000150",
        name="Empresa Contratante",
        street="Rua Fausto Silveira Pires",
        number=93,
        complement=None,
        district="Jardim Primavera",
        city="Várzea Paulista",
        uf=StatesChoices.SP,
        postal_code="13220270",
    )
    ensure_company(
        org_primary,
        "49279736000130",
        name="Empresa Contratada",
        street="Rua Senador Vergueiro",
        number=250,
        complement="Apto 305",
        district="Flamengo",
        city="Rio de Janeiro",
        uf=StatesChoices.RJ,
        postal_code="22220000",
    )
    ensure_company(
        org_primary,
        "21135963000172",
        name="Software Vitor Toledo S.A.",
        street="Rua Xavier da Silveira",
        number=29,
        complement="Apto 901",
        district="Copacabana",
        city="Rio de Janeiro",
        uf=StatesChoices.RJ,
        postal_code="22061010",
    )
    ensure_company(
        org_primary,
        "98521329000100",
        name="Empresa Teste",
        street="Rua Testes",
        number=100,
        complement="Bloco B",
        district="Jardim Testes",
        city="Testópolis",
        uf=StatesChoices.GO,
        postal_code="11110000",
    )

    scenario = seed_contracts_and_movements(
        organization=org_primary,
        area_primary=a1,
        area_secondary=a2,
    )

    return {
        "logins": [
            ("admin@admin.com", User.AccessChoices.MASTER, True),
            ("contador@dev.local", User.AccessChoices.ORGANIZATION_ACCOUNTANT, False),
        ],
        "scenario": scenario,
    }


class Command(BaseCommand):
    help = (
        "Idempotent dev seed: cria prefeituras, organizações, empresas, contratos, "
        "contas bancárias, transações e prestações de contas para um cenário completo."
    )

    def handle(self, *args, **options):
        if not getattr(settings, "DEVELOPMENT", False):
            raise CommandError("Este comando só roda com DEVELOPMENT=true.")

        result = run_seed()
        self.stdout.write(self.style.SUCCESS("Seed concluído."))
        self.stdout.write(f"Senha dev: {DEV_PASSWORD!r}")
        for email, level, staff in result["logins"]:
            self.stdout.write(f"  {email}  access={level}  staff={staff}")

        scenario = result["scenario"]
        self.stdout.write("")
        self.stdout.write("Cenário criado:")
        for contract in scenario["contracts"]:
            self.stdout.write(
                f"  contrato {contract.internal_code}: {contract.name} "
                f"[{contract.get_status_display()}]"
            )
        for account in scenario["bank_accounts"]:
            self.stdout.write(
                f"  conta {account.bank_name} {account.account} "
                f"({account.get_account_type_display()}) "
                f"saldo abertura={account.opening_balance}"
            )

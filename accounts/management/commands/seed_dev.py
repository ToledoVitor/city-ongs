"""Idempotent dev seed.

Creates a full development scenario:
  - 3 city halls
  - 2 organizations (one with rich data, one mostly empty for cross-org tests)
  - 4 areas, 4 users (incl. 2 gestores de pasta), 6 companies
  - 2 contracts (one in EXECUTION with full history, one in PLANNING)
  - 2 funding sources, 3 favored payees
  - Bank accounts (checking + investing) per contract, with statements + transactions
  - Monthly accountabilities with expenses and revenues across mixed statuses
  - AUDESP Fase V fixtures: org-wide Employee/CededServant rolls (manual
    §5/§13) and one ajuste contract per Contract.ConcessionChoices (5 total,
    covering every Fase V ajuste type: Contrato de Gestão, Convênio, Termo de
    Colaboração, Termo de Fomento, Termo de Parceria — the last two reuse the
    contracts from the base scenario above). Each carries the AUDESP
    structural rows every builder needs: audesp_agreement_code, a
    SupplierContract, an Asset, all 8 CertificateReference types, and an
    AnnualStatement plus the satellite rows its ajuste type reads (see
    audesp/builders/common.py + the matching audesp/builders/<tipo>.py). The
    Convênio contract is additionally run through the real
    audesp.builders.convenio.build_payload / audesp.validators.validate_payload
    pipeline and recorded as an AudespSubmission — a smoke test that the
    seeded data actually clears the AUDESP builder, not just sits in the DB.

Safe to run repeatedly. Every record is keyed by a natural identifier so a
second run upserts instead of duplicating. Only runs when DEVELOPMENT=True.

Also seeds one AudespCredential registry row (PILOTO environment) for the
primary city hall — it carries no real secret (see audesp/secrets.py:
local dev resolves the actual username/password from .env, not from this
DB row), it just marks that city hall as AUDESP-configured.
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
    ActivityReportPublication,
    ActivityReportPublicationStatus,
    AnnualStatement,
    ConclusiveOpinion,
    ConclusiveOpinionDeclaration,
    ConflictOfInterestDeclaration,
    EvaluationReport,
    Expense,
    Favored,
    FinancialStatements,
    FinancialStatementsPublication,
    OpinionOrMinutes,
    OpinionOrMinutesPublication,
    PhysicalFinancialExecutionStatement,
    PhysicalFinancialExecutionStatementPublication,
    PurchasingRegulation,
    PurchasingRegulationPublication,
    ResourceSource,
    Revenue,
)
from accounts.models import (
    Area,
    CededServant,
    CededServantRemunerationPeriod,
    CityHall,
    Employee,
    EmployeeRemunerationPeriod,
    Organization,
    User,
)
from audesp import services as audesp_services
from audesp.models import AudespCredential, AudespSubmission
from bank.models import BankAccount, BankStatement, Transaction
from contracts.choices import (
    AudespDocumentTypeChoices,
    AudespPublicationVehicleChoices,
    NatureChoices,
)
from contracts.models import (
    Asset,
    CertificateReference,
    Company,
    Contract,
    ContractItem,
    SupplierContract,
)
from transparency_portal.models import TransparencyChecklist
from utils.choices import MonthChoices, StatesChoices

DEV_PASSWORD = "admin"
AUDESP_FISCAL_YEAR = 2026


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


def ensure_city_hall(*, name, mayor, document, audesp_municipality_code=None):
    obj, _ = CityHall.objects.get_or_create(
        document=_digits(document),
        defaults={
            "name": name,
            "mayor": mayor,
            "audesp_municipality_code": audesp_municipality_code,
        },
    )
    fields = {"name": name, "mayor": mayor}
    if audesp_municipality_code is not None:
        fields["audesp_municipality_code"] = audesp_municipality_code
    if _apply_updates(obj, fields):
        obj.save()
    return obj


def ensure_organization(*, city_hall, name, owner, document, audesp_entity_code=None):
    org, _ = Organization.objects.get_or_create(
        city_hall=city_hall,
        document=_digits(document),
        defaults={
            "name": name,
            "owner": owner or "",
            "audesp_entity_code": audesp_entity_code,
        },
    )
    fields = {"name": name, "owner": owner or ""}
    if audesp_entity_code is not None:
        fields["audesp_entity_code"] = audesp_entity_code
    if _apply_updates(org, fields):
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


def ensure_contract_parties(organization):
    """The four Company rows every seeded contract points at.

    A contract renders four parties (see contracts/tabs/details-tab.html): the
    two sides of the agreement and the managing folder on each side. All four
    are nullable FKs to Company, so leaving them unset produces a contract list
    where "Gestora contratante" and "Gestora contratada" render blank.

    Idempotent via ensure_company, so this is safe to call from every seed
    function that creates contracts.
    """
    return {
        "contractor_company": ensure_company(
            organization,
            "24479422000150",
            name="Empresa Contratante",
        ),
        "contractor_manager": ensure_company(
            organization,
            "11222333000181",
            name="Secretaria Municipal de Gestão",
            street="Praça São Judas Tadeu",
            number=10,
            district="Centro",
            city="Várzea Paulista",
            uf=StatesChoices.SP,
            postal_code="13220000",
        ),
        "hired_company": ensure_company(
            organization,
            "49279736000130",
            name="Empresa Contratada",
        ),
        "hired_manager": ensure_company(
            organization,
            "33444555000181",
            name="Instituto Gestor Cidadania",
            street="Avenida Paulista",
            number=1578,
            district="Bela Vista",
            city="São Paulo",
            uf=StatesChoices.SP,
            postal_code="01310200",
        ),
    }


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
# AUDESP Fase V ensure_* helpers
# ---------------------------------------------------------------------------
# Org-wide rolls (manual §5 "Relação de Empregados", §13 "Servidores Cedidos")
# --------------------------------------------------------------------------


def ensure_employee(organization, cpf, admission_date, **fields):
    with tenant_context(organization):
        employee, _ = Employee.objects.get_or_create(
            organization=organization,
            cpf=_digits(cpf),
            admission_date=admission_date,
            defaults=fields,
        )
        if _apply_updates(employee, fields):
            employee.save()
    return employee


def ensure_employee_remuneration_period(employee, *, year, month, **fields):
    with tenant_context(employee.organization):
        period, _ = EmployeeRemunerationPeriod.objects.get_or_create(
            organization=employee.organization,
            employee=employee,
            year=year,
            month=month,
            defaults=fields,
        )
        if _apply_updates(period, fields):
            period.save()
    return period


def ensure_ceded_servant(organization, cpf, cession_start_date, **fields):
    with tenant_context(organization):
        servant, _ = CededServant.objects.get_or_create(
            organization=organization,
            cpf=_digits(cpf),
            cession_start_date=cession_start_date,
            defaults=fields,
        )
        if _apply_updates(servant, fields):
            servant.save()
    return servant


def ensure_ceded_servant_remuneration_period(servant, *, year, month, **fields):
    with tenant_context(servant.organization):
        period, _ = CededServantRemunerationPeriod.objects.get_or_create(
            organization=servant.organization,
            servant=servant,
            year=year,
            month=month,
            defaults=fields,
        )
        if _apply_updates(period, fields):
            period.save()
    return period


# --------------------------------------------------------------------------
# Per-ajuste structural rows (manual §6 "Bens", §7 "Contratos", §20/§21
# "Certidões") — every Fase V builder reads these off the ajuste `Contract`
# itself, regardless of ajuste type.
# --------------------------------------------------------------------------


def ensure_supplier_contract(
    contract,
    number,
    *,
    signature_date,
    creditor_document_type,
    creditor_document_number,
    **fields,
):
    with tenant_context(contract.organization):
        supplier_contract, _ = SupplierContract.objects.get_or_create(
            organization=contract.organization,
            contract=contract,
            number=number,
            signature_date=signature_date,
            creditor_document_type=creditor_document_type,
            creditor_document_number=_digits(creditor_document_number),
            defaults=fields,
        )
        if _apply_updates(supplier_contract, fields):
            supplier_contract.save()
    return supplier_contract


def ensure_asset(contract, *, category, event, description, date, **fields):
    with tenant_context(contract.organization):
        asset, _ = Asset.objects.get_or_create(
            organization=contract.organization,
            contract=contract,
            category=category,
            event=event,
            description=description,
            date=date,
            defaults=fields,
        )
        if _apply_updates(asset, fields):
            asset.save()
    return asset


def ensure_certificate_reference(contract, cert_type, identification):
    with tenant_context(contract.organization):
        reference, _ = CertificateReference.objects.get_or_create(
            organization=contract.organization,
            contract=contract,
            type=cert_type,
            defaults={"identification": identification},
        )
        if _apply_updates(reference, {"identification": identification}):
            reference.save()
    return reference


# --------------------------------------------------------------------------
# Annual statement (manual §32) + its satellite blocks. All of these hang
# off one (contract, fiscal_year) AnnualStatement — see
# audesp/builders/common.py for exactly which blocks each ajuste type reads.
# --------------------------------------------------------------------------


def ensure_annual_statement(contract, *, fiscal_year, **fields):
    with tenant_context(contract.organization):
        statement, _ = AnnualStatement.objects.get_or_create(
            organization=contract.organization,
            contract=contract,
            fiscal_year=fiscal_year,
            defaults=fields,
        )
        if _apply_updates(statement, fields):
            statement.save()
    return statement


def ensure_conflict_of_interest_declaration(annual_statement, **fields):
    with tenant_context(annual_statement.organization):
        declaration, _ = ConflictOfInterestDeclaration.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            defaults=fields,
        )
        if _apply_updates(declaration, fields):
            declaration.save()
    return declaration


def ensure_evaluation_report(annual_statement, report_type, **fields):
    with tenant_context(annual_statement.organization):
        report, _ = EvaluationReport.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            type=report_type,
            defaults=fields,
        )
        if _apply_updates(report, fields):
            report.save()
    return report


def ensure_financial_statements(annual_statement, **fields):
    with tenant_context(annual_statement.organization):
        statements, _ = FinancialStatements.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            defaults=fields,
        )
        if _apply_updates(statements, fields):
            statements.save()
    return statements


def ensure_financial_statements_publication(
    financial_statement, *, publication_vehicle_type, publication_date, **fields
):
    with tenant_context(financial_statement.organization):
        publication, _ = FinancialStatementsPublication.objects.get_or_create(
            organization=financial_statement.organization,
            financial_statement=financial_statement,
            publication_vehicle_type=publication_vehicle_type,
            publication_date=publication_date,
            defaults=fields,
        )
        if _apply_updates(publication, fields):
            publication.save()
    return publication


def ensure_opinion_or_minutes(annual_statement, opinion_type, **fields):
    with tenant_context(annual_statement.organization):
        opinion, _ = OpinionOrMinutes.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            type=opinion_type,
            defaults=fields,
        )
        if _apply_updates(opinion, fields):
            opinion.save()
    return opinion


def ensure_opinion_or_minutes_publication(
    opinion_or_minutes, *, publication_vehicle_type, publication_date, **fields
):
    with tenant_context(opinion_or_minutes.organization):
        publication, _ = OpinionOrMinutesPublication.objects.get_or_create(
            organization=opinion_or_minutes.organization,
            opinion_or_minutes=opinion_or_minutes,
            publication_vehicle_type=publication_vehicle_type,
            publication_date=publication_date,
            defaults=fields,
        )
        if _apply_updates(publication, fields):
            publication.save()
    return publication


def ensure_conclusive_opinion(annual_statement, *, conclusion, **fields):
    with tenant_context(annual_statement.organization):
        opinion, _ = ConclusiveOpinion.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            defaults={"conclusion": conclusion, **fields},
        )
        if _apply_updates(opinion, {"conclusion": conclusion, **fields}):
            opinion.save()
    return opinion


def ensure_conclusive_opinion_declaration(
    conclusive_opinion, declaration_type, answer, **fields
):
    with tenant_context(conclusive_opinion.organization):
        declaration, _ = ConclusiveOpinionDeclaration.objects.get_or_create(
            organization=conclusive_opinion.organization,
            conclusive_opinion=conclusive_opinion,
            declaration_type=declaration_type,
            defaults={"answer": answer, **fields},
        )
        if _apply_updates(declaration, {"answer": answer, **fields}):
            declaration.save()
    return declaration


def ensure_transparency_checklist(annual_statement, **fields):
    # TransparencyChecklist extends plain BaseModel (not
    # BaseOrganizationTenantModel) — it isn't tenant-scoped itself, only
    # reachable via annual_statement.contract.organization, so no
    # tenant_context wrap is needed for this get_or_create/save.
    checklist, _ = TransparencyChecklist.objects.get_or_create(
        annual_statement=annual_statement,
        defaults=fields,
    )
    if _apply_updates(checklist, fields):
        checklist.save()
    return checklist


# --- Contrato de Gestão only (manual §22, §30) -----------------------------


def ensure_purchasing_regulation(annual_statement, **fields):
    with tenant_context(annual_statement.organization):
        regulation, _ = PurchasingRegulation.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            defaults=fields,
        )
        if _apply_updates(regulation, fields):
            regulation.save()
    return regulation


def ensure_purchasing_regulation_publication(
    regulation, *, phase, publication_vehicle_type, publication_date, **fields
):
    with tenant_context(regulation.organization):
        publication, _ = PurchasingRegulationPublication.objects.get_or_create(
            organization=regulation.organization,
            regulation=regulation,
            phase=phase,
            publication_vehicle_type=publication_vehicle_type,
            publication_date=publication_date,
            defaults=fields,
        )
        if _apply_updates(publication, fields):
            publication.save()
    return publication


def ensure_activity_report_publication_status(annual_statement, **fields):
    with tenant_context(annual_statement.organization):
        status, _ = ActivityReportPublicationStatus.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            defaults=fields,
        )
        if _apply_updates(status, fields):
            status.save()
    return status


def ensure_activity_report_publication(
    publication_status, *, publication_vehicle_type, publication_date, **fields
):
    with tenant_context(publication_status.organization):
        publication, _ = ActivityReportPublication.objects.get_or_create(
            organization=publication_status.organization,
            publication_status=publication_status,
            publication_vehicle_type=publication_vehicle_type,
            publication_date=publication_date,
            defaults=fields,
        )
        if _apply_updates(publication, fields):
            publication.save()
    return publication


# --- Termo de Parceria only (manual §23) -----------------------------------


def ensure_physical_financial_execution_statement(annual_statement, **fields):
    with tenant_context(annual_statement.organization):
        statement, _ = PhysicalFinancialExecutionStatement.objects.get_or_create(
            organization=annual_statement.organization,
            annual_statement=annual_statement,
            defaults=fields,
        )
        if _apply_updates(statement, fields):
            statement.save()
    return statement


def ensure_physical_financial_execution_statement_publication(
    statement, *, publication_vehicle_type, publication_date, **fields
):
    with tenant_context(statement.organization):
        publication, _ = (
            PhysicalFinancialExecutionStatementPublication.objects.get_or_create(
                organization=statement.organization,
                statement=statement,
                publication_vehicle_type=publication_vehicle_type,
                publication_date=publication_date,
                defaults=fields,
            )
        )
        if _apply_updates(publication, fields):
            publication.save()
    return publication


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

    parties = ensure_contract_parties(organization)

    # --- Contract A (active, with full history) -------------------------
    contract_a = ensure_contract(
        organization,
        **parties,
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
        **parties,
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
# AUDESP Fase V scenario
# ---------------------------------------------------------------------------
# Covers every Fase V ajuste type (Contrato de Gestão, Convênio, Termo de
# Colaboração, Termo de Fomento, Termo de Parceria) by pairing one contract
# per contracts.Contract.ConcessionChoices with the structural rows its
# builder needs. Termo de Colaboração / Termo de Parceria reuse contract_a /
# contract_b from seed_contracts_and_movements() above (extended in place);
# the other 3 ajuste types get a dedicated new contract each.


def _audesp_agreement_code(internal_code, fiscal_year=AUDESP_FISCAL_YEAR):
    """A 19-digit codigo_ajuste (schema pattern ^[0-9]{15,19}$), distinct per
    contract and stable across reseeds."""
    return f"{fiscal_year}{internal_code:015d}"


def seed_audesp_org_wide_rolls(organization):
    """AUDESP manual §5 "Relação de Empregados" + §13 "Servidores Cedidos" —
    scoped to the organization, not to any single ajuste contract, so every
    ajuste type's builder sees the same roll for a given fiscal year."""
    employees = [
        ensure_employee(
            organization,
            "36452506706",
            dt.date(2020, 3, 1),
            cbo="223405",
            contractual_salary=Decimal("4200.00"),
        ),
        ensure_employee(
            organization,
            "70269412085",
            dt.date(2022, 7, 15),
            cbo="513205",
            contractual_salary=Decimal("2400.00"),
        ),
    ]
    for employee in employees:
        for month in range(1, 13):
            ensure_employee_remuneration_period(
                employee,
                year=AUDESP_FISCAL_YEAR,
                month=month,
                hours_worked=Decimal("220.00"),
                gross_remuneration=employee.contractual_salary,
            )

    servant = ensure_ceded_servant(
        organization,
        "80243776080",
        dt.date(2025, 2, 1),
        public_position_held="Analista Administrativo",
        role_performed="Coordenação Financeira",
        payment_burden=CededServant.PaymentBurdenChoices.GRANTING_AGENCY,
    )
    for month in range(1, 13):
        ensure_ceded_servant_remuneration_period(
            servant,
            year=AUDESP_FISCAL_YEAR,
            month=month,
            hours_worked=Decimal("160.00"),
            gross_remuneration=Decimal("5800.00"),
        )

    return {"employees": employees, "ceded_servants": [servant]}


def seed_audesp_structural_fixtures(contract, *, supplier_number, asset_description):
    """Seeds the (contract, fiscal_year)-independent Fase V structural rows
    every ajuste-type builder reads via audesp/builders/common.py:
    build_contratos (manual §7), build_relacao_bens (manual §6) and
    build_dados_gerais/build_responsaveis_orgao (manual §20/§21)."""
    ensure_supplier_contract(
        contract,
        supplier_number,
        signature_date=contract.start_of_vigency,
        creditor_document_type=AudespDocumentTypeChoices.CNPJ,
        creditor_document_number="49279736000130",
        validity_type=SupplierContract.ValidityTypeChoices.INDETERMINATE,
        validity_start_date=contract.start_of_vigency,
        purpose="Fornecimento de insumos e serviços de apoio à execução do ajuste.",
        contracting_nature=[4],
        selection_criteria=SupplierContract.SelectionCriteriaChoices.WAIVER,
        amount=Decimal("36000.00"),
        value_type=SupplierContract.ValueTypeChoices.GLOBAL,
    )
    ensure_asset(
        contract,
        category=Asset.CategoryChoices.MOVABLE,
        event=Asset.EventChoices.ACQUIRED,
        description=asset_description,
        date=contract.start_of_vigency,
        asset_number=f"PAT-{contract.internal_code}",
        value=Decimal("4200.00"),
    )
    for index, cert_type in enumerate(CertificateReference.TypeChoices.values, start=1):
        identification = f"{contract.internal_code:04d}{index:02d}0000"
        ensure_certificate_reference(contract, cert_type, identification)


def seed_audesp_annual_statement(
    contract,
    *,
    fiscal_year,
    evaluation_report_type=None,
    include_purchasing_regulation=False,
    include_activity_report_publication=False,
    include_execution_statement=False,
):
    """Seeds one contract's AnnualStatement (manual §32) plus every satellite
    block common to all 5 ajuste types (ConflictOfInterestDeclaration,
    FinancialStatements, OpinionOrMinutes, ConclusiveOpinion + its 7
    declaration types, TransparencyChecklist), and — via the flags — the
    handful of blocks that only apply to some ajuste types:
      - evaluation_report_type: EvaluationReport (Contrato de Gestão /
        Convênio / Termo de Colaboração / Termo de Fomento; see
        EvaluationReport.TypeChoices for which type each uses).
      - include_purchasing_regulation / include_activity_report_publication:
        Contrato de Gestão only (manual §22 / §30).
      - include_execution_statement: Termo de Parceria only (manual §23).
    """
    statement = ensure_annual_statement(
        contract,
        fiscal_year=fiscal_year,
        statement_date=dt.date(fiscal_year + 1, 1, 20),
        reference_period_start_date=dt.date(fiscal_year, 1, 1),
        reference_period_end_date=dt.date(fiscal_year, 12, 31),
    )

    ensure_conflict_of_interest_declaration(
        statement,
        hired_related_companies=False,
        had_political_agents_in_board=False,
    )

    financial_statements = ensure_financial_statements(
        statement,
        accountant_crc_number="1SP123456",
        accountant_cpf="11144477735",
        accountant_crc_in_good_standing=True,
    )
    ensure_financial_statements_publication(
        financial_statements,
        publication_vehicle_type=AudespPublicationVehicleChoices.MUNICIPAL_OFFICIAL_GAZETTE,
        publication_date=dt.date(fiscal_year + 1, 2, 1),
    )

    opinion = ensure_opinion_or_minutes(
        statement,
        OpinionOrMinutes.TypeChoices.FISCAL_COUNCIL,
        was_published=True,
        conclusion=OpinionOrMinutes.ConclusionChoices.UNQUALIFIED_FAVORABLE,
    )
    ensure_opinion_or_minutes_publication(
        opinion,
        publication_vehicle_type=AudespPublicationVehicleChoices.MUNICIPAL_OFFICIAL_GAZETTE,
        publication_date=dt.date(fiscal_year + 1, 2, 5),
    )

    conclusive_opinion = ensure_conclusive_opinion(
        statement,
        conclusion=ConclusiveOpinion.ConclusionChoices.FAVORABLE,
        opinion_identification=f"0001/{fiscal_year + 1}",
    )
    for declaration_type in ConclusiveOpinionDeclaration.DeclarationTypeChoices.values:
        ensure_conclusive_opinion_declaration(
            conclusive_opinion,
            declaration_type,
            ConclusiveOpinionDeclaration.AnswerChoices.YES,
        )

    ensure_transparency_checklist(statement, has_website=False)

    if evaluation_report_type is not None:
        ensure_evaluation_report(
            statement,
            evaluation_report_type,
            final_report_issued=True,
            conclusion=EvaluationReport.ConclusionChoices.UNQUALIFIED_FAVORABLE,
        )

    if include_purchasing_regulation:
        regulation = ensure_purchasing_regulation(
            statement,
            had_initial_publication=True,
            was_regulation_amended=False,
        )
        ensure_purchasing_regulation_publication(
            regulation,
            phase=PurchasingRegulationPublication.PhaseChoices.INITIAL,
            publication_vehicle_type=AudespPublicationVehicleChoices.MUNICIPAL_OFFICIAL_GAZETTE,
            publication_date=dt.date(fiscal_year + 1, 1, 10),
        )

    if include_activity_report_publication:
        publication_status = ensure_activity_report_publication_status(
            statement,
            was_published_in_fiscal_year=True,
        )
        ensure_activity_report_publication(
            publication_status,
            publication_vehicle_type=AudespPublicationVehicleChoices.MUNICIPAL_OFFICIAL_GAZETTE,
            publication_date=dt.date(fiscal_year + 1, 1, 25),
        )

    if include_execution_statement:
        execution_statement = ensure_physical_financial_execution_statement(
            statement,
            has_statement=True,
            statement_follows_template=True,
        )
        ensure_physical_financial_execution_statement_publication(
            execution_statement,
            publication_vehicle_type=AudespPublicationVehicleChoices.MUNICIPAL_OFFICIAL_GAZETTE,
            publication_date=dt.date(fiscal_year + 1, 1, 30),
        )

    return statement


def seed_audesp_phase_v_fixtures(*, organization, areas, contract_a, contract_b):
    """Seeds every AUDESP Fase V fixture beyond the base scenario: the
    org-wide Employee/CededServant rolls, the AUDESP fields/structural rows
    on one contract per Fase V ajuste type (5 total), and each contract's
    AnnualStatement + satellite rows.

    Returns the Convênio contract + fiscal year so run_seed() can put it
    through the real build_payload/validate_payload pipeline as a smoke test.
    """
    area_primary, area_secondary, area_committee = areas
    fiscal_year = AUDESP_FISCAL_YEAR

    seed_audesp_org_wide_rolls(organization)

    # Termo de Colaboração / Termo de Parceria: backfill the one AUDESP field
    # seed_contracts_and_movements() doesn't set. get_or_create finds the
    # existing rows (created above in run_seed()), so only
    # audesp_agreement_code changes — every other field is left untouched.
    contract_a = ensure_contract(
        organization,
        internal_code=contract_a.internal_code,
        audesp_agreement_code=_audesp_agreement_code(contract_a.internal_code),
    )
    contract_b = ensure_contract(
        organization,
        internal_code=contract_b.internal_code,
        audesp_agreement_code=_audesp_agreement_code(contract_b.internal_code),
    )

    # Contrato de Gestão, Convênio and Termo de Fomento: no existing contract
    # covers these 3 ConcessionChoices, so create them fresh.
    parties = ensure_contract_parties(organization)

    contract_gestao = ensure_contract(
        organization,
        **parties,
        internal_code=1003,
        name="Gestão do Hospital Municipal 2026",
        concession_type=Contract.ConcessionChoices.MANAGEMENT,
        code="VP-2026-003",
        audesp_agreement_code=_audesp_agreement_code(1003),
        objective="Gestão integral da unidade hospitalar municipal.",
        bidding="Chamamento Público 010/2025",
        law_num="Lei Municipal 4.820/2025",
        law_date=dt.date(2025, 11, 20),
        agreement_num="Contrato de Gestão 2026/001",
        agreement_date=dt.date(2025, 12, 20),
        original_value=Decimal("1200000.00"),
        total_value=Decimal("1200000.00"),
        municipal_value=Decimal("1200000.00"),
        counterpart_value=Decimal("0.00"),
        start_of_vigency=dt.date(2026, 1, 1),
        end_of_vigency=dt.date(2026, 12, 31),
        status=Contract.ContractStatusChoices.EXECUTION,
        area=area_committee,
    )
    contract_convenio = ensure_contract(
        organization,
        **parties,
        internal_code=1004,
        name="Convênio Assistência Social 2026",
        concession_type=Contract.ConcessionChoices.AGREEMENT,
        code="VP-2026-004",
        audesp_agreement_code=_audesp_agreement_code(1004),
        objective="Atendimento socioassistencial a famílias em vulnerabilidade.",
        bidding="Chamamento Público 011/2025",
        law_num="Lei Municipal 4.825/2025",
        law_date=dt.date(2025, 11, 25),
        agreement_num="Convênio 2026/002",
        agreement_date=dt.date(2025, 12, 22),
        original_value=Decimal("480000.00"),
        total_value=Decimal("480000.00"),
        municipal_value=Decimal("480000.00"),
        counterpart_value=Decimal("0.00"),
        start_of_vigency=dt.date(2026, 1, 1),
        end_of_vigency=dt.date(2026, 12, 31),
        status=Contract.ContractStatusChoices.EXECUTION,
        area=area_primary,
    )
    contract_fomento = ensure_contract(
        organization,
        **parties,
        internal_code=1005,
        name="Termo de Fomento Esporte e Lazer 2026",
        concession_type=Contract.ConcessionChoices.DEVELOPMENTO,
        code="VP-2026-005",
        audesp_agreement_code=_audesp_agreement_code(1005),
        objective="Fomento a atividades esportivas comunitárias.",
        bidding="Chamamento Público 012/2025",
        law_num="Lei Municipal 4.830/2025",
        law_date=dt.date(2025, 11, 28),
        agreement_num="Termo de Fomento 2026/001",
        agreement_date=dt.date(2025, 12, 23),
        original_value=Decimal("180000.00"),
        total_value=Decimal("180000.00"),
        municipal_value=Decimal("180000.00"),
        counterpart_value=Decimal("0.00"),
        start_of_vigency=dt.date(2026, 1, 1),
        end_of_vigency=dt.date(2026, 12, 31),
        status=Contract.ContractStatusChoices.EXECUTION,
        area=area_secondary,
    )

    ajuste_contracts = [
        contract_a,
        contract_b,
        contract_gestao,
        contract_convenio,
        contract_fomento,
    ]
    for contract in ajuste_contracts:
        seed_audesp_structural_fixtures(
            contract,
            supplier_number=f"SUP-{fiscal_year}-{contract.internal_code}",
            asset_description=f"Equipamento de informática — {contract.name}",
        )

    seed_audesp_annual_statement(
        contract_a,
        fiscal_year=fiscal_year,
        evaluation_report_type=EvaluationReport.TypeChoices.MONITORING_AND_EVALUATION,
    )
    seed_audesp_annual_statement(
        contract_b,
        fiscal_year=fiscal_year,
        include_execution_statement=True,
    )
    seed_audesp_annual_statement(
        contract_gestao,
        fiscal_year=fiscal_year,
        evaluation_report_type=EvaluationReport.TypeChoices.EVALUATION_COMMITTEE,
        include_purchasing_regulation=True,
        include_activity_report_publication=True,
    )
    seed_audesp_annual_statement(
        contract_convenio,
        fiscal_year=fiscal_year,
        evaluation_report_type=EvaluationReport.TypeChoices.GOVERNMENT_EXECUTION_ANALYSIS,
    )
    seed_audesp_annual_statement(
        contract_fomento,
        fiscal_year=fiscal_year,
        evaluation_report_type=EvaluationReport.TypeChoices.MONITORING_AND_EVALUATION,
    )

    return {
        "ajuste_contracts": ajuste_contracts,
        "convenio_contract": contract_convenio,
        "convenio_fiscal_year": fiscal_year,
    }


def ensure_audesp_credential(city_hall, environment):
    """AudespCredential is a plain BaseModel (not tenant-scoped) — it FKs to
    CityHall, which sits above the Organization tenant boundary, so no
    tenant_context wrap is needed here."""
    credential, _ = AudespCredential.objects.get_or_create(
        city_hall=city_hall,
        environment=environment,
        defaults={"is_active": True},
    )
    if _apply_updates(credential, {"is_active": True}):
        credential.save()
    return credential


def build_and_record_convenio_submission(contract, fiscal_year):
    """Runs `contract` (a Convênio ajuste) through the real Fase V pipeline
    via `audesp.services.build_and_validate` and records the outcome as an
    AudespSubmission (VALID/INVALID status + validation_errors), proving the
    seeded data is realistic enough to actually clear the AUDESP builder,
    not just be present in the DB.

    Skips building a new submission if one already exists for this
    (contract, fiscal_year, ajuste_type) — AudespSubmission is an
    append-only build log, not a natural-key upsert target, and fixed
    dev-seed data shouldn't pile up a fresh "build" every time `make seed`
    runs.

    Never raises: a build or validation problem is reported back to the
    caller instead of crashing the seed command.
    """
    ajuste_type = AudespSubmission.AjusteTypeChoices.CONVENIO
    with tenant_context(contract.organization):
        if AudespSubmission.objects.filter(
            contract=contract, fiscal_year=fiscal_year, ajuste_type=ajuste_type
        ).exists():
            return {"skipped": True}

        try:
            submission = audesp_services.build_and_validate(
                contract, fiscal_year, ajuste_type
            )
        except Exception as exc:  # noqa: BLE001 - dev seed diagnostic, never fatal
            return {"build_error": repr(exc)}

        return {"status": submission.status, "errors": submission.validation_errors}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@transaction.atomic
def run_seed():
    varzea = ensure_city_hall(
        name="Prefeitura Municipal de Várzea Paulista",
        mayor="Jorge Prefeito",
        document="11222333000181",
        audesp_municipality_code=3556,
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
    ensure_audesp_credential(varzea, AudespCredential.EnvironmentChoices.PILOTO)

    org_primary = ensure_organization(
        city_hall=varzea,
        name="ONG Contabilidade Vitor Toledo",
        owner="Marcos Dono",
        document="52998224725",
        audesp_entity_code=15042,
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
    # Gestores de pasta. FolderManagersListView filters on
    # access_level=FOLDER_MANAGER *and* areas__in=request.user.areas, so these
    # only show up for a viewer sharing at least one area — hence primary_areas,
    # which is what admin@admin.com carries.
    ensure_user(
        email="gestor.saude@dev.local",
        organization=org_primary,
        access_level=User.AccessChoices.FOLDER_MANAGER,
        cpf="52998224725",
        first_name="Carla",
        last_name="Gestora",
        is_superuser=False,
        is_staff=False,
        areas=[a1, a3],
    )
    ensure_user(
        email="gestor.cultura@dev.local",
        organization=org_primary,
        access_level=User.AccessChoices.FOLDER_MANAGER,
        cpf="39053344705",
        first_name="Bruno",
        last_name="Gestor",
        is_superuser=False,
        is_staff=False,
        areas=[a2],
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

    audesp_fixtures = seed_audesp_phase_v_fixtures(
        organization=org_primary,
        areas=(a1, a2, a3),
        contract_a=scenario["contracts"][0],
        contract_b=scenario["contracts"][1],
    )
    audesp_submission = build_and_record_convenio_submission(
        audesp_fixtures["convenio_contract"],
        audesp_fixtures["convenio_fiscal_year"],
    )

    return {
        "logins": [
            ("admin@admin.com", User.AccessChoices.MASTER, True),
            ("contador@dev.local", User.AccessChoices.ORGANIZATION_ACCOUNTANT, False),
            ("gestor.saude@dev.local", User.AccessChoices.FOLDER_MANAGER, False),
            ("gestor.cultura@dev.local", User.AccessChoices.FOLDER_MANAGER, False),
        ],
        "scenario": scenario,
        "audesp_fixtures": audesp_fixtures,
        "audesp_submission": audesp_submission,
    }


class Command(BaseCommand):
    help = (
        "Idempotent dev seed: cria prefeituras, organizações, empresas, contratos, "
        "contas bancárias, transações, prestações de contas e fixtures AUDESP Fase V "
        "(um ajuste por tipo, com empregados/servidores cedidos, prestação de contas "
        "anual e satélites) para um cenário completo."
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

        self.stdout.write("")
        self.stdout.write("Fixtures AUDESP Fase V:")
        for contract in result["audesp_fixtures"]["ajuste_contracts"]:
            self.stdout.write(
                f"  ajuste {contract.internal_code}: {contract.name} "
                f"[{contract.get_concession_type_display()}] "
                f"codigo_ajuste={contract.audesp_agreement_code}"
            )

        audesp_submission = result["audesp_submission"]
        if audesp_submission.get("build_error"):
            self.stdout.write(
                self.style.WARNING(
                    "  [audesp] falha ao construir/validar o payload do Convênio: "
                    f"{audesp_submission['build_error']}"
                )
            )
        elif audesp_submission.get("skipped"):
            self.stdout.write(
                "  [audesp] submissão do Convênio já existente para este "
                "(contrato, exercício) — nada a fazer."
            )
        elif audesp_submission["errors"]:
            self.stdout.write(
                self.style.WARNING(
                    "  [audesp] payload do Convênio construído com "
                    f"{len(audesp_submission['errors'])} erro(s) de validação "
                    f"contra o JSON Schema (status={audesp_submission['status']})."
                )
            )
            for error in audesp_submission["errors"][:5]:
                self.stdout.write(f"      - {error['path']}: {error['message']}")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "  [audesp] payload do Convênio construído e validado com "
                    "sucesso contra o JSON Schema oficial."
                )
            )

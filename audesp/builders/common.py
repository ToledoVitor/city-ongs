"""Block builders shared by all 5 ajuste-type builders (see
AUDESP_FASE_V_AUDIT.md §3 for the ajuste-type x required-block matrix).

These 21 blocks are byte-for-byte identical in shape across all 5 official
JSON Schemas, except for three spots where one extra key is allowed only for
Contrato de Gestão / Termo de Parceria (`dados_gerais_entidade_beneficiaria`,
`responsaveis_membros_orgao_concessor`, `declaracoes`) — those take an
explicit flag rather than branching on ajuste_type here, so this module has
no knowledge of which ajuste types exist.

A handful of blocks used by only some ajuste types (servidores_cedidos,
publicacao_regulamento_compras, the shared `$defs/relatorio` shape, publicacao_
relatorio_atividades, publicacao_extrato_execucao_fisica_financeira) also live
here since they reuse the same query/serialize pattern, even though no single
ajuste type uses all of them — each per-type builder module calls only the
ones its schema requires.

Known simplifications, inherited from the Convênio reference implementation:
- Employee/servidor eligibility only filters remuneration periods to the
  fiscal year; it doesn't yet implement manual §5 rule 8 ("re-inform anyone
  without a demissão date") or servidores_cedidos' equivalent.
- Documento fiscal `identificacao_contrato` (optional link to a
  SupplierContract) is omitted — Expense has no FK to SupplierContract yet.
- `pagamento_data` uses `Expense.liquidation`; `data_emissao` uses
  `Expense.competency` — the closest existing fields, not a literal
  "document issuance date" column.
"""

from accountability.models import (
    ActivityReportPublicationStatus,
    AvailableFunds,
    BalanceAdjustment,
    ConflictOfInterestDeclaration,
    Deduction,
    EvaluationReport,
    Expense,
    ExpenseRejection,
    FinancialStatements,
    PhysicalFinancialExecutionStatement,
    PurchasingRegulation,
    PurchasingRegulationPublication,
    Refund,
    Revenue,
)
from accounts.models import CededServant, Employee
from audesp.serializers.shared import (
    serialize_agency,
    serialize_creditor,
    serialize_date,
    serialize_money,
    serialize_publications,
)
from contracts.models import (
    Asset,
    CertificateReference,
    ContractGoalAnnualResult,
    SupplierContract,
)
from transparency_portal.models import TransparencyChecklist


def build_descritor(contract, fiscal_year, tipo_documento):
    return {
        "tipo_documento": tipo_documento,
        "municipio": contract.area.city_hall.audesp_municipality_code,
        "entidade": contract.organization.audesp_entity_code,
        "ano": fiscal_year,
        "mes": 12,
    }


def build_relacao_empregados(contract, fiscal_year):
    employees = Employee.objects.filter(organization=contract.organization)
    result = []
    for employee in employees:
        periods = employee.remuneration_periods.filter(year=fiscal_year)
        entry = {
            "cpf": employee.cpf,
            "data_admissao": serialize_date(employee.admission_date),
            "cbo": employee.cbo,
            "salario_contratual": serialize_money(employee.contractual_salary),
            "periodos_remuneracao": [
                {
                    "mes": period.month,
                    "carga_horaria": serialize_money(period.hours_worked),
                    "remuneracao_bruta": serialize_money(period.gross_remuneration),
                }
                for period in periods
            ],
        }
        if employee.termination_date:
            entry["data_demissao"] = serialize_date(employee.termination_date)
        if employee.cns:
            entry["cns"] = employee.cns
        result.append(entry)
    return result


def build_relacao_bens(contract, fiscal_year):
    """Each of the 6 sub-arrays uses a *different* date/value key name
    (data_aquisicao/valor_aquisicao vs data_cessao/valor_cessao vs just
    data_baixa_devolucao with no value) — not a single generic shape, so
    each is built explicitly rather than through one parameterized helper.
    """
    assets = list(Asset.objects.filter(contract=contract, date__year=fiscal_year))

    def by(category, event):
        return [a for a in assets if a.category == category and a.event == event]

    movable, immovable = Asset.CategoryChoices.MOVABLE, Asset.CategoryChoices.IMMOVABLE
    acquired, ceded, written_off = (
        Asset.EventChoices.ACQUIRED,
        Asset.EventChoices.CEDED,
        Asset.EventChoices.WRITTEN_OFF,
    )

    return {
        "relacao_bens_moveis_adquiridos": [
            {
                "numero_patrimonio": a.asset_number,
                "descricao": a.description,
                "data_aquisicao": serialize_date(a.date),
                "valor_aquisicao": serialize_money(a.value),
            }
            for a in by(movable, acquired)
        ],
        "relacao_bens_moveis_cedidos": [
            {
                "numero_patrimonio": a.asset_number,
                "descricao": a.description,
                "data_cessao": serialize_date(a.date),
                "valor_cessao": serialize_money(a.value),
            }
            for a in by(movable, ceded)
        ],
        "relacao_bens_moveis_baixados_devolvidos": [
            {
                "numero_patrimonio": a.asset_number,
                "data_baixa_devolucao": serialize_date(a.date),
            }
            for a in by(movable, written_off)
        ],
        "relacao_bens_imoveis_adquiridos": [
            {
                "descricao": a.description,
                "data_aquisicao": serialize_date(a.date),
            }
            for a in by(immovable, acquired)
        ],
        "relacao_bens_imoveis_cedidos": [
            {
                "descricao": a.description,
                "data_cessao": serialize_date(a.date),
            }
            for a in by(immovable, ceded)
        ],
        "relacao_bens_imoveis_baixados_devolvidos": [
            {
                "descricao": a.description,
                "data_baixa_devolucao": serialize_date(a.date),
            }
            for a in by(immovable, written_off)
        ],
    }


def build_contratos(contract):
    result = []
    for supplier_contract in SupplierContract.objects.filter(contract=contract):
        entry = {
            "numero": supplier_contract.number,
            "credor": serialize_creditor(
                supplier_contract.creditor_document_type,
                supplier_contract.creditor_document_number,
                supplier_contract.creditor_name,
            ),
            "data_assinatura": serialize_date(supplier_contract.signature_date),
            "vigencia_tipo": supplier_contract.validity_type,
            "vigencia_data_inicial": serialize_date(
                supplier_contract.validity_start_date
            ),
            "objeto": supplier_contract.purpose,
            "natureza_contratacao": supplier_contract.contracting_nature,
            "criterio_selecao": supplier_contract.selection_criteria,
            "valor_montante": serialize_money(supplier_contract.amount),
            "valor_tipo": supplier_contract.value_type,
        }
        if supplier_contract.validity_end_date:
            entry["vigencia_data_final"] = serialize_date(
                supplier_contract.validity_end_date
            )
        if supplier_contract.contracting_nature_other:
            entry["natureza_contratacao_outro"] = (
                supplier_contract.contracting_nature_other
            )
        if supplier_contract.selection_criteria_other:
            entry["criterio_selecao_outro"] = supplier_contract.selection_criteria_other
        if supplier_contract.purchase_regulation_article:
            entry["artigo_regulamento_compras"] = (
                supplier_contract.purchase_regulation_article
            )
        result.append(entry)
    return result


def _expenses_for_year(contract, fiscal_year):
    return Expense.objects.filter(
        accountability__contract=contract,
        accountability__year=fiscal_year,
    )


def build_documentos_fiscais(contract, fiscal_year):
    result = []
    for expense in _expenses_for_year(contract, fiscal_year):
        entry = {
            "numero": expense.document_number,
            "credor": serialize_creditor(
                expense.creditor_document_type,
                expense.favored.document if expense.favored else None,
                expense.favored.name if expense.favored else None,
            ),
            "descricao": expense.identification,
            "data_emissao": serialize_date(expense.competency),
            "estado_emissor": expense.issuing_state,
            "valor_bruto": serialize_money(expense.value),
            "valor_encargos": serialize_money(expense.encumbrance_value or 0),
            "categoria_despesas_tipo": expense.expense_category_type,
        }
        entry["rateio_proveniente_tipo"] = 1 if expense.from_apportionment else 2
        if expense.from_apportionment and expense.apportionment_percentage is not None:
            entry["rateio_percentual"] = serialize_money(
                expense.apportionment_percentage
            )
        result.append(entry)
    return result


def build_pagamentos(contract, fiscal_year):
    result = []
    for expense in _expenses_for_year(contract, fiscal_year).filter(paid=True):
        entry = {
            "identificacao_documento_fiscal": {
                "numero": expense.document_number,
                "identificacao_credor": {
                    "documento_tipo": expense.creditor_document_type,
                    "documento_numero": expense.favored.document
                    if expense.favored
                    else None,
                },
            },
            "pagamento_data": serialize_date(expense.liquidation),
            "pagamento_valor": serialize_money(expense.value),
            "fonte_recurso_tipo": expense.funding_source_type,
            "meio_pagamento_tipo": expense.payment_method_type,
        }
        if expense.transaction_number:
            entry["numero_transacao"] = expense.transaction_number
        result.append(entry)
    return result


def build_disponibilidades(annual_statement):
    try:
        available_funds = annual_statement.available_funds
    except AvailableFunds.DoesNotExist:
        return {"saldos": [], "saldo_fundo_fixo": 0.0}
    return {
        "saldos": [
            {
                "banco": balance.bank_account.bank_id,
                "agencia": serialize_agency(balance.bank_account.agency),
                "conta": balance.bank_account.account,
                "conta_tipo": balance.account_type,
                "saldo_bancario": serialize_money(balance.bank_balance),
                "saldo_contabil": serialize_money(balance.accounting_balance),
            }
            for balance in available_funds.balances.all()
        ],
        "saldo_fundo_fixo": serialize_money(available_funds.petty_cash_balance),
    }


def build_receitas(contract, fiscal_year):
    revenues = Revenue.objects.filter(
        accountability__contract=contract,
        accountability__year=fiscal_year,
    )
    return {
        "receitas_aplic_financ_repasses_publicos_municipais": 0.0,
        "receitas_aplic_financ_repasses_publicos_estaduais": 0.0,
        "receitas_aplic_financ_repasses_publicos_federais": 0.0,
        "repasses_recebidos": [],
        "outras_receitas": [
            {
                "descricao": revenue.identification,
                "valor": serialize_money(revenue.value),
            }
            for revenue in revenues
        ],
        "recursos_proprios": [],
    }


def build_ajustes_saldo(contract, fiscal_year):
    adjustments = BalanceAdjustment.objects.filter(
        contract=contract, date__year=fiscal_year
    )

    def entries(adjustment_type):
        return list(adjustments.filter(type=adjustment_type))

    return {
        "retificacao_repasses": [
            {
                "data_prevista": serialize_date(a.planned_date),
                "data_repasse": serialize_date(a.date),
                "fonte_recurso_tipo": a.funding_source_type,
                "valor_retificado": serialize_money(a.value),
            }
            for a in entries(BalanceAdjustment.TypeChoices.TRANSFER_CORRECTION)
        ],
        "inclusao_repasses": [
            {
                "data_prevista": serialize_date(a.planned_date),
                "data_repasse": serialize_date(a.date),
                "valor": serialize_money(a.value),
                "fonte_recurso_tipo": a.funding_source_type,
            }
            for a in entries(BalanceAdjustment.TypeChoices.TRANSFER_INCLUSION)
        ],
        "retificacao_pagamentos": [
            {
                "identificacao_documento_fiscal": {
                    "numero": a.expense.document_number if a.expense else None,
                    "identificacao_credor": {
                        "documento_tipo": a.expense.creditor_document_type
                        if a.expense
                        else None,
                        "documento_numero": (
                            a.expense.favored.document
                            if a.expense and a.expense.favored
                            else None
                        ),
                    },
                },
                "pagamento_data": serialize_date(a.date),
                "pagamento_valor": serialize_money(
                    a.expense.value if a.expense else None
                ),
                "fonte_recurso_tipo": a.funding_source_type,
                "valor_retificado": serialize_money(a.value),
            }
            for a in entries(BalanceAdjustment.TypeChoices.PAYMENT_CORRECTION)
        ],
        "inclusao_pagamentos": [
            {
                "identificacao_documento_fiscal": {
                    "numero": a.expense.document_number if a.expense else None,
                    "identificacao_credor": {
                        "documento_tipo": a.expense.creditor_document_type
                        if a.expense
                        else None,
                        "documento_numero": (
                            a.expense.favored.document
                            if a.expense and a.expense.favored
                            else None
                        ),
                    },
                },
                "pagamento_data": serialize_date(a.date),
                "pagamento_valor": serialize_money(a.value),
                "fonte_recurso_tipo": a.funding_source_type,
                "meio_pagamento_tipo": a.payment_method_type,
                "banco": a.bank,
                "agencia": serialize_agency(a.bank_branch),
                "conta_corrente": a.account_number,
                "numero_transacao": a.transaction_number,
            }
            for a in entries(BalanceAdjustment.TypeChoices.PAYMENT_INCLUSION)
        ],
    }


def build_servidores_cedidos(contract, fiscal_year):
    servants = CededServant.objects.filter(organization=contract.organization)
    result = []
    for servant in servants:
        periods = servant.remuneration_periods.filter(year=fiscal_year)
        entry = {
            "cpf": servant.cpf,
            "data_inicial_cessao": serialize_date(servant.cession_start_date),
            "cargo_publico_ocupado": servant.public_position_held,
            "funcao_desempenhada_entidade_beneficiaria": servant.role_performed,
            "onus_pagamento": servant.payment_burden,
            "periodos_cessao": [
                {
                    "mes": period.month,
                    "carga_horaria": serialize_money(period.hours_worked),
                    "remuneracao_bruta": serialize_money(period.gross_remuneration),
                }
                for period in periods
            ],
        }
        if servant.cession_end_date:
            entry["data_final_cessao"] = serialize_date(servant.cession_end_date)
        result.append(entry)
    return result


def build_descontos(contract, fiscal_year):
    return [
        {
            "data": serialize_date(d.date),
            "descricao": d.description,
            "valor": serialize_money(d.value),
        }
        for d in Deduction.objects.filter(contract=contract, date__year=fiscal_year)
    ]


def build_devolucoes(contract, fiscal_year):
    return [
        {
            "data": serialize_date(r.date),
            "natureza_devolucao_tipo": r.nature,
            "valor": serialize_money(r.value),
        }
        for r in Refund.objects.filter(contract=contract, date__year=fiscal_year)
    ]


def build_glosas(contract, fiscal_year):
    result = []
    for rejection in ExpenseRejection.objects.filter(contract=contract):
        entry = {"resultado_analise": rejection.analysis_result}
        if rejection.expense_id:
            entry["identificacao_documento_fiscal"] = {
                "numero": rejection.expense.document_number,
                "identificacao_credor": {
                    "documento_tipo": rejection.expense.creditor_document_type,
                    "documento_numero": (
                        rejection.expense.favored.document
                        if rejection.expense.favored
                        else None
                    ),
                },
            }
        if rejection.payment_date:
            entry["pagamento_data"] = serialize_date(rejection.payment_date)
        if rejection.rejected_value is not None:
            entry["valor_glosa"] = serialize_money(rejection.rejected_value)
        result.append(entry)
    return result


def build_empenhos(contract, fiscal_year):
    return [
        {
            "numero": c.number,
            "data_emissao": serialize_date(c.issue_date),
            "classificacao_economica_tipo": c.economic_classification,
            "fonte_recurso_tipo": c.funding_source_type,
            "valor": serialize_money(c.value),
            "historico": c.description,
            "cpf_ordenador_despesa": c.spending_authority_cpf,
        }
        for c in contract.budget_commitments.filter(issue_date__year=fiscal_year)
    ]


def build_repasses(contract, fiscal_year):
    result = []
    for transfer in contract.fund_transfers.filter(transfer_date__year=fiscal_year):
        entry = {
            "identificacao_empenho": {
                "numero": transfer.budget_commitment.number,
                "data_emissao": serialize_date(transfer.budget_commitment.issue_date),
            },
            "data_prevista": serialize_date(transfer.planned_date),
            "data_repasse": serialize_date(transfer.transfer_date),
            "valor_previsto": serialize_money(transfer.planned_value),
            "valor_repasse": serialize_money(transfer.transferred_value),
            "tipo_documento_bancario": transfer.bank_document_type,
            "numero_documento": transfer.document_number,
            "banco": transfer.bank,
            "agencia": serialize_agency(transfer.bank_branch),
            "conta": transfer.account_number,
        }
        if transfer.planned_value != transfer.transferred_value:
            entry["justificativa_diferenca_valor"] = (
                transfer.value_difference_justification
            )
        if transfer.other_description:
            entry["descricao_outros"] = transfer.other_description
        result.append(entry)
    return result


def build_relatorio_atividades(contract, fiscal_year):
    programas = []
    for goal in contract.goals.exclude(goal_code__isnull=True):
        try:
            annual_result = goal.annual_results.get(fiscal_year=fiscal_year)
        except ContractGoalAnnualResult.DoesNotExist:
            continue
        meta = {
            "codigo_meta": goal.goal_code,
            "periodicidades": [
                {
                    "periodo": period.period,
                    **(
                        {
                            "quantidade_realizada": serialize_money(
                                period.achieved_quantity
                            )
                        }
                        if period.achieved_quantity is not None
                        else {}
                    ),
                    **(
                        {"resultado_meta": period.goal_result}
                        if period.goal_result
                        else {}
                    ),
                    **(
                        {"justificativa": period.justification}
                        if period.justification
                        else {}
                    ),
                }
                for period in annual_result.period_results.all()
            ],
        }
        if annual_result.goal_met is not None:
            meta["meta_atendida"] = annual_result.goal_met
        if annual_result.justification:
            meta["justificativa"] = annual_result.justification
        programas.append({"nome_programa": goal.name, "metas": [meta]})
    return {"programas": programas}


def build_dados_gerais(contract, include_entity_responsible_parties=False):
    """The base 3 keys apply to all 5 ajuste types. `identificacao_certidao_
    responsaveis` (the *managed-entity* certidão — manual §20 rule 6, distinct
    from the órgão concessor certidão of the same name in
    `responsaveis_membros_orgao_concessor`) is Contrato de Gestão only —
    including it for any other type would violate that schema's
    `additionalProperties: false`.
    """
    refs = {
        ref.type: ref.identification
        for ref in CertificateReference.objects.filter(contract=contract)
    }
    data = {}
    mapping = [
        (
            "identificacao_certidao_dados_gerais",
            CertificateReference.TypeChoices.GENERAL_DATA,
        ),
        (
            "identificacao_certidao_corpo_diretivo",
            CertificateReference.TypeChoices.GOVERNING_BODY,
        ),
        (
            "identificacao_certidao_membros_conselho",
            CertificateReference.TypeChoices.COUNCIL_MEMBERS,
        ),
    ]
    if include_entity_responsible_parties:
        mapping.append(
            (
                "identificacao_certidao_responsaveis",
                CertificateReference.TypeChoices.ENTITY_RESPONSIBLE_PARTIES,
            )
        )
    for key, cert_type in mapping:
        value = refs.get(cert_type)
        if value:
            data[key] = value
    return data


def build_responsaveis_orgao(contract, include_execution_oversight=True):
    """`identificacao_certidao_responsaveis_fiscalizacao_execucao` isn't even
    a defined property for Contrato de Gestão's schema (unlike the other 4
    types, where it's present but not always required) — pass
    `include_execution_oversight=False` there to avoid an
    `additionalProperties: false` violation.
    """
    refs = {
        ref.type: ref.identification
        for ref in CertificateReference.objects.filter(contract=contract)
    }
    mapping = [
        (
            "identificacao_certidao_responsaveis",
            CertificateReference.TypeChoices.GRANTOR_RESPONSIBLE_PARTIES,
        ),
        (
            "identificacao_certidao_membros_comissao_avaliacao",
            CertificateReference.TypeChoices.EVALUATION_COMMITTEE_MEMBERS,
        ),
        (
            "identificacao_certidao_membros_controle_interno",
            CertificateReference.TypeChoices.INTERNAL_CONTROL_MEMBERS,
        ),
    ]
    if include_execution_oversight:
        mapping.append(
            (
                "identificacao_certidao_responsaveis_fiscalizacao_execucao",
                CertificateReference.TypeChoices.EXECUTION_OVERSIGHT_RESPONSIBLE_PARTIES,
            )
        )
    data = {}
    for key, cert_type in mapping:
        value = refs.get(cert_type)
        if value:
            data[key] = value
    return data


def build_declaracoes(annual_statement, include_purchasing_regulation_compliance=False):
    """`compras_contratacoes_adequados_regulamento_proprio` is Contrato de
    Gestão / Termo de Parceria only — Convênio/Colaboração/Fomento's schemas
    don't define that property at all, so it must never be emitted for them.
    """
    try:
        declaration = annual_statement.conflict_of_interest_declaration
    except ConflictOfInterestDeclaration.DoesNotExist:
        data = {
            "houve_contratacao_empresas_pertencentes": False,
            "houve_participacao_quadro_diretivo_administrativo": False,
        }
        return data
    data = {
        "houve_contratacao_empresas_pertencentes": declaration.hired_related_companies,
        "houve_participacao_quadro_diretivo_administrativo": declaration.had_political_agents_in_board,
    }
    if declaration.hired_related_companies:
        data["empresas_pertencentes"] = [
            {"cnpj": c.cnpj, "cpf": c.cpf} for c in declaration.related_companies.all()
        ]
    if declaration.had_political_agents_in_board:
        data["participacoes_quadro_diretivo_administrativo"] = [
            {"cpf_dirigente": p.officer_cpf, "cpf_contratados": p.hired_cpfs}
            for p in declaration.board_participations.all()
        ]
    if (
        include_purchasing_regulation_compliance
        and declaration.purchases_comply_with_own_regulation is not None
    ):
        data["compras_contratacoes_adequados_regulamento_proprio"] = (
            declaration.purchases_comply_with_own_regulation
        )
    return data


def build_relatorio(annual_statement, report_type):
    """Shared `$defs/relatorio` shape (manual §25/26/27) — same fields for
    `relatorio_comissao_avaliacao` (Contrato de Gestão), `relatorio_
    governamental_analise_execucao` (Convênio) and `relatorio_monitoramento_
    avaliacao` (Termo de Colaboração/Fomento), keyed by EvaluationReport.type.
    """
    try:
        report = annual_statement.evaluation_reports.get(type=report_type)
    except EvaluationReport.DoesNotExist:
        return {"houve_emissao_relatorio_final": False}
    data = {"houve_emissao_relatorio_final": report.final_report_issued}
    if report.conclusion:
        data["conclusao_relatorio"] = report.conclusion
    if report.justification:
        data["justificativa"] = report.justification
    return data


def build_demonstracoes_contabeis(annual_statement):
    try:
        statements = annual_statement.financial_statements
    except FinancialStatements.DoesNotExist:
        return {"publicacoes": [], "responsavel": {}}
    return {
        "publicacoes": serialize_publications(statements.publications.all()),
        "responsavel": {
            "numero_crc": statements.accountant_crc_number,
            "cpf": statements.accountant_cpf,
            "situacao_regular_crc": statements.accountant_crc_in_good_standing,
        },
    }


def build_publicacoes_parecer_ata(annual_statement):
    """`conclusao_parecer` is unconditionally required per entry — manual
    §29 rule 7 ("mandatory when there is an ata/parecer"), which is always
    true for a row that exists in `opinions_or_minutes`."""
    return [
        {
            "tipo_parecer_ata": opinion.type,
            "houve_publicacao": opinion.was_published,
            "publicacoes": serialize_publications(opinion.publications.all()),
            "conclusao_parecer": opinion.conclusion,
        }
        for opinion in annual_statement.opinions_or_minutes.all()
    ]


def build_prestacao_entidade(annual_statement):
    return {
        "data_prestacao": serialize_date(annual_statement.statement_date),
        "periodo_referencia_data_inicial": serialize_date(
            annual_statement.reference_period_start_date
        ),
        "periodo_referencia_data_final": serialize_date(
            annual_statement.reference_period_end_date
        ),
    }


def build_parecer_conclusivo(annual_statement):
    opinion = annual_statement.conclusive_opinion
    data = {
        "conclusao_parecer": opinion.conclusion,
        "declaracoes": [
            {
                "tipo_declaracao": d.declaration_type,
                "declaracao": d.answer,
                **({"justificativa": d.justification} if d.justification else {}),
            }
            for d in opinion.declarations.all()
        ],
    }
    if opinion.opinion_identification:
        data["identificacao_parecer"] = opinion.opinion_identification
    if opinion.remarks:
        data["consideracoes_parecer"] = opinion.remarks
    return data


def build_transparencia(annual_statement):
    try:
        checklist = annual_statement.transparency_checklist
    except TransparencyChecklist.DoesNotExist:
        return {"entidade_beneficiaria_mantem_sitio_internet": False}

    data = {"entidade_beneficiaria_mantem_sitio_internet": checklist.has_website}
    if not checklist.has_website:
        return data

    data["sitios_internet"] = checklist.websites

    art_7_8_1_fields = [
        checklist.art7_8_1_organizational_structure,
        checklist.art7_8_1_contact_information,
        checklist.art7_8_1_transfer_records,
        checklist.art7_8_1_expense_records,
        checklist.art7_8_1_procurement_information,
        checklist.art7_8_1_goals_tracking_information,
        checklist.art7_8_1_faq,
        checklist.art7_8_1_audit_results,
    ]
    data["requisitos_artigos_7o_8o_paragrafo_1o"] = [
        {"requisito": i + 1, "atende": bool(value)}
        for i, value in enumerate(art_7_8_1_fields)
    ]

    art_8_3_fields = [
        checklist.art8_3_content_search_tool,
        checklist.art8_3_open_format_reports,
        checklist.art8_3_automated_external_access,
        checklist.art8_3_discloses_data_structure_formats,
        checklist.art8_3_ensures_authenticity_integrity,
        checklist.art8_3_periodic_updates,
    ]
    data["requisitos_sitio_artigo_8o_paragrafo_3o"] = [
        {"requisito": i + 1, "atende": bool(value)}
        for i, value in enumerate(art_8_3_fields)
    ]

    disclosure_fields = [
        checklist.disclosure_updated_bylaws,
        checklist.disclosure_agreements,
        checklist.disclosure_work_plan,
        checklist.disclosure_officers_list,
        checklist.disclosure_service_providers_list,
        checklist.disclosure_individualized_compensation,
        checklist.disclosure_financial_statements,
        checklist.disclosure_purchasing_regulation,
        checklist.disclosure_hiring_regulation,
        checklist.disclosure_sic_statistical_report,
    ]
    data["requisitos_divulgacao_informacoes"] = [
        {"requisito": i + 1, "atende": bool(value)}
        for i, value in enumerate(disclosure_fields)
    ]
    return data


def build_publicacao_regulamento_compras(annual_statement):
    """Contrato de Gestão only (manual §22)."""
    try:
        regulation = annual_statement.purchasing_regulation
    except PurchasingRegulation.DoesNotExist:
        return {"houve_publicacao_inicial": False}
    data = {"houve_publicacao_inicial": regulation.had_initial_publication}
    if regulation.had_initial_publication:
        data["publicacoes_regulamento_inicial"] = serialize_publications(
            regulation.publications.filter(
                phase=PurchasingRegulationPublication.PhaseChoices.INITIAL
            )
        )
    if regulation.was_regulation_amended is not None:
        data["houve_alteracao_do_regulamento"] = regulation.was_regulation_amended
    if regulation.had_amended_regulation_publication is not None:
        data["houve_publicacao_regulamento_alterado"] = (
            regulation.had_amended_regulation_publication
        )
    if regulation.had_amended_regulation_publication:
        data["publicacoes_alteracao_regulamento"] = serialize_publications(
            regulation.publications.filter(
                phase=PurchasingRegulationPublication.PhaseChoices.AMENDMENT
            )
        )
    return data


def build_publicacao_relatorio_atividades(annual_statement):
    """Contrato de Gestão only (manual §30)."""
    try:
        status = annual_statement.activity_report_publication_status
    except ActivityReportPublicationStatus.DoesNotExist:
        return {"houve_publicacao_exercicio": False}
    data = {"houve_publicacao_exercicio": status.was_published_in_fiscal_year}
    if status.was_published_in_fiscal_year:
        data["publicacoes"] = serialize_publications(status.publications.all())
    return data


def build_publicacao_extrato_execucao(annual_statement):
    """Termo de Parceria only (manual §23)."""
    try:
        statement = annual_statement.execution_statement
    except PhysicalFinancialExecutionStatement.DoesNotExist:
        return {"ha_extrato_execucao_fisica_financeira": False}
    data = {"ha_extrato_execucao_fisica_financeira": statement.has_statement}
    if statement.statement_follows_template is not None:
        data["extrato_elaborado_conforme_modelo"] = statement.statement_follows_template
    if statement.has_statement:
        data["publicacoes"] = serialize_publications(statement.publications.all())
    return data

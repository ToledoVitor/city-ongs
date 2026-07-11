"""Builds the Fase V JSON payload for a Convênio ajuste's annual statement.

Convênio requires the 21 blocks in `audesp/builders/common.py` plus
`servidores_cedidos` and `relatorio_governamental_analise_execucao` (see
AUDESP_FASE_V_AUDIT.md §3). The other 4 ajuste types differ only in which
blocks apply and reuse the same common.py helpers.
"""

from easy_tenants import tenant_context

from accountability.models import EvaluationReport
from audesp.builders import common


def build_payload(contract, fiscal_year):
    """Assemble the full Fase V JSON document for `contract` (a Convênio
    ajuste) in `fiscal_year`. Raises `AnnualStatement.DoesNotExist` if no
    annual statement has been created for that (contract, fiscal_year).

    Runs under `tenant_context(contract.organization)` since every model
    queried here goes through `easy_tenants`' `TenantManager`, which filters
    by the *current* tenant — outside a request (no `TenantMiddleware`) or
    outside this wrapper, those queries would silently return empty
    querysets instead of raising, rather than the data actually there.
    """
    with tenant_context(contract.organization):
        return _build_payload(contract, fiscal_year)


def _build_payload(contract, fiscal_year):
    annual_statement = contract.annual_statements.get(fiscal_year=fiscal_year)

    return {
        "descritor": common.build_descritor(
            contract, fiscal_year, "Prestação de Contas de Convênio"
        ),
        "codigo_ajuste": contract.audesp_agreement_code,
        "relacao_empregados": common.build_relacao_empregados(contract, fiscal_year),
        "relacao_bens": common.build_relacao_bens(contract, fiscal_year),
        "contratos": common.build_contratos(contract),
        "documentos_fiscais": common.build_documentos_fiscais(contract, fiscal_year),
        "pagamentos": common.build_pagamentos(contract, fiscal_year),
        "disponibilidades": common.build_disponibilidades(annual_statement),
        "receitas": common.build_receitas(contract, fiscal_year),
        "ajustes_saldo": common.build_ajustes_saldo(contract, fiscal_year),
        "servidores_cedidos": common.build_servidores_cedidos(contract, fiscal_year),
        "descontos": common.build_descontos(contract, fiscal_year),
        "devolucoes": common.build_devolucoes(contract, fiscal_year),
        "glosas": common.build_glosas(contract, fiscal_year),
        "empenhos": common.build_empenhos(contract, fiscal_year),
        "repasses": common.build_repasses(contract, fiscal_year),
        "relatorio_atividades": common.build_relatorio_atividades(
            contract, fiscal_year
        ),
        "dados_gerais_entidade_beneficiaria": common.build_dados_gerais(contract),
        "responsaveis_membros_orgao_concessor": common.build_responsaveis_orgao(
            contract
        ),
        "declaracoes": common.build_declaracoes(annual_statement),
        "relatorio_governamental_analise_execucao": common.build_relatorio(
            annual_statement, EvaluationReport.TypeChoices.GOVERNMENT_EXECUTION_ANALYSIS
        ),
        "demonstracoes_contabeis": common.build_demonstracoes_contabeis(
            annual_statement
        ),
        "publicacoes_parecer_ata": common.build_publicacoes_parecer_ata(
            annual_statement
        ),
        "prestacao_contas_entidade_beneficiaria": common.build_prestacao_entidade(
            annual_statement
        ),
        "parecer_conclusivo": common.build_parecer_conclusivo(annual_statement),
        "transparencia": common.build_transparencia(annual_statement),
    }

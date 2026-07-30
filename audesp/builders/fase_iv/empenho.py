"""Fase IV "Empenho" JSON builder — registers an additional budget
commitment note against an already-registered ajuste. Per the official
manual this is a "sub-módulo" of Ajuste sharing its submission endpoint
(`/f4/enviar-ajuste`), not a standalone one. Real JSON Schema:
docs/audesp_fase_iv/empenho_v1/empenho_schema_v1.json.

That schema sets `additionalProperties: false` at the top level — only
descritor/codigoContrato/dataEmissaoEmpenho are accepted today, even
though TCE-SP's 2026 label spreadsheet documents extra fields
(tipoPessoa, niCredorFornecedor, nomeCredorFornecedor,
codigoNaturezaDespesa, fonteRecurso) that aren't in the currently
downloadable schema — see AUDESP_FASE_IV_AUDIT.md. Sending them today
would fail schema validation, so this builder deliberately doesn't.
"""

from audesp.serializers.shared import serialize_date


def build_payload(budget_commitment, *, retificacao=False):
    contract = budget_commitment.contract
    city_hall = contract.area.city_hall
    organization = contract.organization

    return {
        "descritor": {
            "municipio": city_hall.audesp_municipality_code,
            "entidade": organization.audesp_entity_code,
            "numeroEmpenho": budget_commitment.number,
            "anoEmpenho": budget_commitment.issue_date.year,
            "retificacao": retificacao,
        },
        "codigoContrato": contract.audesp_agreement_code,
        "dataEmissaoEmpenho": serialize_date(budget_commitment.issue_date),
    }

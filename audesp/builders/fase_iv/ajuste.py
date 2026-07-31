"""Fase IV "Ajuste" JSON builder — registers a contract/instrument itself
with AUDESP (parties, value, dates, funding source), as distinct from
Fase V's own accountability-of-repasses reporting. Real JSON Schema:
docs/audesp_fase_iv/ajuste_v2_0_0/ajuste_schema_v2.json.

See AUDESP_FASE_IV_AUDIT.md for the full field-mapping rationale,
including which values below are confirmed by TCE-SP's official 2026
label spreadsheet vs. best-effort inferred from it — this schema's
classification domains (tipoContratoId, categoriaProcessoId,
tipoObjetoContrato) come from PNCP's generic public-procurement
taxonomy and have no member that names a third-sector partnership
explicitly.
"""

from audesp.serializers.shared import serialize_date, serialize_money

# PNCP "Tipo de Contrato" domain. Value 6 ("Convênio") was revoked by
# Portaria Conjunta MGI/MF/CGU 33/2023 and is no longer a valid enum
# member in the schema (enum: [1,2,3,4,5,7,8,12] — 6, 9, 10, 11 excluded).
# None of the remaining values name a third-sector instrument; 1
# ("Contrato (termo inicial): Acordo formal recíproco de vontades firmado
# entre as partes") is the closest generic fit for all 5 SITTS ajuste
# types — inferred, not confirmed by TCE-SP.
TIPO_CONTRATO_ID = 1

# PNCP "Categoria do Processo" domain (11 values: Cessão, Compras, TIC,
# Internacional, Locação Imóveis, Mão de Obra, Obras, Serviços, Serviços
# de Engenharia, Serviços de Saúde, Alienação). None names a third-sector
# partnership; 8 ("Serviços") is the closest fit, since a Contrato de
# Gestão/Convênio/Termo organization delivers a public service on the
# city's behalf — inferred, not confirmed.
CATEGORIA_PROCESSO_ID = 8

# AUDESP "Tipo objeto do Contrato" domain, constrained to
# categoriaProcessoId per the label spreadsheet's own cross-reference
# rule. Within categoria 8 (Serviços), 27 ("Outras prestações de
# serviço") is the generic catch-all — inferred, not confirmed.
TIPO_OBJETO_CONTRATO = 27

# Organization (the beneficiary OSC) is always a legal entity in this
# system, never a natural person — PJ without a length-based CPF/CNPJ guess.
TIPO_PESSOA_FORNECEDOR = "PJ"


def build_payload(
    contract, *, codigo_edital, itens, retificacao=False, funding_sources=None
):
    """Builds a Fase IV "ajuste" payload for `contract`.

    `codigo_edital` and `itens` are required, explicit parameters rather
    than derived from the contract — both reference a Licitação/Dispensa
    record this codebase does not register (see AUDESP_FASE_IV_AUDIT.md
    "Open questions" — TCE-SP's own field rules require the Licitação to
    already exist before an Ajuste can reference it). Callers must source
    real values from wherever that registration actually happens today.

    `funding_sources` defaults to the distinct `funding_source_type`
    values across the contract's existing BudgetCommitments; raises if
    none are available rather than guessing a default — a compliance
    submission with a fabricated funding source is worse than a loud
    failure here.
    """
    if funding_sources is None:
        funding_sources = sorted(
            {c.funding_source_type for c in contract.budget_commitments.all()}
        )
    if not funding_sources:
        raise ValueError(
            "No fonteRecursosContratacao available — pass funding_sources "
            "explicitly, or register at least one BudgetCommitment for "
            f"{contract!r} first."
        )

    city_hall = contract.area.city_hall
    organization = contract.organization
    signature_date = contract.signature_date or contract.start_of_vigency

    return {
        "descritor": {
            "municipio": city_hall.audesp_municipality_code,
            "entidade": organization.audesp_entity_code,
            "adesaoParticipacao": False,
            "codigoEdital": codigo_edital,
            "codigoContrato": contract.audesp_agreement_code,
            "retificacao": retificacao,
        },
        "fonteRecursosContratacao": funding_sources,
        "itens": itens,
        "tipoContratoId": TIPO_CONTRATO_ID,
        "numeroContratoEmpenho": contract.code or str(contract.internal_code),
        "anoContrato": signature_date.year,
        "categoriaProcessoId": CATEGORIA_PROCESSO_ID,
        "receita": False,
        "niFornecedor": organization.document,
        "tipoPessoaFornecedor": TIPO_PESSOA_FORNECEDOR,
        "nomeRazaoSocialFornecedor": organization.name,
        "objetoContrato": contract.objective,
        "valorInicial": serialize_money(contract.original_value),
        "dataAssinatura": serialize_date(signature_date),
        "dataVigenciaInicio": serialize_date(contract.start_of_vigency),
        "dataVigenciaFim": serialize_date(contract.end_of_vigency),
        "tipoObjetoContrato": TIPO_OBJETO_CONTRATO,
    }

---
name: sitts-audesp
description: How SITTS builds and submits AUDESP payloads to TCE-SP — the Fase IV vs Fase V split, the JSON Schema traps (multipleOf float rounding, additionalProperties, never emit null), where credentials actually live, and the retificação cascade. Use for any work under audesp/, on AudespSubmission, the builders, the client, or anything touching TCE-SP compliance data.
---

# AUDESP (TCE-SP) integration

Two separate phases, both mandatory for the same five third-sector instruments,
sequential: **Fase IV** registers the legal instrument (the ajuste itself);
**Fase V** registers the accountability of repasses made under it.

| | Fase IV | Fase V |
|---|---|---|
| Registers | the instrument — ajuste, empenho | accountability of repasses |
| Endpoint namespace | `/recepcao-fase-4/f4/…` | `/f5/…` |
| Builders | `audesp/builders/fase_iv/` | `audesp/builders/` |
| Submission model | `AudespFaseIVSubmission` | `AudespSubmission` |
| Data model shape | generic government procurement, not third-sector-aware | third-sector-specific |

They share base URLs and bearer auth (`AudespClient._login` / `_auth_headers` are
reused as-is), and nothing else. Fase IV is **not** a variant of Fase V — different
schemas, different vocabularies, and its own Declaração Negativa meaning
("no ajuste was signed this period", not "zero repasses under this ajuste").

The five ajuste types: Contrato de Gestão, Convênio, Termo de Colaboração, Termo
de Fomento, Termo de Parceria. Each has its own Fase V endpoint and its own
builder module; `declaracao_negativa.py` covers the trivial case.

## Ground truth is in the repo — use it

The real JSON Schemas are committed. Read them instead of prose:

- `docs/audesp/*/**_schema_v1_14.json` — Fase V, all five types + declaração negativa
- `docs/audesp_fase_iv/ajuste_v2_0_0/ajuste_schema_v2.json`, `docs/audesp_fase_iv/empenho_v1/empenho_schema_v1.json`

`audesp/tests.py` (12 tests) is the highest-fidelity statement of Fase IV view and
submit behaviour in the codebase. One of them currently fails for an unrelated
reason — see `sitts-verify`.

## Schema traps

**`multipleOf` on money fields is a float-rounding minefield.** Every money field
in these schemas is `multipleOf: 0.01`, and jsonschema's stock validator divides
raw floats — `4.56 / 0.01` is `455.99999999999994` in IEEE 754, so nearly every
money field would be falsely rejected. `audesp/validators.py` overrides the keyword
to compare via `Fraction(str(x))`. Don't remove that override, and remember it if
you ever validate money against JSON Schema anywhere else.

**Never emit `null` — omit the key.** Every field is typed `string` or `boolean`
with no `null` in its type union, so an included-but-null key fails exactly like a
missing required key, with a worse error (`None is not of type 'string'` instead of
`'x' is a required property`). Every builder block follows "omit when the value is
`None`".

**Each ajuste type's schema is stricter than the union of all types.** They all set
`additionalProperties: false`, so emitting a key that belongs to a different type
fails. Three spots vary and are parameterized in `common.py` rather than
special-cased per builder:

1. `dados_gerais_entidade_beneficiaria` gains `identificacao_certidao_responsaveis` **only** for Contrato de Gestão — and it sources from a *different* `CertificateReference` type than the same-named key elsewhere ("responsáveis da entidade gerenciada" vs "do órgão concessor").
2. `responsaveis_membros_orgao_concessor`'s optional 4th key doesn't exist as a property at all for Contrato de Gestão.
3. `declaracoes` gains `compras_contratacoes_adequados_regulamento_proprio` for Contrato de Gestão and Termo de Parceria only.

**`build_payload()` must never raise.** `audesp/services.build_and_validate`
assumes building from incomplete data produces an *INVALID* submission, not an
exception. Every block returns `{}` when its related object is missing and lets
the schema's `required[]` catch it. `build_parecer_conclusivo` was the one block
that read its OneToOne directly and raised `RelatedObjectDoesNotExist`; it's fixed,
and new blocks must follow the same pattern.

**Type coercion at the edges.** `agencia` is an integer in AUDESP but free text in
our `BankAccount`; use `audesp/serializers/shared.serialize_agency()`. In
`relacao_bens`, each of the 6 sub-arrays uses *different* date/value key names
(`data_aquisicao`/`valor_aquisicao` vs `data_cessao`/`valor_cessao` vs
`data_baixa_devolucao` alone) — handled explicitly, not generically.

## Credentials belong to the CityHall, not the Organization

One município reports every organization under it through a single TCESP account.
This matches `descritor.municipio` keying off `CityHall.audesp_municipality_code`.

**No username or password is ever stored in Postgres.**
`audesp.models.AudespCredential` is a pure existence/`is_active` registry with an
FK to `CityHall`. `audesp/secrets.py` resolves the real pair: `.env` locally (one
shared dev pair via `AUDESP_PILOTO_*` / `AUDESP_PRODUCAO_*`), GCP Secret Manager
otherwise, one secret per `(city_hall, environment)`. Don't add credential fields
to the model.

## Retificação cascades, and that's expensive

Retifying an exercício older than the latest submitted one flips every later
exercício to `Excluído` at TCESP, requiring a full resend of each.

The backend guard exists: `audesp/services.submit` calls
`find_cascade_affected_submissions` and raises `AudespCascadeConfirmationRequired`
(carrying the affected fiscal years) unless called with `confirm_cascade=True`,
then flips the affected rows to `EXCLUDED` atomically. `find_cascade_affected_submissions`
is public so a caller can preview the impact before submitting.

`StatusChoices.EXCLUDED` is deliberately distinct from `REJECTED`: a
cascade-excluded submission was itself fine and needs a plain resend, while a
rejected one needs a fix first.

`AudespSubmission` is **append-only** — one row per build/submit attempt, not a
singleton, because AUDESP's own retificação flow means multiple attempts over time.

## Never fabricate reference-table labels

This is in `CLAUDE.MD` as a non-negotiable and it originates here. `bank`
(~400 BACEN codes) and `Expense.issuing_state` (27 codes) store raw integers
because no official label list is published in the manual or the schema. The raw
values are already correct for the wire format. Fabricating a label that a
município then files with the TCE is worse than showing a code.

Also: `AudespExpenseCategoryTypeChoices` (89 values) and our `NatureChoices`
(~90 values) are **different taxonomies**, not a rename. Mapping them is real
modeling work with room for misclassification.

## What is deliberately not built

- **Licitação / Dispensa / Inexigibilidade registration.** Ajuste's `codigoEdital` must reference an already-registered Licitação document, so `codigo_edital` and `itens` are **required explicit parameters** on `fase_iv.ajuste.build_payload` — never inferred or defaulted, so a caller can't get a silently-wrong value. Building the module itself would mean modeling the city hall's procurement process, which this platform doesn't capture.
- **Termo Aditivo, Execução, Documento Fiscal, Pagamentos, Fase IV's Declaração Negativa.** TCE-SP has not published JSON Schemas for these. Building them means guessing.
- **Any UI beyond Django admin** for the ~30 models added for Fase V. Admin is the only data-entry surface today. That's a known scope cut, not an oversight.
- **Declaração Negativa orchestration** in `services` (the builder exists).

## Watch out for

- **`ContractMonthTransfer` is not an AUDESP repasse.** It's the upfront planning/budget split entered via the contract timeline UI. AUDESP's repasse (actual transfer execution, linked to a budget commitment) is `accountability.FundTransfer`. Don't conflate them.
- **`Contract.ConcessionChoices` doesn't map 1:1 onto the five ajuste types** — there's a typo'd member and a sixth value with no AUDESP counterpart. This is why `declaracao_negativa.build_payload` takes `ajuste_type` explicitly instead of inferring it from `contract.concession_type`, and why the other builders don't read that field at all. See `sitts-known-bugs`.
- **LGPD.** The Employee/CededServant registry stores CPF, CNS (health-card number) and salary for people who may never log into the system. CNS ties to health records; treat it at least as tightly as existing personal data.
- **Reference data is versioned by TCESP** and has already been corrected across manual revisions 1.9–1.18. Hardcoded enums drift; recheck on manual version bumps.
- **Deadlines are external and carry penalties** — 10 business days from signature for these instruments since 2023-06-01. Unlike internal accountability, lateness has consequences.
- **No async infrastructure.** A scheduled submission or batch resubmission has nowhere to run today; see `CLAUDE.MD`.

## Not verified against a live server

The client is scaffolded and tested against mocked HTTP and a mocked Secret
Manager — URL construction, auth header format, multipart field name, token-cache
reuse, retry/backoff, exception classification, secret create-vs-rotate. **No
piloto credentials have ever been exercised**, for either phase. Fase IV's
retificação/status vocabulary is likewise unconfirmed against a real
`/f4/consulta/{protocolo}` response. Don't describe submission as working
end-to-end.

## References

- [`references/fase-v.md`](references/fase-v.md) — the Fase V audit: 37 field-blocks, the ajuste-type × required-block matrix, gap analysis, phased roadmap with what's actually done, risks, and resolved decisions.
- [`references/fase-iv.md`](references/fase-iv.md) — the Fase IV audit: what Fase IV is, endpoints, field mapping, the scope decision, and three open questions (one blocking, on `codigoEdital` for non-bidding instruments).

# AUDESP Fase IV — "Licitações e Contratos" Integration Audit

> Moved here from the repo root during the context audit. Loaded via the
> `sitts-audesp` skill. Kept intact; note that §7 corrects a stale claim in
> `fase-v.md`, so read this one second.


Status: Ajuste + Empenho builders scaffolded and verified against real TCE-SP JSON Schemas; Licitação/Dispensa registration deliberately **not** built (see §4 Scope decision). Source docs: real JSON Schemas v2.0.0 (ajuste) and v1 (empenho) downloaded from `tce.sp.gov.br/audesp/documentacao/reformulacao-fase-iv-jsonschemas-e-documentacao-xlsx`, the OpenAPI spec (`audesp.tce.sp.gov.br/api/audesp.yaml`), and TCE-SP's own 2026 field/label spreadsheet (`Novo Modelo da Fase IV_2026_v02_externo.xlsx`) — not just search-result prose. Nothing deployed yet — every recommendation below assumes schemas/flows can still change freely.

---

## 0. Why this exists

[fase-v.md](fase-v.md) §2 flagged, unresolved, that Fase V's `codigo_ajuste` and certidão references (§20/§21) point at "a separate subsystem, likely Fase IV / cadastro" without confirming it. This doc resolves that hedge: yes, Fase IV is that subsystem, and it is a **different AUDESP phase with its own JSON Schemas, its own endpoint namespace (`/f4/...` vs Fase V's `/f5/...`), and its own generic (non-third-sector-aware) data model** — it is not a variant of Fase V, and building it is not a matter of reusing Fase V's builders.

## 1. What Fase IV actually is

Per TCE-SP's own presentation text (all 5 manual PDFs read for this audit): *"Fase IV do Sistema AUDESP – Licitações e Contratos"*, covering the modules Licitação, Ajuste (sub-módulo Empenho), Exigência de Obras, Execução do Ajuste, Termo Aditivo, Documento Fiscal, Pagamentos, Declaração Negativa (a **different** Declaração Negativa from Fase V's — this one covers "no ajuste/empenho/execução/etc. was signed this period," not "zero repasses this ajuste").

It registers the **legal instrument itself** — a contract, comodato, arrendamento, concessão, or (per the current schema) a bare nota de empenho — as a generic government-procurement artifact. Fase V, by contrast, registers the **accountability of repasses already made** under an ajuste that (per this audit) Fase IV should already know about. The two phases are sequential and both mandatory for the same 5 third-sector instrument types (Contrato de Gestão, Convênio, Termo de Colaboração, Termo de Fomento, Termo de Parceria) per TCE-SP's own communications: mandatory electronic remittance for these instruments started 2023-06-01, with a 10-business-day-from-signature deadline — language that appears in both phases' own manuals.

**Reformulation in flight.** Most of the 8 sub-modules above still read as the legacy browser-only "Coletor" UI (the 2016/2018 manual PDFs are screenshots of a login-and-click flow: "Prestação de Dados – Interação Direta"). Only **Licitação, Edital, Ata, Ajuste, and Empenho** currently have downloadable JSON Schemas (`tce.sp.gov.br/audesp/documentacao/reformulacao-fase-iv-jsonschemas-e-documentacao-xlsx`) — Termo Aditivo, Execução, Documento Fiscal, Pagamentos, and Fase IV's own Declaração Negativa do **not**, despite `ContractAddendum` already existing in our domain model. Building JSON automation for those today would mean guessing at a schema TCE-SP hasn't published — not attempted here.

## 2. Endpoints (confirmed from the live OpenAPI spec)

Same base URLs and bearer-token auth as Fase V (`AudespClient._login`/`_auth_headers` reused as-is — confirmed against the same `audesp.yaml` spec):

| Action | Method | Path |
|---|---|---|
| Send Ajuste (or Empenho — see below) | POST | `/recepcao-fase-4/f4/enviar-ajuste` |
| Query status | GET | `/f4/consulta/{protocolo}` |
| Send Edital / Licitação / Ata (not built — see §4) | POST | `/recepcao-fase-4/f4/enviar-edital` / `enviar-licitacao` / `enviar-ata` |

No dedicated "enviar-empenho" endpoint exists. Per the Ajuste manual's own footnote ("O sub-módulo Empenho será utilizado apenas para cadastrar outras Notas de Empenhos para um mesmo contrato") and confirmed by the OpenAPI spec having no empenho path, **both document shapes post to the same `enviar-ajuste` endpoint** — `AudespClient.enviar_ajuste()` is shape-agnostic by design.

## 3. Field mapping (ground truth: the downloaded JSON Schemas + TCE-SP's 2026 label spreadsheet)

### 3.1 Ajuste (`docs/audesp_fase_iv/ajuste_v2_0_0/ajuste_schema_v2.json`)

| Schema field | Source | Confidence |
|---|---|---|
| `descritor.municipio` / `.entidade` | `contract.area.city_hall.audesp_municipality_code` / `contract.organization.audesp_entity_code` | Confirmed (Phase 0 fields) |
| `descritor.adesaoParticipacao` | `False` | Confirmed — third-sector direct instruments aren't bidding-consortium adhesions |
| `descritor.codigoContrato` | `contract.audesp_agreement_code` | Confirmed — same field Fase V already uses for `codigo_ajuste` |
| `descritor.codigoEdital` | **caller-supplied, required param** | **Open** — see §5.1 |
| `fonteRecursosContratacao` | distinct `BudgetCommitment.funding_source_type` values, or explicit `funding_sources=` | Confirmed — same `AudespFundingSourceTypeChoices` enum, values match the schema's `enum` exactly |
| `itens` | **caller-supplied, required param** | **Open** — see §5.1 |
| `tipoContratoId` | `1` ("Contrato (termo inicial)") | Inferred — see §5.2 |
| `numeroContratoEmpenho` | `contract.code` (fallback `str(contract.internal_code)`) | Confirmed, with fallback |
| `anoContrato` | `(signature_date or start_of_vigency).year` | Confirmed |
| `categoriaProcessoId` | `8` ("Serviços") | Inferred — see §5.2 |
| `receita` | `False` | Confirmed — SITTS only models city-hall-pays-OSC transfers |
| `niFornecedor` / `tipoPessoaFornecedor` / `nomeRazaoSocialFornecedor` | `contract.organization.document` / `"PJ"` / `contract.organization.name` | Confirmed — OSCs are always legal entities in this system |
| `objetoContrato` | `contract.objective` | Confirmed |
| `valorInicial` | `contract.original_value` | Confirmed |
| `dataAssinatura` | `contract.signature_date` (new field — §6) | Confirmed |
| `dataVigenciaInicio` / `dataVigenciaFim` | `contract.start_of_vigency` / `end_of_vigency` | Confirmed |
| `tipoObjetoContrato` | `27` ("Outras prestações de serviço") | Inferred — see §5.2 |

### 3.2 Empenho (`docs/audesp_fase_iv/empenho_v1/empenho_schema_v1.json`)

Only 3 top-level fields (`additionalProperties: false`): `descritor` (municipio/entidade/numeroEmpenho/anoEmpenho/retificacao), `codigoContrato`, `dataEmissaoEmpenho` — all sourced directly from the pre-existing `accountability.BudgetCommitment` model (which already closes the gap [fase-v.md](fase-v.md) §5 flagged as missing — see §7 below). No open questions on this half.

**Discrepancy worth flagging:** TCE-SP's 2026 label spreadsheet's "Empenho de Contrato" sheet documents 5 more fields (`tipoPessoa`, `niCredorFornecedor`, `nomeCredorFornecedor`, `codigoNaturezaDespesa`, `fonteRecurso`) that are **not** in the currently-downloadable schema, which forbids additional properties. The spreadsheet appears to describe a schema revision ahead of what's live — sending those fields today would fail validation, so the builder deliberately omits them. Re-check `empenho_schema_v1.json` for a new version before this goes live.

## 4. Scope decision

**Built:** Ajuste registration + Empenho registration (`audesp/builders/fase_iv/`, `AudespFaseIVSubmission`, `AudespClient.enviar_ajuste`/`consulta_fase_iv`, `audesp.services.build_and_validate_fase_iv_*`/`submit_fase_iv`).

**Not built, by design:** Licitação/Dispensa/Inexigibilidade registration (the `enviar-licitacao` module). TCE-SP's own field rules for Ajuste are explicit that `codigoEdital` must reference an **already-registered** Licitação/Dispensa document ("Validar se a Licitação foi cadastrada: -Se adesaoParticipação = false: município, entidade e codigoEdital") — Ajuste is not a standalone submission. The Licitação module's own field list (50 rows: licitantes, habilitação results, orçamento/proposta values, garantias, índices econômicos) models the city hall's own procurement/selection process — a different business process SITTS has never captured and, per this system's own scope (third-sector fund-transfer accountability for the receiving OSC side), arguably shouldn't: it's the city hall's procurement/legal department's process, not the NGO-accountability platform's.

This mirrors the precedent [fase-v.md](fase-v.md) §2 already set for certidão references: *"these are NOT free text — they're IDs of records that must already exist in AUDESP itself... we only need to store and validate the reference id, not build the issuance system."* `codigo_edital` and `itens` are therefore **required, explicit parameters** on `fase_iv.ajuste.build_payload` — never inferred or defaulted — so a caller is forced to supply a real, externally-registered value rather than get a silently-wrong one.

If SITTS should own Licitação/Dispensa registration too (e.g., because no other system currently does it for these city halls), that's a real, separate scope decision — flag it and this doc can be extended with a §8 the same way Fase V grew phases.

## 5. Open questions

### 5.1 `codigoEdital` / `itens` for non-bidding instruments (blocking)

Convênios, Termos de Parceria/Colaboração/Fomento are typically selected via chamamento público (Lei 13.019/2014) or dispensa/inexigibilidade, not a formal competitive licitação. The Licitação module's title ("Cadastro e retificação de Licitações, **Dispensas e Inexigibilidades**") confirms exemption processes do get a Licitação-shaped record — but this audit did not confirm exactly which of that module's ~50 fields are mandatory-even-for-a-dispensa vs. bidding-only, nor whether a chamamento público (a Lei 13.019 concept, not a Lei 8.666/14.133 one) maps cleanly onto "Dispensa" or needs its own treatment. Resolve via TCE-SP support ("Fale Conosco" → "Fase IV") before any real submission.

### 5.2 `tipoContratoId` / `categoriaProcessoId` / `tipoObjetoContrato` (non-blocking, but unconfirmed)

These are PNCP's generic public-procurement taxonomies (confirmed via the 2026 label spreadsheet), and **none of their values name a third-sector partnership** — `tipoContratoId = 6` ("Convênio") was in fact revoked by Portaria Conjunta MGI/MF/CGU 33/2023 and is excluded from the schema's own `enum`. The values used here (`1`, `8`, `27`) are the closest reasonable fit by definition text, not a TCE-SP-confirmed mapping for "this is a Termo de Parceria." Low risk (these are classification/reporting fields, not identity/linkage ones), but worth a support-ticket confirmation before produção use.

### 5.3 Fase IV's own retificação/status vocabulary

`AudespClient.consulta_fase_iv` returns whatever `/f4/consulta/{protocolo}` sends — not yet confirmed against a live response (no piloto credentials exercised against Fase IV yet, mirroring the same caveat already logged for Fase V in [fase-v.md](fase-v.md) §8).

## 6. Model changes

- `Contract.signature_date` (new, nullable) — Contract had no field distinct from `start_of_vigency` for "data de assinatura," which Fase IV's `dataAssinatura` requires as its own concept.
- `Contract.audesp_agreement_code`'s help_text updated — it's now documented as serving both Fase V's `codigo_ajuste` and Fase IV's `descritor.codigoContrato` (same value, same field, confirmed identical semantics from both schemas' field descriptions).
- `audesp.AudespFaseIVSubmission` (new) — mirrors `AudespSubmission`'s shape; one `document_type` (AJUSTE/EMPENHO) instead of a separate model per shape, since both share a lifecycle, an endpoint, and a status vocabulary.

## 7. Corrections to fase-v.md

Its own gap matrix (§5) said *"Empenhos (none) — no concept of 'empenho' (budget commitment) exists anywhere."* That's stale: `accountability.BudgetCommitment` already exists (added during this project's earlier phases) and is exactly what Fase IV's Empenho builder above reads from — no new domain model was needed for it, only the AUDESP-submission-tracking layer (`AudespFaseIVSubmission`).

---

## Sources

- [Reformulação da Fase IV - JSON/Schemas e Documentação em XLSX](https://www.tce.sp.gov.br/audesp/documentacao/reformulacao-fase-iv-jsonschemas-e-documentacao-xlsx) — real `ajuste-schema-v2_0_0.zip`, `empenho-JSONSchemaeExemplo_1.zip`, and `Novo Modelo da Fase IV_2026_v02_externo.xlsx` downloaded from here
- [Fase IV do Sistema AUDESP - Manual](https://www.tce.sp.gov.br/audesp/documentacao/fase-iv-sistema-audesp-manual) — all 8 legacy sub-module PDFs (Edital, Licitação, Ajuste, Execução, Exigências de Obras, Documento Fiscal/Pagamentos, Termo Aditivo, Declaração Negativa)
- [Módulo de Ajuste - Liberação - Sistema Audesp - Nova Fase IV](https://www.tce.sp.gov.br/legislacao/comunicado/modulo-ajuste-liberacao-sistema-audesp-nova-fase-iv)
- `https://audesp.tce.sp.gov.br/api/audesp.yaml` — OpenAPI spec, confirms `/recepcao-fase-4/f4/enviar-ajuste` and `/f4/consulta/{protocolo}`, no dedicated empenho path

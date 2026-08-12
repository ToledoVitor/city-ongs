# AUDESP Fase V — Compliance Audit & Integration Plan

> Moved here from the repo root during the context audit. Loaded via the
> `sitts-audesp` skill rather than sitting in every session's context. Kept
> intact — the reasoning and the caveats are the value, and the phase status
> below is the closest thing to a changelog for this integration.


Status: audit complete, no code changed yet. Source docs cross-checked: Manual v1.18 (TCESP), live JSON Schemas v1.14 (downloaded from `tce.sp.gov.br/audesp/documentacao/audesp-repasses-ao-terceiro-setor-jsonschemas`), OpenAPI spec v1.17.0 (`audesp.tce.sp.gov.br/api/audesp.yaml`), full repo model scan.

Nothing in this codebase is deployed yet — every recommendation below assumes we can redesign schemas/flows/auth freely, no migration-safety constraints, no backward-compat shims.

---

## 0. Goals

- **Primary**: every ajuste type (Contrato de Gestão, Convênio, Termo de Colaboração, Termo de Fomento, Termo de Parceria) can produce a valid Fase V JSON document, pass local schema validation, and submit successfully to AUDESP (piloto first, then produção) — for both the initial submission and the annual retificação/declaração-negativa paths.
- **Data model**: every field AUDESP requires has a single, typed, non-ambiguous home in our schema — no free-text stand-ins for enums (documento_tipo, fonte_recurso_tipo, categoria_despesas_tipo, tipo_veiculo_publicacao, etc.), no CPF/CNPJ stored as plain CharField.
- **No silent submission failures**: every `Rejeitado` response surfaces its `erros[]` in an ops UI with a direct fix-and-resubmit path; every cascading effect (retificação of an old exercício excluding newer ones) is visible before it happens, not discovered after.
- **Single source of truth for the payload**: one builder per ajuste type assembled from real domain models — not a one-off script re-deriving numbers per submission, the same failure mode the current 14 PDF exporters already have.
- **Transparência portal actually matches §34**: the app named for this literally has no compliance checklist today; closing that gap is a named goal, not a side effect.
- **Long-term**: every existing feature (contracts, accountability, reports, transparency_portal) converges toward AUDESP's data shape rather than AUDESP being bolted on as an afterthought — per the original ask, all features should end up serving this compliance requirement.

---

## 1. What AUDESP Fase V actually requires

Third-sector transfer accountability ("Prestação de Contas dos Repasses ao Terceiro Setor") is submitted as a JSON document over REST, one document per `(ajuste, exercício)` per year (`mes` field is always `12` — annual, not monthly, despite the name).

### 1.1 Ajuste types (5) + Declaração Negativa, each its own endpoint

| Ajuste type | Endpoint | Notes |
|---|---|---|
| Contrato de Gestão | `POST /f5/enviar-prestacao-contas-contrato-gestao` | only type requiring §22 Regulamento de Compras, §25 Comissão de Avaliação, §30 Publicação Relatório Atividades, §31 Termo Cessão Bens |
| Convênio | `POST /f5/enviar-prestacao-contas-convenio` | only type requiring §26 Relatório Governamental; `servidores_cedidos` required |
| Termo de Colaboração | `POST /f5/enviar-prestacao-contas-termo-colaboracao` | §27 Relatório Monitoramento; `servidores_cedidos` **not** applicable |
| Termo de Fomento | `POST /f5/enviar-prestacao-contas-termo_fomento` | same shape as Colaboração |
| Termo de Parceria | `POST /f5/enviar-prestacao-contas-termo-parceria` | only type requiring §23 Publicação Extrato Execução; `servidores_cedidos` required |
| Declaração Negativa | `POST /f5/declaracao-negativa` | minimal: only `descritor` + `codigo_ajuste` |

Confirmed directly from the downloaded JSON Schemas' top-level `required[]` (not just manual prose) — see §3 below for the full per-type matrix.

### 1.2 Workflow (no interactive UI — API only)

1. `POST /login` with header `x-authorization: <usuario>:<senha>` → bearer token (JWT).
2. `POST /f5/enviar-prestacao-contas-{tipo}` with `multipart/form-data`, field `documentoJSON` = the JSON file. Returns `{protocolo, mensagem}` on 200, or a schema-validation error list on 400.
3. `GET /f5/consulta/{protocolo}` → `{status, erros[]}`. Status values: `Recebido` → `Armazenado` (accepted) | `Rejeitado` (has `erros[]`, classificação `Indicativo`/`Impeditivo`, fix and resend) → eventually `Substituído` (overwritten by retificação) or `Excluído` (cascaded exclusion, see below).
4. **Retificação**: resend a *complete* document with `retificacao: true`. Fully replaces the prior submission. Retifying an exercício older than the latest submitted one cascades — all subsequent exercícios flip to `Excluído` and must be resent. `retificacao` is an optional top-level boolean in all 5 real ajuste-type JSON Schemas (confirmed against `docs/audesp/`; absent from Declaração Negativa's schema). The cascade rule is now handled locally — see §8 Phase 5 and §9.
5. **Declaração Negativa**: required for any exercício where the ajuste had zero repasses. Auto-overwritten by a real prestação for the same period unless later exercícios already exist (then needs a retificação instead).
6. Environments: `audesp-piloto.tce.sp.gov.br` (piloto starts at exercício 2024) vs `audesp.tce.sp.gov.br` (produção, exercício ≥ 2025). Separate TCESP credential + permission per environment (`Transmissão Pacotes - Fase V`).

### 1.3 Document anatomy — 37 field-blocks in 6 groups

- **Identificação**: descritor, código do ajuste, dados gerais da entidade beneficiária, prestação de contas da entidade beneficiária, responsáveis e membros do órgão concessor
- **Financeiro**: empenhos, repasses, receitas, contratos, documento fiscal, glosas, pagamentos, ajuste de saldo, descontos e devoluções, disponibilidades
- **Empregados e Bens**: relação de empregados, relação de servidores cedidos, relação de bens, termo da relação de bens cedidos
- **Relatórios de Atividades**: programas e metas
- **Relatórios e Publicações**: comissão de avaliação / relatório governamental / monitoramento e avaliação (mutually exclusive by ajuste type), regulamento de compras, extrato de execução física-financeira, relatório de atividades, demonstrações contábeis, parecer/ata
- **Declarações e Parecer Conclusivo**: declarações, transparência, parecer conclusivo

Full field/rule extraction (all 37 sections) is preserved in this session's history; ping for the complete field-by-field table if needed when we get to implementation — this doc keeps only what drives architecture/gap decisions.

---

## 2. Recurring structural patterns (design these once, reuse everywhere)

- **Documento/Credor triple**: `{documento_tipo: 1=CPF|2=CNPJ|3=RNE, documento_numero, nome}` — repeated in Contratos, Documentos Fiscais, Pagamentos, Ajustes de Saldo, Glosas.
- **Publicação relation**: `{tipo_veiculo_publicacao: 1..10, nome_veiculo, data_publicacao, endereco_internet?}` — identical shape + identical validation rules reused across §22/23/28/29/30. Build **one** model/serializer, not five.
- **Folha Ordinária special case**: payroll payments use sentinel `9999` for documento-fiscal número and numero_transacao, have no linked documento fiscal, and glosa analysis for them is optional and keyed by `pagamento_data` instead.
- **Composite uniqueness keys are precise and change between schema versions** (e.g. repasses' key gained `fonte_recurso_tipo` in v1.12) — don't hardcode assumptions, mirror the schema's actual key each time we bump versions.
- **Date-window rule**: virtually everything must fall within the `ano` given in descritor, with explicit named exceptions (first prestação's documento fiscal emissão, §12 inclusão entries predate the period, glosa análise dates may be current-or-earlier).
- **Certidão references** (§20/§21): these are NOT free text — they're IDs of certidão records that must already exist, concluded, in AUDESP itself (a separate subsystem — confirmed to be Fase IV, see [fase-iv.md](fase-iv.md); its own `codigoEdital` field has the identical "must already be registered elsewhere" shape). We only need to **store and validate the reference id**, not build a certidão issuance system.

---

## 3. Ajuste-type × required-block matrix (ground truth from JSON Schema `required[]`)

| Block | Contrato Gestão | Convênio | Termo Colab. | Termo Fomento | Termo Parceria |
|---|:---:|:---:|:---:|:---:|:---:|
| relacao_empregados, relacao_bens, contratos, documentos_fiscais, pagamentos, disponibilidades, receitas, ajustes_saldo, descontos, devolucoes, glosas, empenhos, repasses, relatorio_atividades, dados_gerais_entidade_beneficiaria, responsaveis_membros_orgao_concessor, declaracoes, demonstracoes_contabeis, publicacoes_parecer_ata, prestacao_contas_entidade_beneficiaria, parecer_conclusivo, transparencia | ✓ | ✓ | ✓ | ✓ | ✓ |
| servidores_cedidos | ✓ | ✓ | — | — | ✓ |
| publicacao_regulamento_compras | ✓ | — | — | — | — |
| relatorio_comissao_avaliacao | ✓ | — | — | — | — |
| publicacao_relatorio_atividades | ✓ | — | — | — | — |
| relatorio_governamental_analise_execucao | — | ✓ | — | — | — |
| relatorio_monitoramento_avaliacao | — | — | ✓ | ✓ | — |
| publicacao_extrato_execucao_fisica_financeira | — | — | — | — | ✓ |

Declaração Negativa: only `descritor` + `codigo_ajuste`.

---

## 4. Current system inventory (condensed)

Apps: `accounts`, `accountability`, `activity`, `bank`, `contracts`, `dashboard`, `reports`, `transparency_portal`. No DRF, no outbound HTTP client dependency, no Celery/async worker (Cloud Run WSGI only — inferred from `core/settings.py`'s GCP Secret Manager bootstrap and `*.run.app` CSRF_TRUSTED_ORIGINS; no dedicated architecture doc exists in this repo to cite instead). Session-based Django auth. Zero prior AUDESP work anywhere in the repo (`grep -ri audesp|tce|webservice` → nothing except legal boilerplate text in the PDF exporters).

Closest existing analog: `reports/exporters/pass_on_1.py..14.py` — PDF generators for TCESP's **pre-AUDESP** "Anexo RP-01..14" paper forms. These prove the underlying data (contract, expense, revenue, bank) mostly exists in the DB, but each exporter independently re-queries the DB — there's no shared "prestação de contas payload" object to build the AUDESP JSON from.

Key models today:
- `contracts.Contract` — the "ajuste": objeto, vigência, valores, concession_type (maps loosely to tipo_documento), FKs to `Company` (has typed `CNPJField`), goals/steps/executions/items with a rich `NatureChoices` expense taxonomy (~90 categories).
- `accountability.Accountability` — monthly wrapper around `Expense`/`Revenue` per contract/month/year.
- `accountability.Expense` / `Revenue` — ledger lines with `source` (ResourceSource), `nature`, `document_type`, dates, values.
- `accountability.ResourceSource` — fonte de recurso, has an `origin` enum that loosely parallels `fonte_recurso_tipo` and a `category` enum that parallels ajuste type.
- `bank.BankAccount` / `Transaction` — OFX-based reconciliation.
- `transparency_portal` — public read-only views over contract/accountability data.
- `accounts.User` — login/auth user, **not** an employee/servidor registry (no CBO, no admissão/demissão, no salário contratual).

---

## 5. Gap matrix

This table is the **pre-implementation snapshot** (state at first audit) — it is not re-edited as gaps close. §7/§8 record what was actually built; most "High" rows here (Descritor, Código do ajuste, Relação de Empregados/Servidores Cedidos/Bens, Empenhos, Repasses) were resolved during Phase 0 (§8) — check §7/§8 or the current models before treating any row below as still open.

| AUDESP block | Current model | Gap | Severity |
|---|---|---|---|
| Descritor (município/entidade codes) | none | `CityHall`/`Organization` have no IBGE município code or AUDESP entidade code | High — blocks every submission |
| Código do ajuste | `Contract.code` (free text, 16 char) | no AUDESP-format code, no cross-check against AUDESP's ajuste registry | High |
| Relação de Empregados | **none** | no CPF/CBO/CNS/salário-contratual/admissão-demissão registry at all; `User` is login-only | High |
| Relação de Servidores Cedidos | **none** | same gap, plus `onus_pagamento` concept doesn't exist | High |
| Relação de Bens | `ContractItem` (procurement line, not an asset registry) | no individually-numbered patrimônio, no `valor_cessao`, no baixa/devolução tracking | High |
| Contratos (§7) | `Contract` + `Company` | missing `credor` triple typing (documento_tipo enum), `vigencia_tipo`, `criterio_selecao`, `natureza_contratacao` multi-select, `valor_tipo`; `Company.cnpj` is typed but almost every other document field in the repo is untyped CharField+validator | Medium |
| Documentos Fiscais | `Expense.document_type`/`document_number` | no `estado_emissor`, `categoria_despesas_tipo` (89-value AUDESP taxonomy vs. our ~90-value `NatureChoices` — different codes, need mapping table not 1:1), `rateio_proveniente_tipo`/`rateio_percentual` | Medium |
| Pagamentos | `Expense` (paid/conciled flags) | no `fonte_recurso_tipo`, no `meio_pagamento_tipo`, no `numero_transacao`/banco/agência/conta_corrente as a structured payment record separate from the expense itself | Medium |
| Empenhos | **none** | no concept of "empenho" (budget commitment) exists anywhere; Repasses in AUDESP are *linked to an empenho*, ours aren't | High |
| Repasses (§18, linked to empenho) | `ContractMonthTransfer` (unlinked, just month/year/value) | needs full rebuild: `identificacao_empenho`, `valor_previsto` vs `valor_repasse`, `justificativa_diferenca_valor`, bank-document typing | High |
| Receitas (§11) | `Revenue` | `revenue_nature` enum conceptually anticipates this but doesn't carry `fonte_recurso_tipo`; no split of repasses_recebidos / outras_receitas / recursos_proprios per AUDESP shape | Medium |
| Ajustes de Saldo (§12) | **none** | no retificação/inclusão mechanism for prior-period repasses or pagamentos | High |
| Descontos / Devoluções | side-effect only (`Expense.planned=False` on glosa, no dedicated fields) | no value/date/motivo/`natureza_devolucao_tipo` fields | High |
| Glosas (§16) | boolean flag + `ActivityLog` entry | no `resultado_analise`, no `valor_glosa`, no per-documento-fiscal-required-analysis enforcement, no Folha Ordinária path | High |
| Disponibilidades (§10) | `BankAccount.current_balance` (computed) | no year-end snapshot model (saldo_bancario vs saldo_contabil), no saldo_fundo_fixo | Medium |
| Relatório de Atividades (§19) | `ContractGoal`/`ContractStep`/`ContractExecutionActivity` | conceptually present but missing `periodicidade` typing, `quantidade_realizada`/`resultado_meta`, and the AUDESP `codigo_meta` linkage | Medium |
| Dados Gerais / Responsáveis certidões (§20/21) | **none** | no field to store the AUDESP certidão reference IDs at all | High (but scope = reference-storage, not issuance) |
| Publicação blocks (§22/23/28/29/30) | **none** | no generic "publicação" model; nothing tracks regulamento de compras, demonstrações contábeis, or parecer/ata publication | High |
| Relatório Comissão/Governamental/Monitoramento (§25/26/27) | **none** | no model for these per-ajuste-type-exclusive reports | Medium |
| Declarações (§24) | **none** | conflict-of-interest / related-party declarations don't exist | Medium |
| Transparência (§34) | `transparency_portal` publishes data but has no compliance **self-assessment checklist** | needs the exact 8+6+10-item checklist (arts. 7º/8º§1º, 8º§3º, divulgação) conditioned on `entidade_beneficiaria_mantem_sitio_internet` | High — directly affects the app already named for this |
| Parecer Conclusivo (§33) | **none** | 7 fixed declarações + conclusão + considerações | Medium |
| Prestação de Contas da Entidade Beneficiária (§32) | `Accountability` (month/year only) | no `data_prestacao`/período de referência distinct from the exercício | Low |

---

## 6. Target architecture

New dedicated Django app, e.g. **`audesp`**, holding *integration* concerns only — the domain data stays in `contracts`/`accountability`/`accounts`/etc., `audesp` builds payloads and talks to TCESP:

```
audesp/
  clients.py          # AudespClient: /login token cache+refresh, submit, consulta, retificação, declaração negativa
  builders/            # one builder per ajuste type, composing the 37 blocks from domain models
    contrato_gestao.py
    convenio.py
    termo_colaboracao.py
    termo_fomento.py
    termo_parceria.py
    declaracao_negativa.py
    shared.py          # documento/credor triple, publicação relation, date-window helpers
  validators.py         # validate built payload against the downloaded JSON Schema files (python `jsonschema` lib) before sending
  models.py             # AudespSubmission (protocolo, tipo, exercicio, status, erros, raw_payload, submitted_at), AudespCredential (env-scoped)
  services.py           # orchestration: build → validate → submit → poll → surface inconformidades
  admin.py / views.py    # ops screen: pick ajuste+exercício, preview payload, submit, see status/erros, one-click retificação
```

Why a dedicated app instead of bolting onto `contracts`/`accountability`: the builders need read access across nearly every app (contracts, accountability, accounts, bank, transparency_portal) and the submission lifecycle (protocolo/status/erros) is its own concern, not a property of any single domain model.

New infra needed: `requests` as a direct dependency (already transitive), `jsonschema` for local pre-validation, and *some* background execution — today it's Cloud Run WSGI only with no Celery. Simplest fit: a Django management command triggered by Cloud Scheduler (matches existing GCP setup) rather than introducing Celery for one monthly-ish job. Submission itself is a simple synchronous POST, so no queue is strictly required — only the *trigger* needs to be scheduled.

---

## 7. Concrete model/schema changes, by app

Code is English-only throughout (class/field/choice names) — only `verbose_name`/`help_text`/labels are Portuguese. See `CLAUDE.MD` § Django Conventions. Names below are the actual English names landed in Phase 0, not the Portuguese working names from the original plan.

**accounts**
- Added `audesp_entity_code` (int) and `audesp_municipality_code` (int, IBGE) to `Organization`/`CityHall`.
- New `Employee` model: cpf, cbo, cns (nullable), contractual_salary, admission_date, termination_date, monthly `EmployeeRemunerationPeriod` child rows (year, month, hours_worked, gross_remuneration). New `CededServant` model (cession_start_date/end_date, public_position_held, role_performed, payment_burden) + `CededServantRemunerationPeriod`. Both independent from `User` (login) — an org can have employees/ceded servants who never log in.
- CPF/CNPJ field-type normalization (`Company.cnpj` typed vs. everywhere else plain CharField+validator) explicitly NOT done — logged in the `sitts-known-bugs` skill as out-of-scope tech debt.

**contracts**
- Added `audesp_agreement_code` to `Contract`.
- New `SupplierContract` model (§7 "Contratos" — contracts the *beneficiary entity* signs with suppliers using ajuste money, distinct from `contracts.Contract` which is the ajuste/repasse instrument itself): number, creditor_document_type/number/name, signature_date, validity_type, validity_start/end_date, purpose, contracting_nature (+other), selection_criteria (+other), purchase_regulation_article, amount, value_type.
- New `Asset` model (event-based — one row per lifecycle event, matching the JSON array shape): category (movable/immovable), event (acquired/ceded/written off), asset_number, description, date, value.
- New `CertificateReference` model storing the AUDESP certidão IDs referenced in §20/21, scoped to (contract, type).
- Extended `ContractGoal` with `goal_code`, `periodicity_type` + new `ContractGoalAnnualResult`/`ContractGoalPeriodResult` child models (§19 relatório de atividades).

**accountability**
- New `AnnualStatement` model — the (contract, fiscal_year) anchor matching AUDESP's own unit of submission (one JSON document per descritor.ano). Everything below that's inherently annual (not date-driven like the ledger) hangs off it.
- New `BudgetCommitment` model (number, issue_date, economic_classification, funding_source_type, value, description, spending_authority_cpf) — the "empenho" concept.
- New `FundTransfer` model linked to `BudgetCommitment` (planned_date/transfer_date, planned_value/transferred_value, value_difference_justification, bank-document fields) — the "repasse" concept. Does NOT touch `contracts.ContractMonthTransfer` (see note in §8).
- New `ExpenseRejection` model (expense ref or Folha Ordinária payment_date, analysis_result, rejected_value) — the "glosa" concept; enforce "every documento fiscal needs an analysis" at the builder/validation layer.
- New `Deduction` / `Refund` models (date, description/nature, value) — "desconto"/"devolução", replacing the current boolean-flag-only side effect.
- New `BalanceAdjustment` model (type-discriminated: transfer/payment correction/inclusion) for prior-period corrections — "ajuste de saldo".
- New `AvailableFunds` snapshot model + `BankBalance` children (bank_balance vs accounting_balance per account, petty_cash_balance) taken at fiscal-year close — "disponibilidade".
- Extended `Revenue`/`Expense` to carry `funding_source_type` explicitly instead of relying on the loosely-parallel `origin` enum.
- New `PublicationBase` abstract model (publication_vehicle_type, vehicle_name, publication_date, website_url) with one concrete child per publication context: `PurchasingRegulationPublication`, `PhysicalFinancialExecutionStatementPublication`, `FinancialStatementsPublication`, `ActivityReportPublication`, `OpinionOrMinutesPublication`.
- New `EvaluationReport` model (final_report_issued, conclusion, justification) parametrized by which of §25/26/27 applies (derived from ajuste type, not stored separately).
- New `ConflictOfInterestDeclaration` (§24, + `RelatedCompany`/`BoardParticipation` children) and `ConclusiveOpinion` (§33, + `ConclusiveOpinionDeclaration` — 7 fixed declarations) models.

**transparency_portal**
- New `TransparencyChecklist` model mirroring §34 exactly: `has_website` bool + the 8 art.7º/8º§1º items + 6 art.8º§3º items + 10 divulgação items, each a bool. This app is *named* for this requirement and had nothing that mapped to it — highest-visibility gap, now closed.

---

## 8. Phased roadmap

0. ✅ **Foundational data model rebuild** — done. Models, migrations, and Django admin registration landed across `accounts` (Employee/CededServant registries + remuneration periods, entity/municipality AUDESP codes), `contracts` (SupplierContract, Asset, CertificateReference, ContractGoal annual/period results, audesp_agreement_code), and `accountability` (AnnualStatement anchor + all annual-only blocks: PurchasingRegulation, PhysicalFinancialExecutionStatement, FinancialStatements, ActivityReportPublicationStatus, OpinionOrMinutes, EvaluationReport, ConflictOfInterestDeclaration, ConclusiveOpinion, AvailableFunds — plus the contract-scoped ledger: BudgetCommitment, FundTransfer, ExpenseRejection, Deduction, Refund, BalanceAdjustment, and AUDESP fields added to Expense/Revenue). `transparency_portal.TransparencyChecklist` (§34) also landed. All class/field/choice names are English (only `verbose_name`/`help_text`/labels are Portuguese) — see `CLAUDE.MD` § Django Conventions. `python manage.py check` and `makemigrations --check` both pass. Not done: forms/custom UI for any of this (admin is the only data-entry surface right now) — see note below.
1. ⚠️ **Reference data** — partially done as a side effect of building the models: `AudespFundingSourceTypeChoices` (16 values), `AudespExpenseCategoryTypeChoices` (89 values), `AudespPublicationVehicleChoices` (10 values), and every other small enum are real `IntegerChoices`/`TextChoices` with confirmed labels from the JSON Schema. Still open: `bank` (~400 BACEN codes) and `issuing_state` (27 codes) have no confirmed label text anywhere in the source material, so they're stored as raw integers for now — logged in the `sitts-known-bugs` skill.
2. ✅ **Financial ledger completion** — done (folded into Phase 0 above, since the models turned out too interdependent to sequence separately). `Revenue`/`ResourceSource` got an additive `funding_source_type` field rather than a restructure — see the note on `ContractMonthTransfer` below.
3. ✅ **Reporting layer** — done (also folded into Phase 0): activity-report periodicity fields on `ContractGoal` + `ContractGoalAnnualResult`/`ContractGoalPeriodResult`, `ConflictOfInterestDeclaration`, `ConclusiveOpinion`, and the shared `PublicationBase` abstract model reused across all five publication call sites.
4. ✅ **JSON builder + local schema validation** — all 5 ajuste types plus Declaração Negativa done. New `audesp` app: `audesp/validators.py` validates a built payload against the downloaded JSON Schema files (`docs/audesp/`) using `jsonschema`, with a custom `multipleOf` override (see below). `audesp/builders/common.py` holds the 21 block builders identical in shape across all 5 schemas (parameterized at the 3 spots where Contrato de Gestão / Termo de Parceria allow one extra key — see below); each of `convenio.py`, `contrato_gestao.py`, `termo_colaboracao.py`, `termo_fomento.py`, `termo_parceria.py` composes those plus its own exclusive blocks per the §3 matrix, and `declaracao_negativa.py` handles the trivial descritor+codigo_ajuste-only case. Proven end-to-end against a real (sqlite, in-memory) ORM fixture — not just import-checked: all 5 builders plus Declaração Negativa (tested against all 5 real ajuste types) build a payload that `validate_payload()` accepts with zero errors. `audesp/models.AudespSubmission` tracks built payloads (append-only — one row per build/submit attempt, not a singleton, since AUDESP's own retificação flow means multiple attempts over time).
5. ⚠️ **AUDESP API client** — scaffolded, not yet exercised against a live server (no piloto credentials provisioned). `audesp/clients.py` (`AudespClient`): `/login` token handling (fixed-TTL cache, not a decoded JWT `exp` — see file docstring), `submit`/`submit_declaracao_negativa`, `consulta`, retry/backoff on connection errors, typed exceptions (`AudespAuthenticationError`/`AudespValidationError`/`AudespConnectionError`). Credential storage and ownership are both settled (see §10, no longer open): the AUDESP login belongs to the **`CityHall`** (órgão concessor), not the `Organization` — one município reports every organization under it through the same TCESP account, matching `descritor.municipio` already keying off `CityHall.audesp_municipality_code`. `audesp/models.AudespCredential` (`BaseModel`, FK to `CityHall`) is a pure existence/`is_active` registry — no username/password ever touches the database. `audesp/secrets.py` resolves the actual `(username, password)` pair: `.env` locally (`AUDESP_PILOTO_USERNAME`/`PASSWORD`, `AUDESP_PRODUCAO_USERNAME`/`PASSWORD`, a single shared dev pair regardless of city hall), GCP Secret Manager otherwise (one secret per `(city_hall, environment)`, created/rotated through the admin, mirroring `core/settings.py`'s existing Secret Manager bootstrap but per-tenant instead of one global blob). `audesp/services.py` wires build → validate → submit → poll for the 5 real ajuste types only; Declaração Negativa is still deliberately not orchestrated (see §10 — unrelated to credentials, this is the `AudespSubmission` modeling gap). Verified against a mocked HTTP layer and a mocked Secret Manager client (URL/resource-name construction, auth header format, multipart field name, token-cache reuse, retry/backoff, exception classification, secret create-vs-rotate branching) — not against a real TCESP server or a real GCP project. **Retificação cascade-exclusion is now implemented** (was previously "still missing" here): `audesp/models.AudespSubmission` gained a `retificacao` boolean field and a `StatusChoices.EXCLUDED` member (`Excluído`, distinct from `REJECTED` — a cascade-excluded submission was itself fine, it just needs a plain resend, unlike a rejected one which needs a fix). `build_and_validate(..., retificacao=True)` sets the payload's top-level `retificacao` key and persists the flag on the row. `submit()` checks, for a retificação, whether any `AudespSubmission` for the same `(contract, ajuste_type)` with a later `fiscal_year` is still `SUBMITTED`/`ACCEPTED` (`find_cascade_affected_submissions`, also public so a caller can preview the impact before submitting at all); if so it raises `AudespCascadeConfirmationRequired` unless called with `confirm_cascade=True`, in which case it flips those later rows to `EXCLUDED` atomically alongside the submit — mirroring what TCESP does server-side so local records don't go stale. `check_status` also now maps the webservice's own `Excluído` response to `StatusChoices.EXCLUDED`. Verified with a mocked-`requests` script against an in-memory sqlite fixture (normal submit, retificação with nothing later as a no-op, retificação cascading over a live newer exercício while correctly ignoring an already-rejected later year, a different ajuste_type, and a different contract). Still missing: inconformidade surfacing in an ops UI (the cascade guard above is the backend hook for it, not the UI itself), `Substituído` (same-exercício overwrite) status mapping, Cloud Scheduler-triggered management command for the submission window.
6. ✅ **Transparência alignment** — done (folded into Phase 0): `TransparencyChecklist` in `transparency_portal`.
7. **Cutover** — not started. Decide whether the legacy Anexo RP-01..14 PDF exporters retire once AUDESP submission is live, or stay as an internal/historical artifact.

**Note on `contracts.ContractMonthTransfer`**: the original plan said "rebuild into a repasse model." On closer reading of `contracts/views.py`, `ContractMonthTransfer` is the upfront planning/budget-split entered via the contract timeline UI (`contract_timeline_update_view`) — a different concept from AUDESP's repasse (the actual transfer execution, linked to a budget commitment). Left it untouched and added `accountability.FundTransfer` as a new, separate model instead — lower blast radius, no ambiguity between "planned" and "actual."

**What Phase 0 does *not* include**: forms, templates, or custom views for any of the ~30 new models — Django admin is the only way to enter this data today. That's a deliberate scope cut (matches the project's "no half-finished implementations" rule better than a rushed, non-compliant-with-`DESIGN.md` custom UI) but it's real remaining work, not a rounding error, before any of this is usable outside `/admin`.

**A real bug class the Convênio builder test surfaced**: jsonschema's stock `multipleOf` validator divides raw floats (`4.56 / 0.01` → `455.99999999999994` in IEEE 754), which would falsely reject nearly every AUDESP money field — every `multipleOf` in these schemas is 0.01. Fixed in `audesp/validators.py` by overriding the keyword to compare via `Fraction(str(x))`, which reconstructs the intended decimal value instead of its imprecise binary float. Worth remembering if this pattern gets ported anywhere else that validates money against JSON Schema.

**Also surfaced while building the Convênio reference implementation** (fixed, not deferred): `Expense` was missing `encumbrance_value` (§8 `valor_encargos`, a required documento-fiscal field) — added directly since it's within already-in-progress AUDESP coverage, not new scope. `relacao_bens`'s 6 sub-arrays each use *different* date/value key names (`data_aquisicao`/`valor_aquisicao` vs `data_cessao`/`valor_cessao` vs `data_baixa_devolucao` only) — the builder handles each explicitly rather than through one generic shape. `agencia` fields are AUDESP integers, but our `BankAccount.agency`/similar fields are free-text strings — `audesp/serializers/shared.serialize_agency()` casts between them. `dados_gerais_entidade_beneficiaria`'s `identificacao_certidao_responsaveis` key is Contrato de Gestão-only — including it for Convênio fails `additionalProperties: false`, since each ajuste-type schema is genuinely stricter than the union of all fields across types.

**Diffing all 5 schemas against each other** (ground truth, not assumption) found exactly 3 spots where a "common" block still varies by ajuste type, each parameterized in `common.py` rather than special-cased per builder: (1) `dados_gerais_entidade_beneficiaria` gains a 4th key (`identificacao_certidao_responsaveis`, sourced from a *different* `CertificateReference` type than the same-named key below — "responsáveis da entidade gerenciada" vs "responsáveis pelo órgão concessor") only for Contrato de Gestão; (2) `responsaveis_membros_orgao_concessor`'s optional 4th key doesn't exist as a property at all for Contrato de Gestão (would violate `additionalProperties: false` if emitted); (3) `declaracoes` gains `compras_contratacoes_adequados_regulamento_proprio` — already modeled on `ConflictOfInterestDeclaration.purchases_comply_with_own_regulation`, unused until now — for Contrato de Gestão and Termo de Parceria only. All three follow the same rule: omit the key entirely when the underlying value is `None`, never emit `null` — every field in these schemas is typed `string`/`boolean` with no `null` in its type union, so an included-but-null key fails the same as a missing required key, just with a worse error message (`None is not of type 'string'` vs `'x' is a required property`). Also fixed under this rule: the original Convênio builder's `responsaveis_membros_orgao_concessor` unconditionally emitted all 4 keys (even `None`) — harmless in the happy-path test (all 8 `CertificateReference` types were seeded) but would have broken the first real submission missing the optional 4th certidão.

**One more gap surfaced while writing the Phase 5 client's verification test** (fixed): `build_parecer_conclusivo` was the one block in `common.py` that read its OneToOne related object (`annual_statement.conclusive_opinion`) directly with no `try/except`, unlike its ~10 sibling blocks — so a contract missing a `ConclusiveOpinion` row raised a hard `RelatedObjectDoesNotExist` from inside `build_payload()` instead of producing a clean INVALID submission with a "required property missing" validation error. Fixed to match the pattern used everywhere else (return `{}` when missing, let the schema's `required[]` catch it). This matters specifically for `audesp/services.build_and_validate`, which assumes building a payload from incomplete data always *validates* to INVALID rather than *raising* — that assumption now holds for every block, not just most of them.

---

## 9. Concerns & risks

- **Cascading retificação exclusion**: retifying an exercício older than the latest submitted one flips all subsequent exercícios to `Excluído`, requiring a full resend of every year after it. A bad correction touching an early year is expensive to undo. **Backend guard implemented** (`audesp/services.submit`/`find_cascade_affected_submissions`, §8 Phase 5): submitting a retificação that would cascade-exclude later live exercícios raises `AudespCascadeConfirmationRequired` (carrying the affected fiscal years) unless called with `confirm_cascade=True`, and only then flips the affected rows to `EXCLUDED` locally. That's a backend hook, not the warning itself — the still-unbuilt ops UI is what needs to actually surface it to a human and ask before submission, not after.
- **CPF/CNS/salário data is sensitive (LGPD)**: the new Employee/Servidor registry stores personal data (health-card number, salary) for people who may never log into the system. Needs the same access-control discipline as existing personal data, arguably tighter (CNS ties to health records).
- **Certidão dependency on an external subsystem**: §20/§21 assume certidões already exist, concluded, in AUDESP itself (likely issued via a separate flow/portal, not Fase V). If an org hasn't obtained these certidões, no amount of correct modeling on our side unblocks submission — this is a process dependency outside our codebase.
- **Reference-data staleness**: `AudespFundingSourceTypeChoices`, `AudespExpenseCategoryTypeChoices`, `bank`, and similar enums are versioned by TCESP (already saw several corrected across manual revisions 1.9–1.18). Hardcoding them risks drift; needs an owner and a recheck cadence tied to manual version bumps.
- **`AudespExpenseCategoryTypeChoices` (89 values) vs. our `NatureChoices` (~90 values) are different taxonomies**, not a renaming exercise — building the mapping table is a real modeling task with room for misclassification, not a mechanical find-replace.
- **Annual deadline compliance is now a hard external constraint**: unlike internal accountability (flexible), AUDESP submissions are subject to TCESP deadlines with penalties for lateness — this changes the "nothing deployed yet" freedom for whichever exercício we go live with; confirm target exercício (2024 piloto vs 2025 produção) before scoping Phase 0's timeline.
- **No async infra today**: if a submission or retificação needs to run outside a request/response cycle (e.g., scheduled monthly attempt, batch resubmission after fixing several inconformidades), the Cloud Scheduler + management-command approach is the cheapest fit, but it's new operational surface (need alerting on failed scheduled runs, not just visibility in the ops UI).
- **Scope creep risk on this doc's own recommendations**: several proposed models (BudgetCommitment, Asset, PublicationBase, ExpenseRejection, BalanceAdjustment, etc.) are all "high severity, missing entirely" — this is a genuinely large schema surface for one project; sequencing (§8) matters more than trying to land it all in one PR.

---

## 10. Open decisions needing your input before implementation starts

**Resolved:**

- ~~Credential storage~~ → **GCP Secret Manager** for real credentials (one secret per `(city_hall, environment)`, JSON blob of `{username, password}`), **`.env`** for local dev (`AUDESP_PILOTO_USERNAME`/`PASSWORD`, `AUDESP_PRODUCAO_USERNAME`/`PASSWORD` — one shared pair, not per-city-hall, since local dev has no real multi-tenant AUDESP access anyway). Nothing sensitive is ever stored in Postgres — `AudespCredential` is just an `is_active` registry row. See `audesp/secrets.py`.
- ~~Does the AUDESP login belong to the beneficiary entity or the órgão concessor?~~ → **City hall** (`accounts.CityHall`). `AudespCredential` FKs to `CityHall`, not `Organization` — one município's login covers every organization under it. `audesp/services.py`'s `_client_for` resolves it via `submission.organization.city_hall`.

**Still open:**

- **How should a Declaração Negativa be recorded on `AudespSubmission`?** Its `AjusteTypeChoices` already has a `DECLARACAO_NEGATIVA` member (landed in Phase 4), but no field records *which* of the other 5 real ajuste types the declaration is actually for — `audesp/builders/declaracao_negativa.build_payload` takes that as an explicit parameter precisely to sidestep this, and `audesp/services.py` deliberately doesn't orchestrate Declaração Negativa submissions until this is settled (add a field? repurpose `ajuste_type` to always hold the real type plus a separate `is_declaracao_negativa` flag?).
- **Município/entidade/certidão codes**: manual entry per organization, or import from the TCE "coletor" spreadsheet (`tce.sp.gov.br/audesp/coletor`)?
- **Scheduling**: confirm Cloud Scheduler + management command is acceptable, vs. introducing Celery.
- **Employee data source**: who enters CPF/CBO/CNS/salário for each employee — new admin UI, or bulk import (e.g. from payroll/folha spreadsheet)?
- **`contracts.Contract`'s §7 "Contratos" ambiguity**: confirm the recommendation above (new `SupplierContract` model rather than overloading the ajuste-level `Contract`) matches your mental model of "contrato" in this domain.
- **Legacy Anexo RP reports**: keep, retire, or repurpose as an internal reconciliation view once AUDESP JSON is the real submission channel?

Downloaded reference material (schemas, examples, OpenAPI spec) is in the session scratchpad; worth relocating into the repo (e.g. `docs/audesp/`) once we start Phase 0 so future sessions don't need to re-download.

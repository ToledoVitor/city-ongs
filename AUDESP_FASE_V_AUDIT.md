# AUDESP Fase V — Compliance Audit & Integration Plan

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
4. **Retificação**: resend a *complete* document with `retificacao: true`. Fully replaces the prior submission. Retifying an exercício older than the latest submitted one cascades — all subsequent exercícios flip to `Excluído` and must be resent.
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
- **Certidão references** (§20/§21): these are NOT free text — they're IDs of certidão records that must already exist, concluded, in AUDESP itself (a separate subsystem, likely Fase IV / cadastro). We only need to **store and validate the reference id**, not build a certidão issuance system.

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

Apps: `accounts`, `accountability`, `activity`, `bank`, `contracts`, `dashboard`, `reports`, `transparency_portal`. No DRF, no outbound HTTP client dependency, no Celery/async worker (Cloud Run WSGI only per ARCHITECTURE.MD). Session-based Django auth. Zero prior AUDESP work anywhere in the repo (`grep -ri audesp|tce|webservice` → nothing except legal boilerplate text in the PDF exporters).

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

**accounts**
- Add `codigo_entidade_audesp` (int) and `codigo_municipio_audesp` (int, IBGE) to `CityHall`/`Organization`.
- New `Employee`/`Servidor` model: cpf, cbo, cns (nullable), salario_contratual, data_admissao, data_demissao, tipo (empregado da entidade | servidor cedido), cargo_publico_ocupado, funcao_desempenhada, onus_pagamento, monthly `RemuneracaoPeriodo` child rows (mes, carga_horaria, remuneracao_bruta). Independent from `User` (login) — an org can have employees who never log in.
- Normalize CPF/CNPJ fields to `django_cpf_cnpj`'s typed fields everywhere (currently only `Company.cnpj` is typed; `User.cnpj`, `Organization.document`, `CityHall.document`, `Favored.document`, `ResourceSource.document` are plain CharField+validator).

**contracts**
- Add `codigo_ajuste_audesp` to `Contract`, plus `vigencia_tipo`, `criterio_selecao`(+outro), `natureza_contratacao` (multi-select) — or model these on a new `ContratoAudesp` line-item since §7 "Contratos" is actually a sub-ledger of contracts-with-third-parties inside the ajuste, not the ajuste itself. Worth clarifying: AUDESP's §7 "Contratos" = contracts the *beneficiary entity* signs with suppliers, using ajuste money — distinct from `contracts.Contract` (the ajuste/repasse instrument itself). Recommend a new `SupplierContract` model rather than overloading `Contract`.
- New `Bem` (asset) model: numero_patrimonio, tipo (móvel/imóvel), descricao, data_aquisicao/valor_aquisicao, data_cessao/valor_cessao, data_baixa_devolucao.
- New `CertidaoReferencia` model (or simple FK fields) storing the AUDESP certidão IDs referenced in §20/21, scoped to ajuste + tipo de certidão.

**accountability**
- New `Empenho` model (numero, data_emissao, classificacao_economica, fonte_recurso_tipo, valor, historico, cpf_ordenador_despesa).
- Rebuild `ContractMonthTransfer` into a `Repasse` model linked to `Empenho` (identificacao_empenho, data_prevista/data_repasse, valor_previsto/valor_repasse, justificativa_diferenca_valor, bank-document fields).
- New `Glosa` model (documento fiscal ref or Folha Ordinária pagamento_data, resultado_analise, valor_glosa) — enforce "every documento fiscal needs a glosa analysis" at the builder/validation layer.
- New `Desconto` / `Devolucao` models (data, descricao/natureza_devolucao_tipo, valor) replacing the current boolean-flag-only glosa side effect.
- New `AjusteSaldo` (retificação/inclusão de repasses e pagamentos) for prior-period corrections.
- New `Disponibilidade` snapshot model (saldo_bancario vs saldo_contabil per conta, saldo_fundo_fixo) taken at exercício close.
- Extend `Revenue`/`ResourceSource` to carry `fonte_recurso_tipo` explicitly instead of relying on the loosely-parallel `origin` enum.
- New `Publicacao` generic model (tipo_veiculo_publicacao, nome_veiculo, data_publicacao, endereco_internet) with a `context` FK/tag reused for regulamento de compras, demonstrações contábeis, parecer/ata, extrato execução, relatório atividades.
- New `RelatorioAvaliacao` model (houve_emissao, conclusao, justificativa) parametrized by which of §25/26/27 applies (derived from ajuste type, not stored separately).
- New `Declaracao` (§24 conflict-of-interest) and `ParecerConclusivo` (§33, 7 fixed declarações) models.

**activity**
- Extend `ContractGoal`/`ContractStep` (or the AUDESP builder layer) with `codigo_meta`, `periodicidade` type, `quantidade_realizada`/`resultado_meta` — likely additive fields, not a rebuild, since the goal/step/execution skeleton already fits reasonably well.

**transparency_portal**
- New `TransparenciaChecklist` model mirroring §34 exactly: `mantem_sitio` bool + the 8 art.7º/8º§1º items + 6 art.8º§3º items + 10 divulgação items, each a bool `atende`. This app is *named* for this requirement and currently has nothing that maps to it — highest-visibility gap.

---

## 8. Phased roadmap

0. **Foundational data model rebuild** — since nothing's deployed, do the schema surgery in one pass rather than incrementally patching: add/rebuild the models in §7 above across `accounts`/`contracts`/`accountability`.
1. **Reference data** — seed the AUDESP domain tables we now depend on as choices/lookups: fonte_recurso_tipo (16 values, confirmed), categoria_despesas_tipo (89 values), tipo_veiculo_publicacao (10 values), banco (large BACEN list), estado_emissor (27 values), CBO — decide seed-once vs. periodic sync.
2. **Financial ledger completion** — Empenho, linked Repasse, Glosa, Desconto, Devolução, AjusteSaldo, Disponibilidade, Receita restructure.
3. **Reporting layer** — Relatório de Atividades periodicidade fields, Declarações, Parecer Conclusivo, generic Publicação model + its five call sites.
4. **JSON builder + local schema validation** — one builder per ajuste type assembling all applicable blocks per the §3 matrix, validated locally against the downloaded JSON Schema files before ever calling the API.
5. **AUDESP API client** — `/login` token handling, submit, `/f5/consulta`, retificação flow, declaração negativa, inconformidade surfacing in an ops UI, Cloud Scheduler-triggered management command for the submission window.
6. **Transparência alignment** — the §34 checklist inside `transparency_portal`.
7. **Cutover** — decide whether the legacy Anexo RP-01..14 PDF exporters retire once AUDESP submission is live, or stay as an internal/historical artifact.

---

## 9. Concerns & risks

- **Cascading retificação exclusion**: retifying an exercício older than the latest submitted one flips all subsequent exercícios to `Excluído`, requiring a full resend of every year after it. A bad correction touching an early year is expensive to undo — the ops UI must warn before submission, not after.
- **CPF/CNS/salário data is sensitive (LGPD)**: the new Employee/Servidor registry stores personal data (health-card number, salary) for people who may never log into the system. Needs the same access-control discipline as existing personal data, arguably tighter (CNS ties to health records).
- **Certidão dependency on an external subsystem**: §20/§21 assume certidões already exist, concluded, in AUDESP itself (likely issued via a separate flow/portal, not Fase V). If an org hasn't obtained these certidões, no amount of correct modeling on our side unblocks submission — this is a process dependency outside our codebase.
- **Reference-data staleness**: fonte_recurso_tipo, categoria_despesas_tipo, banco, and similar enums are versioned by TCESP (already saw several corrected across manual revisions 1.9–1.18). Hardcoding them risks drift; needs an owner and a recheck cadence tied to manual version bumps.
- **categoria_despesas_tipo (89 values) vs. our NatureChoices (~90 values) are different taxonomies**, not a renaming exercise — building the mapping table is a real modeling task with room for misclassification, not a mechanical find-replace.
- **Annual deadline compliance is now a hard external constraint**: unlike internal accountability (flexible), AUDESP submissions are subject to TCESP deadlines with penalties for lateness — this changes the "nothing deployed yet" freedom for whichever exercício we go live with; confirm target exercício (2024 piloto vs 2025 produção) before scoping Phase 0's timeline.
- **No async infra today**: if a submission or retificação needs to run outside a request/response cycle (e.g., scheduled monthly attempt, batch resubmission after fixing several inconformidades), the Cloud Scheduler + management-command approach is the cheapest fit, but it's new operational surface (need alerting on failed scheduled runs, not just visibility in the ops UI).
- **Scope creep risk on this doc's own recommendations**: several proposed models (Empenho, Bem, Publicacao, Glosa, AjusteSaldo, etc.) are all "high severity, missing entirely" — this is a genuinely large schema surface for one project; sequencing (§8) matters more than trying to land it all in one PR.

---

## 10. Open decisions needing your input before implementation starts

- **Credential storage**: piloto vs. produção TCESP credentials — store in GCP Secret Manager (already used per ARCHITECTURE.MD) rather than settings/env?
- **Município/entidade/certidão codes**: manual entry per organization, or import from the TCE "coletor" spreadsheet (`tce.sp.gov.br/audesp/coletor`)?
- **Scheduling**: confirm Cloud Scheduler + management command is acceptable, vs. introducing Celery.
- **Employee data source**: who enters CPF/CBO/CNS/salário for each employee — new admin UI, or bulk import (e.g. from payroll/folha spreadsheet)?
- **`contracts.Contract`'s §7 "Contratos" ambiguity**: confirm the recommendation above (new `SupplierContract` model rather than overloading the ajuste-level `Contract`) matches your mental model of "contrato" in this domain.
- **Legacy Anexo RP reports**: keep, retire, or repurpose as an internal reconciliation view once AUDESP JSON is the real submission channel?

Downloaded reference material (schemas, examples, OpenAPI spec) is in the session scratchpad; worth relocating into the repo (e.g. `docs/audesp/`) once we start Phase 0 so future sessions don't need to re-download.

# ALTERACOES.md

Changelog de trabalho — mudanças ainda **não commitadas** no branch `sp-report`, feitas em duas sessões: refactor de padronização + correção de bugs nos exportadores de PDF (RP-01 a RP-14), seguido da reescrita estrutural dos "termo de ciência" (RP-03/05/07/09/11/13) e do RP-14 para bater com os modelos oficiais do TCE-SP.

Detalhe item a item de cada bug/decisão está em [REPORTS_TODO.md](REPORTS_TODO.md) — este arquivo é um índice por arquivo, pra guiar o teste manual.

---

## Infraestrutura compartilhada

### `reports/exporters/base.py`
- `initialize_pdf()` deixou de ser um `raise NotImplementedError` e passou a montar o PDF de verdade (A4, margens, fontes, cor de preenchimento) — antes cada um dos 14 exportadores duplicava esse setup no próprio `__init__`.
- Novo helper `_set_font()`, também antes duplicado em cada arquivo.
- Novo `default_cell_height = 5` como atributo de classe.
- `cleanup()` não chama mais `self.pdf.close()` — fpdf2 não expõe esse método (não é recurso de SO, só objeto em memória); a chamada real sempre teria estourado `AttributeError` se `cleanup()` fosse exercitado. Removido o `try/except` que mascarava isso e o `@dataclass` na classe (não tinha campos tipados que justificassem).

### `reports/exporters/commons/integral_statement.py` *(novo arquivo)*
Extrai a lógica de receitas/despesas duplicada nos 5 "demonstrativo integral" (RP-06/08/10/12/14):
- `build_revenue_summary()` — saldo anterior, repasses públicos, rendimento de aplicação, recursos próprios, outras receitas, último repasse recebido.
- `categorize_expenses()` — despesas por categoria de natureza, com parâmetro `inclusive_bounds` porque RP-06/08 usavam comparação de data exclusiva (`<`) e RP-10/12/14 usavam inclusiva (`<=`) — preservado explícito por chamador pra não mudar nenhum PDF nessa extração (decisão de negócio pendente, ver REPORTS_TODO.md).
- `convert_decimal_to_brl()` — formata um dict de `Decimal` recursivamente pra moeda BRL.

### `reports/exporters/commons/certification_term.py` *(novo arquivo)*
Extrai o corpo compartilhado dos 6 "termo de ciência e notificação" (RP-03/05/07/09/11/13), que eram **byte-idênticos entre si** fora do título/subtítulo do cabeçalho — cada um imprimia literalmente o texto do RP-09, com rótulos de partes errados nos outros 5.
- `TermLabels` (dataclass) — os rótulos que de fato variam por anexo (ÓRGÃO CONCESSOR/BENEFICIÁRIO vs. CONTRATANTE/CONTRATADA vs. ÓRGÃO PÚBLICO PARCEIRO/ENTIDADE PARCEIRA, etc.), texto da cláusula "Estamos CIENTES" item (a), texto da cláusula de dados pessoais item (d), títulos das seções de assinatura, aviso opcional (usado só pelo RP-13).
- `CertificationTermPDFExporter` (base) — desenha cabeçalho, cláusulas legais (com os itens (b) e (c) fixos, idênticos nos 6 modelos oficiais), bloco NOTIFICADOS, autoridades, assinaturas, "DEMAIS RESPONSÁVEIS" e rodapé, tudo dirigido pelos `TermLabels` + `_info_lines()`/`_footnote_lines()` que cada subclasse implementa. Tem 2 ganchos (`_draw_extra_authority_sections`, `_draw_extra_signature_sections`) usados só pelo RP-03 (seção INTERVENIENTE).
- **2 bugs de conteúdo achados e corrigidos na cláusula legal compartilhada** (existiam mesmo no RP-09, que a auditoria anterior tinha marcado como "correto"): o item (c) usava `contract.official_government_link` (um link por contrato) onde o modelo oficial sempre aponta pro Diário Oficial Eletrônico do TCESP (`https://doe.tce.sp.gov.br/`, fixo, igual nos 6 modelos); e citava "Instruções nº01/2020" onde o oficial diz "nº01/2024".

---

## RP-03 / RP-05 / RP-07 / RP-09 / RP-11 / RP-13 — Termo de ciência e notificação

Todos migrados para `CertificationTermPDFExporter` (acima). Cada arquivo agora só define os rótulos e o bloco de informações do topo.

| Arquivo | O que mudou |
|---|---|
| `reports/exporters/pass_on_3.py` | Reescrito. Rótulos "ÓRGÃO CONCESSOR"/"ÓRGÃO BENEFICIÁRIO" (`contract.organization.city_hall.name` / `contract.organization.name`), sem campo OBJETO (não existe no oficial), "Nº DO CONVÊNIO"/"TIPO DE CONCESSÃO" via `contract.agreement_num`/`get_concession_type_display()`. Seção **INTERVENIENTE** implementada (informação + bloco de assinatura "PELO INTERVENIENTE") — sem campo no modelo pra isso, então fica em branco em vez de inventar dado. `LOCAL` passou a usar `contract.contractor_company.city` (não `hired_company.city` — RP-03 não tem uma OSC como contraparte, é repasse entre órgãos públicos). 4 notas de rodapé (o oficial tem 4, não 2). |
| `reports/exporters/pass_on_5.py` | Reescrito. Rótulos "CONTRATANTE"/"CONTRATADA"/"CONTRATO DE GESTÃO Nº (DE ORIGEM)". |
| `reports/exporters/pass_on_7.py` | Reescrito. Rótulos "ÓRGÃO PÚBLICO PARCEIRO"/"ENTIDADE PARCEIRA"/"TERMO DE PARCERIA Nº(DE ORIGEM)". |
| `reports/exporters/pass_on_9.py` | Migrado pra base compartilhada (era a fonte do corpo copiado pelos outros 5) — comportamento igual, só os 2 bugs de cláusula legal acima corrigidos. |
| `reports/exporters/pass_on_11.py` | Reescrito. Rótulos "ÓRGÃO PÚBLICO CONVENENTE"/"ENTIDADE CONVENIADA"/"TERMO DE CONVÊNIO Nº(DE ORIGEM)", inclusive nos blocos de assinatura ("PELO ÓRGÃO PÚBLICO CONVENENTE"/"PELA ENTIDADE CONVENIADA"). |
| `reports/exporters/pass_on_13.py` | Reescrito — o mais divergente do grupo. Aviso "(utilização apenas para os repasses anteriores à edição da LF 13019/2014 atualizada)" abaixo do título; cláusula "Estamos CIENTES" item (a) com o texto mais curto do oficial (sem "o ajuste acima referido e seus aditamentos"); rótulos "AUXÍLIO/SUBVENÇÃO/CONTRIBUIÇÃO" e "Nº DA LEI AUTORIZADORA" (via `contract.law_num`, campo que nenhum exportador usava antes); seções de assinatura com os nomes do oficial ("Responsáveis pelo repasse e/ou Parecer Conclusivo", "Responsáveis pela prestação de contas"); só 1 nota de rodapé (o oficial não numera VALOR/EXERCÍCIO aqui). |

**Teste manual sugerido:** gerar cada um dos 6 pra um contrato com `concession_type` correspondente e comparar rótulo por rótulo com o `.docx` oficial em `../relatorios_sp/`. Prestar atenção especial no RP-03 (seção INTERVENIENTE e LOCAL) e no RP-13 (aviso + cláusula curta + nomes de assinatura).

---

## RP-14 — Demonstrativo integral (auxílios/subvenções/contribuições)

### `reports/exporters/pass_on_14.py`
**Reescrito do zero.** A versão anterior copiava a estrutura do RP-06/08/10/12 (tabela A–G, despesas em H/I/J, "DEMONSTRATIVO DO SALDO FINANCEIRO" G/J/K/L/M) — estrutura que **não existe** no `.docx` oficial do RP-14, que é mais simples. Nova estrutura:
- Bloco de identificação: ÓRGÃO CONCESSOR / TIPO DE CONCESSÃO / **LEI AUTORIZADORA** (`contract.law_num`) / OBJETO / EXERCÍCIO / ENTIDADE BENEFICIÁRIA / CNPJ / endereço / responsável(is) / VALOR TOTAL RECEBIDO / ORIGEM DOS RECURSOS.
- "DEMONSTRATIVO DOS REPASSES PÚBLICOS RECEBIDOS" — sem lettering A–G, uma linha por repasse (`Revenue` de natureza `PUBLIC_TRANSFER`) + linhas de receita c/ aplicação financeira, total e recursos próprios.
- "DEMONSTRATIVO DAS DESPESAS REALIZADAS" — 3 colunas (categoria/período/valor aplicado), reaproveitando `categorize_expenses()` de `commons/integral_statement.py` mas expondo só o total pago por categoria (sem a quebra H/I/J que o oficial não tem).
- "RELAÇÃO DAS DESPESAS" — lista item a item (data/documento fiscal/credor/natureza/valor), igual à Tabela II do RP-02.
- Assinatura "DIRIGENTE" (`organization.owner`/`.position`) + "MEMBROS DO CONSELHO FISCAL" (sem campo no modelo — deixado em branco).
- "VALOR DEVOLVIDO AO ÓRGÃO CONCESSOR" e "VALOR AUTORIZADO PARA O EXERCÍCIO SEGUINTE" ficam em "—" honesto (mesma decisão já tomada no RP-02: não existe campo no modelo pra devolução de recurso).

⚠️ **Ressalva pra teste manual:** a extração do `.docx` oficial pra texto simples achata tabelas em uma lista solta de rótulos — a largura de coluna e o agrupamento exato de linha foram reconstruídos por inferência razoável, não confirmados pixel a pixel contra o Word original. Vale abrir o `.docx` e o PDF gerado lado a lado antes de aprovar este anexo.

---

## Outros exportadores (bugs pontuais, sem mudança de estrutura)

| Arquivo | O que mudou |
|---|---|
| `reports/exporters/pass_on_1.py` | Migrado pra `BasePDFExporter`. `contracts_queryset` ganhou `select_related("organization", "checking_account")` — corrige N+1 (uma query por linha da tabela antes). |
| `reports/exporters/pass_on_2.py` | Migrado pra `BasePDFExporter`. Bug de mutação: `self.start_date -= timedelta(days=365)` no `__init__` vazava pra `_draw_table_I` e somava quase 2 anos de receita em vez de só o período pedido — agora `start_date` fica intocado e existe `self.previous_year_reference` separada, usada só nas 2 queries que precisam do saldo do exercício anterior. Tabela III (aditivos) passou a usar `ContractAddendum` real em vez de renderizar `Ellipsis` literal. Tabela II usa `expense.liquidation_form_label` pro tipo de documento (antes placeholder) e calcula "recurso não aplicado" de verdade. "Valor devolvido"/"valor autorizado" ficam em "—" honesto. |
| `reports/exporters/pass_on_4.py` | Migrado pra `BasePDFExporter`. "ÓRGÃO CONCESSOR" usava `contract.organization.name` (a própria ONG) em vez de `contract.organization.city_hall.name` (a prefeitura) — invertia o dado. "Valor Global do Ajuste - Valor do adendo" era texto literal hardcoded nas 6 subtabelas — agora calcula o valor vigente (aditivo mais recente por vigência, ou `total_value` do contrato). |
| `reports/exporters/pass_on_6.py` | Migrado pra `BasePDFExporter` + `build_revenue_summary`/`categorize_expenses` compartilhados. Soma "(E) Total de recursos públicos" omitia o item D (outras receitas) — corrigido pra `A+B+C+D`. Filtro de despesas trocado de `item__contract` (FK opcional, excluía despesas sem linha orçamentária) pra `accountability__contract` (FK obrigatória). Sufixo " - Confirmar variável"/" - Confirmar campo" (anotação de dúvida do dev que vazava pro PDF final) removido. |
| `reports/exporters/pass_on_8.py` | Mesmos fixes do RP-06, mais: parágrafo inteiro com nome de ONG fixo ("Associação Comunidade Varzina...") e datas fixas ("01/01/2025 a 31/12/2025") trocado pela expressão dinâmica (`contract.name`/`start_date`/`end_date`); "dd/mm/aa" e "Nao sei o que é" hardcoded trocados por `self.latest_pass_on_info` real. |
| `reports/exporters/pass_on_10.py` | Mesmos fixes de `item__contract`, "Confirmar variável/campo" e parágrafo hardcoded que RP-08 (RP-10 já não tinha o bug da soma E). |
| `reports/exporters/pass_on_12.py` | Idem RP-10. |

---

## Testes

### `reports/tests.py`
- Cobertura nova para os 6 "termo de ciência" (`CertificationTermPDFExportersTests`) — smoke test end-to-end de cada um (`handle()` não deve estourar exceção e deve gerar PDF não vazio) + uma regressão específica confirmando que o RP-03 usa `contractor_company.city` (não `hired_company.city`) no LOCAL.
- Cobertura nova para o RP-14 reescrito (`PassOn14PDFExporterTests`).
- Testes pré-existentes de `build_revenue_summary`/`categorize_expenses` e a regressão do RP-06 (soma E) mantidos como estavam.
- **13 testes, todos passando** — rodado contra SQLite em memória (Postgres/Docker não necessário pra isso, ver `CLAUDE.MD`).

---

## Documentação

- **`REPORTS_TODO.md`** *(novo)* — TODO consolidado dos 14 exportadores: bugs catalogados, o que foi corrigido, e o checklist de conformidade contra os `.docx` oficiais em `../relatorios_sp/`. Atualizado nesta sessão pra marcar RP-03/05/07/09/11/13/14 como cobertos.
- **`relatório estrutura e banco de dados.md`**, **`relatório práticas de desenvolvimento e estrutura de código.md`**, **`relatório tema e propósito do sistema.md`** *(novos)* — 3 relatórios exploratórios de auditoria do repositório (arquitetura de dados, ferramental/convenções, propósito do sistema), não relacionados aos exportadores — leitura independente, não exigem teste manual.

---

## Validação já feita (automatizada)

- `manage.py check` — sem erros.
- `ruff check` / `ruff format` — sem apontamentos.
- `reports.tests` completo contra SQLite em memória — 13/13 passando.

**Não feito:** teste visual dos PDFs gerados (comparação lado a lado com os `.docx` oficiais) — é isso que falta antes do commit.

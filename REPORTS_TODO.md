# REPORTS_TODO.md

TODO consolidado dos exportadores de PDF em `reports/exporters/pass_on_*.py` (Anexos RP-01 a RP-14 do TCE-SP). Duas partes: **(1)** bugs de código encontrados na leitura dos 14 exportadores e **(2)** um checklist de conformidade contra os modelos oficiais baixados em `../relatorios_sp/` (14 `.docx` do site do TCE-SP).

Itens já catalogados em [DEBTS.md](DEBTS.md) estão linkados em vez de duplicados — aqui eles viram checklist acionável.

---

## Parte 0 — Refactor de padronização (dev-standards / python-django-standards)

Aplicado depois da Parte 1: os 14 exportadores agora herdam de `BasePDFExporter` (`reports/exporters/base.py`, antes existia mas não era usada — eliminou a duplicação de `__init__`/`__set_font`/`default_cell_height` nos 14 arquivos), a lógica de `__database_queries`/`__categorize_expenses` duplicada em RP-06/08/10/12/14 foi extraída para `reports/exporters/commons/integral_statement.py`, os N+1 confirmados (RP-01, RP-02, e o loop de aditivos de RP-06/08/10/12/14) foram corrigidos, e `reports/tests.py` ganhou cobertura real (antes era um stub de 1 linha).

- [ ] **Achado novo durante a extração: RP-06/08 e RP-10/12/14 divergiam na comparação de datas de `categorize_expenses`.** RP-06/08 usavam `start_date.date() < expense.competency < end_date.date()` (exclusivo) e RP-10/12/14 usavam `<=`/`<=` (inclusivo) para decidir se uma despesa cai dentro do período pedido. Preservado explicitamente via parâmetro `inclusive_bounds` na função compartilhada (`categorize_expenses(..., inclusive_bounds=...)`) para não mudar nenhum PDF nessa extração — mas é uma inconsistência real que merece decisão de negócio: qual comportamento é o correto (uma despesa com vencimento exatamente no primeiro/último dia do período deveria contar ou não)?
  - **Sugestão**: decidir com o time qual dos dois é o certo e normalizar todos os 5 pra um só, removendo o parâmetro.
- [x] Código morto removido: os 16 atributos (`self.hr_expenses`, `self.all_expenses_value`, etc.) calculados em `__database_queries` de RP-06/08/10/12/14 e nunca lidos (a tabela usa só `categorize_expenses()`) — confirmado por grep antes de remover, não mudam nenhum output.
- [x] `self.total_paid_expenses_decimal` em RP-10/12/14 (atribuído, nunca lido) — removido junto.

---

## Parte 1 — Bugs para corrigir

### 🔴 Críticos — conteúdo/rótulos legais errados

- [x] **RP-03, 05, 07, 11 e 13 imprimiam o corpo do RP-09, não o próprio anexo.** `pass_on_3.py`, `pass_on_5.py`, `pass_on_7.py`, `pass_on_11.py`, `pass_on_13.py` eram **byte-idênticos** entre si (confirmado via `diff`) — só a classe e o título/subtítulo do cabeçalho mudavam.
  - **Corrigido**: extraída a lógica e o texto legal comuns aos 6 "termo de ciência" (RP-03/05/07/09/11/13) para `reports/exporters/commons/certification_term.py` (`CertificationTermPDFExporter` + `TermLabels`), com cada `pass_on_N.py` agora só declarando os rótulos e o bloco de informações que de fato variam por anexo. RP-09 também foi migrado pra essa base (era a fonte do corpo compartilhado).
  - **RP-03** (repasse a órgãos públicos) agora usa "ÓRGÃO CONCESSOR" / "ÓRGÃO BENEFICIÁRIO" / "Nº DO CONVÊNIO(1)" / "TIPO DE CONCESSÃO(2)" (via `contract.get_concession_type_display()`) e não tem campo OBJETO, igual ao oficial. A parte **INTERVENIENTE (se houver)** foi implementada (linha de informação + bloco de assinatura "PELO INTERVENIENTE") — como não existe campo no modelo para uma parte interveniente, os campos ficam honestamente em branco em vez de inventar um valor. LOCAL agora usa `contract.contractor_company.city` (não `hired_company.city` — RP-03 não tem uma OSC como contraparte).
  - **RP-05** agora usa "CONTRATANTE" / "CONTRATADA" / "CONTRATO DE GESTÃO Nº (DE ORIGEM)".
  - **RP-07** agora usa "ÓRGÃO PÚBLICO PARCEIRO" / "ENTIDADE PARCEIRA" / "TERMO DE PARCERIA Nº (DE ORIGEM)".
  - **RP-11** agora usa "ÓRGÃO PÚBLICO CONVENENTE" / "ENTIDADE CONVENIADA" / "TERMO DE CONVÊNIO Nº (DE ORIGEM)" (inclusive nos blocos de assinatura: "PELO ÓRGÃO PÚBLICO CONVENENTE" / "PELA ENTIDADE CONVENIADA").
  - **RP-13** (o mais divergente) agora usa "ÓRGÃO/ENTIDADE PÚBLICO(A)" / "ENTIDADE BENEFICIÁRIA" / "AUXÍLIO/SUBVENÇÃO/CONTRIBUIÇÃO" / "Nº DA LEI AUTORIZADORA" (via `contract.law_num`, campo real que não era usado por nenhum exportador antes); tem o aviso obrigatório "(utilização apenas para os repasses anteriores à edição da LF 13019/2014 atualizada)"; a cláusula "Estamos CIENTES de que" item (a) usa o texto mais curto do oficial (sem "o ajuste acima referido e seus aditamentos"); seções de assinatura têm os nomes próprios do oficial ("Responsáveis pelo repasse e/ou Parecer Conclusivo", "Responsáveis pela prestação de contas").
  - **Achado durante a extração**: mesmo o corpo "correto" do RP-09 tinha 2 divergências reais do texto oficial no item (c)/(d) da cláusula "Estamos CIENTES" — usava `contract.official_government_link` (um link por contrato) em vez do link fixo do Diário Oficial Eletrônico do TCESP (`https://doe.tce.sp.gov.br/`, o mesmo em todos os 6 modelos oficiais), e citava "Instruções nº01/2020" em vez de "nº01/2024". Corrigidos nos 6 exportadores junto, já que o texto é compartilhado.

- [x] **RP-14 usava a estrutura de tabelas do RP-06/08/10/12, mas o modelo oficial do RP-14 é outro.** `pass_on_14.py` era quase idêntico a `pass_on_6.py` (mesma tabela "(A) SALDO...(B)...(C)...(D)...(E) TOTAL...(F)...(G)", mesma tabela de despesas categorizada em H/I/J, mesmo "DEMONSTRATIVO DO SALDO FINANCEIRO" G/J/K/L/M) — estrutura que **não existe** no `.docx` oficial do RP-14.
  - **Corrigido**: `pass_on_14.py` reescrito do zero seguindo a estrutura mais simples do modelo oficial (mais próxima do RP-02): "DEMONSTRATIVO DOS REPASSES PÚBLICOS RECEBIDOS" (sem lettering A-G), "DEMONSTRATIVO DAS DESPESAS REALIZADAS" com 3 colunas (categoria/período/valor aplicado, sem quebra H/I/J — reaproveita `categorize_expenses` de `commons/integral_statement.py`, mas só expõe o bucket `paid_on` por categoria), "RELAÇÃO DAS DESPESAS" (data/documento fiscal/credor/natureza/valor, igual à Tabela II do RP-02, reaproveitando `expense.liquidation_form_label`/`nature_label`), e assinatura de "DIRIGENTE" (`organization.owner`/`.position`) + "MEMBROS DO CONSELHO FISCAL" (sem campo no modelo — deixado em branco). "VALOR DEVOLVIDO AO ÓRGÃO CONCESSOR" e "VALOR AUTORIZADO PARA O EXERCÍCIO SEGUINTE" ficam honestamente em "—", mesma decisão já tomada no RP-02.
  - **Ressalva**: a extração do `.docx` oficial pra texto simples achata a geometria da tabela original (linhas/colunas viram uma lista de rótulos soltos) — a reconstrução das larguras de coluna e do agrupamento exato de linhas é uma interpretação razoável, não uma cópia pixel-a-pixel confirmada. Recomendo conferir visualmente o PDF gerado contra o `.docx` antes de considerar o RP-14 fechado.

- [x] **RP-04 rotula o nome do beneficiário como "ÓRGÃO CONCESSOR".** ~~`pass_on_4.py:106` — `text=f"**ÓRGÃO CONCESSOR:** {self.contract.organization.name}"`. Em todo o resto do código (`pass_on_1.py:104`, `pass_on_2.py:123`, `pass_on_3.py:90`) "ÓRGÃO CONCESSOR" é sempre `contract.organization.city_hall.name` (a prefeitura, quem concede o repasse) — aqui usa `contract.organization.name` (a própria ONG/beneficiária), invertendo o dado.~~
  - **Corrigido**: trocado para `self.contract.organization.city_hall.name`, igual aos demais exportadores.

### 🟠 Dados fabricados / texto de placeholder vazando pro PDF final

- [x] **RP-08/10/12/14 imprimiam um parágrafo inteiro hardcoded** — nome de organização fixo ("Associação Comunidade Varzina - Eco & Vida (Meio Ambiente)") e datas fixas ("01/01/2025 a 31/12/2025") em `_draw_expenses_table`, em vez de `self.contract.name` / `self.start_date` / `self.end_date`.
  - **Corrigido**: os 4 arquivos agora usam a mesma expressão dinâmica que já existia em `pass_on_6.py`. (Nota: RP-14 continua com a estrutura de tabela errada — item crítico acima — este fix só evita o dado fabricado até a reescrita.)
- [x] RP-08 também tinha "dd/mm/aa" e "Nao sei o que é" hardcoded — **corrigido**, agora usa `self.latest_pass_on_info`, igual a `pass_on_6.py`. Já estava documentado em [DEBTS.md](DEBTS.md#rp-08-exporter-hardcodes-ddmmaa-and-nao-sei-o-que-é-as-real-report-values).
- [x] RP-02 renderizava "Ellipsis" na tabela de aditivos e placeholders de despesa — **corrigido**: Tabela III agora usa `ContractAddendum` real (contrato base + aditivos); Tabela II usa `expense.liquidation_form_label` para o tipo de documento e calcula "recurso não aplicado" (receita do período − despesas pagas); "valor devolvido" e "valor autorizado para o próximo exercício" ficaram como "—" honesto, pois não existe campo no modelo que registre devolução de recurso — inventar um número seria pior que deixar em branco. Já estava documentado em DEBTS.md ([1](DEBTS.md#rp-02-exporter-renders-literal-ellipsis-in-the-addenda-table-instead-of-real-data), [2](DEBTS.md#rp-02-exporter-hardcodes-instructional-placeholder-text-as-financial-figures)).
- [x] RP-04 renderizava "ClassAdendo" no lugar do valor global do ajuste — **corrigido**: agora computa o valor vigente (aditivo mais recente por vigência, ou `contract.total_value` se não houver aditivo) e usa o mesmo valor nas 6 subtabelas (as outras 5 já tinham o mesmo placeholder "Valor Global do Ajuste - Valor do adendo", não documentado antes — também corrigido). Já estava documentado em [DEBTS.md](DEBTS.md#rp-04-exporter-renders-the-literal-string-classadendo-instead-of-the-global-ajuste-value).
- [x] **"Confirmar variável" / "Confirmar campo" apareciam literalmente no PDF entregue ao usuário.** Texto de anotação do desenvolvedor (dúvida sobre qual campo usar) que nunca foi resolvido e ficou hardcoded no meio do valor real. Ocorria em `pass_on_2.py`, `pass_on_6.py`, `pass_on_8.py`, `pass_on_10.py`, `pass_on_12.py`, `pass_on_14.py`.
  - **Corrigido**: removido o sufixo " - Confirmar variável"/" - Confirmar campo", mantendo `contract.supervision_autority.position`/`.get_full_name()` como já estava.

### 🟡 Bugs de query/cálculo

- [x] **`__categorize_expenses` usava `item__contract` (FK opcional) em vez de `accountability__contract` (FK obrigatória), excluindo despesas silenciosamente.** Em `pass_on_2.py`, `pass_on_6.py`, `pass_on_8.py`, `pass_on_10.py`, `pass_on_12.py`, `pass_on_14.py` — `Expense.item` é `null=True, on_delete=SET_NULL` (`accountability/models.py:466`). Qualquer `Expense` sem `item` (linha orçamentária) vinculado sumia da tabela de despesas por categoria, mesmo aparecendo corretamente no saldo financeiro (`self.expense_queryset`, que usa `accountability__contract` — FK obrigatória).
  - **Corrigido**: trocado `item__contract=self.contract` por `accountability__contract=self.contract` em `__categorize_expenses` nos 5 arquivos, alinhando com `self.expense_queryset`.
- [x] RP-06/RP-08 "total de recursos públicos" (E = A+B+C+D) omitia o item D no cálculo — **corrigido**, agora soma `+ self.other_revenues_value`, igual a RP-10/12/14. Já estava documentado em [DEBTS.md](DEBTS.md#rp-06rp-08-total-public-resources-sum-omits-item-d-other-revenues).
- [x] **RP-02 deslocava `start_date` em -365 dias no `__init__` e essa mutação vazava para outros filtros.** `self.start_date = start_date - timedelta(days=365)` era reusado por `_draw_table_I` para filtrar `revenue_in_time`, somando quase 2 anos de receitas em vez de só o período pedido.
  - **Corrigido**: `start_date` ficou intocado; criada `self.previous_year_reference` separada, usada só nas 2 queries que precisam do saldo do exercício anterior (`statement_queryset` e `opening_balance`).
- [ ] **RP-04 provavelmente só popula 1 das 5 subtabelas.** `pass_on_4.py` filtra `revenue_queryset` pela conta bancária do **contrato selecionado**, e depois separa em 5 subtabelas por `concession_type` do contrato vinculado à receita — como a conta pertence a um único contrato, só a subtabela do tipo daquele contrato terá linhas; as outras 4 sempre vêm vazias. O modelo oficial ("RELAÇÃO DOS VALORES TRANSFERIDOS", análogo ao RP-01) sugere que deveria listar repasses de **todos os contratos da prefeitura** por tipo, como o RP-01 já faz (`Contract.objects.filter(area__city_hall=...)`), não ficar preso à conta de um único contrato.
  - **Sugestão**: revisar com o time se RP-04 deveria agregar por `city_hall` como o RP-01, em vez de por contrato único.

### ⚪ Outros

- [ ] `reports/exporters/contract_progress.py` (`ContractProgressPDFExporter`) existe mas não está no dispatcher `reports/services.py::export_report()` nem no catálogo `REPORT_MODELS` de `reports/forms.py` — inacessível pela UI. Decidir se é pra remover ou finalizar a integração.

---

## Parte 2 — Checklist de conformidade com os modelos oficiais (`../relatorios_sp/`)

Comparação campo a campo entre cada `pass_on_N.py` e o `.docx` oficial correspondente baixado do site do TCE-SP.

| Anexo | Status | Observações |
|---|---|---|
| **RP-01** — Repasses a órgãos públicos (lista) | ✅ Coberto | Cabeçalho, tabela (tipo/beneficiário/CNPJ/endereço/lei/convênio/finalidade/data pgto/fonte/valor), rodapé (*) (**) e assinatura batem com o oficial. |
| **RP-02** — Demonstrativo integral (órgãos públicos) | ✅ Coberto | Estrutura (I/II/III + rodapés 1–5) bate com o oficial. Bugs de dado corrigidos (Tabela III com aditivos reais, Tabela II com tipo de documento e recurso não aplicado reais, bug do `start_date - 365 dias` corrigido). "Valor devolvido"/"valor autorizado" ficam honestamente em branco — não há campo no modelo para isso. |
| **RP-03** — Termo de ciência (órgãos públicos) | ✅ Coberto | Reescrito sobre `commons/certification_term.py`: rótulos "ÓRGÃO CONCESSOR/BENEFICIÁRIO", "Nº DO CONVÊNIO", "TIPO DE CONCESSÃO" e a seção **INTERVENIENTE** (dado + assinatura, honestamente em branco — sem campo no modelo) implementados. |
| **RP-04** — Repasses ao terceiro setor (lista) | 🟡 Parcial | As 6 subtabelas existem e batem em colunas com o oficial. "ÓRGÃO CONCESSOR" e "Valor Global do Ajuste" corrigidos. Ainda pendente: o escopo por conta bancária provavelmente deixa 4 das 5 subtabelas de ajuste sempre vazias — precisa decisão de produto antes de mexer. |
| **RP-05** — Termo de ciência (contrato de gestão) | ✅ Coberto | Reescrito sobre `commons/certification_term.py` com os rótulos "CONTRATANTE/CONTRATADA" e "CONTRATO DE GESTÃO Nº". |
| **RP-06** — Demonstrativo (contrato de gestão) | ✅ Coberto | Estrutura completa bate com o oficial (documento+aditivos, A–G, H/I/J por categoria, G/J/K/L/M). Bugs de dado corrigidos (soma E, `item__contract`, "Confirmar variável/campo"). |
| **RP-07** — Termo de ciência (termo de parceria) | ✅ Coberto | Reescrito sobre `commons/certification_term.py` com os rótulos "ÓRGÃO PÚBLICO PARCEIRO/ENTIDADE PARCEIRA" e "TERMO DE PARCERIA Nº". |
| **RP-08** — Demonstrativo (termo de parceria) | ✅ Coberto | Estrutura bate. Bugs de dado corrigidos (parágrafo hardcoded, "dd/mm/aa"/"Nao sei o que é", soma E, `item__contract`, "Confirmar variável/campo"). |
| **RP-09** — Termo de ciência (colaboração/fomento) | ✅ Coberto | Migrado pra `commons/certification_term.py` (era a fonte do corpo compartilhado). Corrigidas 2 divergências do texto oficial encontradas durante a extração: link fixo do Diário Oficial Eletrônico do TCESP (em vez de `contract.official_government_link`) e "Instruções nº01/2024" (em vez de "nº01/2020"). |
| **RP-10** — Demonstrativo (colaboração/fomento) | ✅ Coberto | Estrutura bate. Bugs de dado corrigidos (parágrafo hardcoded, `item__contract`, "Confirmar variável/campo"). |
| **RP-11** — Termo de ciência (termo de convênio) | ✅ Coberto | Reescrito sobre `commons/certification_term.py` com os rótulos "ÓRGÃO PÚBLICO CONVENENTE/ENTIDADE CONVENIADA" e "TERMO DE CONVÊNIO Nº". |
| **RP-12** — Demonstrativo (termo de convênio) | ✅ Coberto | Estrutura bate. Bugs de dado corrigidos (parágrafo hardcoded, `item__contract`, "Confirmar variável/campo"). |
| **RP-13** — Termo de ciência (auxílios/subvenções/contribuições) | ✅ Coberto | Reescrito sobre `commons/certification_term.py`: aviso "(uso apenas para repasses anteriores à LF 13019/2014)", cláusula "Estamos cientes" item (a) com o texto curto do oficial, rótulos "AUXÍLIO/SUBVENÇÃO/CONTRIBUIÇÃO" e "Nº DA LEI AUTORIZADORA" (via `contract.law_num`), seções de assinatura com os nomes próprios do oficial. |
| **RP-14** — Demonstrativo (auxílios/subvenções/contribuições) | ✅ Coberto | Reescrito do zero seguindo a estrutura mais simples do oficial (estilo RP-02): sem lettering A-G, despesas em 3 colunas (categoria/período/valor aplicado), "RELAÇÃO DAS DESPESAS" itemizada, assinatura "DIRIGENTE" + "MEMBROS DO CONSELHO FISCAL". *Geometria de tabela reconstruída a partir do `.docx` achatado em texto — recomenda-se conferência visual do PDF antes de considerar fechado (ver Parte 0).* |

**Resumo**: dos 14 anexos, **13 cobertos** (RP-01, RP-02, RP-03, RP-05, RP-06, RP-07, RP-08, RP-09, RP-10, RP-11, RP-12, RP-13, RP-14), **1 parcial** (RP-04 — escopo da query ainda pendente de decisão de produto). Os "termo de ciência" (RP-03/05/07/09/11/13) foram unificados em `reports/exporters/commons/certification_term.py`; o RP-14 foi reescrito seguindo o modelo oficial em vez do RP-06/08/10/12. Resta apenas a decisão de produto sobre o escopo do RP-04.

# SITTS - Sistema Integrado de Transparência e Transferências Sociais
## DOCUMENTAÇÃO TÉCNICA DE FUNCIONALIDADES

**Documento:** Especificação Funcional Completa
**Redação original:** 24 de outubro de 2025
**Revisão e conferência contra o código:** 12 de agosto de 2026

---

### Nota de revisão — 12 de agosto de 2026

Este documento passou a ser versionado no repositório (`docs/`) nesta data. Antes
disso vivia em `scripts/`, um diretório ignorado pelo Git, e portanto não chegava a
nenhum clone novo.

Toda contagem e todo nome de estado foram conferidos contra o código em execução.
As correções aplicadas:

| Seção | Constava | Verificado no código |
|---|---|---|
| 2.2.3 | 31 naturezas de despesa | **96** (`NatureChoices`) — cresceu com a incorporação das categorias AUDESP |
| 3.2.1 | 11 naturezas de receita | **13** (`Revenue.Nature`) — a lista no texto já trazia 13; o número estava errado |
| 3.5.1 | 8 modalidades de instrumento | **9** (`ResourceSource.CategoryChoices`) |
| 4.3.2 | 14 tipos de transação | **18** (`Transaction.TransactionTypeChoices`) |
| 6.1 | 18 modelos de relatório | **17** (`REPORTS_OPTIONS`) |
| 6.1 | "Relatório de Progresso Contratual" | não existe; os três modelos gerenciais são Despesas no Período, Repasses Previstos vs Realizados e Consolidado das Conciliações Bancárias |
| 10.5 | "sistema de caching configurável" | **não há** `CACHES` em `core/settings.py` |
| 11.1 | "estilização baseada em Tailwind CSS" | substituída pelo design system próprio em `templates/ui/` |

Confirmados sem alteração: os 5 níveis de acesso, as 6 modalidades de concessão, as
3 fases contratuais, os 4 estados de prestação, as 7 formas de liquidação, os 21
tipos de documento de despesa, as 6 origens de recurso, os 9 níveis de interesse, os
5 tipos de documento contratual, os 3 estados de compra, o limite de 100 registros
na busca avançada e as 84 categorias de log de atividade (o texto dizia "mais de
80").

Dois módulos inteiros não constavam e foram acrescentados ao final, como **seção 13
(AUDESP)** e **seção 14 (Portal da Transparência)**. Ficaram no fim de propósito: a
numeração existente permanece estável para quem já citou este documento.

O AUDESP (`audesp/`) entrou depois de outubro de 2025 e hoje é a principal
superfície de compliance junto ao TCE-SP. O Portal da Transparência
(`transparency_portal/`) existia e só aparecia de passagem em 1.5, embora seja um
aplicativo completo com superfície pública própria em `/transparencia/`.

Para o estado de implementação do AUDESP — o que está pronto, o que é andaime e o
que nunca foi exercitado contra servidor real — a fonte é
`.claude/skills/sitts-audesp/`. Para defeitos conhecidos,
`.claude/skills/sitts-known-bugs/`.

---

## 1. MÓDULO DE GESTÃO DE USUÁRIOS E CONTROLE DE ACESSO

### 1.1 Sistema de Autenticação e Segurança

O sistema disponibiliza mecanismos completos de autenticação e controle de acesso, contemplando autenticação baseada em credenciais de email e senha, funcionalidade de recuperação de senha via correio eletrônico através da integração com SendGrid, política de redefinição obrigatória de senha no primeiro acesso, controle de expiração programável de senhas, gerenciamento de sessões de usuário e sistema hierárquico de controle de acesso baseado em níveis de permissão.

### 1.2 Hierarquia de Níveis de Acesso

O sistema é capaz de gerenciar cinco níveis hierárquicos de acesso de usuário, com controle de login por organização e segmentação de permissões. O primeiro nível, denominado MASTER, proporciona acesso irrestrito a todas as funcionalidades do sistema. O segundo nível, CIVIL_SERVANT (Funcionário Público), oferece acesso administrativo para gestão de dados governamentais. O terceiro nível, FOLDER_MANAGER (Gestor de Pasta), concede permissões para revisão e análise de prestações de contas. O quarto nível, ORGANIZATION_ACCOUNTANT (Contador/Funcionário da Organização), permite acesso para registro e manutenção de dados contábeis. Por fim, o quinto nível, COMMITTEE_MEMBER (Membro do Comitê), fornece acesso restrito à consulta de informações, sem permissões de edição.

### 1.3 Gestão de Perfis de Usuário

#### 1.3.1 Gestão de Gestores de Pasta

O sistema disponibiliza funcionalidades completas para gerenciamento de gestores de pasta, contemplando interface de listagem com recursos de busca textual e paginação, funcionalidade de criação de novos perfis de gestores, edição de informações cadastrais incluindo nome completo, CPF/CNPJ, cargo e telefone, atribuição de usuários a múltiplas áreas organizacionais ou pastas gestoras, controle de ativação e desativação de contas de usuário, além de visualização detalhada de informações de perfil.

#### 1.3.2 Gestão de Contadores e Funcionários Organizacionais

O módulo disponibiliza sistema de listagem com funcionalidades de busca e paginação, cadastro de novos perfis de contadores, atualização de dados cadastrais, vinculação de usuários a áreas organizacionais específicas, gerenciamento de status de ativação de contas e acesso a informações detalhadas de perfil.

#### 1.3.3 Gestão de Membros de Comitê

O sistema oferece interface de listagem com recursos de busca e paginação, processo de cadastro de novos membros, atualização de informações cadastrais, vinculação a comitês organizacionais específicos, atribuição a áreas de atuação, controle de ativação e desativação de contas e visualização completa de dados de perfil.

### 1.4 Estrutura Organizacional

#### 1.4.1 Gestão de Prefeituras

O sistema permite o cadastro e gerenciamento de entidades municipais, contemplando o registro de dados institucionais tais como denominação, nome do prefeito, documento identificador (CPF ou CNPJ) e cargo, além de validação automatizada de unicidade de documentos e sistema de auditoria com registro histórico de alterações.

#### 1.4.2 Gestão de Organizações

O módulo disponibiliza funcionalidades para cadastro de organizações vinculadas a prefeituras, incluindo registro de dados como denominação, presidente, documento identificador e cargo, validação de unicidade de documentos por prefeitura e rastreamento histórico de modificações.

#### 1.4.3 Gestão de Áreas Organizacionais

O sistema permite a criação e organização de áreas dentro de organizações, oferecendo recursos para descrição e categorização de áreas, bem como estabelecimento de vínculos com prefeituras e organizações.

#### 1.4.4 Gestão de Comitês

O módulo oferece capacidades para criação e configuração de comitês, gerenciamento de composição de membros e vinculação a áreas organizacionais específicas.

### 1.5 Sistema de Gerenciamento Documental Organizacional

O sistema disponibiliza funcionalidades completas para gestão de documentos institucionais, permitindo upload e armazenamento de documentos organizacionais com categorização por tipo documental, incluindo Balanço Patrimonial, Demonstrativo do Resultado do Exercício (DRE), Estatuto Social e documentos diversos. O sistema oferece controle granular de visibilidade através de classificação como público ou privado, integração com portal de transparência para publicação, sistema de versionamento com rastreamento temporal e suporte a múltiplos formatos como PDF, DOC, DOCX, XLS e XLSX.

---

## 2. MÓDULO DE GESTÃO DE CONTRATOS E INSTRUMENTOS DE PARCERIA

### 2.1 Sistema de Gestão Contratual

#### 2.1.1 Cadastro e Administração de Contratos

O sistema oferece funcionalidades completas para gerenciamento do ciclo de vida de contratos e convênios, incluindo criação e registro de instrumentos contratuais com suporte a seis modalidades de concessão, sendo estas: Contrato de Gestão, Termo de Parceria, Termo de Colaboração, Contrato de Fomento, Convênio e Concessão. O registro detalhado de informações contratuais contempla identificação através de denominação e código, código interno para integração e importação, objeto e objetivo do instrumento, processo licitatório, fundamentação legal com número e data da lei, dados de convênio incluindo número e data, especificação de valores contemplando valor original, total, municipal e contrapartida, período de vigência com data inicial e final, além de referência para link oficial governamental. O sistema permite vinculação a áreas organizacionais e comitês, bem como funcionalidade de anexação de documento contratual.

#### 2.1.2 Gerenciamento de Ciclo de Vida Contratual

O sistema implementa controle completo de estados contratuais através de três fases distintas: PLANNING (fase de planejamento e estruturação), EXECUTION (fase de execução) e FINISHED (fase de finalização), com rastreamento automatizado de mudanças de status entre estas fases.

#### 2.1.3 Gestão de Entidades Envolvidas

No âmbito do cadastro de empresas, o sistema permite o registro de empresas participantes, sejam contratante, contratada ou gestores, contemplando identificação fiscal através de CNPJ, dados de contato incluindo telefone, endereço completo e detalhado, além de sistema de auditoria histórica.

O gerenciamento de partes interessadas disponibiliza funcionalidades para registro e gestão de stakeholders contratuais, incluindo cadastro de interessados no instrumento contratual e classificação por nível de interesse, contemplando as categorias de Gestor de Projeto, Gestor Financeiro, Responsável Técnico, Coordenador do Projeto, Responsável pela Entidade, Conselho Fiscal, Vice Presidente, Tesoureiro e Secretário, com capacidade de edição e remoção de registros.

O sistema permite a designação de responsáveis através da atribuição de Responsável Contábil (accountability_autority) e Responsável Fiscal (supervision_autority) aos contratos.

### 2.2 Módulo de Plano de Trabalho

#### 2.2.1 Gestão de Metas Contratuais

O sistema oferece funcionalidades para definição e acompanhamento de metas, permitindo criação e edição de metas contratuais com registro de informações detalhadas. Estas informações incluem denominação da meta, objetivo específico, metodologia de execução, observações complementares e status de execução que pode ser classificado como Analisando, Em Progresso ou Finalizado. O sistema incorpora funcionalidade de sistema de comentários e revisões, além de rastreamento histórico completo de todas as revisões realizadas.

#### 2.2.2 Gestão de Etapas de Execução

O módulo disponibiliza capacidades para criação de etapas vinculadas a metas específicas, contemplando registro detalhado de denominação da etapa, objetivo, metodologia e recursos necessários, além de funcionalidade de acompanhamento de progresso.

#### 2.2.3 Gestão de Itens Contratuais

O sistema permite o cadastro detalhado de itens e despesas previstas, iniciando pela especificação de fonte de recursos que pode ser Prefeitura ou Contrapartida de Parceiro. As informações descritivas contemplam denominação do item, objetivo, metodologia e observações. A configuração de valores inclui custo mensal unitário, quantidade de meses, custo anual, quantidade e tipo de unidade. O sistema oferece classificação por natureza da despesa através de 96 categorias disponíveis, definição de período de execução através de data inicial e final, controle de status de análise e funcionalidade de anexação de documentos.

#### 2.2.4 Sistema de Gestão de Processos de Aquisição

O módulo oferece controle de status de compra através de três estados: Analisando Opções, Em Andamento e Finalizado. O registro de dados de aquisição contempla data de aquisição, valor total da aquisição, número de parcelas e data de vencimento das parcelas. O cadastro de informações do fornecedor inclui razão social, documento identificador, telefone, email e endereço. O sistema permite upload de documentação completa do processo de compra.

#### 2.2.5 Gestão de Suplementação de Itens

O sistema disponibiliza funcionalidades para solicitação de suplementação de valores de itens, processo de aprovação ou rejeição de solicitações, bem como registro de observações e justificativas relacionadas.

#### 2.2.6 Sistema de Remanejamento de Recursos

O sistema permite solicitação de remanejamento de valores entre itens contratuais através da identificação de item de origem (com redução de valor) e item de destino (com acréscimo de valor), especificação de incrementos tanto mensal quanto anual, workflow estruturado de aprovação e registro de motivo de rejeição quando aplicável.

### 2.3 Gestão de Aditamentos e Documentação Contratual

#### 2.3.1 Aditivos Contratuais

O sistema disponibiliza funcionalidades para criação e registro de aditivos contratuais, contemplando atualização de vigência, atualização de valores incluindo total, municipal e contrapartida, além de upload de documento do aditivo.

#### 2.3.2 Documentos Contratuais

O módulo oferece capacidades para upload de documentação relacionada ao contrato, categorização por tipo contemplando Aditivo, Contrato, Planilha, Termos e Outros, além de organização sistemática por categoria.

### 2.4 Gestão de Transferências Financeiras

O sistema permite registro de repasses mensais programados, especificação de fonte identificando se é Prefeitura ou Contrapartida, controle de valores e períodos, além de acompanhamento de cronograma de transferências.

### 2.5 Linha Temporal Contratual

O módulo disponibiliza visualização cronológica de eventos contratuais, atualização de marcos significativos e timeline completa de evolução contratual.

---

## 3. MÓDULO DE PRESTAÇÃO DE CONTAS

### 3.1 Sistema de Gestão de Prestações

#### 3.1.1 Criação e Administração

O sistema oferece funcionalidades completas para gestão de prestações de contas mensais, contemplando criação de prestação mensal vinculada a contrato, especificação de período de referência através de mês e ano, e controle de estado da prestação. Os estados disponíveis incluem WIP (Em Andamento), SENT (Enviada para Análise), CORRECTING (Em Correção) e FINISHED (Finalizada). O sistema permite registro de pendências e observações, atribuição de revisor através de gestor de pasta designado, designação de membro de comitê para notificação, interface de listagem com filtros avançados e funcionalidade de busca por denominação de contrato.

#### 3.1.2 Workflow de Aprovação

O sistema implementa fluxo estruturado de aprovação em cinco etapas sequenciais. Inicialmente, a organização efetua criação e preenchimento da prestação. Em seguida, ocorre a submissão para análise com seleção de revisor. Na terceira etapa, o gestor de pasta executa revisão completa. Na quarta etapa, há decisão de aprovação (FINISHED) ou solicitação de correção (CORRECTING). Em caso de correção, ocorre retorno para nova análise. Na aprovação final, existe possibilidade de notificação de membro do comitê designado.

### 3.2 Gestão de Receitas

#### 3.2.1 Cadastro e Controle

O sistema disponibiliza funcionalidades para registro de receitas, contemplando criação de registros de receita com identificação e observações descritivas, especificação de valor, registro de data de competência e data de recebimento. A classificação de fonte permite identificar se a receita é proveniente de Prefeitura ou Contrapartida, com vinculação a conta bancária de destino. O sistema oferece classificação por natureza da receita através de 13 categorias distintas, sendo estas: Crédito Indevido, Depósito Bancário, Depósito para Devolução ao Órgão Concedente, Estorno de Pagamento, Estorno de Tarifas, Outras Receitas Decorrentes da Execução do Ajuste, Recurso Próprio da Entidade Parceira, Reembolso de Juros Multas e Glosas, Reembolso de Tarifas, Rendimento de Aplicação Financeira, Rendimento de Poupança, Repasse Público e Saldo Anterior para Acerto. O sistema de status de revisão contempla quatro estados: Em Análise, Atualizada, Rejeitada e Aprovada. O controle de flags permite marcar se a receita está paga ou conciliada, além de permitir registro de pendências.

#### 3.2.2 Funcionalidades Operacionais

O módulo oferece edição de registros de receita, duplicação de receitas, exclusão de registros, upload de múltiplos arquivos comprobatórios, revisão individual ou processamento em lote, conciliação bancária e funcionalidade de desconciliação.

### 3.3 Gestão de Despesas

#### 3.3.1 Cadastro e Administração

O sistema disponibiliza capacidades completas para registro de despesas, contemplando criação de registros de despesa com identificação e observações, especificação de valor e vinculação a favorecido (beneficiário). A especificação de fonte de recursos e vinculação a item contratual relacionado permite controle detalhado. O sistema oferece classificação por natureza da despesa e registro de múltiplas datas, incluindo data de competência, data de vencimento e data de liquidação. A especificação de forma de liquidação contempla sete modalidades: Boleto, Cheque, Cartão de Débito/Crédito, Débito em Conta, Transferência Eletrônica, Dinheiro e Ordem Bancária de Transferência Voluntária (OBTV). A classificação de tipo de documento oferece 21 categorias distintas, incluindo Apólice de Seguro, Aviso de Débito, Boleto, Cupom Fiscal, DARF (Documento de Arrecadação de Receitas Federais), GPS (Guia da Previdência Social), GRF (Guia de Recolhimento do FGTS), GRRF (Guia de Recolhimento Rescisório do FGTS), GRCS ou DOC, Fatura, Holerite, diversas modalidades de Nota Fiscal (NF, NF-E, NFS, NFS-E), Outros, Recibo, Recibo de Férias, RPA (Recibo de Pagamento Autônomo) e Termo de Rescisão. O sistema permite registro de número do documento, controle através de sistema de status de revisão, controle de flags indicando se está pago, conciliado ou planejado, além de registro de pendências.

#### 3.3.2 Funcionalidades Avançadas

O módulo oferece edição de registros de despesa, duplicação de despesas, funcionalidade de glosa para marcação como não planejada, exclusão de registros e upload de múltiplos arquivos comprobatórios. O sistema disponibiliza revisão individual de despesas, revisão em lote com navegação sequencial, conciliação bancária individual, conciliação bancária em lote com matching automatizado, desconciliação e vinculação de múltiplas despesas a transações únicas.

### 3.4 Gestão de Favorecidos

#### 3.4.1 Controle de Beneficiários

O sistema disponibiliza cadastro de favorecidos com registro de dados incluindo nome e CPF/CNPJ, interface de listagem com busca e edição de informações cadastrais. O dashboard analítico de beneficiários oferece visualização de custo total por beneficiário, custo segmentado por contrato, listagem detalhada de despesas, filtros por área e contrato, além de visualização detalhada individual de beneficiário.

### 3.5 Gestão de Fontes de Recursos

#### 3.5.1 Administração de Fontes

O módulo oferece cadastro de fontes de recursos com registro de dados incluindo nome, CPF/CNPJ e número do contrato. A classificação por origem contempla seis categorias: Federal, Estadual, Municipal, Contrapartida de Parceiro, Patrocinador Privado e Emenda Parlamentar. A categorização por tipo de instrumento oferece nove modalidades: Acordo de Cooperação, Convênio, Termo de Colaboração, Termo de Fomento, Contrato de Doação, Contrato de Gestão, Contrato de Repasse, Termo de Parceria e Outros. O sistema disponibiliza funcionalidades de listagem e edição.

### 3.6 Sistema de Arquivos de Prestação

O sistema disponibiliza upload de documentação geral da prestação, funcionalidade de nomeação de arquivos, capacidade de exclusão de arquivos e rastreamento de autoria de uploads.

### 3.7 Funcionalidades de Importação e Exportação

#### 3.7.1 Importação XLSX

O sistema oferece download de template estruturado pré-formatado e importação em lote contemplando receitas, despesas e aplicações financeiras. A validação automatizada de dados é acompanhada de geração de relatório de inconsistências.

#### 3.7.2 Exportação XLSX

O módulo disponibiliza exportação de dados completos da prestação em formato estruturado para edição externa.

### 3.8 Sistema de Busca Avançada

O módulo oferece capacidades de busca com busca global em receitas e despesas através de múltiplos critérios de filtragem. O sistema permite filtrar por tipo de registro (receita, despesa ou todos), intervalo de período com data inicial e final, status de conciliação, contrato específico, favorecido específico, status de revisão e status de pagamento. A funcionalidade inclui limitação de resultados com máximo de 100 registros e cálculo automático de totalizadores.

### 3.9 Visualização de Pendências

O sistema disponibiliza listagem consolidada de todas as pendências, agrupamento por categoria contemplando receitas e despesas, além de acesso direto aos itens pendentes.

---

## 4. MÓDULO DE GESTÃO BANCÁRIA

### 4.1 Sistema de Gestão de Contas Bancárias

#### 4.1.1 Cadastro e Administração

O sistema disponibiliza funcionalidades para criação e registro de contas bancárias, contemplando registro de informações detalhadas. Estas informações incluem denominação da instituição bancária, código identificador do banco, número da conta, agência, tipo de conta podendo ser Conta Corrente ou Investimento, origem da fonte de recursos e saldo atual. O sistema permite vinculação a instrumentos contratuais, oferece interface de listagem e busca, possibilita edição de dados cadastrais e implementa validações de unicidade.

### 4.2 Gestão de Extratos Bancários

#### 4.2.1 Controle de Extratos

O módulo oferece upload de extratos mensais com registro de informações contemplando saldo inicial do período, saldo final do período e período de referência especificado por dia, mês e ano. O sistema implementa validação de saldos não negativos, garante unicidade por período e mantém histórico completo de extratos.

### 4.3 Sistema de Transações Bancárias

#### 4.3.1 Registro de Transações

O sistema disponibiliza ferramentas para a leitura e extração de dados bancários em formato OFX, contemplando importação automatizada de transações via arquivo OFX e registro detalhado de dados transacionais. Os dados registrados incluem valor (positivo para crédito, negativo para débito), data de efetivação, classificação por tipo de transação através de 18 categorias, número identificador da transação, denominação/descrição e campo de memorando/observações. O sistema implementa validação de unicidade por número de transação e ordenação cronológica.

#### 4.3.2 Taxonomia de Transações

O sistema suporta classificação de transações através de 18 tipos distintos, contemplando Débito e Crédito, Juros e Dividendos, Taxas e Taxas de Serviço, Depósito, Caixa Eletrônico (ATM), Ponto de Venda (POS), Transferência entre Contas, Cheque, Fatura ou Débito Programado, Saque em Dinheiro, Depósito Direto, Débito Automático, Pagamento Recorrente, Retorno de Investimentos e categoria Outros.

#### 4.3.3 Sistema de Conciliação

O módulo oferece vinculação manual de transações a despesas e receitas, relacionamento múltiplo através de estrutura many-to-many, conciliação em lote automatizada, matching algorítmico por valor e identificação de favorecido, além de funcionalidade de desconciliação.

### 4.4 Processamento de Arquivos OFX

O sistema disponibiliza parser especializado para arquivos OFX, importação automatizada de transações, validação de duplicidades e atualização automática de saldos.

---

## 5. MÓDULO DE RELATÓRIOS DE EXECUÇÃO

### 5.1 Sistema de Relatórios Mensais

#### 5.1.1 Criação e Gestão

O sistema oferece criação de relatórios mensais de execução por contrato, especificação de período de referência através de mês e ano, e controle de status. Os estados disponíveis contemplam Em Andamento, Enviada para Análise, Em Correção e Finalizada. O sistema garante unicidade por contrato, mês e ano.

#### 5.1.2 Workflow de Aprovação

O sistema implementa processo estruturado similar ao de prestação de contas, iniciando com criação e preenchimento inicial, seguido de submissão para análise técnica, revisão por autoridade competente, decisão de aprovação ou solicitação de correção e, finalmente, finalização do processo.

### 5.2 Gestão de Atividades Executadas

#### 5.2.1 Registro de Atividades

O sistema disponibiliza criação de registros de atividades executadas com vinculação a etapas do plano de trabalho, registro de informações contemplando denominação da atividade, descrição detalhada e percentual de conclusão variando de 0 a 100%. O sistema garante unicidade por execução, etapa e denominação, além de oferecer funcionalidade de edição de atividades.

### 5.3 Sistema de Arquivos de Execução

O módulo oferece upload de arquivos comprobatórios, suporte a múltiplos formatos de arquivo, detecção automática de tipo de arquivo e organização sistemática por relatório.

---

## 6. SISTEMA DE GERAÇÃO DE RELATÓRIOS

### 6.1 Biblioteca de Modelos de Relatórios

O sistema disponibiliza 17 modelos especializados de relatórios em formato PDF,
organizados em três grupos.

Os **Repasses a órgãos públicos** compreendem os anexos RP-01 a RP-03: RP-01
(Repasses a órgãos públicos), RP-02 (Demonstrativo integral de receitas e despesas)
e RP-03 (Termo de ciência e de notificação).

Os **Repasses ao terceiro setor** compreendem os anexos RP-04 a RP-14, alternando
entre Demonstrativo integral de receitas e despesas (RP-06, RP-08, RP-10, RP-12,
RP-14) e Termo de ciência e de notificação (RP-05, RP-07, RP-09, RP-11, RP-13),
além do RP-04 (Repasses ao terceiro setor).

Os **Demonstrativos gerenciais** compreendem três modelos: Despesas realizadas no
período, Repasses previstos versus realizados e Consolidado das conciliações
bancárias.

### 6.2 Sistema de Geração

#### 6.2.1 Funcionalidades

O módulo oferece seleção de instrumento contratual, definição de período customizável através de intervalo de datas, seleção de modelo de relatório e designação de responsáveis com respectivos cargos. O sistema permite geração de documento em formato PDF, download direto, visualização em nova aba do navegador e disponibiliza API para integração com retorno em formato base64.

#### 6.2.2 Conteúdo dos Relatórios

Os relatórios incluem dados completos do contrato e organização, informações das empresas participantes, receitas e despesas do período especificado, saldos e movimentações bancárias, transações bancárias detalhadas, informações de responsáveis técnicos e campos para assinaturas e dados de aprovação.


## 7. MÓDULO DE DASHBOARD E INDICADORES GERENCIAIS

### 7.1 Dashboard Executivo

#### 7.1.1 Indicadores Principais

O sistema apresenta indicadores consolidados contemplando total de contratos ativos, prestações de contas em andamento, total de receitas acumuladas no período, total de despesas acumuladas no período e saldo financeiro calculado através da diferença entre receitas e despesas.

#### 7.1.2 Mecanismos de Filtragem

O sistema disponibiliza diferentes tipos de filtros permitindo filtrar por intervalos pré-determinados de datas contemplando mês corrente, últimos três meses, últimos seis meses e últimos doze meses, além de permitir filtragem por status da prestação de contas e por contratos específicos.

#### 7.1.3 Visualizações Gráficas

O dashboard oferece gráfico de prestações mensais mostrando quantitativo de prestações por período, gráfico de receitas demonstrando evolução temporal mensal, gráfico de despesas apresentando evolução temporal mensal, gráfico de repasses exibindo cronograma de transferências programadas e tabela de progresso mensal possibilitando análise comparativa mês a mês.

### 7.2 Módulo de Prestações Recentes

O sistema apresenta listagem das 10 prestações mais recentes, quantitativo de receitas e despesas por prestação, status atual de cada prestação e acesso direto às prestações.

---

## 8. SISTEMA DE NOTIFICAÇÕES

### 8.1 Notificações In-App

#### 8.1.1 Categorias de Notificação

O sistema implementa notificações para eventos contemplando criação de prestação de contas, prestação enviada para análise, prestação enviada para correção, prestação finalizada, criação de novo contrato, atualização de status contratual, comentário em meta contratual, comentário em item contratual, solicitação de remanejamento de recursos, revisão de remanejamento, execução enviada para análise, execução enviada para correção e execução finalizada.

#### 8.1.2 Funcionalidades

O módulo oferece badge indicativo de notificações não lidas, interface de listagem de notificações, marcação de leitura, redirecionamento automático para objeto relacionado e segmentação por perfil de usuário.

### 8.2 Notificações por Correio Eletrônico

O sistema implementa integração com serviço SendGrid, email de criação de conta de usuário, email com credenciais temporárias, email de recuperação de senha e notificações de eventos críticos.

---

## 9. SISTEMA DE AUDITORIA E RASTREABILIDADE

### 9.1 Activity Log (Registro de Atividades)

#### 9.1.1 Taxonomia de Ações

O sistema registra 84 categorias distintas de ações organizadas por módulo. Na gestão de usuários, contempla criação, edição e exclusão de funcionários públicos, criação, edição e exclusão de gestores de pasta, ativação e desativação de gestores, criação, edição e exclusão de contadores, ativação e desativação de contadores, criação, edição e exclusão de membros de comitê, além de ativação e desativação de membros.

No módulo de prestação de contas, registra criação de prestação, upload e exclusão de documentação, envio para análise, envio para correção, marcação como finalizada e importação de arquivo estruturado.

Para receitas e despesas, o sistema rastreia criação, edição e exclusão, conciliação bancária, revisão técnica, duplicação de registros, glosa de despesas, além de upload e exclusão de arquivos comprobatórios.

Na gestão bancária, contempla criação de conta bancária, atualização de informações e upload de extrato bancário.

A gestão contratual registra criação de contrato, criação e edição de aditivos, criação e edição de documentos, atualização de status, gestão de partes interessadas, atualização de repasses mensais, criação e edição de metas, registro de comentários em metas, criação e edição de itens, registro de comentários em itens, solicitação e análise de remanejamento, gestão de suplementações, além de upload e exclusão de arquivos de compra.

Os relatórios de execução contemplam criação de relatório, envio para análise, envio para correção, finalização, criação e edição de atividades, além de criação e edição de arquivos.

O sistema também registra criação, edição e exclusão de favorecidos e fontes de recursos, bem como criação e edição de empresas.

#### 9.1.2 Estrutura de Rastreamento

O sistema registra timestamp preciso de todas as ações, identificação do usuário executor, email do usuário, objeto alvo da ação, tipo de conteúdo através de implementação via GenericForeignKey e indexação otimizada por usuário e tipo de ação.

### 9.2 Historical Records (Histórico Versionado)

O sistema implementa versionamento histórico completo utilizando django-simple-history para entidades contemplando prefeituras, organizações, áreas organizacionais, contratos, aditivos contratuais, metas, etapas, itens contratuais, prestações de contas, arquivos de prestação, receitas, despesas, arquivos de receitas e despesas, contas bancárias, extratos bancários e transações bancárias.

---

## 10. INFRAESTRUTURA TÉCNICA E FUNCIONALIDADES TRANSVERSAIS

### 10.1 Arquitetura Multi-tenant

O sistema implementa arquitetura multi-organizacional completa baseada em easy-tenants, oferecendo isolamento total de dados por organização, contexto de tenant automático e transparente, além de managers especializados denominados TenantManager e TenantManagerAllObjects.

### 10.2 Sistema de Exclusão Lógica

O sistema implementa exclusão lógica (soft delete) em todos os modelos principais através da utilização de campo deleted_at para marcação, preservação completa de histórico e possibilidade de recuperação de registros.

### 10.3 Validações e Integridade de Dados

#### 10.3.1 Validações Implementadas

O sistema oferece validação de CPF e CNPJ com algoritmos específicos, normalização automática de emails para lowercase, validação de formato de telefone brasileiro, validação de não negatividade de valores monetários, validação de consistência temporal e validação de unicidade de documentos por organização.

#### 10.3.2 Constraints de Banco de Dados

O sistema implementa unique constraints com condições de soft delete, foreign keys com proteção de integridade referencial e indexes otimizados para queries de alta frequência.

### 10.4 Segurança da Informação

O sistema implementa autenticação obrigatória para todas as funcionalidades, middleware de controle de tenant, middleware de gestão de sessão, validação de permissões por view, mixins especializados de controle de acesso, proteção CSRF (Cross-Site Request Forgery) e hashing de senhas com algoritmos criptográficos seguros.

### 10.5 Otimização de Performance

O sistema implementa utilização de select_related e prefetch_related em queries complexas, indexes estratégicos para otimização, paginação em todas as listagens e agregações otimizadas. Não há backend de cache configurado — `core/settings.py` não define `CACHES`, de modo que vale o padrão em memória por processo do Django.

### 10.6 Integrações Externas

O sistema integra-se com SendGrid para envio de emails transacionais e com Google Cloud Platform contemplando Cloud Storage para armazenamento de arquivos, Cloud SQL para banco de dados PostgreSQL e Cloud Logging para centralização de logs. Também oferece integração com Health Check para monitoramento de saúde da aplicação.

### 10.7 Formatos e Padrões Suportados

O sistema suporta formato OFX para importação de extratos bancários, formato XLSX para importação e exportação de prestações, formato PDF para geração de relatórios utilizando biblioteca FPDF, formato JSON para respostas de API e UUID para identificadores únicos universais.

### 10.8 Sistema de Logging

O sistema implementa logging estruturado e hierarquizado, diferentes níveis de severidade contemplando INFO, WARNING e ERROR, decoradores para logging automatizado de views, logging de operações de banco de dados e integração com Cloud Logging em ambiente de produção.

---

## 11. FUNCIONALIDADES DE EXPERIÊNCIA DO USUÁRIO

### 11.1 Interface de Usuário

O sistema oferece design responsivo com suporte mobile e estilização baseada em design system próprio, definido em `templates/ui/_styles.html` e especificado em `DESIGN.md` — uma dupla tinta/tela em preto e branco, geometria de pílula e voz em caixa baixa, com cor semântica reservada a sinal (situação, severidade, ação destrutiva) e nunca a cromo. Oferece ainda componentes reutilizáveis e modulares sob `templates/ui/`, sistema de mensagens de feedback contemplando sucesso, erro e aviso, navegação breadcrumb contextual e paginação intuitiva e consistente.

### 11.2 Mecanismos de Busca e Filtragem

O sistema disponibiliza busca textual em múltiplas entidades, combinação de múltiplos filtros, filtros temporais, filtros por status e estados, filtros por valores numéricos e busca case-insensitive.

### 11.3 Sistema de Formulários

O sistema implementa validação dual contemplando client-side e server-side, máscaras de entrada para CPF, CNPJ, telefone e CEP, seleção múltipla via checkboxes, date pickers especializados, upload de arquivos com preview, formsets dinâmicos e mensagens de erro contextualizadas.

### 11.4 Navegação

O sistema oferece menu hierárquico estruturado, links contextuais, botões de ação rápida, modais para confirmações críticas, redirecionamentos inteligentes e URLs semânticas e significativas.

### 11.5 Exportação de Dados

O sistema disponibiliza download de relatórios em formato PDF, download de templates XLSX pré-formatados, exportação de extratos OFX e nomenclatura automática contextual de arquivos.

---

## 12. REGRAS DE NEGÓCIO IMPLEMENTADAS

### 12.1 Workflow de Prestação de Contas

O sistema implementa regras específicas contemplando permissão de prestações apenas em contratos com status "Em Execução", unicidade de prestação por período (mês/ano) por contrato, edição permitida somente nos estados "Em Andamento" ou "Corrigindo", obrigatoriedade de revisor ser Gestor de Pasta ativo, possibilidade de notificação de membro do comitê na aprovação e registro automático em log de auditoria para mudanças de status.

### 12.2 Conciliação Bancária

O sistema implementa processamento exclusivo de transações não conciliadas, matching automático por equivalência exata de valor, matching secundário por normalização de nome do favorecido, possibilidade de vinculação múltipla permitindo agregar despesas em transação única, atualização automática de data de liquidação e marcação automática como pago e conciliado.

### 12.3 Remanejamento de Valores

O sistema valida operação permitida somente em contratos ativos, suficiência de valor no item de origem, necessidade de aprovação por gestor autorizado, atualização automática de valores mensais e anuais e manutenção de histórico completo da solicitação.

### 12.4 Controle de Acesso Hierárquico

O sistema implementa níveis de acesso onde MASTER e CIVIL_SERVANT possuem acesso irrestrito a todas as funcionalidades, FOLDER_MANAGER possui capacidade de revisão sem permissão de edição de dados, ORGANIZATION_ACCOUNTANT possui capacidade de criação e edição sem permissão de aprovação e COMMITTEE_MEMBER possui acesso restrito a modo consulta.

### 12.5 Sistema de Glosa

O sistema permite remoção de vinculação com item planejado, marcação de despesa como não planejada, manutenção de registro da despesa e registro automático em log de auditoria.

---

## 13. TAXONOMIAS E CATEGORIZAÇÕES

### 13.1 Naturezas de Despesa

O sistema suporta 31 categorias de natureza de despesa contemplando pessoal e encargos trabalhistas, serviços de terceiros pessoa física e jurídica, material de consumo, equipamentos e material permanente, obras e instalações, tecnologia da informação, comunicação e divulgação, locomoção, hospedagem e alimentação, entre outras categorias específicas.

### 13.2 Unidades Federativas

O sistema oferece suporte completo aos 27 estados brasileiros.

### 13.3 Sistema de Meses

O sistema disponibiliza representação multilíngue em português e formato numérico e textual.

### 13.4 Status de Revisão

O sistema implementa padronização de estados para múltiplas entidades contemplando Analisando, Em Progresso e Finalizado.

---

## 14. CÁLCULOS E TOTALIZADORES AUTOMÁTICOS

### 14.1 Agregações Implementadas

O sistema calcula automaticamente total de receitas por prestação de contas, total de despesas por prestação de contas, saldo financeiro calculado pela diferença entre receitas e despesas, custo mensal por item contratual, custo anual por item contratual, total executado versus planejado, percentual de execução e valor de renda mensal média por contrato.

### 14.2 Funcionalidades de Agregação

O sistema disponibiliza somatórios de valores por período, contagem de registros, cálculo de médias, agrupamento por categoria, agrupamento por status, agrupamento por favorecido e agrupamento por contrato.

---

## 15. FUNCIONALIDADES DIFERENCIADORAS

### 15.1 Características Únicas

O sistema oferece funcionalidades diferenciadas contemplando conciliação bancária automatizada com algoritmo de matching inteligente, biblioteca de 18 modelos de relatórios especializados e customizáveis, arquitetura multi-organizacional completa e escalável, workflow de aprovação estruturado em múltiplos níveis hierárquicos, sistema de auditoria abrangente com mais de 80 tipos de ações rastreadas, portal de transparência totalmente integrado ao sistema, gestão completa do ciclo de vida de instrumentos contratuais, capacidades de importação e exportação em múltiplos formatos, histórico versionado de todas as alterações significativas e sistema de notificações contextual e direcionado.

### 15.2 Integrações Especializadas

O sistema integra-se com SendGrid para envio de emails transacionais profissionais, Google Cloud Platform completo contemplando Storage, SQL e Logging, importação OFX compatível com múltiplas instituições bancárias, geração de PDFs profissionais e customizados e armazenamento de arquivos em nuvem escalável.

### 15.3 Compliance e Governança

O sistema garante rastreabilidade total de todas as ações executadas, soft delete para preservação completa de histórico, versionamento automático de documentos críticos, controle de acesso granular e hierarquizado, validações rigorosas de integridade de dados e portal de transparência para prestação de contas pública.

---

## 16. SÍNTESE EXECUTIVA

### 16.1 Arquitetura Modular

O sistema é estruturado em 8 módulos principais contemplando Gestão de Usuários e Controle de Acesso, Gestão de Contratos e Instrumentos de Parceria, Prestação de Contas, Gestão Bancária, Relatórios de Execução, Sistema de Geração de Relatórios, Portal de Transparência e Dashboard e Indicadores Gerenciais.

### 16.2 Quantitativo de Funcionalidades

O sistema disponibiliza mais de 250 funcionalidades distintas distribuídas entre os diversos módulos.

### 16.3 Entidades Principais

O sistema gerencia entidades contemplando Prefeituras e Organizações, Usuários distribuídos em 5 níveis hierárquicos, Comitês e Áreas Organizacionais, Contratos e Instrumentos de Parceria, Metas, Etapas e Itens Contratuais, Prestações de Contas, Receitas e Despesas, Favorecidos e Fontes de Recursos, Contas Bancárias e Transações, Relatórios de Execução, Documentos e Arquivos, além de Logs de Auditoria e Notificações.

### 16.4 Suporte a Formatos

O sistema oferece suporte a documentos em formatos PDF, DOC, DOCX, XLS, XLSX, OFX e diversos formatos de imagem para comprovantes.

### 16.5 Capacidades de Relatório

O sistema disponibiliza 18 modelos especializados de relatórios com geração em formato PDF e customização por período e responsáveis.

### 16.6 Auditoria

O sistema implementa rastreamento de mais de 80 tipos de ações, histórico versionado completo e logs centralizados.

---

## CONSIDERAÇÕES FINAIS

O SITTS (Sistema Integrado de Transparência e Transferências Sociais) configura-se como uma plataforma tecnológica robusta e abrangente, especificamente desenvolvida para a gestão de parcerias sociais entre entidades públicas municipais e organizações do terceiro setor.

O sistema apresenta funcionalidades avançadas e integradas contemplando gestão administrativa com controle completo de usuários, organizações e estruturas hierárquicas, controle financeiro através de gestão detalhada e auditável de receitas, despesas e movimentações bancárias, prestação de contas implementando workflow estruturado com múltiplos níveis de aprovação, transparência pública mediante portal integrado para acesso público às informações, auditoria e rastreabilidade através de sistema abrangente de logs e versionamento, geração de relatórios oferecendo biblioteca extensa de modelos profissionais, arquitetura multi-organizacional proporcionando solução escalável e isolada por tenant e integrações modernas garantindo conectividade com serviços em nuvem e padrões de mercado.

O sistema demonstra elevado nível de maturidade técnica implementando práticas avançadas de desenvolvimento contemplando exclusão lógica de dados, arquitetura multi-tenant, versionamento histórico, logging estruturado e validações rigorosas de integridade.

A arquitetura do sistema está preparada para escalabilidade, manutenibilidade e conformidade com requisitos de governança e transparência pública, atendendo plenamente às demandas de gestão de parcerias sociais no âmbito da administração pública municipal.

---

**Fim do Documento**

---

## 13. MÓDULO AUDESP — REMESSA AO TRIBUNAL DE CONTAS

> Acrescentado na revisão de 12 de agosto de 2026. O módulo entrou em produção no
> repositório depois da redação original. Para o estado de implementação detalhado —
> o que está pronto, o que é andaime e o que nunca foi exercitado contra servidor
> real — consultar `.claude/skills/sitts-audesp/`.

### 13.1 Escopo e Estrutura

O sistema implementa a remessa eletrônica de dados ao Sistema AUDESP do Tribunal de
Contas do Estado de São Paulo, contemplando duas fases distintas e sequenciais, ambas
obrigatórias para os mesmos cinco instrumentos de parceria com o terceiro setor.

A **Fase IV** ("Licitações e Contratos") registra o instrumento jurídico em si —
o ajuste e suas notas de empenho — como artefato genérico de contratação pública.
A **Fase V** ("Repasses ao Terceiro Setor") registra a prestação de contas dos
repasses já efetuados sob um ajuste previamente cadastrado na Fase IV.

As duas fases compartilham as mesmas URLs base e a mesma autenticação por token
portador, e nada além disso: cada uma possui seus próprios esquemas JSON, seu próprio
espaço de endpoints e seu próprio vocabulário de estados.

### 13.2 Tipos de Ajuste Suportados

O sistema produz documentos válidos para os cinco tipos de ajuste previstos pelo
TCE-SP — Contrato de Gestão, Convênio, Termo de Colaboração, Termo de Fomento e Termo
de Parceria — além da Declaração Negativa, utilizada quando não houve repasse no
exercício. Cada tipo possui endpoint próprio e módulo construtor próprio.

Cabe registrar que a Declaração Negativa da Fase IV tem significado distinto da
Declaração Negativa da Fase V: a primeira declara que nenhum ajuste foi firmado no
período, a segunda que não houve repasses sob um ajuste específico.

### 13.3 Construção e Validação de Documentos

O sistema monta o documento JSON a partir dos dados já registrados no domínio e o
valida localmente contra os esquemas JSON oficiais do TCE-SP, versionados no
repositório em `docs/audesp/` e `docs/audesp_fase_iv/`, antes de qualquer tentativa de
envio. A validação local recusa o documento incompleto sem consumir tentativa junto ao
Tribunal.

Os blocos de campo comuns aos cinco esquemas são construídos uma única vez e
parametrizados nos três pontos em que os esquemas efetivamente divergem entre tipos de
ajuste.

### 13.4 Envio, Consulta e Retificação

O sistema efetua o envio autenticado do documento, consulta a situação do protocolo
junto ao Tribunal e mapeia a resposta para os estados internos de acompanhamento.

Cada tentativa de montagem ou envio gera registro próprio, sem sobrescrever o
anterior, de modo que o histórico de tentativas fica preservado — exigência prática do
fluxo de retificação do próprio AUDESP.

A retificação de exercício anterior ao último enviado provoca, no Tribunal, a exclusão
em cascata de todos os exercícios posteriores, que passam a exigir reenvio integral. O
sistema identifica previamente os exercícios afetados e exige confirmação explícita
antes de efetuar uma retificação com esse efeito, refletindo localmente o que o
Tribunal faz do seu lado.

### 13.5 Credenciais de Acesso

A credencial de acesso ao AUDESP pertence à **Prefeitura** (órgão concessor), não à
organização: um município reporta todas as organizações sob sua responsabilidade
através de uma única conta junto ao Tribunal.

Nenhum usuário ou senha é armazenado em banco de dados. O registro em banco limita-se
à existência e ao estado de ativação da credencial; os valores efetivos são resolvidos
em tempo de execução a partir do Google Secret Manager em ambiente real, ou de variáveis
de ambiente em desenvolvimento local. O sistema mantém ambientes distintos de piloto e
produção.

### 13.6 Dados de Referência

As tabelas de domínio do AUDESP — tipos de fonte de recurso, categorias de despesa,
veículos de publicação e demais — são implementadas como enumerações com os rótulos
oficiais extraídos dos esquemas.

Duas tabelas permanecem armazenadas como código numérico bruto, sem rótulo: o código do
banco (tabela BACEN, com cerca de 400 valores) e o código do estado emissor (27
valores). Não há lista oficial de rótulos publicada para nenhuma das duas no manual ou
nos esquemas. Em sistema de compliance, exibir o código correto é preferível a inventar
um rótulo que o município venha a protocolar junto ao Tribunal.

### 13.7 Prazos

Diferentemente da prestação de contas interna, cuja periodicidade é definida pela
própria gestão, a remessa ao AUDESP está sujeita a prazos externos com penalidade por
atraso — dez dias úteis contados da assinatura, para estes instrumentos, desde 1º de
junho de 2023.

---

## 14. MÓDULO DE PORTAL DA TRANSPARÊNCIA

> Acrescentado na revisão de 12 de agosto de 2026. O módulo já existia à época da
> redação original, mencionado apenas de passagem em 1.5.

### 14.1 Escopo

O sistema disponibiliza superfície pública de consulta em `/transparencia/`, com shell
visual próprio, distinto da aplicação autenticada. É o canal pelo qual a sociedade
consulta as parcerias firmadas, os valores repassados e a documentação institucional
das organizações.

### 14.2 Publicação de Parcerias

Cada contrato pode ter uma ficha de transparência associada, contendo objeto, número e
datas do ajuste, valores, situação e a relação de transferências financeiras
realizadas — cada uma com data, valor, conta creditada, tipo, número e exercício do
documento.

A publicação é controlada por sinalizador explícito de visibilidade pública. **O
sinalizador é portão de publicação, não filtro de interface:** parceria marcada como
não pública não deve ser acessível por nenhuma via, inclusive por endereço direto.

### 14.3 Prestação de Contas Pública

O sistema permite associar a uma parceria a descrição das atividades executadas, o
atingimento das metas e os resultados esperados, com registro de motivo em caso de
rejeição.

### 14.4 Canal de Denúncia de Irregularidades

O portal disponibiliza formulário público para comunicação de irregularidade em
parceria, com registro de data, descrição e resolução. A situação de tratamento
contempla quatro estados: Pendente (padrão), Em investigação, Resolvido e Rejeitado.

### 14.5 Documentação Institucional

O portal expõe os documentos organizacionais classificados como públicos, conforme o
controle de visibilidade descrito em 1.5.

### 14.6 Checklist de Transparência

O sistema mantém, vinculado à demonstração anual, o checklist de divulgação previsto no
§34 do manual AUDESP: existência de sítio eletrônico, os respectivos endereços, e a
verificação item a item da divulgação de estatuto atualizado, ajustes firmados, plano
de trabalho, relação de dirigentes, relação de prestadores de serviço, remuneração
individualizada, demonstrações contábeis, regulamento de compras, regulamento de
contratação e relatório estatístico do serviço de informação ao cidadão.

Os dez itens de verificação só têm significado quando há sítio eletrônico declarado; na
ausência dele, o documento AUDESP omite os blocos inteiros, conforme a regra 1 do
§34.2 do manual.

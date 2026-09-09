# Case técnico — Cientista de Dados Sênior | ML e IA Generativa

**Instituição Financeira Aurora (fictícia)**  
**Área:** Recuperação de Crédito — Pessoa Jurídica  
**Nível:** Sênior  
**Prazo sugerido:** 6 dias corridos

## 1. Contexto

A Instituição Financeira Aurora deseja evoluir a recuperação de crédito de clientes Pessoa Jurídica (PJ). Atualmente, a priorização de carteiras e a escolha das estratégias de contato combinam regras manuais, informações dispersas e análises pontuais. Isso limita a escala da operação e pode gerar abordagens pouco adequadas ao momento financeiro, ao perfil e ao histórico de cada empresa.

O desafio é desenhar uma solução analítica que ajude a operação a priorizar clientes com maior propensão à regularização, compreender os fatores associados a essa propensão e recomendar estratégias coerentes com as políticas internas. Além da modelagem preditiva, a instituição deseja explorar IA Generativa para apoiar analistas na consulta de informações, interpretação de evidências e tomada de decisão — sem automatizar decisões materiais sem supervisão humana.

A solução deverá considerar o caráter sensível do domínio financeiro: temporalidade correta, prevenção de vazamento de informação, explicabilidade, rastreabilidade, segurança, governança, uso responsável de IA e monitoramento contínuo.

## 2. Objetivo

Construir e apresentar uma proposta capaz de:

- Estimar a probabilidade de cada cliente regularizar sua situação nos próximos 30 dias.
- Identificar os fatores que mais influenciam essa probabilidade, tanto no nível global quanto no nível individual.
- Recomendar estratégias de recuperação coerentes com o score, o perfil do cliente, as regras de negócio e o histórico de interações.
- Utilizar IA Generativa para apoiar analistas com respostas fundamentadas, consulta a dados e recuperação de documentos.
- Propor uma arquitetura produtiva escalável, segura, observável e governável.

O protótipo não precisa automatizar a decisão final. Espera-se que o candidato deixe claros os pontos de intervenção humana, as limitações e os riscos.

## 3. Dados disponibilizados

Todos os dados e documentos deste case são **100% sintéticos** e foram produzidos exclusivamente para fins de avaliação.

### clientes.csv

Base estruturada no nível cliente/data de referência, contendo:

- Informações cadastrais, como setor, porte, UF e tempo de relacionamento.
- Informações financeiras, como faturamento estimado, saldo devedor, limite, utilização e atraso.
- Perfil de relacionamento, como canal preferencial, contatos anteriores, promessas e renegociações.
- Variável target `regularizou_30d`, que indica se houve regularização dentro da janela futura de 30 dias.

O arquivo contém ainda variáveis de score simuladas. Pelo menos uma delas pode ter sido atualizada após a data de referência ou durante a janela de performance. O candidato deverá investigar a definição temporal das variáveis e decidir se existe risco de **vazamento de informação (target leakage)**. Não se espera que nomes de colunas sejam aceitos como evidência suficiente: a decisão deve ser justificada com base na disponibilidade da informação no momento da inferência.

### interacoes.csv

Base com o histórico textual de interações entre analistas e clientes, incluindo data, canal, direção, resultado e texto sintético da interação.

Pode ser utilizada para:

- Extração de features estruturadas a partir de texto e eventos.
- Técnicas de NLP e representação textual.
- Análise qualitativa de objeções, intenção, dificuldade financeira e preferência de canal.
- Geração de sinais para recomendação de estratégia.
- Composição do contexto consultado pelo agente.

O candidato deverá respeitar a data de referência ao construir variáveis históricas e explicar como evitaria usar interações futuras em treinamento ou inferência.

### documentos_rag/

Conjunto de documentos fictícios de negócio que forma a base de conhecimento do agente:

- `politica_recuperacao_pj.txt`
- `faq_negociacao_pj.txt`
- `manual_canais_contato.txt`
- `criterios_ofertas_renegociacao.txt`
- `guia_conduta_atendimento.txt`

Os documentos contêm políticas, critérios, orientações operacionais e restrições. O candidato pode propor chunking, metadados, embeddings, indexação híbrida, filtros e estratégia de atualização.

### mock_tools.py

Módulo Python com ferramentas locais simuladas para:

- Consulta de dados cadastrais e financeiros do cliente.
- Consulta de score de regularização.
- Recuperação do histórico de interações.
- Busca na documentação de negócio.
- Recomendação básica por regras, usada apenas como baseline.

As ferramentas utilizam `pandas`, não acessam serviços externos e podem ser adaptadas ou substituídas.

## 4. Tarefas Esperadas

### Parte 1 - Análise Exploratória

Realize uma análise exploratória que contemple, no mínimo:

- Qualidade, completude, consistência, cardinalidade e distribuição das variáveis.
- Distribuição e prevalência da target `regularizou_30d`.
- Relações entre variáveis cadastrais, financeiras, comportamentais e a regularização.
- Análise temporal e identificação de variáveis potencialmente indisponíveis no momento da decisão.
- Possíveis vieses, limitações e riscos de representatividade.
- Hipóteses de negócio levantadas a partir dos dados.
- Sugestão de novos dados que poderiam melhorar a solução, indicando utilidade, disponibilidade e cuidados de governança.

Não é necessário produzir um catálogo exaustivo de gráficos. Priorize análises que ajudem a tomar decisões sobre modelagem e produto.

### Parte 2 - Modelo Preditivo

Desenvolva uma abordagem supervisionada para estimar a probabilidade de regularização em 30 dias. Apresente:

- Tratamento de dados ausentes, inconsistências, outliers e variáveis categóricas.
- Estratégia de feature engineering, incluindo, se aplicável, sinais derivados de `interacoes.csv`.
- Divisão entre treino, validação e teste. Justifique especialmente a escolha entre divisão aleatória, temporal ou por grupos.
- Um baseline e pelo menos uma alternativa de modelagem.
- Ajuste de hiperparâmetros compatível com o tamanho e o propósito do case.
- Justificativas técnicas e de negócio para as principais escolhas.
- Interpretação global e individual das previsões.
- Análise de estabilidade, generalização, viés e limitações.

Podem ser utilizadas métricas como:

- AUC-ROC.
- KS.
- Precision.
- Recall.
- F1-score.
- Matriz de confusão.
- Calibração, por exemplo Brier Score e curva de calibração.
- Lift ou ganhos por faixa de score.

**Não é obrigatório utilizar todas as métricas.** Selecione as mais relevantes para a decisão operacional e explique limiares, custos de erro e trade-offs. Caso proponha uma política de priorização, mostre como ela se relaciona com capacidade operacional e benefício esperado.

### Parte 3 - Recomendação

Crie uma lógica explicável de recomendação que combine:

- Score ou probabilidade calibrada.
- Perfil cadastral, financeiro e de relacionamento do cliente.
- Regras e restrições de negócio presentes nos documentos.
- Histórico e resultado das interações.

As recomendações podem incluir:

- Contato digital.
- Parcelamento.
- Oferta customizada.
- Análise especializada.
- Nova tentativa de contato em canal ou horário alternativo.
- Priorização operacional.

Para cada recomendação, informe ao menos: ação proposta, justificativa, evidências utilizadas, restrições aplicáveis, nível de confiança e condição de encaminhamento para análise humana. Discuta como evitar recomendações inadequadas, discriminatórias ou incompatíveis com a política vigente.

### Parte 4 - Agente com IA Generativa

Desenvolva um protótipo de agente de apoio ao analista contendo:

- Integração com um LLM à sua escolha ou uma interface claramente substituível por LLM.
- RAG sobre os documentos fornecidos.
- Consulta a dados estruturados do cliente.
- Consulta de score de regularização.
- Uso de Tool Calling ou Function Calling.
- Respostas fundamentadas em evidências recuperadas, com indicação das fontes.

O agente deve ser capaz de responder perguntas como:

- Qual é o perfil do cliente?
- Qual é a probabilidade de regularização?
- Quais fatores influenciam a previsão?
- Qual estratégia é recomendada?
- Quais evidências sustentam a recomendação?
- Quais documentos suportam a decisão?
- Existem restrições para essa estratégia?

Espera-se uma separação clara entre fatos recuperados, inferências do modelo e sugestões geradas. O agente não deve inventar dados ausentes, regras ou autorizações. Quando não houver evidência suficiente, deve declarar a limitação, pedir informação adicional ou encaminhar para análise humana.

O `agent_skeleton.py` fornecido é apenas um baseline determinístico sem LLM. O candidato pode evoluí-lo, substituí-lo ou reutilizar suas interfaces.

### Parte 5 - Avaliação do Agente

Defina uma estratégia de avaliação offline e, se aplicável, online. Inclua um conjunto de perguntas de teste e métricas para avaliar:

- Faithfulness: aderência da resposta ao contexto e às saídas das ferramentas.
- Relevância da resposta para a pergunta e para a tarefa do analista.
- Precisão do contexto recuperado.
- Recall do contexto relevante.
- Seleção, parametrização e uso correto das ferramentas.
- Taxa de respostas sem evidência, sem citação ou com afirmações não sustentadas.
- Avaliação humana por analistas e especialistas de política.

Podem ser utilizados frameworks como RAGAS, DeepEval ou avaliação própria. Explique limitações de LLM-as-a-judge, critérios de aceitação, amostragem, golden set, testes adversariais e como falhas seriam registradas e corrigidas.

### Parte 6 - Arquitetura de Produção

Proponha uma arquitetura de referência para produção contemplando:

- Ingestão batch e/ou streaming de dados estruturados, interações e documentos.
- Pipeline de features com consistência entre treino e inferência.
- Treinamento, validação e registro do modelo.
- Política de retreinamento por calendário, performance ou drift.
- Versionamento de dados, features, modelos, prompts, documentos, índices e configurações.
- Deploy batch e/ou online, conforme necessidade de negócio.
- Vector store e estratégia de indexação, filtros, atualização e exclusão documental.
- Orquestração do agente, roteamento, memória permitida, ferramentas e limites de execução.
- Observabilidade de dados, modelo, recuperação, LLM, ferramentas, latência, custo e resultado de negócio.
- Segurança: autenticação, autorização, segregação, criptografia, gestão de segredos, proteção contra prompt injection e minimização de dados.
- Governança: responsáveis, trilha de auditoria, aprovação, explicabilidade, retenção, revisão humana e gestão de mudanças.
- Fallback para indisponibilidade de modelo, LLM, vector store, ferramenta ou baixa confiança.
- Evolução contínua por feedback, experimentação controlada, reavaliação e rollback.

Inclua um diagrama e explicite as decisões que são automatizadas, assistidas ou reservadas a humanos. Não é necessário vincular a solução a um provedor específico de nuvem.

## 5. Entregáveis

Entregue:

- Notebook(s) ou scripts reproduzíveis para análise, preparação e modelagem.
- Protótipo funcional do agente, com instruções de execução e exemplos.
- `README` com premissas, estrutura, instalação, execução, decisões, limitações e próximos passos.
- Apresentação executiva com **até 10 slides**, adequada a uma banca mista de negócio e tecnologia.

Organize o repositório de modo que outra pessoa consiga executar os principais fluxos. Dependências, versões e variáveis de ambiente devem estar documentadas. Não inclua chaves, credenciais ou dados reais.

## 6. Observações

- Os dados deste case são **100% sintéticos**.
- **Nenhum dado real** de cliente, contrato, colaborador ou instituição foi utilizado.
- O objetivo **NÃO é maximizar métricas**.
- O foco é avaliar raciocínio analítico, visão de negócio, qualidade técnica e capacidade de implementação.
- Não existe resposta única. Premissas bem explicitadas e decisões coerentes são parte central da avaliação.
- Escopo e profundidade devem ser compatíveis com o prazo; decisões conscientes de simplificação são aceitas quando documentadas.
- Soluções submetidas serão avaliadas apenas no contexto do processo seletivo fictício deste exercício.

## 7. Prazo

O prazo sugerido é de **6 dias corridos**, dentro da faixa recomendada de 5 a 7 dias. Caso alguma parte não seja concluída, documente a abordagem pretendida, as decisões já tomadas e os próximos passos.


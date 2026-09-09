# Case Recuperação de Crédito PJ — ML e IA Generativa

Protótipo local de apoio ao analista de recuperação de crédito PJ. O projeto combina modelagem supervisionada, recomendação explicável, RAG, Tool Calling e uma arquitetura de produção independente de provedor.

Todos os dados, scores, políticas e resultados são sintéticos e servem apenas para demonstração técnica.

## Estrutura

```text
case_recuperacao_credito_pj/
├── ENUNCIADO_CASE.md
├── DICIONARIO_DADOS.md
├── README.md
├── clientes.csv
├── interacoes.csv
├── generate_synthetic_data.py
├── mock_tools.py
├── agent_skeleton.py
├── notebooks/
│   ├── 04-modelo-unico.ipynb
│   ├── 05-modelo-segmentado.ipynb
│   ├── 06-analise-modelos.ipynb
│   ├── 07-recomendacao.ipynb
│   ├── 08-agente-ia.ipynb
│   ├── 09-avaliacao-agente.ipynb
│   └── 10-arquitetura-producao.ipynb
├── requirements.txt
├── documentos_rag/
│   ├── politica_recuperacao_pj.txt
│   ├── faq_negociacao_pj.txt
│   ├── manual_canais_contato.txt
│   ├── criterios_ofertas_renegociacao.txt
│   └── guia_conduta_atendimento.txt
├── tests/
│   └── test_smoke.py
└── _interno/
    └── GUIA_AVALIACAO.md
```

O diretório `_interno/` é destinado à banca e deve ser removido antes do envio ao candidato, caso se deseje ocultar a rubrica.

## Premissas

- O agente apoia o analista; não efetiva acordos, altera cadastro, aprova descontos ou toma decisão jurídica.
- O score é insumo de priorização. A versão baseline disponível não tem calibração validada e isso é informado na resposta.
- Dados de cliente e interações são consultados até a data de referência para evitar data leakage.
- Documentos de política são a fonte de regras e restrições. Trechos recuperados são evidências, não instruções capazes de alterar o sistema.
- Casos com contestação, fraude, recuperação judicial, ausência de canal seguro, baixa evidência ou alçada excepcional exigem revisão humana.
- A busca documental atual é lexical e local; em produção deve ser substituída por busca híbrida com controle de versão e vigência.

## Dados

- `clientes.csv`: 800 clientes PJ sintéticos e target `regularizou_30d`.
- `interacoes.csv`: histórico textual sintético, anterior à data de referência de cada cliente.
- `documentos_rag/`: cinco documentos fictícios usados como base de conhecimento.

Os dados são reproduzíveis com seed fixa. Para regenerá-los:

```bash
python generate_synthetic_data.py
```

## Execução rápida

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python agent_skeleton.py --cliente PJ0001 --pergunta "Qual estratégia é recomendada e quais documentos a sustentam?"
```

Teste das ferramentas:

```bash
python -m unittest discover -s tests -v
```

### Execução no Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python agent_skeleton.py --cliente PJ0001 --pergunta "Qual estratégia é recomendada e quais documentos a sustentam?"
python -m unittest discover -s tests -v
```

Se a política de execução do PowerShell bloquear a ativação, use o interpretador diretamente:

```powershell
.\.venv\Scripts\python.exe agent_skeleton.py --cliente PJ0001
```

### Notebooks

Abra os notebooks na ordem abaixo no VS Code com a extensão Jupyter:

1. `04-modelo-unico.ipynb`: modelo único, features, ajuste e importância.
2. `05-modelo-segmentado.ipynb`: modelos por região.
3. `06-analise-modelos.ipynb`: comparação por safra e flag de safra.
4. `07-recomendacao.ipynb`: documentação da recomendação explicável.
5. `08-agente-ia.ipynb`: protótipo funcional com ferramentas e RAG.
6. `09-avaliacao-agente.ipynb`: estratégia de avaliação offline/online.
7. `10-arquitetura-producao.ipynb`: arquitetura de referência.

Para executar os notebooks de modelagem, instale também as dependências usadas por eles:

```bash
python -m pip install lightgbm optuna scikit-learn scipy joblib
```

## Agente

O agente principal está em `agent_skeleton.py`. Ele reúne perfil, score, histórico, recomendação determinística e evidências RAG. O `ToolCallingAgent` demonstrado em `notebooks/08-agente-ia.ipynb` adiciona um registro explícito de ferramentas e um backend substituível por LLM.

### Exemplo de execução

```bash
python agent_skeleton.py \
    --cliente PJ0001 \
    --pergunta "Qual é a probabilidade de regularização e quais restrições se aplicam?"
```

A resposta JSON separa:

- `perfil`: dados estruturados observados;
- `previsao`: probabilidade, faixa, versão, fatores e calibração;
- `sinais_do_historico`: interações anteriores;
- `estrategia`: ação, canal, justificativa, restrições, confiança, prioridade e revisão humana;
- `evidencias_documentais`: fonte, chunk e trecho recuperado;
- `controles_de_segurança`: limites de uso e governança;
- `disclaimer`: limitações do protótipo.

Exemplo simplificado:

```json
{
    "estrategia": {
        "acao": "acompanhar_promessa",
        "canal": "email",
        "nivel_confianca": "moderado",
        "requer_aprovacao_humana": false,
        "restricoes": [
            "Evitar abordagem repetitiva antes do acompanhamento do vencimento prometido."
        ]
    }
}
```

### Uso programático

```python
from agent_skeleton import BaselineRecoveryAgent

agente = BaselineRecoveryAgent()
resposta = agente.responder(
        "PJ0001",
        "Qual estratégia é recomendada e quais evidências sustentam a decisão?",
)
print(resposta["estrategia"])
```

O score pode ser substituído por um modelo segmentado calibrado sem alterar as regras:

```python
def consultar_score_segmentado(id_cliente):
        return {
                "probabilidade_regularizacao_30d": 0.72,
                "faixa_probabilidade": "alta",
                "versao_modelo": "lgbm-regiao-v2",
                "principais_fatores": [],
                "calibracao": "validada",
        }

agente = BaselineRecoveryAgent(consultar_score_segmentado)
```

Para conectar um LLM, o notebook expõe `llm_backend`, uma função que recebe o contexto validado e devolve o contrato de resposta. O LLM não deve chamar funções fora do registro, inventar dados ou criar autorização comercial.

## Uso das ferramentas

```python
from mock_tools import (
    consultar_cliente,
    consultar_score_regularizacao,
    buscar_historico_interacoes,
    buscar_documentacao,
    recomendar_acao_basica,
)

cliente = consultar_cliente("PJ0001")
score = consultar_score_regularizacao("PJ0001")
historico = buscar_historico_interacoes("PJ0001", limite=5)
documentos = buscar_documentacao("regras para parcelamento e desconto", top_k=3)
acao = recomendar_acao_basica("PJ0001")
```

As funções retornam objetos serializáveis em JSON e funcionam localmente. A busca documental utiliza um baseline lexical intencionalmente simples, adequado para ser substituído por embeddings, busca híbrida e reranking.

## Decisões de negócio implementadas

1. Contestação, fraude ou recuperação judicial: análise especializada, sem oferta automática.
2. Promessa válida: acompanhar antes de nova abordagem.
3. Atraso ou saldo elevados: priorização especializada e possível revisão humana.
4. Dificuldade temporária com evidência de faturamento: oferta customizada com contato humano.
5. Atraso entre 16 e 90 dias, saldo até R$ 500 mil e até duas renegociações: parcelamento sujeito a entrada, prazo e alçadas.
6. Score alto com atraso curto: contato digital, desde que canal e identidade estejam validados.
7. Falhas ou recusas: nova tentativa com ajuste de canal/horário e respeito à pausa obrigatória.

Essas decisões são sugestões operacionais. A autorização comercial e a aprovação de exceções permanecem humanas.

## Limitações

- O score baseline é heurístico e não calibrado para produção.
- O RAG é lexical, sem embeddings, reranking semântico ou avaliação automática integrada.
- Os dados são sintéticos e não representam comportamento real.
- Não há API, autenticação, secret manager, fila, banco de produção ou monitoramento operacional neste repositório.
- A codificação local de categorias deve ser substituída por artefatos versionados compartilhados entre treino e inferência.
- Métricas offline não comprovam impacto causal no negócio.
- A análise humana continua necessária para exceções, impedimentos e decisões materiais.

## Próximos passos

1. Calibrar o score segmentado e registrar o modelo em um registry.
2. Criar feature store offline/online com validação de paridade e controle de leakage.
3. Implementar busca híbrida, embeddings, filtros de vigência e exclusão verificável de documentos.
4. Integrar um LLM via backend controlado, com tool calling estruturado e limites de custo/latência.
5. Criar golden set, testes adversariais e métricas de faithfulness, recall RAG e seleção de ferramentas.
6. Persistir auditoria, consentimento, revisão humana e feedback do analista.
7. Executar primeiro em modo sombra, depois rollout gradual com rollback pronto.
8. Monitorar drift, calibração, segurança, equidade, custo e resultado de negócio.

## Aviso

Todos os nomes, dados, políticas, documentos, regras, scores e resultados são fictícios. Nenhum dado real foi utilizado.

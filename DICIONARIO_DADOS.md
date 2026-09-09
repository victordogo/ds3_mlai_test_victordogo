# Dicionário de dados sintéticos

## clientes.csv

Unidade de análise: um cliente PJ em uma data de referência. A target cobre os 30 dias posteriores a essa data.

| Campo | Tipo esperado | Definição sintética | Momento esperado de disponibilidade |
|---|---|---|---|
| `id_cliente` | string | Identificador fictício no formato `PJ0001` | Data de referência |
| `data_referencia` | data | Data de corte entre observação e performance | Data de referência |
| `setor` | categoria | Setor econômico cadastrado | Data de referência |
| `porte` | categoria | Faixa fictícia de porte da empresa | Data de referência |
| `uf` | categoria | UF cadastral | Data de referência |
| `tempo_relacionamento_meses` | inteiro | Meses desde o início do relacionamento | Data de referência |
| `faturamento_mensal_estimado` | decimal | Estimativa sintética de faturamento mensal em R$ | Última estimativa anterior ou igual à referência |
| `saldo_devedor` | decimal | Saldo consolidado sintético em R$ | Data de referência |
| `dias_atraso` | inteiro | Dias corridos desde o vencimento de referência | Data de referência |
| `qtd_contratos_ativos` | inteiro | Quantidade de contratos ativos | Data de referência |
| `qtd_parcelas_vencidas` | inteiro | Quantidade de parcelas vencidas | Data de referência |
| `limite_credito` | decimal | Limite consolidado sintético em R$ | Data de referência |
| `utilizacao_limite_pct` | decimal | Razão sintética de utilização do limite; 1,00 equivale a 100% | Data de referência |
| `qtd_contatos_ult_30d` | inteiro | Contatos registrados nos 30 dias anteriores | Janela histórica |
| `promessa_pagamento_ult_30d` | binário | Indica promessa registrada nos 30 dias anteriores | Janela histórica |
| `renegociacoes_ult_12m` | inteiro | Renegociações nos 12 meses anteriores | Janela histórica |
| `canal_preferencial` | categoria | Canal preferido e autorizado no cadastro sintético | Data de referência |
| `risco_setorial` | categoria | Classificação setorial fictícia | Data de referência |
| `score_regularizacao_legado` | inteiro 0–1000 | Score legado sintético, disponível no corte | Data de referência; origem deve ser discutida |
| `score_cobranca_atualizado_30d` | inteiro 0–1000 | Score sintético atualizado durante ou ao final da janela futura | Potencialmente posterior à referência; investigar leakage |
| `regularizou_30d` | binário | Target: regularização em até 30 dias após a referência | Somente após a janela de performance |

Há ausências sintéticas em `faturamento_mensal_estimado`, `canal_preferencial` e `risco_setorial`.

## interacoes.csv

Unidade de análise: uma interação registrada entre a instituição fictícia e um cliente.

| Campo | Tipo esperado | Definição sintética |
|---|---|---|
| `id_interacao` | string | Identificador fictício da interação |
| `id_cliente` | string | Chave para `clientes.csv` |
| `data_interacao` | data | Data da interação |
| `canal` | categoria | WhatsApp, e-mail, telefone ou portal |
| `direcao` | categoria | Interação ativa ou receptiva |
| `resultado` | categoria | Resultado operacional sintético |
| `texto` | texto | Registro textual sintético da interação |

Para qualquer feature derivada, a elegibilidade temporal deve ser calculada relativamente à `data_referencia` do respectivo cliente.

## Observação de privacidade

Não existem nomes, documentos, telefones, e-mails, endereços ou identificadores reais. Todos os registros foram gerados programaticamente com seed fixa.


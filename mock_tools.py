"""Ferramentas locais simuladas para o case de recuperação de crédito PJ.

As funções retornam estruturas serializáveis em JSON e não acessam serviços
externos. O código é deliberadamente simples para que o candidato possa evoluir
interfaces, score, busca, validações e observabilidade.
"""

from __future__ import annotations

import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
CLIENTES_PATH = BASE_DIR / "clientes.csv"
INTERACOES_PATH = BASE_DIR / "interacoes.csv"
DOCUMENTOS_DIR = BASE_DIR / "documentos_rag"

STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "entre", "é", "na", "nas", "no", "nos", "o", "os", "ou", "para",
    "por", "qual", "quais", "que", "se", "sem", "um", "uma",
}


def _validar_arquivos() -> None:
    ausentes = [str(path) for path in (CLIENTES_PATH, INTERACOES_PATH) if not path.exists()]
    if ausentes:
        raise FileNotFoundError(
            "Arquivos de dados ausentes: " + ", ".join(ausentes) +
            ". Execute `python generate_synthetic_data.py`."
        )


@lru_cache(maxsize=1)
def _clientes() -> pd.DataFrame:
    _validar_arquivos()
    return pd.read_csv(CLIENTES_PATH, dtype={"id_cliente": "string", "uf": "string"})


@lru_cache(maxsize=1)
def _interacoes() -> pd.DataFrame:
    _validar_arquivos()
    return pd.read_csv(INTERACOES_PATH, dtype={"id_cliente": "string", "id_interacao": "string"})


def _normalizar_id(id_cliente: str) -> str:
    valor = str(id_cliente).strip().upper()
    if not re.fullmatch(r"PJ\d{4}", valor):
        raise ValueError("id_cliente deve seguir o formato PJ0001.")
    return valor


def _registro_cliente(id_cliente: str) -> pd.Series:
    cliente_id = _normalizar_id(id_cliente)
    encontrados = _clientes().loc[_clientes()["id_cliente"] == cliente_id]
    if encontrados.empty:
        raise KeyError(f"Cliente {cliente_id} não encontrado.")
    return encontrados.iloc[0]


def _pythonizar(valor: Any) -> Any:
    if pd.isna(valor):
        return None
    if hasattr(valor, "item"):
        return valor.item()
    return valor


def consultar_cliente(id_cliente: str) -> dict[str, Any]:
    """Consulta perfil estruturado disponível na data de referência.

    A target e o score pós-evento são ocultados para simular uma consulta de
    produção e reduzir o risco de leakage acidental.
    """

    registro = _registro_cliente(id_cliente)
    bloqueados = {"regularizou_30d", "score_cobranca_atualizado_30d"}
    dados = {coluna: _pythonizar(valor) for coluna, valor in registro.items() if coluna not in bloqueados}
    return {
        "status": "ok",
        "fonte": "clientes.csv",
        "data_referencia": dados["data_referencia"],
        "cliente": dados,
    }


def _sigmoid(valor: float) -> float:
    return 1.0 / (1.0 + math.exp(-valor))


def consultar_score_regularizacao(id_cliente: str) -> dict[str, Any]:
    """Calcula um score heurístico baseline sem usar target ou variável vazada."""

    registro = _registro_cliente(id_cliente)
    dias = float(registro["dias_atraso"])
    saldo = float(registro["saldo_devedor"])
    utilizacao = float(registro["utilizacao_limite_pct"])
    renegociacoes = float(registro["renegociacoes_ult_12m"])
    promessa = float(registro["promessa_pagamento_ult_30d"])
    legado = float(registro["score_regularizacao_legado"]) / 1000.0

    contribuicoes = {
        "score_legado": 2.2 * (legado - 0.5),
        "dias_atraso": -0.022 * dias,
        "saldo_devedor": -0.0000005 * saldo,
        "utilizacao_limite": -0.65 * max(0.0, utilizacao - 0.80),
        "renegociacoes_recentes": -0.24 * renegociacoes,
        "promessa_pagamento_recente": 0.72 * promessa,
    }
    logit = 0.55 + sum(contribuicoes.values())
    probabilidade = round(_sigmoid(logit), 4)
    faixa = "alta" if probabilidade >= 0.65 else "media" if probabilidade >= 0.35 else "baixa"
    fatores = sorted(contribuicoes.items(), key=lambda item: abs(item[1]), reverse=True)[:4]

    return {
        "status": "ok",
        "id_cliente": _normalizar_id(id_cliente),
        "data_referencia": str(registro["data_referencia"]),
        "probabilidade_regularizacao_30d": probabilidade,
        "faixa_probabilidade": faixa,
        "versao_modelo": "baseline-heuristico-v1",
        "calibracao": "não validada; uso exclusivo como baseline do case",
        "principais_fatores": [
            {
                "fator": nome,
                "direcao": "aumenta" if valor > 0 else "reduz",
                "contribuicao_logit": round(valor, 4),
            }
            for nome, valor in fatores
        ],
    }


def buscar_historico_interacoes(id_cliente: str, limite: int = 10) -> list[dict[str, Any]]:
    """Retorna as interações mais recentes do cliente até a data de referência."""

    if not 1 <= int(limite) <= 100:
        raise ValueError("limite deve estar entre 1 e 100.")
    registro = _registro_cliente(id_cliente)
    cliente_id = _normalizar_id(id_cliente)
    data_referencia = str(registro["data_referencia"])
    df = _interacoes()
    encontrados = df.loc[
        (df["id_cliente"] == cliente_id) & (df["data_interacao"] <= data_referencia)
    ].sort_values(["data_interacao", "id_interacao"], ascending=False).head(int(limite))
    return [
        {coluna: _pythonizar(valor) for coluna, valor in linha.items()}
        for linha in encontrados.to_dict(orient="records")
    ]


def _normalizar_texto(texto: str) -> str:
    texto_sem_acento = "".join(
        caractere for caractere in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(caractere)
    )
    return re.sub(r"[^a-z0-9\s]", " ", texto_sem_acento.lower())


def _tokens(texto: str) -> set[str]:
    return {
        token for token in _normalizar_texto(texto).split()
        if len(token) > 2 and token not in STOPWORDS
    }


@lru_cache(maxsize=1)
def _chunks_documentais() -> pd.DataFrame:
    if not DOCUMENTOS_DIR.exists():
        raise FileNotFoundError(f"Diretório documental ausente: {DOCUMENTOS_DIR}")
    chunks: list[dict[str, Any]] = []
    for caminho in sorted(DOCUMENTOS_DIR.glob("*.txt")):
        conteudo = caminho.read_text(encoding="utf-8")
        paragrafos = [p.strip() for p in re.split(r"\n\s*\n", conteudo) if p.strip()]
        for indice, paragrafo in enumerate(paragrafos, start=1):
            chunks.append(
                {
                    "fonte": caminho.name,
                    "chunk_id": f"{caminho.stem}:{indice}",
                    "conteudo": paragrafo,
                    "tokens": _tokens(paragrafo),
                }
            )
    return pd.DataFrame(chunks)


def buscar_documentacao(consulta: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Busca lexical simples nos documentos; baseline para substituição por RAG."""

    if not str(consulta).strip():
        raise ValueError("consulta não pode ser vazia.")
    if not 1 <= int(top_k) <= 10:
        raise ValueError("top_k deve estar entre 1 e 10.")
    consulta_tokens = _tokens(consulta)
    if not consulta_tokens:
        return []

    df = _chunks_documentais().copy()

    def pontuar(tokens_doc: set[str]) -> float:
        intersecao = consulta_tokens & tokens_doc
        cobertura = len(intersecao) / len(consulta_tokens)
        especificidade = len(intersecao) / math.sqrt(max(1, len(tokens_doc)))
        return round(0.75 * cobertura + 0.25 * especificidade, 6)

    df["score_busca"] = df["tokens"].map(pontuar)
    df = df.loc[df["score_busca"] > 0].sort_values(
        ["score_busca", "fonte", "chunk_id"], ascending=[False, True, True]
    ).head(int(top_k))
    return [
        {
            "fonte": linha["fonte"],
            "chunk_id": linha["chunk_id"],
            "score_busca": float(linha["score_busca"]),
            "trecho": linha["conteudo"],
        }
        for linha in df.to_dict(orient="records")
    ]


def recomendar_acao_basica(id_cliente: str) -> dict[str, Any]:
    """Combina score, perfil e histórico em regras explicáveis de baseline."""

    registro = _registro_cliente(id_cliente)
    score = consultar_score_regularizacao(id_cliente)
    historico = buscar_historico_interacoes(id_cliente, limite=10)
    resultados = {item["resultado"] for item in historico}
    dias = int(registro["dias_atraso"])
    saldo = float(registro["saldo_devedor"])
    probabilidade = float(score["probabilidade_regularizacao_30d"])
    canal = _pythonizar(registro["canal_preferencial"])
    restricoes: list[str] = []
    requer_aprovacao_humana = False

    if "contestacao" in resultados:
        acao = "analise_especializada_contestacao"
        justificativa = "Há contestação registrada; a negociação deve ser interrompida até validação."
        restricoes.append("Não apresentar oferta enquanto a contestação estiver aberta.")
        requer_aprovacao_humana = True
    elif "recuperacao_judicial" in resultados:
        acao = "analise_especializada_recuperacao_judicial"
        justificativa = "Há informação de recuperação judicial no histórico."
        restricoes.append("Não gerar oferta automatizada nem fornecer orientação jurídica.")
        requer_aprovacao_humana = True
    elif dias > 90 or (dias > 60 and saldo >= 250_000):
        acao = "priorizacao_operacional_especializada"
        justificativa = "A combinação de atraso e saldo exige tratamento especializado."
        requer_aprovacao_humana = True
    elif int(registro["promessa_pagamento_ult_30d"]) == 1 and "promessa_registrada" in resultados:
        acao = "acompanhar_promessa"
        justificativa = "Existe promessa recente; evite abordagem repetitiva antes do acompanhamento."
    elif probabilidade >= 0.65 and dias <= 30:
        acao = "contato_digital"
        justificativa = "Atraso curto e alta probabilidade favorecem abordagem simples de baixo custo."
    elif 16 <= dias <= 90 and int(registro["renegociacoes_ult_12m"]) <= 2:
        acao = "avaliar_parcelamento_ou_oferta_customizada"
        justificativa = "Atraso intermediário e histórico de renegociação dentro do limite do baseline."
        requer_aprovacao_humana = saldo >= 250_000 or dias > 60
    else:
        acao = "nova_tentativa_contato"
        justificativa = "Não há evidência suficiente para uma oferta automática; coletar contexto adicional."

    if canal is None:
        restricoes.append("Canal preferencial ausente; validar canal e consentimento antes do contato.")
        requer_aprovacao_humana = True

    consulta_documental = f"{acao} atraso {dias} dias saldo alto regras restrições canal oferta"
    evidencias_documentais = buscar_documentacao(consulta_documental, top_k=3)
    return {
        "status": "ok",
        "id_cliente": _normalizar_id(id_cliente),
        "acao_recomendada": acao,
        "canal_sugerido": canal,
        "justificativa": justificativa,
        "probabilidade_regularizacao_30d": probabilidade,
        "nivel_confianca": "baixo" if requer_aprovacao_humana else "moderado",
        "restricoes": restricoes,
        "requer_aprovacao_humana": requer_aprovacao_humana,
        "fontes_documentais": [item["fonte"] for item in evidencias_documentais],
        "aviso": "Baseline fictício; validar elegibilidade no motor de ofertas antes de qualquer proposta.",
    }


TOOL_SCHEMAS = [
    {
        "name": "consultar_cliente",
        "description": "Consulta o perfil estruturado de um cliente PJ na data de referência.",
        "parameters": {"type": "object", "properties": {"id_cliente": {"type": "string"}}, "required": ["id_cliente"]},
    },
    {
        "name": "consultar_score_regularizacao",
        "description": "Retorna a probabilidade baseline de regularização em 30 dias e fatores.",
        "parameters": {"type": "object", "properties": {"id_cliente": {"type": "string"}}, "required": ["id_cliente"]},
    },
    {
        "name": "buscar_historico_interacoes",
        "description": "Recupera interações anteriores à data de referência.",
        "parameters": {
            "type": "object",
            "properties": {"id_cliente": {"type": "string"}, "limite": {"type": "integer", "default": 10}},
            "required": ["id_cliente"],
        },
    },
    {
        "name": "buscar_documentacao",
        "description": "Busca trechos relevantes na base documental fictícia.",
        "parameters": {
            "type": "object",
            "properties": {"consulta": {"type": "string"}, "top_k": {"type": "integer", "default": 3}},
            "required": ["consulta"],
        },
    },
    {
        "name": "recomendar_acao_basica",
        "description": "Retorna recomendação determinística explicável usada como baseline.",
        "parameters": {"type": "object", "properties": {"id_cliente": {"type": "string"}}, "required": ["id_cliente"]},
    },
]


if __name__ == "__main__":
    import json

    exemplo = "PJ0001"
    print(json.dumps({
        "cliente": consultar_cliente(exemplo),
        "score": consultar_score_regularizacao(exemplo),
        "historico": buscar_historico_interacoes(exemplo, limite=3),
        "documentos": buscar_documentacao("parcelamento para atraso acima de 60 dias", top_k=2),
        "recomendacao": recomendar_acao_basica(exemplo),
    }, ensure_ascii=False, indent=2))


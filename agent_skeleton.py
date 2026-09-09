"""Esqueleto determinístico de agente para o candidato evoluir.

Este baseline não usa LLM. Ele demonstra orquestração de ferramentas, reunião de
contexto e resposta fundamentada. Em uma evolução com LLM, mantenha a separação
entre dados, score, regras e recomendação, além de validar argumentos e saídas.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from mock_tools import (
    buscar_documentacao,
    buscar_historico_interacoes,
    consultar_cliente,
    consultar_score_regularizacao,
    recomendar_acao_basica,
)


class BaselineRecoveryAgent:
    """Orquestrador local sem LLM, memória ou acesso externo."""

    def __init__(
        self,
        score_provider: Callable[[str], dict[str, Any]] = consultar_score_regularizacao,
    ) -> None:
        self.score_provider = score_provider

    @staticmethod
    def _recomendacao_explicavel(
        cliente: dict[str, Any],
        score: dict[str, Any],
        historico: list[dict[str, Any]],
        documentos: list[dict[str, Any]],
    ) -> dict[str, Any]:
        dados = cliente["cliente"]
        resultados = {item.get("resultado") for item in historico}
        dias_atraso = int(dados.get("dias_atraso") or 0)
        saldo_devedor = float(dados.get("saldo_devedor") or 0)
        faturamento = dados.get("faturamento_mensal_estimado")
        renegociacoes = int(dados.get("renegociacoes_ult_12m") or 0)
        probabilidade = float(score["probabilidade_regularizacao_30d"])
        canal = dados.get("canal_preferencial")
        restricoes: list[str] = []
        evidencias: list[str] = [
            f"probabilidade de regularização em 30 dias: {probabilidade:.4f}",
            f"score/modelo: {score.get('versao_modelo', 'não informado')}",
            f"dias em atraso: {dias_atraso}",
            f"saldo devedor: {saldo_devedor:.2f}",
            f"faturamento mensal estimado: {faturamento}",
            f"renegociações nos últimos 12 meses: {renegociacoes}",
            f"resultados recentes: {sorted(resultado for resultado in resultados if resultado)}",
        ]
        requer_humano = False

        impedimentos = {
            "contestacao": "contestação de dívida registrada",
            "fraude": "suspeita de fraude registrada",
            "recuperacao_judicial": "recuperação judicial registrada",
        }
        impedimento = next(
            ((resultado, motivo) for resultado, motivo in impedimentos.items() if resultado in resultados),
            None,
        )

        if impedimento:
            acao = "analise_especializada"
            justificativa = f"Há {impedimento[1]}; a negociação deve ser interrompida."
            restricoes.append("Não apresentar oferta automatizada até a validação especializada.")
            requer_humano = True
            encaminhamento = "Encaminhar imediatamente ao fluxo especializado e registrar o motivo."
        elif canal is None:
            acao = "analise_especializada"
            justificativa = "Não há canal preferencial registrado para contato seguro."
            restricoes.append("Validar cadastro e consentimento antes de qualquer contato.")
            requer_humano = True
            encaminhamento = "Encaminhar para atualização cadastral ou análise humana."
        elif "promessa_registrada" in resultados and int(dados.get("promessa_pagamento_ult_30d") or 0) == 1:
            acao = "acompanhar_promessa"
            justificativa = "Há promessa de pagamento registrada e ainda indicada como válida."
            restricoes.append("Evitar abordagem repetitiva antes do acompanhamento do vencimento prometido.")
            encaminhamento = "Encaminhar se a promessa vencer, for quebrada ou houver pedido do cliente."
        elif dias_atraso > 90 or (dias_atraso > 60 and saldo_devedor >= 250_000):
            acao = "priorizacao_operacional"
            justificativa = "Atraso elevado ou combinação de atraso e saldo exige tratamento especializado."
            restricoes.append("Qualquer medida jurídica ou condição excepcional exige aprovação humana.")
            requer_humano = True
            encaminhamento = "Encaminhar para especialista antes de negociar ou alterar condições."
        elif "dificuldade_temporaria" in resultados and faturamento not in (None, ""):
            acao = "oferta_customizada"
            justificativa = "O histórico indica dificuldade temporária e há faturamento informado para avaliar o ciclo de caixa."
            restricoes.extend([
                "Exigir contato humano e registro da evidência de fluxo de caixa.",
                "Não alterar principal nem ultrapassar 36 meses sem a alçada aplicável.",
            ])
            requer_humano = True
            encaminhamento = "Encaminhar a especialista para validar elegibilidade e alçada."
        elif 16 <= dias_atraso <= 90 and saldo_devedor <= 500_000 and renegociacoes <= 2:
            acao = "parcelamento"
            justificativa = "Atraso, saldo e histórico de renegociação estão dentro dos critérios do parcelamento padronizado."
            restricoes.extend([
                "Exigir entrada mínima de 10% e prazo máximo de 24 meses.",
                "Acima de R$ 250.000 ou 60 dias de atraso, exigir especialista.",
            ])
            requer_humano = saldo_devedor > 250_000 or dias_atraso > 60
            encaminhamento = (
                "Encaminhar para especialista antes da oferta por limite de saldo/atraso."
                if requer_humano
                else "Encaminhar se o motor de ofertas reprovar a elegibilidade."
            )
        elif probabilidade >= 0.65 and dias_atraso <= 30:
            acao = "contato_digital"
            justificativa = "Probabilidade alta e atraso curto favorecem abordagem digital de baixo custo."
            restricoes.extend([
                "Usar somente canal autorizado e validar a identidade antes de expor dados financeiros.",
                "Não prometer aprovação, desconto ou retirada de restrição.",
            ])
            encaminhamento = "Encaminhar se o canal não for validado, houver recusa ou surgirem impedimentos."
        elif resultados.intersection({"sem_sucesso", "recusa_oferta"}):
            acao = "nova_tentativa_contato"
            justificativa = "O histórico mostra contato sem sucesso ou recusa; ajustar canal, horário ou estratégia."
            restricoes.append("Após três tentativas sem sucesso em sete dias, pausar 48 horas.")
            encaminhamento = "Encaminhar se não houver canal alternativo autorizado ou após novas falhas."
        else:
            acao = "analise_especializada"
            justificativa = "As evidências não são suficientes para uma oferta segura e específica."
            restricoes.append("Não gerar oferta automática sem evidência de elegibilidade.")
            requer_humano = True
            encaminhamento = "Solicitar revisão humana e coleta de contexto adicional."

        if canal in {"whatsapp", "sms"}:
            restricoes.append("Exigir consentimento/base válida e confirmação de identidade antes de detalhar a dívida.")
        elif canal == "email":
            restricoes.append("Usar endereço corporativo validado e assunto neutro.")
        elif canal == "telefone":
            restricoes.append("Confirmar razão social e representante; não revelar motivo financeiro a terceiros.")
        elif canal == "portal":
            restricoes.append("Usar o portal para detalhes e aceite; não simular confirmação de acordo.")

        if not documentos:
            restricoes.append("Nenhuma evidência documental foi recuperada; aplicar fallback seguro.")
            requer_humano = True
            encaminhamento = "Encaminhar para análise humana por ausência de evidência documental."

        nivel_confianca = "baixo"
        if documentos and score.get("calibracao") == "validada":
            nivel_confianca = "alto" if not requer_humano else "moderado"
        elif documentos and not requer_humano:
            nivel_confianca = "moderado"

        fontes = [
            f"{item['fonte']} ({item['chunk_id']})"
            for item in documentos
        ]
        evidencias.extend(fontes)
        return {
            "acao_proposta": acao,
            "canal_sugerido": canal,
            "justificativa": justificativa,
            "evidencias_utilizadas": evidencias,
            "restricoes_aplicaveis": restricoes,
            "nivel_confianca": nivel_confianca,
            "encaminhamento_humano": {
                "necessario": requer_humano,
                "condicao": encaminhamento,
            },
            "prioridade_operacional": (
                "alta" if requer_humano or saldo_devedor >= 250_000 or dias_atraso > 60
                else "media" if dias_atraso > 30 or probabilidade < 0.35
                else "baixa"
            ),
        }

    def montar_contexto(self, id_cliente: str, pergunta: str) -> dict[str, Any]:
        cliente = consultar_cliente(id_cliente)
        score = self.score_provider(id_cliente)
        historico = buscar_historico_interacoes(id_cliente, limite=8)
        recomendacao = recomendar_acao_basica(id_cliente)
        consulta_rag = (
            f"{pergunta} ação {recomendacao['acao_recomendada']} "
            f"restrições aprovação atraso negociação canal"
        )
        documentos = buscar_documentacao(consulta_rag, top_k=4)
        return {
            "cliente": cliente,
            "score": score,
            "historico": historico,
            "recomendacao": recomendacao,
            "documentos": documentos,
        }

    @staticmethod
    def _perfil(cliente: dict[str, Any]) -> dict[str, Any]:
        dados = cliente["cliente"]
        campos = [
            "setor", "porte", "uf", "tempo_relacionamento_meses",
            "faturamento_mensal_estimado", "saldo_devedor", "dias_atraso",
            "canal_preferencial", "renegociacoes_ult_12m",
        ]
        return {campo: dados.get(campo) for campo in campos}

    @staticmethod
    def _sinais_historico(historico: list[dict[str, Any]]) -> list[str]:
        sinais: list[str] = []
        for item in historico[:5]:
            sinais.append(
                f"{item['data_interacao']} | {item['canal']} | "
                f"{item['resultado']}: {item['texto']}"
            )
        return sinais

    def responder(self, id_cliente: str, pergunta: str) -> dict[str, Any]:
        if not pergunta.strip():
            raise ValueError("A pergunta não pode ser vazia.")
        contexto = self.montar_contexto(id_cliente, pergunta)
        score = contexto["score"]
        recomendacao = contexto["recomendacao"]
        documentos = contexto["documentos"]
        recomendacao_explicavel = self._recomendacao_explicavel(
            contexto["cliente"], score, contexto["historico"], documentos
        )

        resposta = {
            "id_cliente": id_cliente.upper(),
            "pergunta": pergunta,
            "perfil": self._perfil(contexto["cliente"]),
            "previsao": {
                "probabilidade_regularizacao_30d": score["probabilidade_regularizacao_30d"],
                "faixa": score["faixa_probabilidade"],
                "versao_modelo": score["versao_modelo"],
                "fatores": score["principais_fatores"],
                "limitacao": score["calibracao"],
            },
            "sinais_do_historico": self._sinais_historico(contexto["historico"]),
            "estrategia": {
                "acao": recomendacao_explicavel["acao_proposta"],
                "canal": recomendacao_explicavel["canal_sugerido"],
                "justificativa": recomendacao_explicavel["justificativa"],
                "restricoes": recomendacao_explicavel["restricoes_aplicaveis"],
                "requer_aprovacao_humana": recomendacao_explicavel["encaminhamento_humano"]["necessario"],
                "nivel_confianca": recomendacao_explicavel["nivel_confianca"],
                "evidencias_utilizadas": recomendacao_explicavel["evidencias_utilizadas"],
                "encaminhamento_humano": recomendacao_explicavel["encaminhamento_humano"],
                "prioridade_operacional": recomendacao_explicavel["prioridade_operacional"],
            },
            "controles_de_segurança": [
                "Usar somente dados necessários e autorizados; não usar setor, porte ou UF como proxy de atributo sensível.",
                "Tratar score como insumo de priorização, nunca como autorização de oferta ou medida jurídica.",
                "Separar fatos observados, saída do modelo, regra aplicada e sugestão do agente.",
                "Exigir revisão humana para impedimentos, baixa evidência, score não calibrado ou alçada excepcional.",
                "Respeitar consentimento, canal, identidade, janela de contato e pedido de não contato.",
                "Registrar dados consultados, versão do score, regras, fontes e responsável pela aprovação.",
            ],
            "evidencias_documentais": [
                {
                    "fonte": item["fonte"],
                    "chunk_id": item["chunk_id"],
                    "trecho": item["trecho"],
                }
                for item in documentos
            ],
            "disclaimer": (
                "Resposta produzida por baseline determinístico com dados sintéticos. "
                "A recomendação não aprova nem efetiva uma oferta; o score atual não tem calibração validada."
            ),
        }
        if not documentos:
            resposta["estrategia"]["restricoes"].append(
                "Nenhuma evidência documental foi recuperada; encaminhar para análise humana."
            )
            resposta["estrategia"]["requer_aprovacao_humana"] = True
        return resposta


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline local do agente de recuperação PJ")
    parser.add_argument("--cliente", default="PJ0001", help="ID no formato PJ0001")
    parser.add_argument(
        "--pergunta",
        default="Qual estratégia é recomendada e quais evidências sustentam a decisão?",
        help="Pergunta do analista",
    )
    args = parser.parse_args()
    agente = BaselineRecoveryAgent()
    print(json.dumps(agente.responder(args.cliente, args.pergunta), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


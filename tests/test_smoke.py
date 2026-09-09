from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_skeleton import BaselineRecoveryAgent  # noqa: E402
from mock_tools import (  # noqa: E402
    buscar_documentacao,
    buscar_historico_interacoes,
    consultar_cliente,
    consultar_score_regularizacao,
    recomendar_acao_basica,
)


class TestMockTools(unittest.TestCase):
    def test_consulta_cliente_oculta_target_e_leakage(self):
        resultado = consultar_cliente("PJ0001")
        self.assertEqual(resultado["status"], "ok")
        self.assertNotIn("regularizou_30d", resultado["cliente"])
        self.assertNotIn("score_cobranca_atualizado_30d", resultado["cliente"])

    def test_score_esta_no_intervalo(self):
        score = consultar_score_regularizacao("PJ0001")
        self.assertGreaterEqual(score["probabilidade_regularizacao_30d"], 0)
        self.assertLessEqual(score["probabilidade_regularizacao_30d"], 1)
        self.assertTrue(score["principais_fatores"])

    def test_historico_e_documentacao(self):
        historico = buscar_historico_interacoes("PJ0001", limite=3)
        documentos = buscar_documentacao("parcelamento atraso 60 dias", top_k=2)
        self.assertLessEqual(len(historico), 3)
        self.assertTrue(documentos)
        self.assertIn("fonte", documentos[0])

    def test_recomendacao_e_agente(self):
        recomendacao = recomendar_acao_basica("PJ0001")
        resposta = BaselineRecoveryAgent().responder(
            "PJ0001", "Qual estratégia é recomendada e quais são as restrições?"
        )
        self.assertIn("acao_recomendada", recomendacao)
        self.assertIn("previsao", resposta)
        self.assertIn("evidencias_documentais", resposta)
        self.assertIn("nivel_confianca", resposta["estrategia"])
        self.assertIn("evidencias_utilizadas", resposta["estrategia"])
        self.assertIn("encaminhamento_humano", resposta["estrategia"])
        self.assertIn("controles_de_segurança", resposta)

    def test_score_provider_segmentado_pode_ser_injetado(self):
        def score_segmentado(_id_cliente):
            return {
                "probabilidade_regularizacao_30d": 0.91,
                "faixa_probabilidade": "alta",
                "versao_modelo": "lgbm-segmentado-v1",
                "principais_fatores": [],
                "calibracao": "validada",
            }

        resposta = BaselineRecoveryAgent(score_segmentado).responder(
            "PJ0002", "Qual ação deve ser priorizada?"
        )
        self.assertEqual(
            resposta["previsao"]["versao_modelo"],
            "lgbm-segmentado-v1",
        )
        self.assertEqual(resposta["estrategia"]["nivel_confianca"], "alto")

    def test_id_invalido(self):
        with self.assertRaises(ValueError):
            consultar_cliente("cliente-1")


if __name__ == "__main__":
    unittest.main()


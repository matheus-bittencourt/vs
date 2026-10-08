import unittest

from political_analysis import analisar_posicionamento_voto


class AnaliseVotoTests(unittest.TestCase):
    def analisar(
        self,
        *,
        descricao_votacao="",
        objetivo="Se aprovado, o texto reduz a maioridade penal.",
        voto="Sim",
        participacao="Votou",
        proposicao="PL 123/2024",
    ):
        return analisar_posicionamento_voto(
            proposicao=proposicao,
            objetivo=objetivo,
            ementa=objetivo,
            participacao=participacao,
            voto=voto,
            descricao_votacao=descricao_votacao,
        )

    def test_sim_e_favoravel_a_reducao_da_maioridade_penal(self):
        medida, leitura, posicao = self.analisar(
            descricao_votacao="Redução da maioridade penal"
        )

        self.assertEqual(medida, "Redução da maioridade penal")
        self.assertEqual(posicao, "Favorável")
        self.assertIn("Votou Sim", leitura)
        self.assertIn("favorável à medida", leitura)
        self.assertIn("redução da maioridade penal", leitura)

    def test_nao_e_contrario_a_reducao_da_maioridade_penal(self):
        medida, leitura, posicao = self.analisar(
            descricao_votacao="Redução da maioridade penal",
            voto="Não",
        )

        self.assertEqual(medida, "Redução da maioridade penal")
        self.assertEqual(posicao, "Contrário")
        self.assertIn("contrário à medida", leitura)

    def test_verbo_de_acao_no_resumo_tambem_identifica_a_medida(self):
        medida, leitura, posicao = self.analisar(
            descricao_votacao="O texto reduz a idade mínima para aposentadoria."
        )

        self.assertEqual(medida, "Reduz a idade mínima para aposentadoria")
        self.assertEqual(posicao, "Favorável")
        self.assertIn("no item específico informado pela fonte", leitura)

    def test_mencao_sem_direcao_nao_classifica_posicionamento(self):
        medida, leitura, posicao = self.analisar(
            descricao_votacao="Maioridade penal"
        )

        self.assertEqual(medida, "Tema sem regra específica")
        self.assertEqual(posicao, "Não classificado")
        self.assertIn("não explicita uma medida concreta", leitura)

    def test_texto_negado_nao_e_classificado_como_apoio_a_medida(self):
        _, leitura, posicao = self.analisar(
            descricao_votacao="O texto não reduz a maioridade penal."
        )

        self.assertEqual(posicao, "Não classificado")
        self.assertIn("não explicita uma medida concreta", leitura)

    def test_ausencia_nao_e_convertida_em_posicao(self):
        tema, leitura, posicao = analisar_posicionamento_voto(
            "PL 123/2024",
            "Resumo",
            "Ementa",
            "Ausente",
            "Sem voto registrado",
            "Redução da maioridade penal",
        )

        self.assertEqual(tema, "Não classificado")
        self.assertIn("Não há voto nominal", leitura)
        self.assertEqual(posicao, "Não classificado")

if __name__ == "__main__":
    unittest.main()

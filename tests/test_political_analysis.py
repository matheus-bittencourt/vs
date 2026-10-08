from io import BytesIO
import unittest

from csv_validation import ler_csv_limitado
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


class LimitesCsvTests(unittest.TestCase):
    def test_aceita_csv_ate_o_limite_de_linhas(self):
        arquivo = BytesIO(b"coluna\n1\n2\n")

        dados = ler_csv_limitado(arquivo, 2)

        self.assertEqual(len(dados), 2)

    def test_rejeita_csv_acima_do_limite_de_linhas(self):
        arquivo = BytesIO(b"coluna\n1\n2\n")

        with self.assertRaisesRegex(ValueError, "linhas de dados"):
            ler_csv_limitado(arquivo, 1)

    def test_rejeita_csv_acima_do_limite_de_tamanho(self):
        arquivo = BytesIO(b"x" * (5 * 1024 * 1024 + 1))

        with self.assertRaisesRegex(ValueError, "5 MB"):
            ler_csv_limitado(arquivo, 1)


if __name__ == "__main__":
    unittest.main()

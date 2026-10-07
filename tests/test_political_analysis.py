from io import BytesIO
import unittest

from csv_validation import ler_csv_limitado
from political_analysis import analisar_posicionamento_voto


class AnaliseVotoTests(unittest.TestCase):
    def analisar(self, *, descricao_votacao="", voto="Sim", proposicao="PEC 6/2019"):
        return analisar_posicionamento_voto(
            proposicao=proposicao,
            objetivo="Se aprovado, a proposta muda regras previdenciárias.",
            ementa="A proposta altera o sistema de previdência social.",
            participacao="Votou",
            voto=voto,
            descricao_votacao=descricao_votacao,
        )

    def test_pec6_item_de_idade_nao_inventa_sentido_do_destaque(self):
        tema, leitura = self.analisar(descricao_votacao="Idade mínima para mulheres")

        self.assertEqual(tema, "Previdência — idade mínima para mulheres")
        self.assertIn("de 60 para 62 anos", leitura)
        self.assertIn("não esclarece se o item votado", leitura)
        self.assertNotIn("Apoiou a proposta", leitura)

    def test_mesma_pec_em_item_distinto_nao_herda_tema_da_proposta(self):
        tema, leitura = self.analisar(
            descricao_votacao="Supressão da expressão no âmbito da União"
        )

        self.assertEqual(tema, "Tema sem regra específica")
        self.assertIn("Supressão da expressão", leitura)
        self.assertNotIn("idade mínima", leitura)

    def test_sem_descricao_especifica_nao_classifica_pec_inteira(self):
        tema, leitura = self.analisar()

        self.assertEqual(tema, "Tema sem regra específica")
        self.assertIn("item específico não foi descrito separadamente", leitura)

    def test_leitura_usa_sentido_registrado_sem_atribuir_motivacao(self):
        _, leitura_sim = self.analisar(
            proposicao="PL 123/2024",
            descricao_votacao="Amplia o acesso à educação",
            voto="Sim",
        )
        _, leitura_nao = self.analisar(
            proposicao="PL 123/2024",
            descricao_votacao="Amplia o acesso à educação",
            voto="Não",
        )

        self.assertIn("Votou Sim", leitura_sim)
        self.assertIn("Votou Não", leitura_nao)
        self.assertNotIn("intenção pessoal", leitura_sim)

    def test_ausencia_nao_e_convertida_em_posicao(self):
        tema, leitura = analisar_posicionamento_voto(
            "PEC 6/2019",
            "Resumo",
            "Ementa",
            "Ausente",
            "Sem voto registrado",
            "Idade mínima para mulheres",
        )

        self.assertEqual(tema, "Não classificado")
        self.assertIn("Não há voto nominal", leitura)


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

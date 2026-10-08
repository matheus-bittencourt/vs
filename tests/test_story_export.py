import unittest
from io import BytesIO

from PIL import Image

from story_export import STORY_HEIGHT, STORY_WIDTH, criar_imagem_story


class StoryExportTests(unittest.TestCase):
    def test_cria_png_vertical_com_todos_os_indicadores(self):
        indicadores = [
            ("Crescimento médio do PIB (ao ano)", "3,4%", "1,9%"),
            ("IPCA acumulado no período", "45,6%", "25,1%"),
            ("Desocupação média anual", "N/D", "10,5%"),
            ("Desocupação no último ano disponível", "N/D", "9,3%"),
            ("Rendimento real mensal (último dado)", "N/D", "R$ 2.659"),
            ("Famílias atendidas em transferência de renda", "12,8 mi", "21,6 mi"),
            ("IED médio anual", "US$ 27,0 bi", "US$ 57,0 bi"),
            ("Resultado primário médio (% do PIB)", "3,2%", "-4,3%"),
        ]

        conteudo = criar_imagem_story(
            "Lula 2003–2010",
            "Bolsonaro 2019–2022",
            indicadores,
        )

        with Image.open(BytesIO(conteudo)) as imagem:
            self.assertEqual(imagem.format, "PNG")
            self.assertEqual(imagem.size, (STORY_WIDTH, STORY_HEIGHT))

    def test_rejeita_quantidade_incorreta_de_indicadores(self):
        with self.assertRaisesRegex(ValueError, "oito indicadores"):
            criar_imagem_story("Período A", "Período B", [])


if __name__ == "__main__":
    unittest.main()

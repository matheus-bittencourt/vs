import json
import unittest
from io import BytesIO
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from idea_submission import (
    GITHUB_OWNER,
    GITHUB_REPOSITORY,
    IdeaSubmissionError,
    create_idea_issue,
)


class CreateIdeaIssueTests(unittest.TestCase):
    @patch("idea_submission.urlopen")
    def test_cria_issue_publica_com_conteudo_e_token(self, urlopen):
        resposta = Mock()
        resposta.read.return_value = json.dumps(
            {
                "number": 42,
                "html_url": (
                    f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPOSITORY}/issues/42"
                ),
            }
        ).encode()
        urlopen.return_value.__enter__.return_value = resposta

        numero, url = create_idea_issue(
            "  Incluir dados sobre educação e saúde.  ", "token-secreto"
        )

        self.assertEqual(numero, 42)
        self.assertTrue(url.endswith("/issues/42"))
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPOSITORY}/issues",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer token-secreto")
        payload = json.loads(request.data.decode())
        self.assertIn("educação", payload["title"])
        self.assertIn("educação e saúde", payload["body"])

    def test_rejeita_ideia_curta(self):
        with self.assertRaisesRegex(ValueError, "pelo menos 10"):
            create_idea_issue("curta", "token")

    def test_rejeita_ideia_acima_do_limite(self):
        with self.assertRaisesRegex(ValueError, "no máximo"):
            create_idea_issue("a" * 10_001, "token")

    def test_rejeita_token_vazio_sem_chamar_github(self):
        with patch("idea_submission.urlopen") as urlopen:
            with self.assertRaisesRegex(ValueError, "não está configurada"):
                create_idea_issue("Uma ideia válida para o painel", " ")
        urlopen.assert_not_called()

    @patch("idea_submission.urlopen")
    def test_explica_recusa_da_api_sem_expor_detalhes_da_resposta(self, urlopen):
        urlopen.side_effect = HTTPError(
            "https://api.github.com", 403, "Forbidden", {}, BytesIO(b"secret response")
        )

        with self.assertRaisesRegex(IdeaSubmissionError, "HTTP 403") as erro:
            create_idea_issue("Uma ideia válida para o painel", "token")

        self.assertNotIn("secret response", str(erro.exception))

    @patch("idea_submission.urlopen")
    def test_informa_falha_de_conexao(self, urlopen):
        urlopen.side_effect = URLError("offline")

        with self.assertRaisesRegex(IdeaSubmissionError, "offline"):
            create_idea_issue("Uma ideia válida para o painel", "token")

    @patch("idea_submission.urlopen")
    def test_rejeita_resposta_sem_url_de_issue_do_repositorio(self, urlopen):
        resposta = Mock()
        resposta.read.return_value = json.dumps(
            {"number": 42, "html_url": "https://example.com/issue/42"}
        ).encode()
        urlopen.return_value.__enter__.return_value = resposta

        with self.assertRaisesRegex(IdeaSubmissionError, "endereço válido"):
            create_idea_issue("Uma ideia válida para o painel", "token")


if __name__ == "__main__":
    unittest.main()

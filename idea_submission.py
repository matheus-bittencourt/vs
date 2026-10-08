"""Public GitHub issue submissions for dashboard improvement ideas."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GITHUB_OWNER = "matheus-bittencourt"
GITHUB_REPOSITORY = "vs"
MAX_IDEA_LENGTH = 10_000


class IdeaSubmissionError(Exception):
    """Raised when an idea cannot be submitted to GitHub."""


def create_idea_issue(text: str, token: str) -> tuple[int, str]:
    """Create a public issue with a user's idea and return its number and URL."""
    idea = text.strip()
    if len(idea) < 10:
        raise ValueError("Descreva a ideia com pelo menos 10 caracteres.")
    if len(idea) > MAX_IDEA_LENGTH:
        raise ValueError(f"A ideia deve ter no máximo {MAX_IDEA_LENGTH:,} caracteres.")
    if not token.strip():
        raise ValueError("A integração com o GitHub não está configurada.")

    titulo_base = next((linha.strip() for linha in idea.splitlines() if linha.strip()), "")
    titulo_base = " ".join(titulo_base.split())
    if len(titulo_base) > 70:
        titulo_base = titulo_base[:67].rsplit(" ", 1)[0] + "..."

    payload = {
        "title": f"Sugestão da comunidade: {titulo_base}",
        "body": (
            "Sugestão enviada pelo formulário público do painel:\n\n"
            f"{idea}\n\n"
            "---\n"
            "Esta issue foi criada automaticamente para avaliação. "
            "O texto é público e pode ser editado pela equipe do repositório."
        ),
    }
    request = Request(
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPOSITORY}/issues",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "BrasilEmPerspectiva-IdeaForm",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise IdeaSubmissionError(
            f"O GitHub recusou a criação da issue (HTTP {error.code})."
        ) from error
    except URLError as error:
        raise IdeaSubmissionError(
            f"Não foi possível conectar ao GitHub: {error.reason}."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise IdeaSubmissionError(
            "O GitHub retornou uma resposta inválida ao criar a issue."
        ) from error

    numero = result.get("number")
    url = result.get("html_url")
    url_esperada = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPOSITORY}/issues/"
    if not isinstance(numero, int) or not isinstance(url, str) or not url.startswith(url_esperada):
        raise IdeaSubmissionError(
            "O GitHub não confirmou a issue com um endereço válido."
        )
    return numero, url

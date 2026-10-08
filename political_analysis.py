"""Leitura factual de posicionamentos em votações nominais."""

import re
import unicodedata


_ACOES = {
    "redução": (
        r"redução|reduzir|reduz(?:e|iu)?|diminuição|diminuir|"
        r"diminui(?:u)?|rebaixamento|rebaixar|baixa(?:r)?|corte|cortar"
    ),
    "aumento": (
        r"aumento|aumentar|aumenta(?:r)?|elevação|elevar|eleva(?:r)?|"
        r"ampliação|ampliar|amplia(?:r)?|expansão|expandir|expande"
    ),
    "criação": (
        r"criação|criar|cria(?:r)?|instituição|instituir|institui|"
        r"implantação|implantar|implanta"
    ),
    "privatização": r"privatização|privatizar|privatiza(?:r)?",
    "proibição": r"proibição|proibir|proíbe|vedação|vedar|veda",
    "autorização": (
        r"autorização|autorizar|autoriza|permissão|permitir|permite"
    ),
    "suspensão": r"suspensão|suspender|suspende",
    "extinção": r"extinção|extinguir|extingue|revogação|revogar|revoga",
}


def _remover_acentos(s: str) -> str:
    """Replace accented characters with their ASCII base, preserving length/positions."""
    if not s:
        return ""
    normalized = unicodedata.normalize("NFKD", s)
    return "".join(c for c in normalized if not unicodedata.combining(c))

# Build a pattern using accentless forms so matching works regardless of source encoding
acao_source = "|".join(_ACOES.values())
acao_source_norm = _remover_acentos(acao_source)
_PADRAO_MEDIDA = re.compile(
    r"(?P<acao>" + acao_source_norm + r")\s+"
    r"(?:(?:gradualmente|temporariamente|progressivamente)\s+)?"
    r"(?P<alvo>(?:(?:da|do|de|das|dos|a|o|as|os)\s+)?[^.;!?\n]+)",
    re.IGNORECASE,
)

# Normalized negation words (accentless)
_PADRAO_NEGACAO = re.compile(r"\b(?:nao|rejeita|rejeicao|contra|retira|suprime|exclui|impede|revoga|cancela)\b", re.IGNORECASE)


def _texto_util(valor: str) -> str:
    texto = re.sub(r"\s+", " ", str(valor or "")).strip()
    return "" if texto.casefold() in {"nan", "none", "<na>"} else texto


def _extrair_medida(texto: str) -> str | None:
    # Use an accentless normalized version for reliable matching, but map spans back to
    # the original text so captured fragments preserve accents and original wording.
    texto_norm = _remover_acentos(texto).lower()
    for correspondencia in _PADRAO_MEDIDA.finditer(texto_norm):
        inicio_clausula = max(
            texto.rfind(marcador, 0, correspondencia.start())
            for marcador in (".", ";", "!", "?", "\n")
        ) + 1
        contexto_anterior_norm = texto_norm[inicio_clausula : correspondencia.start()]
        if _PADRAO_NEGACAO.search(contexto_anterior_norm):
            continue

        acao_span = correspondencia.span("acao")
        alvo_span = correspondencia.span("alvo")
        acao_original = texto[acao_span[0] : acao_span[1]].strip()
        alvo_original = re.split(
            r"\s+(?:e|mas|porém|contudo|que)\s+|,\s*",
            texto[alvo_span[0] : alvo_span[1]],
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" ,:-")

        medida = f"{acao_original} {alvo_original}".strip()
        if not alvo_original or len(medida) > 180:
            continue
        return medida[0].upper() + medida[1:]
    return None


def analisar_posicionamento_voto(
    proposicao: str,
    objetivo: str,
    ementa: str,
    participacao: str,
    voto: str,
    descricao_votacao: str = "",
) -> tuple[str, str, str]:
    """Relaciona Sim/Não à medida descrita, sem atribuir motivos ou efeitos."""
    if participacao != "Votou":
        return (
            "Não classificado",
            "Não há voto nominal individual para interpretar.",
            "Não classificado",
        )
    if voto == "Abstenção":
        return (
            "Não classificado",
            "Absteve-se; não registrou voto Sim ou Não sobre a medida.",
            "Não classificado",
        )
    if voto == "Obstrução":
        return (
            "Não classificado",
            "Registrou obstrução; isso não equivale a voto Sim ou Não sobre a medida.",
            "Não classificado",
        )
    if voto not in {"Sim", "Não"}:
        return (
            "Não classificado",
            "O sentido do voto nominal não está disponível para esta leitura.",
            "Não classificado",
        )

    detalhe = _texto_util(descricao_votacao)
    resumo = _texto_util(objetivo)
    ementa_limpa = _texto_util(ementa)
    if detalhe:
        texto_base = detalhe
        origem = "no item específico informado pela fonte"
    elif resumo:
        texto_base = resumo
        origem = "no resumo disponível da proposta"
    else:
        texto_base = ementa_limpa
        origem = "na ementa oficial da proposta"

    medida = _extrair_medida(texto_base)
    if medida:
        descricao_medida = medida
        posicao = "Favorável" if voto == "Sim" else "Contrário"
        leitura = (
            f"Votou {voto}; portanto, posicionamento {posicao.lower()} à medida "
            f"descrita {origem}: “{descricao_medida}”. ({descricao_medida.lower()})"
        )
        if not detalhe:
            leitura += (
                " A fonte não identifica separadamente eventual emenda ou destaque; "
                "a leitura se limita à medida descrita para a proposta."
            )
        return descricao_medida, leitura, posicao

    texto_item = texto_base or _texto_util(proposicao)
    if len(texto_item) > 420:
        texto_item = texto_item[:417].rsplit(" ", 1)[0] + "..."
    descricao_item = f"“{texto_item}”" if texto_item else "item sem descrição disponível"
    leitura = (
        f"Votou {voto} no {origem} descrito como {descricao_item}. "
        "O texto identifica o assunto, mas não explicita uma medida concreta cuja "
        "direção permita classificar este voto como favorável ou contrário."
    )
    return "Tema sem regra específica", leitura, "Não classificado"

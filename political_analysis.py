"""Leituras descritivas de votações, sem atribuir motivação aos parlamentares."""

import re


def analisar_posicionamento_voto(
    proposicao: str,
    objetivo: str,
    ementa: str,
    participacao: str,
    voto: str,
    descricao_votacao: str = "",
) -> tuple[str, str]:
    """Relaciona o voto ao item registrado pela fonte, sem inferir sua intenção."""
    if participacao != "Votou":
        return "Não classificado", "Não há voto nominal individual para interpretar."
    if voto == "Abstenção":
        return "Não classificado", "Absteve-se; isso não indica apoio nem oposição ao texto."
    if voto == "Obstrução":
        return "Não classificado", "Registrou obstrução; não classifico como voto Sim ou Não."
    if voto not in {"Sim", "Não"}:
        return "Não classificado", "O sentido do voto não está disponível para esta leitura."

    detalhe = re.sub(r"\s+", " ", descricao_votacao).strip()
    if detalhe.casefold() in {"nan", "none", "<na>"}:
        detalhe = ""

    texto_proposicao = proposicao.casefold()
    idade_minima_mulheres = bool(
        re.search(r"\bpec\s*6\s*/\s*2019\b", texto_proposicao)
        and re.search(r"\bidade mínima\b.*\bmulheres\b|\bmulheres\b.*\bidade mínima\b", detalhe, re.I)
    )
    if idade_minima_mulheres:
        contexto_pec = (
            "A proposta original da PEC previa elevar gradualmente de 60 para 62 anos "
            "a idade mínima das mulheres na aposentadoria urbana do INSS. A descrição "
            "desta votação, porém, identifica apenas o tema; ela não esclarece se o item "
            "votado aprovava, rejeitava ou destacava essa mudança."
        )
        return (
            "Previdência — idade mínima para mulheres",
            f"Votou {voto} em um item descrito como “{detalhe}”. {contexto_pec}",
        )

    item = detalhe or ementa or objetivo
    item = re.sub(r"\s+", " ", str(item)).strip()
    if item.casefold() in {"nan", "none", "<na>"}:
        item = ""
    if len(item) > 420:
        item = item[:417].rsplit(" ", 1)[0] + "..."
    descricao_item = (
        f"“{item}”"
        if item
        else "um item cuja descrição não está disponível"
    )
    origem = (
        "descrição oficial da votação"
        if detalhe
        else "ementa geral da matéria; o item específico não foi descrito separadamente"
    )
    leitura = (
        f"Votou {voto} no item registrado como {descricao_item}. "
        f"A informação vem da {origem}; sem o texto específico do item, não é possível "
        "afirmar qual mudança prática esse voto apoiava ou rejeitava."
    )
    return "Tema sem regra específica", leitura

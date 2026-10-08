"""Geração de cartões comparativos verticais para Instagram Stories."""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont


STORY_WIDTH = 1080
STORY_HEIGHT = 1920

_FUNDO = "#F3F5F8"
_TEXTO = "#182230"
_SECUNDARIO = "#475467"
_VERMELHO = "#B42332"
_AZUL = "#234E70"
_BRANCO = "#FFFFFF"
_CARACTERES_NECESSARIOS = "áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ–—-"


@lru_cache(maxsize=2)
def _caminhos_fontes(negrito: bool) -> tuple[Path, ...]:
    nomes = (
        (
            r"C:\Windows\Fonts\arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        )
        if negrito
        else (
            r"C:\Windows\Fonts\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        )
    )
    caminhos = [Path(nome) for nome in nomes]
    raizes_fontes = (
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".local" / "share" / "fonts",
        Path.home() / ".fonts",
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
    )
    familias = ("arial", "dejavusans", "liberationsans", "notosans", "freesans")
    fontes_encontradas = [
        caminho
        for raiz in raizes_fontes
        if raiz.is_dir()
        for caminho in raiz.rglob("*")
        if caminho.suffix.lower() in {".ttf", ".otf"}
        and any(familia in caminho.stem.lower().replace(" ", "") for familia in familias)
    ]
    caminhos.extend(
        sorted(
            fontes_encontradas,
            key=lambda caminho: (
                familias.index(
                    next(
                        familia
                        for familia in familias
                        if familia in caminho.stem.lower().replace(" ", "")
                    )
                ),
                0 if ("bold" in caminho.stem.lower() or "bd" in caminho.stem.lower()) == negrito else 1,
            ),
        )
    )
    return tuple(dict.fromkeys(caminhos))


def _fonte_tem_glifos(fonte: ImageFont.FreeTypeFont) -> bool:
    mascara_ausente = fonte.getmask("\U0010ffff")
    glifo_ausente = Image.frombytes(
        "L",
        mascara_ausente.size,
        bytes(mascara_ausente),
    )
    for caractere in _CARACTERES_NECESSARIOS:
        mascara = fonte.getmask(caractere)
        glifo = Image.frombytes("L", mascara.size, bytes(mascara))
        if not mascara.getbbox() or glifo == glifo_ausente:
            return False
    return True


def _fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    for caminho in _caminhos_fontes(negrito):
        try:
            fonte = ImageFont.truetype(str(caminho), tamanho)
        except OSError:
            continue
        if _fonte_tem_glifos(fonte):
            return fonte

    raise RuntimeError(
        "Não foi encontrada uma fonte TrueType com suporte a acentos, cedilha e hífens "
        "para gerar a imagem. Instale Arial, DejaVu Sans, Liberation Sans, Noto Sans "
        "ou FreeSans no sistema."
    )


def _quebrar_linhas(
    desenho: ImageDraw.ImageDraw,
    texto: str,
    fonte: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    largura: int,
) -> list[str]:
    linhas: list[str] = []
    linha = ""
    for palavra in texto.split():
        candidata = f"{linha} {palavra}".strip()
        if linha and desenho.textbbox((0, 0), candidata, font=fonte)[2] > largura:
            linhas.append(linha)
            linha = palavra
        else:
            linha = candidata
    if linha:
        linhas.append(linha)
    return linhas


def _texto_ajustado(
    desenho: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    texto: str,
    fonte: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    largura: int,
    preenchimento: str,
    espacamento: int = 5,
) -> int:
    x, y = xy
    linhas = _quebrar_linhas(desenho, texto, fonte, largura)
    caixa = desenho.textbbox((0, 0), "Ag", font=fonte)
    altura_linha = caixa[3] - caixa[1] + espacamento
    for linha in linhas:
        desenho.text((x, y), linha, font=fonte, fill=preenchimento)
        y += altura_linha
    return y


def criar_imagem_story(
    periodo_a: str,
    periodo_b: str,
    indicadores: list[tuple[str, str, str]],
) -> bytes:
    """Renderiza as métricas comparativas como PNG vertical de 1080 × 1920."""
    if len(indicadores) != 8:
        raise ValueError("O Story comparativo precisa conter exatamente oito indicadores.")

    imagem = Image.new("RGB", (STORY_WIDTH, STORY_HEIGHT), _FUNDO)
    desenho = ImageDraw.Draw(imagem)
    fonte_marca = _fonte(25, negrito=True)
    fonte_titulo = _fonte(54, negrito=True)
    fonte_subtitulo = _fonte(26)
    fonte_periodo = _fonte(27, negrito=True)
    fonte_rotulo = _fonte(22, negrito=True)
    fonte_valor = _fonte(25, negrito=True)
    fonte_rodape = _fonte(20)

    desenho.rectangle((0, 0, STORY_WIDTH, 300), fill="#101828")
    desenho.text((64, 55), "BRASIL EM PERSPECTIVA", font=fonte_marca, fill="#F2B8BE")
    desenho.text((64, 100), "Comparativo de", font=fonte_titulo, fill=_BRANCO)
    desenho.text((64, 160), "indicadores", font=fonte_titulo, fill=_BRANCO)
    desenho.text(
        (67, 244),
        "Dados por período — leitura descritiva, não causal",
        font=fonte_subtitulo,
        fill="#D0D5DD",
    )

    margem = 64
    espacamento_coluna = 24
    largura_coluna = (STORY_WIDTH - 2 * margem - espacamento_coluna) // 2
    topo_cartoes = 330
    altura_cartao = 185
    for indice, (periodo, cor) in enumerate(
        ((periodo_a, _VERMELHO), (periodo_b, _AZUL))
    ):
        x = margem + indice * (largura_coluna + espacamento_coluna)
        desenho.rounded_rectangle(
            (x, topo_cartoes, x + largura_coluna, topo_cartoes + altura_cartao),
            radius=22,
            fill=_BRANCO,
        )
        desenho.rounded_rectangle(
            (x, topo_cartoes, x + 12, topo_cartoes + altura_cartao),
            radius=6,
            fill=cor,
        )
        _texto_ajustado(
            desenho,
            (x + 28, topo_cartoes + 28),
            periodo,
            fonte_periodo,
            largura_coluna - 55,
            _TEXTO,
            espacamento=7,
        )

    topo_linhas = 545
    altura_linha = 119
    largura_valor = 435
    for indice, (rotulo, valor_a, valor_b) in enumerate(indicadores):
        y = topo_linhas + indice * altura_linha
        desenho.rounded_rectangle(
            (margem, y, STORY_WIDTH - margem, y + altura_linha - 10),
            radius=18,
            fill=_BRANCO,
        )
        _texto_ajustado(
            desenho,
            (margem + 22, y + 12),
            rotulo,
            fonte_rotulo,
            STORY_WIDTH - 2 * margem - 44,
            _SECUNDARIO,
            espacamento=2,
        )
        y_valor = y + 59
        for coluna, (valor, cor) in enumerate(
            ((valor_a, _VERMELHO), (valor_b, _AZUL))
        ):
            x = margem + coluna * (largura_valor + 18)
            desenho.rounded_rectangle(
                (x, y_valor, x + largura_valor, y_valor + 42),
                radius=12,
                fill="#F2F4F7",
            )
            valor_fonte = fonte_valor
            if desenho.textbbox((0, 0), valor, font=valor_fonte)[2] > largura_valor - 28:
                valor_fonte = _fonte(21, negrito=True)
            desenho.text(
                (x + 14, y_valor + 7),
                valor,
                font=valor_fonte,
                fill=cor if valor != "N/D" else _SECUNDARIO,
            )

    y_rodape = topo_linhas + len(indicadores) * altura_linha + 10
    desenho.text(
        (margem, y_rodape),
        "COMO LER",
        font=fonte_marca,
        fill=_TEXTO,
    )
    notas = (
        "N/D indica série indisponível na base para o período. Renda e transferências "
        "são os últimos valores disponíveis; programas e coberturas podem diferir.",
        "Comparações dependem dos anos e dos dados disponíveis. Choques externos, "
        "revisões metodológicas e diferenças entre políticas impedem atribuir "
        "resultados apenas ao governo.",
        "Base aproximada e arredondada. Confira fontes e metodologia no painel antes "
        "de reutilizar os dados.",
    )
    y_rodape += 42
    for nota in notas:
        y_rodape = _texto_ajustado(
            desenho,
            (margem, y_rodape),
            nota,
            fonte_rodape,
            STORY_WIDTH - 2 * margem,
            _SECUNDARIO,
            espacamento=5,
        )
        y_rodape += 9

    buffer = BytesIO()
    imagem.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()

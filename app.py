"""Dashboard exploratório para comparação de indicadores políticos e econômicos."""

from __future__ import annotations

import json
import math
import re
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import streamlit as st

from csv_validation import ler_csv_limitado
from political_analysis import analisar_posicionamento_voto


st.set_page_config(
    page_title="Brasil: comparação de governos e propostas",
    page_icon="📊",
    layout="wide",
)

CORES = {
    "Lula / PT": "#B42332",
    "Bolsonaro / Flávio": "#234E70",
    "Contexto PT (Dilma)": "#D97706",
}

# Séries anuais arredondadas para apresentação. Na ausência de CSV externo,
# esta base embarcada mantém o dashboard utilizável e declara suas lacunas.
DADOS_BASE = [
    {"ano": 2003, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": 1.1, "ipca": 9.30, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 10.1, "resultado_primario_pct_pib": 3.2},
    {"ano": 2004, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": 5.8, "ipca": 7.60, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 18.2, "resultado_primario_pct_pib": 3.7},
    {"ano": 2005, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": 3.2, "ipca": 5.69, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 15.1, "resultado_primario_pct_pib": 3.8},
    {"ano": 2006, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": 4.0, "ipca": 3.14, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 18.8, "resultado_primario_pct_pib": 3.2},
    {"ano": 2007, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": 6.1, "ipca": 4.46, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 34.6, "resultado_primario_pct_pib": 3.3},
    {"ano": 2008, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": 5.1, "ipca": 5.90, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 45.1, "resultado_primario_pct_pib": 3.4},
    {"ano": 2009, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": -0.1, "ipca": 4.31, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 25.9, "resultado_primario_pct_pib": 2.0},
    {"ano": 2010, "periodo": "Lula I e II", "grupo": "Lula / PT", "pib": 7.5, "ipca": 5.91, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": 12.8, "ied_usd_bilhoes": 48.5, "resultado_primario_pct_pib": 2.8},
    {"ano": 2011, "periodo": "Dilma I e II (contexto PT)", "grupo": "Contexto PT (Dilma)", "pib": 4.0, "ipca": 6.50, "desemprego": None, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 66.7, "resultado_primario_pct_pib": 3.1},
    {"ano": 2012, "periodo": "Dilma I e II (contexto PT)", "grupo": "Contexto PT (Dilma)", "pib": 1.9, "ipca": 5.84, "desemprego": 7.4, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 65.3, "resultado_primario_pct_pib": 2.2},
    {"ano": 2013, "periodo": "Dilma I e II (contexto PT)", "grupo": "Contexto PT (Dilma)", "pib": 3.0, "ipca": 5.91, "desemprego": 7.1, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 63.9, "resultado_primario_pct_pib": 1.7},
    {"ano": 2014, "periodo": "Dilma I e II (contexto PT)", "grupo": "Contexto PT (Dilma)", "pib": 0.5, "ipca": 6.41, "desemprego": 6.8, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 67.1, "resultado_primario_pct_pib": -0.6},
    {"ano": 2015, "periodo": "Dilma I e II (contexto PT)", "grupo": "Contexto PT (Dilma)", "pib": -3.5, "ipca": 10.67, "desemprego": 8.5, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 61.6, "resultado_primario_pct_pib": -1.9},
    {"ano": 2016, "periodo": "Dilma I e II (contexto PT)", "grupo": "Contexto PT (Dilma)", "pib": -3.3, "ipca": 6.29, "desemprego": 11.5, "renda_real_brl": None, "transferencias_milhoes": 13.6, "ied_usd_bilhoes": 74.7, "resultado_primario_pct_pib": -2.5},
    {"ano": 2019, "periodo": "Bolsonaro", "grupo": "Bolsonaro / Flávio", "pib": 1.2, "ipca": 4.31, "desemprego": 11.8, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 69.2, "resultado_primario_pct_pib": -0.8},
    {"ano": 2020, "periodo": "Bolsonaro", "grupo": "Bolsonaro / Flávio", "pib": -3.3, "ipca": 4.52, "desemprego": 13.7, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 37.8, "resultado_primario_pct_pib": -9.4},
    {"ano": 2021, "periodo": "Bolsonaro", "grupo": "Bolsonaro / Flávio", "pib": 4.8, "ipca": 10.06, "desemprego": 14.0, "renda_real_brl": None, "transferencias_milhoes": None, "ied_usd_bilhoes": 46.4, "resultado_primario_pct_pib": 0.7},
    {"ano": 2022, "periodo": "Bolsonaro", "grupo": "Bolsonaro / Flávio", "pib": 3.0, "ipca": 5.79, "desemprego": 9.3, "renda_real_brl": 2659, "transferencias_milhoes": 21.6, "ied_usd_bilhoes": 74.6, "resultado_primario_pct_pib": 1.3},
    {"ano": 2023, "periodo": "Lula III", "grupo": "Lula / PT", "pib": 3.2, "ipca": 4.62, "desemprego": 7.8, "renda_real_brl": 3032, "transferencias_milhoes": None, "ied_usd_bilhoes": 64.2, "resultado_primario_pct_pib": -2.3},
    {"ano": 2024, "periodo": "Lula III", "grupo": "Lula / PT", "pib": 3.4, "ipca": 4.83, "desemprego": 6.6, "renda_real_brl": 3225, "transferencias_milhoes": 20.8, "ied_usd_bilhoes": 71.1, "resultado_primario_pct_pib": -0.4},
]

COLUNAS_CSV = [
    "ano",
    "periodo",
    "grupo",
    "pib",
    "ipca",
    "desemprego",
    "renda_real_brl",
    "transferencias_milhoes",
    "ied_usd_bilhoes",
    "resultado_primario_pct_pib",
]

EIXOS = {
    "Economia": [
        ("pib", "Variação anual do PIB (%)"),
        ("ipca", "IPCA anual (%)"),
        ("resultado_primario_pct_pib", "Resultado primário (% do PIB)"),
        ("ied_usd_bilhoes", "IED (US$ bilhões)"),
    ],
    "Social & Redução de Pobreza": [
        ("desemprego", "Desocupação média anual (%)"),
        ("renda_real_brl", "Rendimento real habitual (R$ por mês)"),
        ("transferencias_milhoes", "Famílias atendidas (milhões)"),
    ],
    "Infraestrutura & Privatizações": [],
    "Geopolítica & Relações Internacionais": [],
    "Meio Ambiente/Clima": [],
}

PERIODOS = {
    "Lula 2003–2010": ("Lula I e II",),
    "Governo Dilma 2011–2016 (contexto PT)": ("Dilma I e II (contexto PT)",),
    "Bolsonaro 2019–2022": ("Bolsonaro",),
    "Lula 2023–2024 (parcial)": ("Lula III",),
}

COLUNAS_PROPOSTAS = [
    "bloco",
    "proposta",
    "ano",
    "iniciativa",
    "autor_iniciativa",
    "status",
    "aprovada",
    "fonte_url",
]

COLUNAS_VOTOS = [
    "agente",
    "casa",
    "cargo",
    "data",
    "sessao",
    "id_votacao",
    "proposicao",
    "objetivo_impacto",
    "participacao",
    "voto",
    "fonte_url",
]

VOTOS_POSSIVEIS = {"Sim", "Não", "Abstenção", "Obstrução", "Sem voto registrado"}
PARTICIPACOES_POSSIVEIS = {
    "Votou",
    "Presente, sem voto nominal",
    "Ausente",
    "Licença registrada",
    "Em missão oficial",
    "Atividade parlamentar registrada; sem voto nominal",
    "Presidiu a sessão",
    "Participou de votação secreta",
    "Sem informação",
}

SENADO_CODIGO_FLAVIO = 5894

# Exemplos legislativos verificáveis, não um inventário completo de promessas
# eleitorais ou de toda a produção legislativa de cada agente.
PROPOSTAS_BASE = [
    {
        "bloco": "Lula / PT",
        "proposta": "Novo regime fiscal sustentável (PLP 93/2023)",
        "ano": 2023,
        "iniciativa": "PLP",
        "autor_iniciativa": "Poder Executivo federal — Lula III",
        "status": "Aprovado; convertido na LC 200/2023",
        "aprovada": True,
        "fonte_url": "https://www.camara.leg.br/propostas-legislativas/2357053",
    },
    {
        "bloco": "Lula / PT",
        "proposta": "Retomada do Programa Bolsa Família (MP 1.164/2023)",
        "ano": 2023,
        "iniciativa": "Medida Provisória",
        "autor_iniciativa": "Poder Executivo federal — Lula III",
        "status": "Aprovada; convertida na Lei 14.601/2023",
        "aprovada": True,
        "fonte_url": "https://www.camara.leg.br/busca-portal/proposicoes/?q=MPV%201164%2F2023",
    },
]


def ler_csv_upload(arquivo: Any) -> pd.DataFrame:
    """Lê e valida CSV no esquema documentado no painel."""
    dados = ler_csv_limitado(arquivo, 50_000)
    faltantes = sorted(set(COLUNAS_CSV) - set(dados.columns))
    if faltantes:
        raise ValueError(f"Colunas ausentes no CSV: {', '.join(faltantes)}.")
    dados = dados[COLUNAS_CSV].copy()
    for coluna in COLUNAS_CSV:
        if coluna not in ("periodo", "grupo"):
            originais = dados[coluna]
            dados[coluna] = pd.to_numeric(originais, errors="coerce")
            invalidos = originais.notna() & dados[coluna].isna()
            if invalidos.any():
                raise ValueError(f"A coluna '{coluna}' contém valores que não são numéricos.")
    if dados["ano"].isna().any():
        raise ValueError("A coluna 'ano' não pode conter valores vazios.")
    grupos_validos = set(CORES)
    grupos_invalidos = sorted(set(dados["grupo"].dropna()) - grupos_validos)
    if grupos_invalidos:
        raise ValueError(
            "Valores de 'grupo' não reconhecidos: "
            f"{', '.join(map(str, grupos_invalidos))}. Use: {', '.join(grupos_validos)}."
        )
    return dados.sort_values("ano")


def ler_csv_propostas(arquivo: Any) -> pd.DataFrame:
    """Valida catálogo de propostas fornecido pelo usuário."""
    propostas = ler_csv_limitado(arquivo, 10_000)
    faltantes = sorted(set(COLUNAS_PROPOSTAS) - set(propostas.columns))
    if faltantes:
        raise ValueError(f"Colunas ausentes: {', '.join(faltantes)}.")

    propostas = propostas[COLUNAS_PROPOSTAS].copy()
    propostas["ano"] = pd.to_numeric(propostas["ano"], errors="coerce")
    if propostas["ano"].isna().any():
        raise ValueError("A coluna 'ano' precisa conter anos numéricos.")
    if propostas.isna().any().any():
        raise ValueError("O CSV de propostas não pode conter campos vazios.")

    bloco_validos = {"Lula / PT", "Flávio Bolsonaro"}
    invalidos = sorted(set(propostas["bloco"].dropna()) - bloco_validos)
    if invalidos:
        raise ValueError(
            f"Bloco(s) não reconhecido(s): {', '.join(invalidos)}. "
            f"Use: {', '.join(sorted(bloco_validos))}."
        )

    def normalizar_aprovada(valor: Any) -> bool:
        if isinstance(valor, bool):
            return valor
        texto = str(valor).strip().casefold()
        if texto in {"true", "1", "sim", "aprovada", "aprovado"}:
            return True
        if texto in {"false", "0", "não", "nao", "rejeitada", "rejeitado", "em tramitação"}:
            return False
        raise ValueError(
            "A coluna 'aprovada' deve ser sim/não, true/false ou 1/0."
        )

    propostas["aprovada"] = propostas["aprovada"].map(normalizar_aprovada)
    for coluna in ("proposta", "iniciativa", "autor_iniciativa", "status", "fonte_url"):
        if propostas[coluna].isna().any() or propostas[coluna].astype(str).str.strip().eq("").any():
            raise ValueError(f"A coluna '{coluna}' não pode ficar vazia.")
    if not propostas["fonte_url"].astype(str).str.startswith(("https://", "http://")).all():
        raise ValueError("A coluna 'fonte_url' deve conter links HTTP ou HTTPS.")

    return propostas


def ler_csv_votos(arquivo: Any) -> pd.DataFrame:
    """Valida votos nominais e participação para o catálogo carregado pelo usuário."""
    votos = ler_csv_limitado(arquivo, 10_000)
    faltantes = sorted(set(COLUNAS_VOTOS) - set(votos.columns))
    if faltantes:
        raise ValueError(f"Colunas ausentes: {', '.join(faltantes)}.")

    colunas_opcionais = ["descricao_votacao"] if "descricao_votacao" in votos else []
    votos = votos[COLUNAS_VOTOS + colunas_opcionais].copy()
    if votos[COLUNAS_VOTOS].isna().any().any():
        raise ValueError("O CSV de votações não pode conter campos vazios.")
    if "descricao_votacao" in votos:
        votos["descricao_votacao"] = votos["descricao_votacao"].fillna("").astype(str).str.strip()

    campos_texto = [
        "agente",
        "casa",
        "cargo",
        "sessao",
        "id_votacao",
        "proposicao",
        "objetivo_impacto",
        "participacao",
        "voto",
        "fonte_url",
    ]
    for coluna in campos_texto:
        votos[coluna] = votos[coluna].astype(str).str.strip()
        if votos[coluna].eq("").any():
            raise ValueError(f"A coluna '{coluna}' não pode ficar vazia.")

    votos["data"] = pd.to_datetime(votos["data"], errors="coerce", dayfirst=True)
    if votos["data"].isna().any():
        raise ValueError("A coluna 'data' precisa conter datas válidas.")

    regras_cargo = {
        "Luiz Inácio Lula da Silva": {
            ("Câmara dos Deputados", "Deputado federal")
        },
        "Flávio Bolsonaro": {("Senado Federal", "Senador")},
    }
    for linha in votos.itertuples(index=False):
        if (linha.casa, linha.cargo) not in regras_cargo.get(linha.agente, set()):
            raise ValueError(
                f"Casa/cargo incompatível com '{linha.agente}'. "
                "Lula: Câmara dos Deputados + Deputado federal; "
                "Flávio Bolsonaro: Senado Federal + Senador."
            )

    casas_validas = {"Câmara dos Deputados", "Senado Federal"}
    if not votos["casa"].isin(casas_validas).all():
        raise ValueError(f"Use casa: {', '.join(sorted(casas_validas))}.")
    if not votos["voto"].isin(VOTOS_POSSIVEIS).all():
        raise ValueError(f"Valores de voto aceitos: {', '.join(sorted(VOTOS_POSSIVEIS))}.")
    if not votos["participacao"].isin(PARTICIPACOES_POSSIVEIS).all():
        raise ValueError(
            "Valores de participação aceitos: "
            f"{', '.join(sorted(PARTICIPACOES_POSSIVEIS))}."
        )

    votou = votos["participacao"].eq("Votou")
    if (votou & votos["voto"].eq("Sem voto registrado")).any():
        raise ValueError("Registros marcados como 'Votou' precisam indicar o sentido do voto.")
    if (~votou & ~votos["voto"].eq("Sem voto registrado")).any():
        raise ValueError(
            "Para quem não tem voto nominal registrado, use 'Sem voto registrado' "
            "na coluna 'voto'."
        )
    if not votos["fonte_url"].str.startswith(("https://", "http://")).all():
        raise ValueError("A coluna 'fonte_url' deve conter links HTTP ou HTTPS.")

    return votos.drop_duplicates(
        subset=["agente", "casa", "id_votacao"], keep="last"
    ).sort_values("data")


def resumir_objetivo_popular(proposicao: str, ementa: str) -> str:
    """Resume o que a proposta mudaria se aprovada, sem prever seus resultados."""
    texto = f"{proposicao} {ementa}".casefold()

    resumos_por_materia = {
        "pec 6/2019": (
            "Se aprovado, o texto eleva gradualmente de 60 para 62 anos a idade mínima "
            "das mulheres na aposentadoria urbana do INSS. Para os homens, a idade mínima "
            "permanece em 65 anos. A proposta também muda regras de contribuição, "
            "transição e cálculo de benefícios."
        ),
        "pec 133/2019": (
            "Se aprovado, estados e municípios podem adotar regras de aposentadoria "
            "parecidas com as da União. O texto também muda benefícios fiscais e prevê "
            "um benefício da Seguridade Social para crianças em situação de pobreza."
        ),
        "pec 10/2020": (
            "Se aprovado, o governo pode usar regras fiscais, financeiras e de contratação "
            "especiais durante a emergência nacional da pandemia."
        ),
        "mpv 915/2019": (
            "Se aprovado, o texto muda as regras para administrar e vender imóveis "
            "pertencentes à União."
        ),
        "pec 18/2020": (
            "Na versão descrita na ementa, o texto adiava as eleições municipais de "
            "4 de outubro para 6 de dezembro de 2020 por causa da pandemia."
        ),
        "pl 1328/2020": (
            "Se aprovado, o texto suspende temporariamente o desconto das parcelas de "
            "empréstimos consignados feitos por aposentados e pensionistas durante a "
            "emergência da Covid-19."
        ),
        "pl 2630/2020": (
            "Se aprovado, o texto cria regras para liberdade, responsabilidade e "
            "transparência na internet."
        ),
        "pec 25/2017": (
            "Se aprovado, o texto atualiza a expressão usada na Constituição para "
            "“pessoa com deficiência”."
        ),
        "pl 4162/2019": (
            "Se aprovado, o texto define metas para ampliar o acesso à água e ao esgoto "
            "tratados e muda como esses serviços são organizados e contratados, incluindo "
            "regras para empresas privadas."
        ),
        "plp 19/2019": (
            "Se aprovado, o Banco Central ganha autonomia definida em lei em relação ao "
            "governo federal. O presidente e os diretores passam a ter mandatos com datas "
            "próprias, que não coincidem com o mandato presidencial."
        ),
        "mpv 1031/2021": (
            "Se aprovado, o texto permite privatizar a Eletrobras por meio da venda de "
            "ações, reduzindo a participação da União, e muda regras do setor elétrico."
        ),
    }
    for identificador, resumo in resumos_por_materia.items():
        if identificador in texto:
            return resumo

    if not ementa or ementa.strip().casefold() in {"nan", "none", "<na>"}:
        return "A descrição oficial da proposta não está disponível para resumir seu conteúdo."

    resumo = re.sub(r"\s+", " ", ementa).strip()
    resumo = re.sub(r"\s*e dá outras providências\.?$", "", resumo, flags=re.IGNORECASE)
    indicacao = re.search(
        r"\bnome\s+(?:do senhor|da senhora|de)\s+(.+?)\s+"
        r"para exercer o cargo de\s+(.+?)(?:[.;]|$)",
        resumo,
        flags=re.IGNORECASE,
    )
    if indicacao:
        nome, cargo = (parte.strip(" ,") for parte in indicacao.groups())
        return (
            f"Se aprovado, o Senado confirma a indicação de {nome} para o cargo de "
            f"{cargo}."
        )

    objetivo_de_alteracao = re.match(
        r"^altera\b.+?\bpara\s+(.+)$", resumo, flags=re.IGNORECASE
    )
    if objetivo_de_alteracao:
        resumo = objetivo_de_alteracao.group(1)
        resumo = re.sub(
            r"^dispor sobre\b", "definir regras para", resumo, flags=re.IGNORECASE
        )
        verbos = {
            "instituir": "criar",
            "estabelecer": "definir",
            "assegurar": "garantir",
            "vedar": "proibir",
            "dispor": "tratar",
            "regulamentar": "definir regras",
            "alterar": "mudar",
            "autorizar": "permitir",
            "disciplinar": "definir regras",
            "ampliar": "aumentar",
            "aumentar": "aumentar",
            "elevar": "aumentar",
            "reduzir": "diminuir",
            "diminuir": "diminuir",
            "prorrogar": "estender",
            "estender": "estender",
            "suspender": "suspender",
            "revogar": "cancelar",
            "fixar": "definir",
            "conceder": "conceder",
        }
        for verbo, traducao in verbos.items():
            resumo = re.sub(
                rf"^{verbo}\b", traducao, resumo, flags=re.IGNORECASE
            )
        return (
            f"Se aprovada, a proposta tem como objetivo {resumo.rstrip('.')}."
            " A ementa resumida não detalha todos os possíveis efeitos práticos."
        )

    resumo = re.sub(r"^dispõe sobre\b", "trata de", resumo, flags=re.IGNORECASE)
    resumo = re.sub(r"^altera\b", "muda", resumo, flags=re.IGNORECASE)
    resumo = re.sub(r"^institui\b", "cria", resumo, flags=re.IGNORECASE)
    resumo = re.sub(r"^estabelece\b", "define", resumo, flags=re.IGNORECASE)
    resumo = re.sub(r"^autoriza\b", "permite", resumo, flags=re.IGNORECASE)
    resumo = re.sub(r"^regulamenta\b", "define regras para", resumo, flags=re.IGNORECASE)
    resumo = re.sub(r"^acrescenta\b", "inclui", resumo, flags=re.IGNORECASE)
    resumo = re.sub(
        r"^dá nova redação\b", "muda o texto", resumo, flags=re.IGNORECASE
    )
    resumo = re.sub(r"^susta\b", "suspende", resumo, flags=re.IGNORECASE)
    resumo = re.sub(r"^revoga\b", "cancela", resumo, flags=re.IGNORECASE)
    resumo = re.sub(
        r"\b(art\.|arts\.|inciso|incisos|§)\s*[\wºª.,/-]+",
        "",
        resumo,
        flags=re.IGNORECASE,
    )
    resumo = re.sub(r"\s+", " ", resumo).strip(" .;")
    if len(resumo) > 450:
        resumo = resumo[:447].rsplit(" ", 1)[0] + "..."
    return (
        f"Se aprovado, o texto {resumo.rstrip('.')}."
        " A ementa resumida não detalha quem será afetado nem todos os efeitos práticos."
    )


@st.cache_data(ttl=3600)
def buscar_votos_senado_flavio() -> pd.DataFrame:
    """Obtém votos nominais de Flávio na API oficial de Dados Abertos do Senado."""
    parametros = urlencode(
        {
            "codigoParlamentar": SENADO_CODIGO_FLAVIO,
            "dataInicio": "2019-02-01",
            "dataFim": date.today().isoformat(),
        }
    )
    url_api = f"https://legis.senado.leg.br/dadosabertos/votacao.json?{parametros}"
    requisicao = Request(
        url_api,
        headers={
            "Accept": "application/json",
            "User-Agent": "DashboardComparativoBrasil/1.0",
        },
    )
    with urlopen(requisicao, timeout=12) as resposta:
        payload = json.load(resposta)
    if not isinstance(payload, list):
        raise ValueError("A API do Senado retornou um formato de dados inesperado.")

    linhas: list[dict[str, Any]] = []
    mapas_voto = {"Sim": "Sim", "Não": "Não", "Abstenção": "Abstenção"}
    for item in payload:
        voto_parlamentar = next(
            (
                voto
                for voto in item.get("votos", [])
                if int(voto.get("codigoParlamentar", -1)) == SENADO_CODIGO_FLAVIO
            ),
            None,
        )
        if voto_parlamentar is None:
            continue

        codigo_voto = str(voto_parlamentar.get("siglaVotoParlamentar", "")).strip()
        descricao_voto = str(
            voto_parlamentar.get("descricaoVotoParlamentar") or ""
        ).strip()
        if codigo_voto in mapas_voto:
            participacao = "Votou"
            sentido_voto = mapas_voto[codigo_voto]
        elif codigo_voto == "Votou" and item.get("votacaoSecreta") == "S":
            participacao = "Participou de votação secreta"
            sentido_voto = "Sem voto registrado"
        elif codigo_voto == "P-NRV":
            participacao = "Presente, sem voto nominal"
            sentido_voto = "Sem voto registrado"
        elif codigo_voto == "NCom":
            participacao = "Ausente"
            sentido_voto = "Sem voto registrado"
        elif codigo_voto == "LP":
            participacao = "Licença registrada"
            sentido_voto = "Sem voto registrado"
        elif codigo_voto == "MIS":
            participacao = "Em missão oficial"
            sentido_voto = "Sem voto registrado"
        elif codigo_voto == "AP":
            participacao = "Atividade parlamentar registrada; sem voto nominal"
            sentido_voto = "Sem voto registrado"
        elif codigo_voto.startswith("Presidente"):
            participacao = "Presidiu a sessão"
            sentido_voto = "Sem voto registrado"
        else:
            participacao = "Sem informação"
            sentido_voto = "Sem voto registrado"

        codigo_votacao = item.get("codigoSessaoVotacao")
        descricao_votacao = str(item.get("descricaoVotacao") or "").strip()
        ementa = str(item.get("ementa") or descricao_votacao).strip()
        if not codigo_votacao or not item.get("dataSessao") or not ementa:
            continue
        linhas.append(
            {
                "agente": "Flávio Bolsonaro",
                "casa": "Senado Federal",
                "cargo": "Senador",
                "data": item["dataSessao"],
                "sessao": (
                    f"{item.get('siglaTipoSessao', 'Sessão')} "
                    f"{item.get('numeroSessao', '')} "
                    f"(código {item.get('codigoSessao', 'N/D')})"
                ).strip(),
                "id_votacao": str(codigo_votacao),
                "proposicao": str(item.get("identificacao") or "Matéria sem identificação"),
                "objetivo_impacto": ementa,
                "ementa_oficial": ementa,
                "participacao": participacao,
                "voto": sentido_voto,
                "fonte_url": (
                    "https://www25.senado.leg.br/web/atividade/"
                    f"votacoes-nominais/-/v/{codigo_votacao}"
                ),
                "codigo_voto_api": codigo_voto,
                "detalhe_voto_api": descricao_voto,
                "descricao_votacao": descricao_votacao,
            }
        )

    colunas_api = COLUNAS_VOTOS + [
        "ementa_oficial",
        "codigo_voto_api",
        "detalhe_voto_api",
        "descricao_votacao",
    ]
    if not linhas:
        return pd.DataFrame(columns=colunas_api)
    dados_api = pd.DataFrame(linhas, columns=colunas_api)
    dados_api["data"] = pd.to_datetime(dados_api["data"], errors="coerce")
    if dados_api["data"].isna().any():
        raise ValueError("A API do Senado retornou datas de votação inválidas.")
    return (
        dados_api
        .drop_duplicates(subset=["agente", "casa", "id_votacao"], keep="last")
        .sort_values("data")
        .reset_index(drop=True)
    )


def media_segura(serie: pd.Series) -> float | None:
    valores = serie.dropna()
    return float(valores.mean()) if not valores.empty else None


def ultimo_valor(serie: pd.Series) -> float | None:
    valores = serie.dropna()
    return float(valores.iloc[-1]) if not valores.empty else None


def fmt_numero(valor: float | None, casas: int = 1, sufixo: str = "") -> str:
    if valor is None or not math.isfinite(valor):
        return "N/D"
    texto = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto}{sufixo}"


def formatar_grupo(
    grupo: pd.DataFrame,
    coluna: str,
    casas: int = 1,
    sufixo: str = "",
    acumulado: bool = False,
) -> str:
    valores = grupo[coluna].dropna()
    if valores.empty:
        return "N/D"
    if acumulado:
        resultado = ((1 + valores / 100).prod() - 1) * 100
    else:
        resultado = valores.mean()
    return fmt_numero(float(resultado), casas, sufixo)


def resumo_periodo(dados: pd.DataFrame, periodo: str) -> pd.DataFrame:
    nomes = PERIODOS[periodo]
    return dados[dados["periodo"].isin(nomes)].sort_values("ano")


st.title("Brasil em perspectiva: governos, indicadores e propostas")
st.caption(
    "Painel comparativo e exploratório. Indicadores descrevem períodos; não isolam "
    "causalidade nem equivalem a uma avaliação de mérito."
)
st.info(
    "A base econômica embarcada cobre 2003–2024; não há projeções para 2025–2026. "
    "Votações do Senado são consultadas na fonte oficial e podem ser atualizadas "
    "independentemente dos indicadores."
)

with st.sidebar:
    st.header("Configuração da comparação")
    modo = st.radio(
        "Visualização",
        ["Comparar dois períodos", "Ver trajetória histórica"],
        help="Os períodos podem ser trocados para comparar diferentes ciclos e contextos.",
    )
    periodos_escolhidos = st.multiselect(
        "Períodos para comparar",
        list(PERIODOS),
        default=["Lula 2003–2010", "Bolsonaro 2019–2022"],
        max_selections=2,
    )
    eixo = st.selectbox("Eixo temático", list(EIXOS))
    upload = st.file_uploader(
        "Opcional: carregar CSV próprio",
        type=["csv"],
        help="O arquivo precisa conter as colunas descritas na seção 'Dados e metodologia'.",
    )

    st.markdown("**Blocos incluídos**")
    st.markdown("- Lula / PT: mandatos de Lula.")
    st.markdown("- Contexto PT: governo Dilma (2011–2016), separado de Lula.")
    st.markdown("- Bolsonaro / Flávio: dados de governo são do mandato de Jair Bolsonaro; "
                "Flávio não exerceu a Presidência.")

if upload is not None:
    try:
        dados = ler_csv_upload(upload)
        st.sidebar.success("CSV carregado e validado.")
    except (ValueError, pd.errors.ParserError, UnicodeError) as erro:
        st.sidebar.error(f"Não foi possível usar o CSV: {erro}")
        dados = pd.DataFrame(DADOS_BASE)
        st.sidebar.info("O painel está usando a base embarcada.")
else:
    dados = pd.DataFrame(DADOS_BASE)

if modo == "Comparar dois períodos":
    if len(periodos_escolhidos) != 2:
        st.info("Escolha exatamente dois períodos na barra lateral para exibir a comparação.")
        periodos_para_metricas: list[str] = []
    else:
        periodos_para_metricas = periodos_escolhidos

    if periodos_para_metricas:
        primeiro, segundo = [
            resumo_periodo(dados, periodo) for periodo in periodos_para_metricas
        ]
        col_a, col_b = st.columns(2)
        for coluna, titulo, serie in (
            (col_a, periodos_para_metricas[0], primeiro),
            (col_b, periodos_para_metricas[1], segundo),
        ):
            anos = serie["ano"].dropna()
            faixa = (
                f"{int(anos.min())}–{int(anos.max())}"
                if not anos.empty
                else "sem dados"
            )
            with coluna:
                st.subheader(titulo)
                st.caption(f"Anos com registros na base: {faixa}")
                st.metric("Crescimento médio anual do PIB", formatar_grupo(serie, "pib", 2, "%"))
                st.metric(
                    "IPCA acumulado no período",
                    formatar_grupo(serie, "ipca", 2, "%", acumulado=True),
                    help="Composição das taxas anuais disponíveis; não é a média anual do IPCA.",
                )
                st.metric("Desocupação média anual", formatar_grupo(serie, "desemprego", 1, "%"))
                st.metric("Desocupação no último ano disponível", fmt_numero(ultimo_valor(serie["desemprego"]), 1, "%"))
                st.metric("Rendimento real mensal (último dado)", fmt_numero(ultimo_valor(serie["renda_real_brl"]), 0, " R$"))
                st.metric("Famílias em transferência de renda (último dado)", fmt_numero(ultimo_valor(serie["transferencias_milhoes"]), 1, " mi"))
                st.metric("IED médio anual", formatar_grupo(serie, "ied_usd_bilhoes", 1, " US$ bi"))
                st.metric("Resultado primário médio", formatar_grupo(serie, "resultado_primario_pct_pib", 2, "% do PIB"))

        st.caption(
            "Nas métricas, N/D indica série não disponível ou não comparável na base. "
            "Para desemprego, a base prioriza a PNAD Contínua a partir de 2012; "
            "não há média apresentada para 2003–2010. Rendimento e cobertura de "
            "transferências são observações pontuais e não séries anuais completas."
        )
else:
    st.subheader("Trajetória histórica")
    st.caption("A série distingue Lula, o governo Dilma como contexto do campo petista e Bolsonaro.")

if modo == "Ver trajetória histórica" or (
    modo == "Comparar dois períodos" and len(periodos_escolhidos) == 2
):
    opcoes = EIXOS[eixo]
    if not opcoes:
        st.info(
            "Este eixo é tratado qualitativamente neste protótipo: não há uma série "
            "anual homogênea embarcada para comparação direta."
        )
    else:
        indicadores = st.multiselect(
            "Indicadores no gráfico",
            [nome for _, nome in opcoes],
            default=[nome for _, nome in opcoes],
        )
        mapa = dict(opcoes)
        chaves = [chave for chave, nome in opcoes if nome in indicadores]
        if chaves:
            if modo == "Comparar dois períodos" and len(periodos_escolhidos) == 2:
                nomes_periodos = [nome for periodo in periodos_escolhidos for nome in PERIODOS[periodo]]
                dados_grafico = dados[dados["periodo"].isin(nomes_periodos)].copy()
            else:
                dados_grafico = dados.copy()
            longa = dados_grafico.melt(
                id_vars=["ano", "grupo", "periodo"],
                value_vars=chaves,
                var_name="indicador",
                value_name="valor",
            ).dropna(subset=["valor"])
            if longa.empty:
                st.info("Não há valores disponíveis para os indicadores e períodos selecionados.")
            else:
                longa["indicador"] = longa["indicador"].map(mapa)
                figura = px.line(
                    longa,
                    x="ano",
                    y="valor",
                    color="grupo",
                    facet_col="indicador",
                    facet_col_wrap=2,
                    markers=True,
                    hover_data=["periodo"],
                    color_discrete_map=CORES,
                    title=f"Evolução anual — {eixo}",
                )
                figura.update_layout(
                    height=max(380, 320 * math.ceil(len(chaves) / 2)),
                    legend_title_text="Bloco / governo",
                    margin=dict(t=80, b=30),
                )
                figura.update_xaxes(dtick=2)
                st.plotly_chart(figura, width="stretch")

st.subheader("Contexto, propostas e limites da comparação")

with st.expander("Estratégia geopolítica e relações externas", expanded=eixo == "Geopolítica & Relações Internacionais"):
    st.markdown(
        """
        **Lula:** ênfase declarada em multilateralismo, integração regional e atuação
        em fóruns como ONU, G20 e BRICS, combinada com relações comerciais amplas.

        **Bolsonaro (2019–2022):** diplomacia descrita por maior proximidade política
        com governos conservadores e ênfase em soberania e relações bilaterais.
        **Flávio Bolsonaro:** esta tela não atribui automaticamente ao senador todas
        as decisões de política externa do governo de Jair Bolsonaro; não há série
        de resultados presidenciais próprios para Flávio.

        São caracterizações gerais de orientação diplomática, não medidas quantitativas
        de resultado. Sanções, conflitos, preços de commodities e decisões de outros
        países afetam os resultados observados.
        """
    )

with st.expander("Propostas e visão de Estado"):
    st.markdown(
        """
        **Lula / PT:** historicamente, defesa de políticas sociais e de investimento
        público, presença de empresas estatais em setores estratégicos e uso de
        instrumentos de política industrial. No terceiro mandato, o arcabouço fiscal
        substituiu o teto de gastos e a reforma tributária sobre o consumo foi
        promulgada em 2023; o desenho e a implementação devem ser avaliados ao longo
        do tempo.

        **Bolsonaro / Flávio:** o governo Bolsonaro defendeu concessões, desestatizações
        e reformas pró-mercado em diferentes áreas, com resultados e alcance variáveis.
        Flávio Bolsonaro é senador, não ex-presidente; seu histórico legislativo e
        declarações não devem ser confundidos com um plano de governo ou com o legado
        executivo do pai. A síntese sobre propostas de Flávio neste painel é
        deliberadamente cautelosa e requer atualização a partir de programa oficial
        e declarações primárias.

        **Reforma tributária e regra fiscal:** compare objetivos e textos legais,
        além dos indicadores fiscais. O resultado primário anual é influenciado por
        receitas extraordinárias, ciclo econômico e eventos excepcionais; não mede
        sozinho sustentabilidade da dívida nem qualidade do gasto.
        """
    )

with st.expander("Choques externos e contexto dos períodos"):
    st.markdown(
        """
        - **2003–2010:** expansão do comércio e ciclo favorável de commodities em parte
          do período; a crise financeira global de 2008–2009 atingiu a atividade.
        - **2011–2016 (governo Dilma, contexto PT):** desaceleração global, queda de
          preços de commodities e recessão doméstica; fatores externos coexistiram
          com decisões internas e mudanças políticas.
        - **2019–2022:** pandemia de COVID-19, disrupções de oferta, inflação global,
          guerra da Rússia contra a Ucrânia e oscilações de energia e alimentos.
        - **2023 em diante:** conflitos e volatilidade global continuaram; o período
          de Lula III mostrado na base termina em 2024 e não representa o mandato
          completo até 2026.

        A cronologia não determina causalidade. Para avaliar políticas, considere
        defasagens, condições herdadas e revisões das séries estatísticas.
        """
    )

st.header("Propostas: apresentadas vs. aprovadas")
st.markdown(
    """
    A aprovação abaixo é contada a partir de iniciativas legislativas documentadas
    no catálogo — não de promessas eleitorais. Para Lula, os exemplos são iniciativas
    do Poder Executivo no mandato Lula III. Para Flávio Bolsonaro, a comparação deve
    usar projetos de sua autoria como senador e propostas de um programa eleitoral,
    quando aplicável; ele não exerceu a Presidência neste recorte histórico. Os papéis e denominadores são diferentes,
    portanto os números não medem produtividade ou taxa de sucesso comparável.
    """
)

modelo_propostas = (
    "bloco,proposta,ano,iniciativa,autor_iniciativa,status,aprovada,fonte_url\n"
    'Flávio Bolsonaro,"Título e número do projeto",2023,PL,'
    '"Flávio Bolsonaro (autor)",Em tramitação,não,https://www25.senado.leg.br/web/atividade/materias\n'
)
st.download_button(
    "Baixar modelo CSV de propostas",
    data=modelo_propostas,
    file_name="modelo_propostas.csv",
    mime="text/csv",
)
arquivo_propostas = st.file_uploader(
    "Adicionar projetos e propostas rastreados em fontes oficiais",
    type=["csv"],
    help=(
        "O CSV deve ter: bloco, proposta, ano, iniciativa, autor_iniciativa, "
        "status, aprovada e fonte_url. Use bloco 'Lula / PT' ou 'Flávio Bolsonaro'."
    ),
    key="propostas_csv",
)

propostas = pd.DataFrame(PROPOSTAS_BASE)
if arquivo_propostas is not None:
    try:
        propostas_usuario = ler_csv_propostas(arquivo_propostas)
        propostas = pd.concat([propostas, propostas_usuario], ignore_index=True)
        propostas = propostas.drop_duplicates(
            subset=["bloco", "proposta", "ano"], keep="last"
        )
        st.success("Propostas do CSV foram validadas e adicionadas aos exemplos.")
    except (ValueError, pd.errors.ParserError, UnicodeError) as erro:
        st.error(f"Não foi possível carregar as propostas: {erro}")

contagem = (
    propostas.groupby("bloco", as_index=False)
    .agg(
        apresentadas=("proposta", "count"),
        aprovadas=("aprovada", "sum"),
    )
)
flavio_sem_dados = not (propostas["bloco"] == "Flávio Bolsonaro").any()
metricas_propostas = st.columns(2)
for coluna, bloco in zip(metricas_propostas, ("Lula / PT", "Flávio Bolsonaro")):
    registro = contagem[contagem["bloco"] == bloco]
    with coluna:
        st.subheader(bloco)
        if registro.empty:
            st.metric("Propostas registradas no catálogo", "N/D")
            st.metric("Aprovadas no catálogo", "N/D")
        else:
            st.metric(
                "Propostas registradas no catálogo",
                int(registro["apresentadas"].iloc[0]),
            )
            st.metric("Aprovadas no catálogo", int(registro["aprovadas"].iloc[0]))

if flavio_sem_dados:
    st.info(
        "Ainda não há projetos de autoria de Flávio cadastrados no catálogo local. "
        "Isso significa 'sem dado no catálogo', não zero projetos ou zero aprovações. "
        "Consulte a busca oficial do Senado ou carregue um CSV documentado."
    )
else:
    st.caption(
        "A contagem é do catálogo demonstrativo mais os registros enviados pelo usuário; "
        "não equivale à totalidade das proposições apresentadas por cada agente."
    )

if not contagem.empty:
    contagem_longa = contagem.melt(
        id_vars="bloco",
        value_vars=["apresentadas", "aprovadas"],
        var_name="resultado",
        value_name="quantidade",
    )
    contagem_longa["resultado"] = contagem_longa["resultado"].map(
        {"apresentadas": "Apresentadas no catálogo", "aprovadas": "Aprovadas"}
    )
    fig_propostas = px.bar(
        contagem_longa,
        x="bloco",
        y="quantidade",
        color="resultado",
        barmode="group",
        text="quantidade",
        color_discrete_map={
            "Apresentadas no catálogo": "#667085",
            "Aprovadas": "#218739",
        },
        title="Iniciativas registradas e aprovadas no catálogo",
    )
    fig_propostas.update_layout(
        xaxis_title="Agente / grupo",
        yaxis_title="Número de registros",
        legend_title="Etapa legislativa",
    )
    st.plotly_chart(fig_propostas, width="stretch")

if not propostas.empty:
    st.dataframe(
        propostas[
            [
                "bloco",
                "proposta",
                "ano",
                "iniciativa",
                "autor_iniciativa",
                "status",
                "aprovada",
                "fonte_url",
            ]
        ],
        hide_index=True,
        width="stretch",
        column_config={
            "fonte_url": st.column_config.LinkColumn("Fonte oficial"),
            "aprovada": st.column_config.CheckboxColumn("Aprovada"),
        },
    )

col_lula, col_flavio = st.columns(2)
with col_lula:
    st.link_button(
        "Buscar tramitação na Câmara",
        "https://www.camara.leg.br/busca-portal/proposicoes/",
        width="stretch",
    )
with col_flavio:
    st.link_button(
        "Consultar matérias no Senado",
        "https://www25.senado.leg.br/web/atividade/materias",
        width="stretch",
    )
st.caption(
    "Para uma auditoria completa, confira autoria, coautoria, relatoria, substitutivos, "
    "tramitação, sanção/veto e conversão em norma no registro oficial de cada matéria. "
    "Um projeto aprovado em uma Casa ainda pode não ter concluído o processo legislativo."
)

st.header("Votos nominais em sessões da Câmara e do Senado")
st.markdown(
    """
    Esta área registra **votos individuais dos parlamentares**, não posições do
    Poder Executivo. O registro de Lula como deputado deve se referir ao mandato
    parlamentar de 1987–1991; como presidente, ele não vota em sessões legislativas.
    Flávio Bolsonaro é comparado em sua atuação como senador. Jair Bolsonaro, quando
    presidente (2019–2022), também não tinha voto parlamentar nessa função.

    Os votos do Senado são consultados automaticamente na API oficial para o código
    parlamentar 5894, a partir de 01/02/2019. “Ausente”, “presente sem voto nominal”,
    voto secreto e “sem informação” são estados distintos; ausência não é inferida
    apenas porque o sentido do voto não foi publicado.
    """
)

modelo_votos = (
    "agente,casa,cargo,data,sessao,id_votacao,proposicao,objetivo_impacto,participacao,voto,fonte_url,descricao_votacao\n"
)
st.download_button(
    "Baixar modelo CSV de votações",
    data=modelo_votos,
    file_name="modelo_votacoes.csv",
    mime="text/csv",
)
arquivo_votos = st.file_uploader(
    "Carregar registros nominais com fonte oficial",
    type=["csv"],
    help=(
        "O CSV exige: agente, casa, cargo, data, sessao, id_votacao, proposicao, "
        "objetivo_impacto, participacao, voto e fonte_url. "
        "descricao_votacao é opcional e identifica o item específico submetido à votação."
    ),
    key="votos_csv",
)

try:
    votos_api = buscar_votos_senado_flavio()
    st.session_state["votos_senado_ultimo_sucesso"] = votos_api.copy()
    st.success(
        f"Dados do Senado consultados: {len(votos_api)} registros de votação de "
        "Flávio Bolsonaro desde 01/02/2019. Atualização em cache por até 1 hora."
    )
except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as erro:
    votos_api = st.session_state.get(
        "votos_senado_ultimo_sucesso",
        pd.DataFrame(
            columns=COLUNAS_VOTOS
            + ["ementa_oficial", "codigo_voto_api", "detalhe_voto_api", "descricao_votacao"]
        ),
    )
    if not votos_api.empty:
        st.warning(
            "A API do Senado está indisponível no momento; exibindo os últimos dados "
            f"obtidos nesta sessão. Erro: {erro}"
        )
    else:
        st.warning(
            "Não foi possível consultar a API do Senado agora. "
            f"Detalhe: {erro}. Você ainda pode carregar um CSV manualmente."
        )

votos = votos_api.copy()
if arquivo_votos is not None:
    try:
        votos_csv = ler_csv_votos(arquivo_votos)
        votos_csv["id_votacao"] = votos_csv["id_votacao"].astype(str)
        votos = pd.concat([votos, votos_csv], ignore_index=True, sort=False)
        votos = votos.drop_duplicates(
            subset=["agente", "casa", "id_votacao"], keep="last"
        ).sort_values("data")
        st.success(f"{len(votos_csv)} registro(s) manual(is) validado(s) e incluído(s).")
    except (ValueError, pd.errors.ParserError, UnicodeError) as erro:
        st.error(f"Não foi possível carregar os votos: {erro}")

if not votos.empty:
    for coluna in ("codigo_voto_api", "detalhe_voto_api", "descricao_votacao"):
        if coluna not in votos:
            votos[coluna] = ""
    votos["codigo_voto_api"] = votos["codigo_voto_api"].fillna("")
    votos["detalhe_voto_api"] = votos["detalhe_voto_api"].fillna("")
    if "ementa_oficial" not in votos:
        votos["ementa_oficial"] = pd.NA
    votos["ementa_oficial"] = votos["ementa_oficial"].fillna(
        votos["objetivo_impacto"]
    )
    votos["objetivo_impacto"] = votos.apply(
        lambda linha: resumir_objetivo_popular(
            str(linha["proposicao"]), str(linha["ementa_oficial"])
        ),
        axis=1,
    )
    leituras = votos.apply(
        lambda linha: analisar_posicionamento_voto(
            str(linha["proposicao"]),
            str(linha["objetivo_impacto"]),
            str(linha["ementa_oficial"]),
            str(linha["participacao"]),
            str(linha["voto"]),
            str(linha["descricao_votacao"]),
        ),
        axis=1,
    )
    votos["tema_perfil"] = [leitura[0] for leitura in leituras]
    votos["leitura_voto"] = [leitura[1] for leitura in leituras]

if votos.empty:
    st.info(
        "A consulta não retornou votos nem há CSV manual carregado. Se a API estiver "
        "indisponível, tente atualizar mais tarde ou carregue registros conferidos "
        "no CSV; a falta de registro não é tratada como voto ou ausência."
    )
else:
    filtro_colunas = st.columns(3)
    with filtro_colunas[0]:
        agentes_disponiveis = sorted(votos["agente"].unique())
        agentes_selecionados = st.multiselect(
            "Agente",
            agentes_disponiveis,
            default=agentes_disponiveis,
            key="filtro_agente_votos",
        )
    with filtro_colunas[1]:
        casas_disponiveis = sorted(votos["casa"].unique())
        casas_selecionadas = st.multiselect(
            "Casa legislativa",
            casas_disponiveis,
            default=casas_disponiveis,
            key="filtro_casa_votos",
        )
    with filtro_colunas[2]:
        anos_disponiveis = sorted(votos["data"].dt.year.unique())
        anos_selecionados = st.multiselect(
            "Ano",
            anos_disponiveis,
            default=anos_disponiveis,
            key="filtro_ano_votos",
        )

    votos_filtrados = votos[
        votos["agente"].isin(agentes_selecionados)
        & votos["casa"].isin(casas_selecionadas)
        & votos["data"].dt.year.isin(anos_selecionados)
    ].copy()
    resumo_votos = st.columns(3)
    resumo_votos[0].metric("Registros de votação no filtro", len(votos_filtrados))
    resumo_votos[1].metric(
        "Votos registrados",
        int(votos_filtrados["participacao"].eq("Votou").sum()),
    )
    resumo_votos[2].metric(
        "Ausências expressamente registradas",
        int(votos_filtrados["participacao"].eq("Ausente").sum()),
    )

    votos_com_sufragio = votos_filtrados[votos_filtrados["participacao"] == "Votou"]
    if votos_com_sufragio.empty:
        st.info("O filtro não contém votos individuais registrados.")
    else:
        distribuicao = (
            votos_com_sufragio.groupby(["agente", "voto"], as_index=False)
            .size()
            .rename(columns={"size": "quantidade"})
        )
        fig_votos = px.bar(
            distribuicao,
            x="agente",
            y="quantidade",
            color="voto",
            barmode="group",
            text="quantidade",
            title="Sentido dos votos nominais registrados",
            color_discrete_map={
                "Sim": "#218739",
                "Não": "#B42332",
                "Abstenção": "#D97706",
                "Obstrução": "#667085",
            },
        )
        fig_votos.update_layout(
            xaxis_title="Parlamentar",
            yaxis_title="Votos no catálogo",
            legend_title="Voto",
        )
        st.plotly_chart(fig_votos, width="stretch")

    with st.expander("Experimento: perfil de posicionamento pelos votos", expanded=True):
        st.markdown(
            "Esta leitura combina **o sentido do voto e a descrição oficial do item "
            "submetido à votação**. Ela não atribui motivação pessoal nem interpreta "
            "contextos externos ao registro. Quando a descrição não permite saber qual "
            "mudança concreta estava em votação, isso fica indicado no texto."
        )
        st.caption(
            "“Sim” e “Não” reproduzem o voto nominal, mas não são convertidos "
            "automaticamente em apoio ou oposição à proposta inteira. Em emendas, destaques "
            "e votações procedimentais, o item pode ser diferente do texto principal. "
            "Abstenção, obstrução, votação secreta e ausência não são convertidas em "
            "posicionamento."
        )
        registros_do_perfil = votos_filtrados.copy()
        votos_para_perfil = registros_do_perfil[
            registros_do_perfil["participacao"].eq("Votou")
        ].copy()
        votos_classificados = votos_para_perfil[
            ~votos_para_perfil["tema_perfil"].eq("Tema sem regra específica")
            & ~votos_para_perfil["tema_perfil"].eq("Não classificado")
        ]
        perfil_metricas = st.columns(3)
        perfil_metricas[0].metric("Registros de votação no filtro", len(registros_do_perfil))
        perfil_metricas[1].metric(
            "Votos nominais individuais", len(votos_para_perfil)
        )
        perfil_metricas[2].metric(
            "Itens com tema identificado",
            len(votos_classificados),
        )

        if votos_classificados.empty:
            st.info(
                "Não há, neste filtro, propostas que correspondam às regras temáticas "
                "específicas. Os votos nominais ainda aparecem abaixo com a descrição "
                "da matéria."
            )
        else:
            contagem_perfil = (
                votos_classificados.groupby(
                    ["agente", "tema_perfil", "voto"], as_index=False
                )
                .size()
                .rename(columns={"size": "votos"})
            )
            fig_perfil = px.bar(
                contagem_perfil,
                x="tema_perfil",
                y="votos",
                color="voto",
                facet_col="agente",
                barmode="group",
                text="votos",
                title="Posicionamentos registrados por tema",
                labels={
                    "tema_perfil": "Tema identificado no texto",
                    "votos": "Quantidade de votos",
                    "voto": "Sentido do voto",
                    "agente": "Parlamentar",
                },
                color_discrete_map={"Sim": "#218739", "Não": "#B42332"},
            )
            fig_perfil.update_layout(legend_title="Voto")
            st.plotly_chart(fig_perfil, width="stretch")

        st.markdown("#### Leitura de todos os registros do filtro")
        st.caption(
            "A descrição do item é mantida separada da ementa geral da proposta. Quando "
            "a fonte não detalha o efeito de uma emenda, destaque ou procedimento, o painel "
            "não presume se o voto aumentaria, reduziria ou manteria uma regra."
        )
        st.dataframe(
            registros_do_perfil[
                [
                    "agente",
                    "data",
                    "proposicao",
                    "tema_perfil",
                    "participacao",
                    "voto",
                    "leitura_voto",
                    "descricao_votacao",
                    "detalhe_voto_api",
                    "fonte_url",
                ]
            ],
            hide_index=True,
            width="stretch",
            column_config={
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "tema_perfil": st.column_config.TextColumn("Tema identificado"),
                "leitura_voto": st.column_config.TextColumn(
                    "Posição registrada e conteúdo da matéria",
                    width="large",
                ),
                "descricao_votacao": st.column_config.TextColumn(
                    "Item específico votado (fonte oficial)", width="large"
                ),
                "detalhe_voto_api": st.column_config.TextColumn(
                    "Descrição da votação", width="large"
                ),
                "fonte_url": st.column_config.LinkColumn("Registro oficial"),
            },
        )

    st.dataframe(
        votos_filtrados[
            [
                "agente",
                "casa",
                "cargo",
                "data",
                "sessao",
                "id_votacao",
                "proposicao",
                "objetivo_impacto",
                "ementa_oficial",
                "participacao",
                "voto",
                "codigo_voto_api",
                "descricao_votacao",
                "detalhe_voto_api",
                "fonte_url",
            ]
        ],
        hide_index=True,
        width="stretch",
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "objetivo_impacto": st.column_config.TextColumn(
                "O que mudaria se o texto fosse aprovado?", width="large"
            ),
            "ementa_oficial": st.column_config.TextColumn(
                "Ementa oficial completa", width="large"
            ),
            "codigo_voto_api": st.column_config.TextColumn("Código original do Senado"),
            "descricao_votacao": st.column_config.TextColumn(
                "Item específico votado (fonte oficial)", width="large"
            ),
            "detalhe_voto_api": st.column_config.TextColumn("Observação original"),
            "fonte_url": st.column_config.LinkColumn("Registro oficial"),
        },
    )

st.markdown(
    "**Fontes oficiais:** "
    "[API de votações nominais do Senado](https://legis.senado.leg.br/dadosabertos/votacao.json?codigoParlamentar=5894&dataInicio=2019-02-01) · "
    "[Dados Abertos da Câmara — API e documentação](https://dadosabertos.camara.leg.br/swagger/api.html) · "
    "[Senado — Dados Abertos](https://legis.senado.leg.br/dadosabertos/) · "
    "[Senado — matérias e tramitação](https://www25.senado.leg.br/web/atividade/materias)."
)
st.caption(
    "A coluna explica em linguagem simples o que o texto prevê caso seja aprovado; "
    "não afirma qual será o efeito real nem por que o parlamentar votou assim. "
    "A ementa oficial permanece disponível para conferência. "
    "Registre o sentido do voto nominal conforme "
    "o painel oficial e inclua o link direto à sessão ou votação sempre que possível. "
    "Votações secretas têm participação confirmada, mas sentido não divulgado."
)

with st.expander("Dados, fontes e metodologia"):
    st.markdown(
        """
        A base padrão é uma seleção **aproximada e arredondada**, incluída no próprio
        `app.py` para o app funcionar sem arquivos externos. A cobertura embarcada vai
        de 2003 a 2024; 2025 e 2026 não são preenchidos por projeções. Para uma
        atualização de 2025–2026, carregue um CSV revisado com fontes e datas de
        extração documentadas.

        - **PIB e IPCA:** IBGE; taxas anuais de variação.
        - **Desocupação e rendimento:** IBGE/PNAD Contínua; a série de desemprego
          usada aqui começa em 2012, sem emendar a antiga PME.
        - **IED e resultado primário:** Banco Central do Brasil; valores em US$ correntes
          e resultado do setor público consolidado como proporção do PIB.
        - **Transferências:** referências aproximadas a famílias atendidas em anos
          selecionados. Bolsa Família, Auxílio Brasil e os desenhos posteriores não
          são programas idênticos; a cobertura não deve ser tratada como série
          diretamente comparável sem harmonização.
        - **Renda real:** valor mensal em reais informado apenas em anos selecionados;
          não é uma média para todo o período de governo.

        **Fontes adicionais para conferência e atualização:**
        - [IBGE — Contas Nacionais/PIB](https://www.ibge.gov.br/explica/pib.php),
          [IPCA](https://www.ibge.gov.br/explica/inflacao.php) e
          [PNAD Contínua](https://www.ibge.gov.br/estatisticas/sociais/trabalho/).
        - [Banco Central — Estatísticas](https://www.bcb.gov.br/estatisticas) e
          [séries temporais SGS](https://www3.bcb.gov.br/sgspub/).
        - [Tesouro Nacional — Estatísticas Fiscais](https://www.tesourotransparente.gov.br/temas/estatisticas-fiscais-e-planejamento).
        - [IpeaData](https://www.ipeadata.gov.br/) para séries econômicas e sociais.
        - [Banco Mundial — World Development Indicators](https://data.worldbank.org/).
        - [MDS — dados e painéis sociais](https://aplicacoes.mds.gov.br/sagi/portal/).
        - [Comex Stat — comércio exterior (MDIC)](https://comexstat.mdic.gov.br/pt/home).
        - [INPE — monitoramento do desmatamento](https://terrabrasilis.dpi.inpe.br/).
        - [TSE — Divulgação de Candidaturas e Contas Eleitorais](https://divulgacandcontas.tse.jus.br/),
          incluindo registros de candidaturas e planos de governo.
        - [Câmara — consulta de proposições](https://www.camara.leg.br/busca-portal/proposicoes/)
          e [Senado — matérias](https://www25.senado.leg.br/web/atividade/materias)
          para autoria e tramitação legislativa.
        - [Câmara — Dados Abertos/API](https://dadosabertos.camara.leg.br/swagger/api.html)
          e [Senado — Dados Abertos](https://legis.senado.leg.br/dadosabertos/)
          para votações nominais e presença parlamentar.

        Exemplos registrados neste app:
        [PLP 93/2023 — regime fiscal (Câmara)](https://www.camara.leg.br/propostas-legislativas/2357053)
        e [MP 1.164/2023 — consulta da tramitação na Câmara](https://www.camara.leg.br/busca-portal/proposicoes/?q=MPV%201164%2F2023).
        As normas resultantes são [LC 200/2023](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp200.htm)
        e [Lei 14.601/2023](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14601.htm).
        Confira as páginas oficiais antes de republicar os dados ou atribuir autoria.

        **CSV esperado:** `ano, periodo, grupo, pib, ipca, desemprego, renda_real_brl,
        transferencias_milhoes, ied_usd_bilhoes, resultado_primario_pct_pib`.
        Valores ausentes devem ficar vazios. Valores de `grupo` aceitos:
        `Lula / PT`, `Bolsonaro / Flávio` e `Contexto PT (Dilma)`. Se houver erro no
        arquivo, o painel informa o motivo e retorna à base embarcada.
        """
    )

st.warning(
    "Nota de interpretação: as médias dependem dos anos e da disponibilidade de cada "
    "série. Comparações entre governos são descritivas; revisões metodológicas, "
    "choques externos, regras institucionais e diferenças entre programas limitam "
    "conclusões diretas. Não há dados de governo presidencial de Flávio Bolsonaro."
)
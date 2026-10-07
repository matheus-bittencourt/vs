"""Leitura de CSVs enviados à aplicação com limites de recursos."""

from typing import Any

import pandas as pd

MAX_CSV_BYTES = 5 * 1024 * 1024


def ler_csv_limitado(arquivo: Any, limite_linhas: int) -> pd.DataFrame:
    """Aplica limites de tamanho e linhas antes de aceitar CSV enviado ao site."""
    try:
        conteudo = arquivo.getvalue()
    except AttributeError as erro:
        raise ValueError("Não foi possível verificar o tamanho do arquivo enviado.") from erro
    tamanho = len(conteudo.encode("utf-8") if isinstance(conteudo, str) else conteudo)
    if tamanho > MAX_CSV_BYTES:
        raise ValueError("O CSV excede o limite de 5 MB.")
    arquivo.seek(0)
    dados = pd.read_csv(arquivo, nrows=limite_linhas + 1)
    if len(dados) > limite_linhas:
        raise ValueError(f"O CSV excede o limite de {limite_linhas:,} linhas de dados.")
    return dados

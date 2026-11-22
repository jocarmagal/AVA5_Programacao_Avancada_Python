"""Consultas da análise de Londrina, separadas para poderem ser testadas."""

from pathlib import Path

import pandas as pd


def media_por_produto(dados: pd.DataFrame) -> pd.DataFrame:
    """Média do valor de venda por produto, da mais barata para a mais cara."""
    return (
        dados.groupby("produto", as_index=False)
        .agg(coletas=("valor_venda", "size"), valor_medio=("valor_venda", "mean"))
        .sort_values("valor_medio")
        .reset_index(drop=True)
    )


def media_por_bairro(dados: pd.DataFrame) -> pd.DataFrame:
    """Média do valor de venda por bairro e produto."""
    tabela = dados.copy()
    tabela["bairro"] = tabela["bairro"].fillna("SEM BAIRRO")
    return (
        tabela.groupby(["bairro", "produto"], as_index=False)
        .agg(coletas=("valor_venda", "size"), valor_medio=("valor_venda", "mean"))
        .sort_values(["produto", "valor_medio"])
        .reset_index(drop=True)
    )


def extremos_por_produto(dados: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Postos mais baratos e mais caros de cada produto, pela média do mês."""
    medias = (
        dados.groupby(["produto", "cnpj"], as_index=False)
        .agg(
            revenda=("revenda", "first"),
            bandeira=("bandeira", "first"),
            bairro=("bairro", "first"),
            valor_medio=("valor_venda", "mean"),
            coletas=("valor_venda", "size"),
        )
    )
    partes = []
    for produto, grupo in medias.groupby("produto"):
        ordenado = grupo.sort_values(["valor_medio", "revenda"]).reset_index(drop=True)
        baratos = ordenado.head(n).copy()
        baratos["grupo"] = "mais_barato"
        baratos["posicao"] = range(1, len(baratos) + 1)
        caros = ordenado.tail(n).sort_values(["valor_medio", "revenda"], ascending=[False, True]).copy()
        caros["grupo"] = "mais_caro"
        caros["posicao"] = range(1, len(caros) + 1)
        partes.extend([baratos, caros])
    colunas = ["produto", "grupo", "posicao", "revenda", "bandeira", "bairro", "cnpj", "valor_medio", "coletas"]
    return pd.concat(partes, ignore_index=True)[colunas]


def gravar_planilha(dados: pd.DataFrame, caminho: Path) -> list[str]:
    """Uma aba por produto, com as coletas da mais barata para a mais cara."""
    colunas = [
        "data_coleta",
        "revenda",
        "cnpj",
        "bandeira",
        "bairro",
        "logradouro",
        "numero",
        "valor_venda",
        "unidade",
    ]
    produtos = media_por_produto(dados)["produto"].tolist()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(caminho, engine="openpyxl") as planilha:
        for produto in produtos:
            aba = dados.loc[dados["produto"] == produto, colunas].sort_values(
                ["valor_venda", "data_coleta", "revenda"],
                ascending=[True, True, True],
            )
            aba.to_excel(planilha, sheet_name=produto[:31], index=False)
    return produtos


def salvar_figura(figura, caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(caminho, dpi=120)
    return caminho

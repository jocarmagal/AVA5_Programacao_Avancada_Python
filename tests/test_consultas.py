"""Testes das consultas e da gravação da planilha."""

from pathlib import Path

import pandas as pd
import pytest

from src.consultas import extremos_por_produto, gravar_planilha, media_por_produto


def _amostra() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "produto": ["GASOLINA", "GASOLINA", "GASOLINA", "ETANOL"],
            "cnpj": ["1", "2", "3", "1"],
            "revenda": ["Posto A", "Posto B", "Posto C", "Posto A"],
            "bandeira": ["BRANCA", "IPIRANGA", "VIBRA", "BRANCA"],
            "bairro": ["CENTRO", "CENTRO", "VILA NOVA", "CENTRO"],
            "valor_venda": [5.0, 6.0, 9.0, 4.0],
            "coletas": [1, 1, 1, 1],
            "data_coleta": pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-04", "2026-01-02"]),
            "logradouro": ["Rua 1", "Rua 2", "Rua 3", "Rua 1"],
            "numero": ["10", "20", "30", "10"],
            "unidade": ["R$ / litro"] * 4,
        }
    )


def test_media_por_produto_ordena_do_menor_para_o_maior():
    tabela = media_por_produto(_amostra())

    assert list(tabela["produto"]) == ["ETANOL", "GASOLINA"]
    gasolina = tabela.loc[tabela["produto"] == "GASOLINA", "valor_medio"].iloc[0]
    assert gasolina == pytest.approx(20 / 3)


def test_extremos_separam_postos_baratos_e_caros():
    tabela = extremos_por_produto(_amostra(), n=1)
    barato = tabela.loc[(tabela["produto"] == "GASOLINA") & (tabela["grupo"] == "mais_barato")].iloc[0]
    caro = tabela.loc[(tabela["produto"] == "GASOLINA") & (tabela["grupo"] == "mais_caro")].iloc[0]

    assert barato["revenda"] == "Posto A"
    assert barato["valor_medio"] == pytest.approx(5.0)
    assert caro["revenda"] == "Posto C"
    assert caro["valor_medio"] == pytest.approx(9.0)


def test_planilha_tem_aba_por_produto_e_preco_crescente(tmp_path: Path):
    caminho = tmp_path / "precos.xlsx"
    abas = gravar_planilha(_amostra(), caminho)
    livro = pd.ExcelFile(caminho)
    etanol = pd.read_excel(livro, "ETANOL")
    gasolina = pd.read_excel(livro, "GASOLINA")

    assert abas == ["ETANOL", "GASOLINA"]
    assert livro.sheet_names == ["ETANOL", "GASOLINA"]
    assert list(gasolina["valor_venda"]) == [5.0, 6.0, 9.0]
    assert etanol["valor_venda"].tolist() == [4.0]


def test_parquet_reproduz_colunas_e_linhas(tmp_path: Path):
    origem = _amostra()[["produto", "valor_venda"]]
    caminho = tmp_path / "amostra.parquet"
    origem.to_parquet(caminho, index=False)
    lido = pd.read_parquet(caminho)

    assert list(lido.columns) == list(origem.columns)
    assert len(lido) == len(origem)
    assert lido.loc[0, "valor_venda"] == pytest.approx(5.0)

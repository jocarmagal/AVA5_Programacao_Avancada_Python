"""Diagnostica o Parquet e só depois grava o DuckDB tratado de Londrina-PR."""

from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PARQUET = RAIZ / "data" / "processed" / "precos_combustiveis.parquet"
BANCO = RAIZ / "data" / "processed" / "precos_combustiveis.duckdb"
DIAGNOSTICO = RAIZ / "reports" / "diagnostico_parquet.txt"


def diagnosticar(caminho: Path) -> None:
    """Lê o Parquet e registra ausência, duplicata e tipo antes de qualquer banco."""
    print("1. Diagnóstico do Parquet, antes de criar o DuckDB")
    dados = pd.read_parquet(caminho)
    linhas = [
        f"Arquivo: {caminho.name}",
        f"Linhas: {len(dados)}",
        f"Colunas: {dados.shape[1]}",
        f"Duplicatas exatas: {int(dados.duplicated().sum())}",
        "",
        "Ausentes e tipo por coluna:",
    ]
    for coluna in dados.columns:
        ausentes = int(dados[coluna].isna().sum())
        percentual = ausentes / len(dados)
        linhas.append(f"- {coluna}: {ausentes} ausentes ({percentual:.1%}), tipo {dados[coluna].dtype}")

    cnpj = dados["CNPJ da Revenda"].astype(str)
    produtos = ", ".join(sorted(dados["Produto"].dropna().astype(str).unique()))
    unidades = ", ".join(sorted(dados["Unidade de Medida"].dropna().astype(str).unique()))
    linhas.extend(
        [
            "",
            f"CNPJ com espaço no início: {int(cnpj.str.startswith(' ').sum())}",
            f"Data da Coleta está como {dados['Data da Coleta'].dtype}, exemplo {dados['Data da Coleta'].dropna().iloc[0]}.",
            f"Produtos encontrados: {produtos}",
            f"Unidades de medida: {unidades}",
            "Valor de Compra está vazio em todas as linhas e sai da tabela tratada.",
        ]
    )
    texto = "\n".join(linhas)
    DIAGNOSTICO.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSTICO.write_text(texto + "\n", encoding="utf-8")
    print(texto)
    print(f"Diagnóstico salvo em {DIAGNOSTICO}")


def main():
    if not PARQUET.is_file():
        raise SystemExit(
            f"Parquet não encontrado: {PARQUET}. Rode antes src/3_csv_para_parquet.py."
        )

    diagnosticar(PARQUET)

    if BANCO.exists():
        try:
            BANCO.unlink()
        except PermissionError:
            raise SystemExit(
                "O DuckDB está aberto em outro programa. Feche essa janela e rode a etapa 4 de novo."
            )

    print("2. Parquet diagnosticado. Agora o arquivo vira DuckDB.")

    print(f"Criando {BANCO.name}...")
    banco = duckdb.connect(str(BANCO))
    banco.execute(
        f"""
        CREATE TABLE precos_bruto AS
        SELECT * FROM read_parquet('{PARQUET.as_posix()}')
        """
    )
    banco.execute(
        """
        CREATE TABLE precos AS
        SELECT DISTINCT
            NULLIF(trim("Regiao - Sigla"), '') AS regiao,
            NULLIF(trim("Estado - Sigla"), '') AS estado,
            NULLIF(trim(Municipio), '') AS municipio,
            NULLIF(trim(Revenda), '') AS revenda,
            NULLIF(trim("CNPJ da Revenda"), '') AS cnpj,
            NULLIF(trim("Nome da Rua"), '') AS logradouro,
            NULLIF(trim("Numero Rua"), '') AS numero,
            NULLIF(trim(Complemento), '') AS complemento,
            NULLIF(trim(Bairro), '') AS bairro,
            NULLIF(trim(Cep), '') AS cep,
            NULLIF(trim(Produto), '') AS produto,
            try_strptime(trim("Data da Coleta"), '%d/%m/%Y')::DATE AS data_coleta,
            "Valor de Venda" AS valor_venda,
            NULLIF(trim("Unidade de Medida"), '') AS unidade,
            NULLIF(trim(Bandeira), '') AS bandeira
        FROM precos_bruto
        WHERE "Valor de Venda" IS NOT NULL
          AND upper(trim("Estado - Sigla")) = 'PR'
          AND upper(trim(Municipio)) = 'LONDRINA'
        """
    )

    bruto, tratado = banco.execute(
        """
        SELECT
            (SELECT count(*) FROM precos_bruto),
            (SELECT count(*) FROM precos)
        """
    ).fetchone()
    banco.close()

    print(f"Banco salvo em {BANCO}")
    print("Tabela precos_bruto: dados como vieram do Parquet.")
    print("Tabela precos: Paraná, município de Londrina, textos sem espaço nas bordas, data em calendário e sem duplicata.")
    print("Valor de Compra não entrou na tabela tratada: estava vazio em todas as linhas.")
    print(f"Linhas brutas: {bruto}")
    print(f"Linhas tratadas (PR / Londrina): {tratado}")


if __name__ == "__main__":
    main()

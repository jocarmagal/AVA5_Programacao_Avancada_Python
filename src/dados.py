"""Leitura da tabela tratada de Londrina, com reserva no Parquet."""

from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PARQUET = RAIZ / "data" / "processed" / "precos_combustiveis.parquet"
BANCO = RAIZ / "data" / "processed" / "precos_combustiveis.duckdb"

SQL_LONDRINA = """
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
FROM leitura
WHERE "Valor de Venda" IS NOT NULL
  AND upper(trim("Estado - Sigla")) = 'PR'
  AND upper(trim(Municipio)) = 'LONDRINA'
"""


def ler_precos() -> pd.DataFrame:
    """Devolve as coletas tratadas de Londrina-PR."""
    if BANCO.is_file():
        try:
            banco = duckdb.connect(str(BANCO), read_only=True)
        except duckdb.IOException:
            print("DuckDB em uso por outro programa. O recorte sai do Parquet.")
        else:
            try:
                return banco.execute("SELECT * FROM precos").fetchdf()
            finally:
                banco.close()

    if not PARQUET.is_file():
        raise SystemExit(
            "Não há dados tratados. Rode src/3_csv_para_parquet.py e src/4_tratamento_duckdb.py."
        )

    banco = duckdb.connect()
    banco.execute(
        f"CREATE VIEW leitura AS SELECT * FROM read_parquet('{PARQUET.as_posix()}')"
    )
    dados = banco.execute(SQL_LONDRINA).fetchdf()
    banco.close()
    return dados

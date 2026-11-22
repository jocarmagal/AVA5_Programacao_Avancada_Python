"""Transforma o CSV bruto da ANP em arquivo Parquet."""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "data" / "raw" / "Preços semestrais - AUTOMOTIVOS_2026.01.csv"
DESTINO = RAIZ / "data" / "processed" / "precos_combustiveis.parquet"


def main():
    if not ORIGEM.is_file():
        raise SystemExit(
            f"CSV não encontrado: {ORIGEM}. Rode antes src/2_extracao_data_set.py."
        )

    print(f"Lendo {ORIGEM.name}...")
    dados = pd.read_csv(ORIGEM, sep=";", decimal=",", encoding="utf-8-sig")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    dados.to_parquet(DESTINO, index=False)

    conferido = pd.read_parquet(DESTINO)
    print(f"Parquet salvo em {DESTINO}")
    print(f"Linhas: {len(conferido)}")
    print(f"Colunas: {len(conferido.columns)}")
    print(f"Tamanho: {DESTINO.stat().st_size} bytes")


if __name__ == "__main__":
    main()

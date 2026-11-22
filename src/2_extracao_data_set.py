"""Descompacta o zip da ANP e extrai o CSV para data/raw/."""

from pathlib import Path
import zipfile

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_ZIP = RAIZ / "data" / "raw" / "ca-2026-01.zip"
DESTINO = RAIZ / "data" / "raw"


def main():
    if not ARQUIVO_ZIP.is_file():
        raise SystemExit(
            f"Zip não encontrado: {ARQUIVO_ZIP}. Rode antes src/1_download_dataset.py."
        )

    print(f"Descompactando {ARQUIVO_ZIP.name}...")
    with zipfile.ZipFile(ARQUIVO_ZIP) as arquivo:
        arquivo.extractall(DESTINO)
        nomes = arquivo.namelist()

    print(f"Extraído em {DESTINO}")
    for nome in nomes:
        caminho = DESTINO / nome
        print(f" - {caminho.name} ({caminho.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

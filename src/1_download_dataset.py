"""Baixa o zip de preços de combustíveis da ANP para data/raw/."""

from pathlib import Path
import urllib.request

URL = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsas/ca/ca-2026-01.zip"
RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "data" / "raw" / "ca-2026-01.zip"


def main():
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    print("Baixando dataset da ANP...")
    print(URL)

    pedido = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pedido, timeout=120) as resposta:
        conteudo = resposta.read()

    DESTINO.write_bytes(conteudo)
    print(f"Arquivo salvo em {DESTINO}")
    print(f"Tamanho: {DESTINO.stat().st_size} bytes")


if __name__ == "__main__":
    main()

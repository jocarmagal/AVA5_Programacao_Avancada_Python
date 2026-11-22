"""Etapa 8. Planilha com uma aba por produto, do menor preço ao maior."""

import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.consultas import gravar_planilha
from src.dados import RAIZ, ler_precos

DESTINO = RAIZ / "data" / "processed" / "precos_londrina_por_produto.xlsx"


def main():
    dados = ler_precos()
    abas = gravar_planilha(dados, DESTINO)
    print(f"Planilha salva em {DESTINO}")
    print("Abas, do produto mais barato para o mais caro: " + ", ".join(abas))
    print("Dentro de cada aba, as coletas sobem do menor valor de venda para o maior.")


if __name__ == "__main__":
    main()

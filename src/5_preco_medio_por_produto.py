"""Etapa 5. Preço médio de venda por produto em Londrina."""

import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from src.consultas import media_por_produto, salvar_figura
from src.dados import RAIZ, ler_precos

DESTINO = RAIZ / "data" / "processed" / "preco_medio_por_produto.parquet"
FIGURA = RAIZ / "reports" / "figuras" / "01_preco_medio_por_produto.png"


def main():
    dados = ler_precos()
    tabela = media_por_produto(dados)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(DESTINO, index=False)
    tabela.to_csv(DESTINO.with_suffix(".csv"), index=False)

    sns.set_theme(style="whitegrid")
    figura, eixo = plt.subplots(figsize=(10, 5.5))
    sns.barplot(data=tabela, x="produto", y="valor_medio", color="#0072B2", ax=eixo)
    eixo.set_title("Preço médio de venda por produto em Londrina — janeiro de 2026")
    eixo.set_xlabel("Produto")
    eixo.set_ylabel("Preço médio (R$/litro)")
    eixo.tick_params(axis="x", rotation=20)
    for barra in eixo.patches:
        eixo.annotate(
            f"{barra.get_height():.2f}",
            (barra.get_x() + barra.get_width() / 2, barra.get_height()),
            ha="center",
            va="bottom",
            fontsize=9,
        )
    figura.tight_layout()
    salvar_figura(figura, FIGURA)
    plt.close(figura)

    print("Preço médio por produto em Londrina:")
    print(tabela.to_string(index=False, float_format=lambda valor: f"{valor:.2f}"))
    print(f"Tabela salva em {DESTINO}")
    print(f"Figura salva em {FIGURA}")


if __name__ == "__main__":
    main()

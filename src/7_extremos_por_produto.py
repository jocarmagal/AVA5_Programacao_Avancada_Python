"""Etapa 7. Dez postos mais baratos e dez mais caros de cada produto."""

import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from src.consultas import extremos_por_produto, salvar_figura
from src.dados import RAIZ, ler_precos

DESTINO = RAIZ / "data" / "processed" / "extremos_por_produto.parquet"
FIGURA = RAIZ / "reports" / "figuras" / "04_extremos_por_produto.png"


def main():
    dados = ler_precos()
    tabela = extremos_por_produto(dados, n=10)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(DESTINO, index=False)
    tabela.to_csv(DESTINO.with_suffix(".csv"), index=False)

    pontas = tabela.loc[tabela["posicao"] == 1].copy()
    pontas["grupo"] = pontas["grupo"].map({"mais_barato": "Mais barato", "mais_caro": "Mais caro"})
    sns.set_theme(style="whitegrid")
    figura, eixo = plt.subplots(figsize=(10, 5.5))
    sns.barplot(data=pontas, x="produto", y="valor_medio", hue="grupo", ax=eixo)
    eixo.set_title("Posto mais barato e mais caro de cada produto em Londrina")
    eixo.set_xlabel("Produto")
    eixo.set_ylabel("Preço médio do posto (R$/litro)")
    eixo.tick_params(axis="x", rotation=20)
    eixo.legend(title="")
    figura.tight_layout()
    salvar_figura(figura, FIGURA)
    plt.close(figura)

    print("Dez postos mais baratos e dez mais caros por produto:")
    print(tabela.to_string(index=False, float_format=lambda valor: f"{valor:.2f}"))
    print(f"Tabela salva em {DESTINO}")
    print(f"Figura salva em {FIGURA}")


if __name__ == "__main__":
    main()

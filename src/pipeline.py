"""Comando único do pipeline: etapas 1 a 8, nesta ordem."""

from __future__ import annotations

import logging
import runpy
from pathlib import Path

logger = logging.getLogger("precos_anp")

RAIZ = Path(__file__).resolve().parents[1]


class PipelineError(Exception):
    """Falha que impede a entrega do pipeline."""


def _rodar(nome: str) -> None:
    caminho = RAIZ / "src" / nome
    if not caminho.is_file():
        raise PipelineError(f"Etapa não encontrada: {caminho}")
    logger.info("Iniciando %s", nome)
    try:
        runpy.run_path(str(caminho), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise PipelineError(f"A etapa {nome} terminou com erro: {exc.code}") from exc
    except Exception as exc:
        raise PipelineError(f"A etapa {nome} falhou: {exc}") from exc
    logger.info("Concluída %s", nome)


def carregar() -> None:
    """Baixa o zip, extrai o CSV e grava o Parquet."""
    _rodar("1_download_dataset.py")
    _rodar("2_extracao_data_set.py")
    _rodar("3_csv_para_parquet.py")


def limpar() -> None:
    """Diagnostica o Parquet e só então grava o DuckDB de Londrina."""
    _rodar("4_tratamento_duckdb.py")


def engenharia() -> None:
    """Geolocaliza os postos e compara os preços por bairro."""
    _rodar("6_geolocalizacao_mapa.py")


def visualizar() -> None:
    """Gera as figuras das perguntas de produto, bairro, mapa e extremos."""
    _rodar("5_preco_medio_por_produto.py")
    engenharia()
    _rodar("7_extremos_por_produto.py")


def salvar() -> None:
    """Grava a planilha final, com uma aba por produto."""
    _rodar("8_planilha_por_produto.py")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        carregar()
        limpar()
        visualizar()
        salvar()
    except PipelineError as exc:
        logger.error("%s", exc)
        return 1
    logger.info("Pipeline concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

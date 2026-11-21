"""Pipeline de preços de combustíveis da ANP.

O comando único previsto é `python -m src.pipeline`.
As etapas abaixo serão implementadas sobre `data/raw/ca-2026-01.zip`.
"""

from __future__ import annotations


class PipelineError(Exception):
    """Falha que impede a entrega do pipeline."""


def carregar():
    """Lê o zip bruto e confere o schema do CSV da ANP."""
    raise PipelineError("carregar() ainda não foi implementado.")


def diagnosticar():
    """Resume ausência, duplicatas e categorias antes da limpeza."""
    raise PipelineError("diagnosticar() ainda não foi implementado.")


def limpar():
    """Padroniza tipos, categorias e registros duplicados."""
    raise PipelineError("limpar() ainda não foi implementado.")


def engenharia():
    """Cria variáveis derivadas para a pergunta orientadora."""
    raise PipelineError("engenharia() ainda não foi implementado.")


def visualizar():
    """Exporta os gráficos para reports/figuras/."""
    raise PipelineError("visualizar() ainda não foi implementado.")


def salvar():
    """Grava o Parquet em data/processed/ e relê o arquivo."""
    raise PipelineError("salvar() ainda não foi implementado.")


def main() -> int:
    """Ponto de entrada único. Ainda não processa os dados."""
    print("Pipeline da ANP ainda não implementado. O arquivo bruto está em data/raw/ca-2026-01.zip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

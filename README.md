# Atividade integradora — preços de combustíveis da ANP

Pipeline reprodutível, na trilha Python, do levantamento de preços de combustíveis automotivos até artefatos auditáveis. Este repositório está na estrutura pedida pela atividade. As etapas de limpeza, engenharia, gráficos, testes e relatório entram nas próximas evoluções.

## Objetivo e pergunta orientadora

Objetivo: transformar o arquivo bruto de janeiro de 2026 em um fluxo que qualquer colega reproduza do zero, com dados processados em Parquet, figuras e um relato das decisões.

Pergunta orientadora de partida: no levantamento de janeiro de 2026, como varia o preço de venda dos combustíveis automotivos entre as regiões do Brasil e entre as bandeiras dos postos?

A pergunta pode ser afinada quando o diagnóstico do arquivo estiver pronto.

## Fonte dos dados

- Arquivo versionado: `data/raw/ca-2026-01.zip`
- URL: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsas/ca/ca-2026-01.zip
- SHA-256 do zip: `a2c95e5dfa324a9d7253d4e8d53022e0c08dcc5eb6f18551527ee9f29305c54c`
- Conteúdo: `Preços semestrais - AUTOMOTIVOS_2026.01.csv` (UTF-8 com BOM, separador `;`, decimal `,`)
- Origem: Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP), dados abertos do Levantamento de Preços de Combustíveis.
- Conferência no Windows: `Get-FileHash data\raw\ca-2026-01.zip -Algorithm SHA256`

Colunas do arquivo bruto: Região, Estado, Município, Revenda, CNPJ da Revenda, Nome da Rua, Número, Complemento, Bairro, CEP, Produto, Data da Coleta, Valor de Venda, Valor de Compra, Unidade de Medida e Bandeira.

A data da coleta não traz horário. O fuso de referência do projeto é `America/Sao_Paulo`: a data civil é mantida como calendário local e, quando houver timestamp, a persistência será em UTC.

## Passo a passo de reprodução

Executar na raiz deste repositório, com Python 3.10 ou superior.

Setup:

```text
python -m venv .venv
.venv\Scripts\activate
```

Build: instalação das dependências fixadas em `requirements.txt`.

```text
python -m pip install -r requirements.txt
```

Teste e execução, nesta ordem, quando o pipeline estiver implementado:

```text
python -m pytest
python -m src.pipeline
```

O comando único previsto é `python -m src.pipeline`. Nesta versão ele ainda não processa o zip.

## Artefatos gerados

Nesta versão o artefato de dados é o zip bruto em `data/raw/`. A evolução do pipeline deve passar a gerar:

- `src/pipeline.py`, com as etapas `carregar`, `limpar`, `engenharia`, `visualizar` e `salvar`
- `data/processed/` em Parquet, relido como validação, e CSV de apoio se fizer falta
- `reports/figuras/` com pelo menos três gráficos ligados à pergunta
- `reports/relatorio.md` com método, resultados e limitações
- `tests/` com testes de transformação e um fluxo de integração em amostra pequena

`data/raw/` permanece somente leitura. Tudo o que o pipeline produzir vai para `data/processed/` e `reports/`.

## Limitações e próximos passos

O arquivo reúne preços informados no levantamento, não volume vendido. Uma linha do CSV já mostra `Valor de Compra` vazio e espaço à esquerda no CNPJ. A frequência desses casos, duplicatas, produtos e bandeiras será medida no diagnóstico, não estimada antes da leitura completa.

Próximos passos, nesta ordem:

1. Diagnosticar encoding, ausência, duplicatas, produtos e bandeiras.
2. Implementar a limpeza com as regras e o impacto registrados no relatório.
3. Gerar Parquet, figuras e testes automatizados.
4. Fechar o relatório técnico em ligação com os artefatos.

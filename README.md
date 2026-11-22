# Atividade integradora — preços de combustíveis em Londrina

Pipeline em Python que parte do levantamento da ANP, diagnostica o Parquet, trata os dados em DuckDB e responde quanto custa o combustível em Londrina.

## Objetivo e pergunta orientadora

Objetivo: entregar um fluxo reproduzível, do arquivo bruto aos gráficos, à planilha e ao relatório.

Pergunta orientadora: em janeiro de 2026, como varia o preço de venda dos combustíveis em Londrina-PR entre produtos, bairros e postos?

O recorte geográfico é o estado do Paraná e o município de Londrina. Dentro da cidade, a sigla de região da ANP é uma só (Sul). A comparação regional do trabalho usa o bairro e a posição dos postos.

## Fonte dos dados

- Arquivo versionado: `data/raw/ca-2026-01.zip`
- URL: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsas/ca/ca-2026-01.zip
- SHA-256 do zip: `a2c95e5dfa324a9d7253d4e8d53022e0c08dcc5eb6f18551527ee9f29305c54c`
- Conteúdo: `Preços semestrais - AUTOMOTIVOS_2026.01.csv` (UTF-8 com BOM, separador `;`, decimal `,`)
- Origem: Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP), dados abertos do Levantamento de Preços de Combustíveis.
- Conferência no Windows: `Get-FileHash data\raw\ca-2026-01.zip -Algorithm SHA256`

A data da coleta não traz horário. O fuso de referência é `America/Sao_Paulo`: a data permanece como calendário local e é gravada como data, sem conversão artificial para timestamp.

## Passo a passo de reprodução

Na raiz do repositório, com Python 3.10 ou superior.

Setup:

```text
python -m venv .venv
.venv\Scripts\activate
```

Build: instalar as versões fixadas em `requirements.txt`.

```text
python -m pip install -r requirements.txt
```

Teste:

```text
python -m pytest
```

Execução, em um comando:

```text
python -m src.pipeline
```

Esse comando chama, nesta ordem, `carregar` (etapas 1 a 3), `limpar` (etapa 4, com diagnóstico do Parquet antes do DuckDB), `visualizar` (etapas 5, 6 e 7) e `salvar` (etapa 8).

As etapas também rodam sozinhas:

```text
python src/1_download_dataset.py
python src/2_extracao_data_set.py
python src/3_csv_para_parquet.py
python src/4_tratamento_duckdb.py
python src/5_preco_medio_por_produto.py
python src/6_geolocalizacao_mapa.py
python src/7_extremos_por_produto.py
python src/8_planilha_por_produto.py
```

Se o arquivo DuckDB estiver aberto em outro programa, feche essa janela antes da etapa 4. As etapas 5 a 8, nesse caso, refazem o recorte de Londrina a partir do Parquet.

## Artefatos gerados

- `data/raw/ca-2026-01.zip` e o CSV extraído. A pasta bruta não é alterada pelas etapas seguintes.
- `reports/diagnostico_parquet.txt`, escrito na etapa 4 antes de criar o banco.
- `data/processed/precos_combustiveis.parquet`, relido ao final da etapa 3.
- `data/processed/precos_combustiveis.duckdb`, com `precos_bruto` (arquivo inteiro) e `precos` (Londrina tratada).
- `data/processed/preco_medio_por_produto.parquet`, `preco_medio_por_bairro.parquet`, `extremos_por_produto.parquet` e `geolocalizacao_postos.parquet`.
- `data/processed/precos_londrina_por_produto.xlsx`, uma aba por produto, do menor preço ao maior.
- `reports/figuras/01_preco_medio_por_produto.png`
- `reports/figuras/02_preco_medio_por_bairro.png`
- `reports/figuras/03_mapas_por_produto.png` e um mapa por produto (`03_mapa_etanol.png`, `03_mapa_gasolina.png`, `03_mapa_diesel.png`, `03_mapa_gasolina_aditivada.png`, `03_mapa_diesel_s10.png`)
- `reports/figuras/03_mapa_postos_londrina.html`, mapa interativo com as ruas e os postos
- `reports/figuras/04_extremos_por_produto.png`
- `reports/relatorio.md`

Decisões de limpeza, aplicadas na etapa 4 e registradas no diagnóstico:

- textos sem espaço nas bordas, inclusive o CNPJ, que vinha com espaço à esquerda em todas as linhas;
- data da coleta convertida de texto `dd/mm/aaaa` para data;
- duplicatas exatas removidas (6 no arquivo nacional);
- `Valor de Compra` ficou de fora da tabela tratada porque estava vazio em 100% das linhas;
- a tabela `precos` mantém só `PR` e `LONDRINA`.

## Limitações e próximos passos

O preço é o valor informado na coleta, não o volume vendido. O mês é só janeiro de 2026. O GNV aparece no arquivo nacional e não entra no recorte de Londrina. O complemento do endereço está ausente na maior parte do Brasil e não foi usado. A geolocalização usa o endereço do posto e, se a busca falha ou cai fora da cidade, o CEP. Dois postos no mesmo ponto podem se sobrepor no mapa.

Próximos passos possíveis: acompanhar outros meses, separar a variação dentro do próprio mês e comparar Londrina com o restante do Paraná.

# Relatório técnico — preços de combustíveis em Londrina

## Objetivo e pergunta

A pergunta é como varia o preço de venda dos combustíveis em Londrina, no Paraná, em janeiro de 2026, entre produtos, bairros e postos. O trabalho usa a trilha Python e o levantamento público da ANP.

## Dados e método

A fonte versionada é `data/raw/ca-2026-01.zip` (SHA-256 `a2c95e5dfa324a9d7253d4e8d53022e0c08dcc5eb6f18551527ee9f29305c54c`). O CSV interno usa UTF-8, separador `;` e decimal `,`. A etapa 3 grava `data/processed/precos_combustiveis.parquet` e relê o arquivo.

A etapa 4 diagnostica esse Parquet antes de abrir o DuckDB. O resultado fica em `reports/diagnostico_parquet.txt`: 422.418 linhas, 16 colunas, 6 duplicatas exatas, CNPJ com espaço inicial em todas as linhas e `Valor de Compra` vazio em 100% dos registros. A data da coleta ainda estava em texto (`02/01/2026`). O complemento estava ausente em 77,2% das linhas nacionais.

A limpeza tira o espaço das bordas, converte a data, descarta duplicata e não imputa ausência. `Valor de Compra` não segue para a tabela `precos`. Em seguida o banco fica restrito ao estado `PR` e ao município `LONDRINA`: 1.833 coletas, 24 postos e 16 bairros. A sigla de região da ANP nessas linhas é apenas `S`. Por isso a leitura regional dentro da cidade usa o bairro, e a etapa 6 coloca cada posto em latitude e longitude.

O fuso de referência é `America/Sao_Paulo`. A coleta não tem hora, então a data é guardada como calendário.

## Resultados

A Figura 1 (`reports/figuras/01_preco_medio_por_produto.png`) mostra a média do valor de venda. O etanol é o mais barato, a R$ 4,37 por litro (469 coletas). A gasolina fica em R$ 6,46 (476). O diesel fica em R$ 6,68 (200), a gasolina aditivada em R$ 6,72 (434) e o diesel S10 em R$ 7,06 (254). Os números também estão em `data/processed/preco_medio_por_produto.parquet`.

A Figura 2 (`reports/figuras/02_preco_medio_por_bairro.png`) cruza bairro e produto. Na gasolina, Vila Nova tem a menor média (R$ 6,07) e Fazenda Palhano a maior (R$ 6,91). O etanol segue o mesmo desenho: R$ 3,99 em Vila Nova e R$ 4,95 em Fazenda Palhano. Células em branco indicam produto sem coleta naquele bairro.

A imagem `reports/figuras/03_mapas_por_produto.png` mostra Londrina com as ruas e, em cada painel, o preço médio do posto para um produto. O número ao lado do ponto é esse preço, em R$/litro. Há também um arquivo por produto: `03_mapa_etanol.png`, `03_mapa_gasolina.png`, `03_mapa_diesel.png`, `03_mapa_gasolina_aditivada.png` e `03_mapa_diesel_s10.png`. As coordenadas estão em `data/processed/geolocalizacao_postos.parquet`.

A Figura 4 (`reports/figuras/04_extremos_por_produto.png`) compara, para cada produto, o posto de menor média com o de maior média. Na gasolina, a Santa Ana Energia Leste fica em R$ 6,03 e o Auto Posto Ecos em R$ 7,09. A lista dos dez postos mais baratos e dos dez mais caros, por produto, está em `data/processed/extremos_por_produto.parquet`. Quando o produto é vendido em poucos postos, as duas listas passam a compartilhar estabelecimentos do meio da distribuição.

A etapa 8 grava `data/processed/precos_londrina_por_produto.xlsx`. As abas seguem a ordem do produto mais barato ao mais caro: Etanol, Gasolina, Diesel, Gasolina aditivada e Diesel S10. Em cada aba, as coletas sobem do menor valor de venda para o maior.

## Limitações

O valor é o preço informado na coleta, não a quantidade vendida. O período é um mês. Não há GNV em Londrina nesse arquivo. A geolocalização depende do endereço publicado e pode cair no centro da via ou no CEP quando o número não é encontrado. Postos muito próximos ficam quase sobrepostos. O mapa Leaflet precisa de internet para carregar as ruas.

## Próximos passos

Repetir o mesmo recorte em outros meses, medir a variação dentro de janeiro e comparar Londrina com as outras cidades do Paraná.

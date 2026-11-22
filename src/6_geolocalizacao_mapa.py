"""Etapa 6. Preços por bairro e mapa dos postos de Londrina."""

import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.consultas import media_por_bairro, media_por_produto, salvar_figura
from src.dados import RAIZ, ler_precos

TABELA = RAIZ / "data" / "processed" / "preco_medio_por_bairro.parquet"
CACHE = RAIZ / "data" / "processed" / "geolocalizacao_postos.parquet"
FIGURA_BAIRRO = RAIZ / "reports" / "figuras" / "02_preco_medio_por_bairro.png"
FIGURA_MAPA = RAIZ / "reports" / "figuras" / "03_mapa_postos_londrina.html"
AGENTE = "atividade-integradora-ava5/1.0 (uso academico)"


def _pedir_json(url: str) -> dict | list | None:
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _dentro_de_londrina(latitude: float, longitude: float) -> bool:
    return -23.55 <= latitude <= -23.15 and -51.45 <= longitude <= -50.90


def coordenada_endereco(consulta: str) -> tuple[float, float] | None:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": consulta, "format": "jsonv2", "limit": 1, "countrycodes": "br"}
    )
    dados = _pedir_json(url)
    time.sleep(1.1)
    if not dados:
        return None
    latitude = float(dados[0]["lat"])
    longitude = float(dados[0]["lon"])
    if not _dentro_de_londrina(latitude, longitude):
        return None
    return latitude, longitude


def coordenada_cep(cep: str) -> tuple[float, float] | None:
    numeros = "".join(caractere for caractere in str(cep) if caractere.isdigit())
    if len(numeros) != 8:
        return None
    dados = _pedir_json(f"https://brasilapi.com.br/api/cep/v2/{numeros}")
    if not isinstance(dados, dict):
        return None
    coordenadas = (dados.get("location") or {}).get("coordinates") or {}
    if "latitude" not in coordenadas or "longitude" not in coordenadas:
        return None
    latitude = float(coordenadas["latitude"])
    longitude = float(coordenadas["longitude"])
    if not _dentro_de_londrina(latitude, longitude):
        return None
    return latitude, longitude


def postos_unicos(dados: pd.DataFrame) -> pd.DataFrame:
    endereco = dados.groupby("cnpj", as_index=False).agg(
        revenda=("revenda", "first"),
        logradouro=("logradouro", "first"),
        numero=("numero", "first"),
        bairro=("bairro", "first"),
        cep=("cep", "first"),
    )
    gasolina = (
        dados.loc[dados["produto"] == "GASOLINA"]
        .groupby("cnpj", as_index=False)["valor_venda"]
        .mean()
        .rename(columns={"valor_venda": "preco_gasolina"})
    )
    return endereco.merge(gasolina, on="cnpj", how="left")


def geolocalizar(postos: pd.DataFrame) -> pd.DataFrame:
    conhecidos = {}
    if CACHE.is_file():
        anterior = pd.read_parquet(CACHE)
        conhecidos = anterior.set_index("cnpj")[["latitude", "longitude", "origem"]].to_dict("index")

    latitudes = []
    longitudes = []
    origens = []
    for indice, posto in postos.reset_index(drop=True).iterrows():
        guardado = conhecidos.get(posto["cnpj"])
        if guardado and pd.notna(guardado["latitude"]):
            latitudes.append(float(guardado["latitude"]))
            longitudes.append(float(guardado["longitude"]))
            origens.append(guardado["origem"])
            continue

        consulta = ", ".join(
            str(parte)
            for parte in (posto["logradouro"], posto["numero"], posto["bairro"], "Londrina", "PR", "Brasil")
            if pd.notna(parte) and str(parte).strip()
        )
        print(f"Geolocalizando {indice + 1}/{len(postos)}: {posto['revenda']}")
        ponto = coordenada_endereco(consulta)
        origem = "nominatim"
        if ponto is None:
            ponto = coordenada_cep(posto["cep"])
            origem = "cep"
        if ponto is None:
            latitudes.append(pd.NA)
            longitudes.append(pd.NA)
            origens.append("nao_encontrado")
            continue
        latitudes.append(ponto[0])
        longitudes.append(ponto[1])
        origens.append(origem)

    resultado = postos.copy()
    resultado["latitude"] = latitudes
    resultado["longitude"] = longitudes
    resultado["origem"] = origens
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_parquet(CACHE, index=False)
    return resultado


def grafico_bairros(dados: pd.DataFrame) -> None:
    tabela = media_por_bairro(dados)
    TABELA.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(TABELA, index=False)
    tabela.to_csv(TABELA.with_suffix(".csv"), index=False)

    produtos = media_por_produto(dados)["produto"].tolist()
    matriz = tabela.pivot(index="bairro", columns="produto", values="valor_medio")
    matriz = matriz.reindex(columns=produtos)
    ordem = (
        tabela.loc[tabela["produto"] == "GASOLINA"]
        .sort_values("valor_medio")["bairro"]
        .tolist()
    )
    restantes = [bairro for bairro in matriz.index if bairro not in ordem]
    matriz = matriz.reindex(ordem + restantes)

    sns.set_theme(style="white")
    figura, eixo = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        matriz,
        annot=True,
        fmt=".2f",
        cmap="YlOrRd",
        linewidths=0.4,
        ax=eixo,
        cbar_kws={"label": "Preço médio (R$/litro)"},
    )
    eixo.set_title("Preço médio por bairro e produto em Londrina — janeiro de 2026")
    eixo.set_xlabel("Produto")
    eixo.set_ylabel("Bairro")
    figura.tight_layout()
    salvar_figura(figura, FIGURA_BAIRRO)
    plt.close(figura)
    print(f"Tabela por bairro salva em {TABELA}")
    print(f"Figura salva em {FIGURA_BAIRRO}")


def _abrir_leque(pontos: pd.DataFrame) -> pd.DataFrame:
    """Afasta pontos com a mesma coordenada para que todos apareçam no mapa."""
    ajustados = pontos.sort_values(["latitude", "longitude", "produto"]).copy()
    ajustados["_lat"] = ajustados["latitude"].round(5)
    ajustados["_lon"] = ajustados["longitude"].round(5)
    ajustados["_ordem"] = ajustados.groupby(["_lat", "_lon"]).cumcount()
    ajustados["_tamanho"] = ajustados.groupby(["_lat", "_lon"])["_ordem"].transform("size")
    raio = 0.0014
    angulo = ajustados["_ordem"] * (2 * math.pi / ajustados["_tamanho"].clip(lower=1))
    mover = ajustados["_tamanho"] > 1
    ajustados["latitude"] = ajustados["latitude"] + mover * raio * angulo.map(math.cos)
    ajustados["longitude"] = ajustados["longitude"] + mover * raio * angulo.map(math.sin)
    return ajustados.drop(columns=["_lat", "_lon", "_ordem", "_tamanho"])


def mapa(dados: pd.DataFrame, postos: pd.DataFrame) -> None:
    base = postos.dropna(subset=["latitude", "longitude"]).copy()
    if base.empty:
        raise SystemExit("Nenhum posto foi geolocalizado. O mapa não foi gerado.")

    precos = (
        dados.groupby(["cnpj", "produto"], as_index=False)
        .agg(preco=("valor_venda", "mean"), coletas=("valor_venda", "size"))
    )
    pontos = _abrir_leque(base.merge(precos, on="cnpj", how="inner"))
    registros = []
    for posto in pontos.itertuples(index=False):
        numero = "" if pd.isna(posto.numero) else str(posto.numero)
        registros.append(
            {
                "nome": posto.revenda,
                "bairro": "" if pd.isna(posto.bairro) else posto.bairro,
                "endereco": f"{posto.logradouro}, {numero}".strip(", "),
                "produto": posto.produto,
                "preco": round(float(posto.preco), 2),
                "coletas": int(posto.coletas),
                "lat": float(posto.latitude),
                "lon": float(posto.longitude),
            }
        )
    produtos = media_por_produto(dados)["produto"].tolist()
    conteudo = json.dumps({"produtos": produtos, "pontos": registros}, ensure_ascii=False)
    conteudo = conteudo.replace("<", "\\u003c")
    FIGURA_MAPA.parent.mkdir(parents=True, exist_ok=True)
    FIGURA_MAPA.write_text(_html_leaflet(conteudo), encoding="utf-8")
    print(f"Pontos no mapa: {len(registros)}, em {pontos['cnpj'].nunique()} postos")
    print(f"Coordenadas salvas em {CACHE}")
    print(f"Mapa Leaflet salvo em {FIGURA_MAPA}")


def _html_leaflet(conteudo_json: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Postos de Londrina — janeiro de 2026</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    html, body, #mapa {{ height: 100%; margin: 0; }}
    .painel {{
      background: #fff;
      padding: 10px 12px;
      line-height: 1.45;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
      font-family: "Segoe UI", sans-serif;
      font-size: 14px;
    }}
    .painel select {{
      margin-left: 6px;
      font-size: 14px;
      padding: 2px 4px;
    }}
    .amostra {{
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 6px;
    }}
  </style>
</head>
<body>
  <div id="mapa"></div>
  <script>
    const dados = {conteudo_json};
    const pontos = dados.pontos;
    const produtos = dados.produtos;
    const coresProduto = {{
      "ETANOL": "#E69F00",
      "GASOLINA": "#0072B2",
      "DIESEL": "#009E73",
      "GASOLINA ADITIVADA": "#D55E00",
      "DIESEL S10": "#CC79A7"
    }};

    const mapa = L.map("mapa");
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}", {{
      maxZoom: 19,
      attribution: "Ruas &copy; Esri, OpenStreetMap"
    }}).addTo(mapa);

    function reais(valor) {{
      return "R$ " + valor.toFixed(2).replace(".", ",");
    }}

    function corPreco(preco, minimo, maximo) {{
      const t = (preco - minimo) / (maximo - minimo || 1);
      const vermelho = Math.round(68 + t * (253 - 68));
      const verde = Math.round(1 + t * (231 - 1));
      const azul = Math.round(84 + t * (37 - 84));
      return "rgb(" + vermelho + "," + verde + "," + azul + ")";
    }}

    function escapar(valor) {{
      return String(valor ?? "").replace(/[&<>]/g, (letra) => (
        {{ "&": "&amp;", "<": "&lt;", ">": "&gt;" }}[letra]
      ));
    }}

    const camada = L.featureGroup().addTo(mapa);

    function desenhar(filtro) {{
      camada.clearLayers();
      const visiveis = filtro === "TODOS"
        ? pontos
        : pontos.filter((ponto) => ponto.produto === filtro);
      const precos = visiveis.map((ponto) => ponto.preco);
      const minimo = Math.min(...precos);
      const maximo = Math.max(...precos);

      visiveis.forEach((ponto) => {{
        const cor = filtro === "TODOS"
          ? (coresProduto[ponto.produto] || "#333333")
          : corPreco(ponto.preco, minimo, maximo);
        const marca = L.circleMarker([ponto.lat, ponto.lon], {{
          radius: 8,
          color: "#ffffff",
          weight: 1.5,
          fillColor: cor,
          fillOpacity: 0.95
        }});
        marca.bindPopup(
          "<strong>" + escapar(ponto.nome) + "</strong><br>" +
          escapar(ponto.endereco) + "<br>" +
          escapar(ponto.bairro) + "<br>" +
          escapar(ponto.produto) + ": " + reais(ponto.preco) +
          "<br>" + ponto.coletas + " coletas"
        );
        marca.bindTooltip(ponto.produto + " " + reais(ponto.preco));
        camada.addLayer(marca);
      }});

      if (visiveis.length) {{
        mapa.fitBounds(camada.getBounds().pad(0.15));
      }}
      atualizarLegenda(filtro, visiveis, minimo, maximo);
    }}

    const filtro = L.control({{ position: "topleft" }});
    filtro.onAdd = function () {{
      const caixa = L.DomUtil.create("div", "painel");
      const opcoes = ["<option value=\\"TODOS\\">Todos os produtos</option>"]
        .concat(produtos.map((produto) => (
          "<option value=\\"" + escapar(produto) + "\\">" + escapar(produto) + "</option>"
        )));
      caixa.innerHTML = "<label>Produto<select id=\\"filtro-produto\\">"
        + opcoes.join("") + "</select></label><div id=\\"resumo\\"></div>";
      L.DomEvent.disableClickPropagation(caixa);
      L.DomEvent.disableScrollPropagation(caixa);
      return caixa;
    }};
    filtro.addTo(mapa);

    const legenda = L.control({{ position: "bottomright" }});
    legenda.onAdd = function () {{
      return L.DomUtil.create("div", "painel");
    }};
    legenda.addTo(mapa);

    function atualizarLegenda(filtroAtual, visiveis, minimo, maximo) {{
      const caixa = document.querySelector(".leaflet-bottom.leaflet-right .painel");
      const resumo = document.getElementById("resumo");
      resumo.textContent = visiveis.length + " pontos no mapa";
      if (filtroAtual === "TODOS") {{
        const itens = produtos.map((produto) => {{
          const quantidade = pontos.filter((ponto) => ponto.produto === produto).length;
          return "<div><span class=\\"amostra\\" style=\\"background:"
            + (coresProduto[produto] || "#333") + "\\"></span>"
            + escapar(produto) + " (" + quantidade + ")</div>";
        }});
        caixa.innerHTML = "<b>Todos os produtos</b>" + itens.join("");
        return;
      }}
      caixa.innerHTML = "<b>" + escapar(filtroAtual) + "</b><br>Mais barato: "
        + reais(minimo) + "<br>Mais caro: " + reais(maximo)
        + "<br><span class=\\"amostra\\" style=\\"background:#440154\\"></span>barato"
        + " <span class=\\"amostra\\" style=\\"background:#fde725\\"></span>caro";
    }}

    document.getElementById("filtro-produto").addEventListener("change", (evento) => {{
      desenhar(evento.target.value);
    }});
    desenhar("TODOS");
  </script>
</body>
</html>
"""


def _tile_xy(latitude: float, longitude: float, zoom: int) -> tuple[int, int]:
    lado = 2**zoom
    coluna = int((longitude + 180) / 360 * lado)
    radiano = math.radians(latitude)
    linha = int((1 - math.log(math.tan(radiano) + 1 / math.cos(radiano)) / math.pi) / 2 * lado)
    return coluna, linha


def _pixel(latitude: float, longitude: float, zoom: int, coluna0: int, linha0: int) -> tuple[float, float]:
    lado = 2**zoom
    coluna = (longitude + 180) / 360 * lado
    radiano = math.radians(latitude)
    linha = (1 - math.log(math.tan(radiano) + 1 / math.cos(radiano)) / math.pi) / 2 * lado
    return (coluna - coluna0) * 256, (linha - linha0) * 256


def _mapa_de_ruas(postos: pd.DataFrame, zoom: int = 14) -> tuple[Image.Image, int, int, int]:
    latitudes = postos["latitude"].astype(float)
    longitudes = postos["longitude"].astype(float)
    canto_noroeste = _tile_xy(latitudes.max() + 0.012, longitudes.min() - 0.012, zoom)
    canto_sudeste = _tile_xy(latitudes.min() - 0.012, longitudes.max() + 0.012, zoom)
    coluna0, linha0 = canto_noroeste[0], canto_noroeste[1]
    coluna1, linha1 = canto_sudeste
    pasta = RAIZ / "data" / "processed" / "mapas_tiles"
    pasta.mkdir(parents=True, exist_ok=True)
    imagem = Image.new("RGB", ((coluna1 - coluna0 + 1) * 256, (linha1 - linha0 + 1) * 256), (245, 245, 245))
    for linha in range(linha0, linha1 + 1):
        for coluna in range(coluna0, coluna1 + 1):
            arquivo = pasta / f"{zoom}_{linha}_{coluna}.jpg"
            if not arquivo.is_file():
                url = (
                    "https://server.arcgisonline.com/ArcGIS/rest/services/"
                    f"World_Street_Map/MapServer/tile/{zoom}/{linha}/{coluna}"
                )
                pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(pedido, timeout=30) as resposta:
                    arquivo.write_bytes(resposta.read())
                time.sleep(0.05)
            peca = Image.open(arquivo).convert("RGB")
            imagem.paste(peca, ((coluna - coluna0) * 256, (linha - linha0) * 256))
    return imagem, coluna0, linha0, zoom


def _separar_pontos_iguais(pontos: pd.DataFrame) -> pd.DataFrame:
    ajustados = pontos.copy()
    grupos = ajustados.groupby(["latitude", "longitude"]).cumcount()
    angulo = grupos * (2 * math.pi / 8)
    ajustados["latitude"] = ajustados["latitude"] + (grupos > 0) * 0.0016 * angulo.map(math.sin)
    ajustados["longitude"] = ajustados["longitude"] + (grupos > 0) * 0.0016 * angulo.map(math.cos)
    return ajustados


def _desenhar_produto(eixo, ruas, produto, pontos, coluna0, linha0, zoom) -> None:
    eixo.imshow(ruas)
    eixo.set_xlim(0, ruas.width)
    eixo.set_ylim(ruas.height, 0)
    if pontos.empty:
        eixo.set_title(f"{produto}\nSem coleta em Londrina")
        eixo.axis("off")
        return
    pixels = [
        _pixel(latitude, longitude, zoom, coluna0, linha0)
        for latitude, longitude in zip(pontos["latitude"], pontos["longitude"])
    ]
    eixo.scatter(
        [px for px, _py in pixels],
        [py for _px, py in pixels],
        c=pontos["valor_medio"],
        cmap="viridis",
        s=55,
        edgecolor="white",
        linewidth=0.6,
        zorder=5,
    )
    for (px, py), preco in zip(pixels, pontos["valor_medio"]):
        eixo.text(
            px + 6,
            py - 6,
            f"{preco:.2f}".replace(".", ","),
            fontsize=7,
            color="#1a1a1a",
            zorder=6,
        )
    media = pontos["valor_medio"].mean()
    eixo.set_title(f"{produto} — média dos postos R$ {media:.2f}".replace(".", ","))
    eixo.axis("off")


def mapas_por_produto(dados: pd.DataFrame, postos: pd.DataFrame) -> None:
    base = postos.dropna(subset=["latitude", "longitude"]).copy()
    if base.empty:
        raise SystemExit("Nenhum posto geolocalizado para montar o mapa.")
    precos = (
        dados.groupby(["produto", "cnpj"], as_index=False)["valor_venda"]
        .mean()
        .rename(columns={"valor_venda": "valor_medio"})
    )
    ruas, coluna0, linha0, zoom = _mapa_de_ruas(base)
    produtos = media_por_produto(dados)["produto"].tolist()
    pasta = RAIZ / "reports" / "figuras"
    figura, eixos = plt.subplots(2, 3, figsize=(18, 12))
    for eixo, produto in zip(eixos.ravel(), produtos):
        pontos = base.merge(precos.loc[precos["produto"] == produto], on="cnpj", how="inner")
        pontos = _separar_pontos_iguais(pontos)
        _desenhar_produto(eixo, ruas, produto, pontos, coluna0, linha0, zoom)
        caminho = pasta / f"03_mapa_{produto.lower().replace(' ', '_')}.png"
        figura_produto, eixo_produto = plt.subplots(figsize=(10, 10))
        _desenhar_produto(eixo_produto, ruas, produto, pontos, coluna0, linha0, zoom)
        figura_produto.tight_layout()
        salvar_figura(figura_produto, caminho)
        plt.close(figura_produto)
        print(f"Mapa do produto salvo em {caminho}")
    eixos.ravel()[-1].axis("off")
    figura.suptitle("Preço médio do posto em Londrina, por produto — janeiro de 2026", fontsize=16)
    figura.tight_layout()
    conjunto = pasta / "03_mapas_por_produto.png"
    salvar_figura(figura, conjunto)
    plt.close(figura)
    print(f"Imagem com todos os produtos salva em {conjunto}")


def main():
    dados = ler_precos()
    regioes = sorted(dados["regiao"].dropna().unique())
    print(f"Região ANP neste recorte: {', '.join(regioes)}. A comparação local usa o bairro.")
    grafico_bairros(dados)
    localizados = geolocalizar(postos_unicos(dados))
    mapa(dados, localizados)
    mapas_por_produto(dados, localizados)


if __name__ == "__main__":
    main()

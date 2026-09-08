"""Dashboard de MPEs por região no estado de São Paulo.

Uso:
    streamlit run src/dashboard/app.py
"""

import json

import geobr
import pandas as pd
import plotly.express as px
import streamlit as st

from src.etl import config
from src.etl.utils import normaliza_nome

# Rampa sequencial azul (step 100 -> 700), do design system de dataviz do projeto.
RAMPA_SEQUENCIAL = [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
    "#256abf", "#184f95", "#0d366b",
]
COR_UNICA = "#2a78d6"
CORES_PORTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]

st.set_page_config(page_title="MPEs em SP", layout="wide")


@st.cache_data
def carregar_dados_processados() -> pd.DataFrame | None:
    caminho = config.PROCESSED_DIR / "mpe_por_municipio.parquet"
    if not caminho.exists():
        return None
    return pd.read_parquet(caminho)


@st.cache_data
def carregar_malha_municipios() -> pd.DataFrame:
    gdf = geobr.read_municipality(code_muni="SP", year=2020)
    gdf["nome_normalizado"] = gdf["name_muni"].map(normaliza_nome)
    return gdf


def main() -> None:
    st.title("MPEs por região — Estado de São Paulo")
    st.caption(
        "Micro e pequenas empresas ativas, a partir dos dados abertos de CNPJ "
        f"da Receita Federal ({config.REFERENCIA})."
    )

    agregado = carregar_dados_processados()
    if agregado is None:
        st.warning(
            "Nenhum dado processado encontrado. Rode o pipeline de ETL antes de "
            "abrir o dashboard:\n\n"
            "```\npython -m src.etl.download\npython -m src.etl.transform\n```"
        )
        st.stop()

    total_ativas = int(agregado["total_mpe_ativas"].sum())
    municipio_top = agregado.loc[agregado["total_mpe_ativas"].idxmax(), "municipio"]
    total_micro = int(agregado.get("Micro Empresa", pd.Series(dtype=int)).sum())
    pct_micro = (total_micro / total_ativas * 100) if total_ativas else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("MPEs ativas em SP", f"{total_ativas:,}".replace(",", "."))
    col2.metric("Município com mais MPEs", municipio_top)
    col3.metric("% Microempresas", f"{pct_micro:.1f}%")

    st.subheader("Distribuição geográfica")
    gdf = carregar_malha_municipios()
    mapa = gdf.merge(
        agregado,
        left_on="nome_normalizado",
        right_on="nome_municipio_normalizado",
        how="left",
    )
    mapa["total_mpe_ativas"] = mapa["total_mpe_ativas"].fillna(0)

    geojson = json.loads(mapa.to_json())
    fig_mapa = px.choropleth(
        mapa,
        geojson=geojson,
        locations=mapa.index,
        color="total_mpe_ativas",
        color_continuous_scale=RAMPA_SEQUENCIAL,
        hover_name="name_muni",
        labels={"total_mpe_ativas": "MPEs ativas"},
    )
    fig_mapa.update_geos(fitbounds="locations", visible=False)
    fig_mapa.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_mapa, use_container_width=True, theme="streamlit")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Top 15 municípios")
        top15 = agregado.nlargest(15, "total_mpe_ativas").sort_values("total_mpe_ativas")
        fig_top = px.bar(
            top15,
            x="total_mpe_ativas",
            y="municipio",
            orientation="h",
            color_discrete_sequence=[COR_UNICA],
            labels={"total_mpe_ativas": "MPEs ativas", "municipio": ""},
        )
        st.plotly_chart(fig_top, use_container_width=True, theme="streamlit")

    with col_b:
        st.subheader("MPEs por porte (estado)")
        colunas_porte = [c for c in config.PORTE_LABELS.values() if c in agregado.columns]
        totais_porte = agregado[colunas_porte].sum().sort_values(ascending=False)
        fig_porte = px.bar(
            totais_porte,
            color=totais_porte.index,
            color_discrete_sequence=CORES_PORTE,
            labels={"value": "MPEs ativas", "index": "Porte"},
        )
        fig_porte.update_layout(showlegend=False)
        st.plotly_chart(fig_porte, use_container_width=True, theme="streamlit")

    with st.expander("Ver dados por município"):
        st.dataframe(agregado.drop(columns=["nome_municipio_normalizado"]))


if __name__ == "__main__":
    main()

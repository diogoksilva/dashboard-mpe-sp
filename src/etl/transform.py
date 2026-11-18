"""Filtra os dados de CNPJ para SP, cruza as tabelas e agrega por município.

Uso:
    python -m src.etl.transform
"""

from typing import Callable

import pandas as pd

from . import config
from .utils import formata_nome_municipio, normaliza_nome


def _ler_particionado(
    prefixo: str,
    colunas: list[str],
    usar: list[str],
    filtro: Callable[[pd.DataFrame], pd.DataFrame],
) -> pd.DataFrame:
    """Lê em blocos, mantendo só as colunas e linhas úteis para caber na memória."""
    partes = []
    for i in range(config.ARQUIVOS_PARTICIONADOS[prefixo]):
        caminho = config.RAW_DIR / f"{prefixo}{i}"
        if not caminho.exists():
            continue
        blocos = pd.read_csv(
            caminho,
            sep=";",
            header=None,
            names=colunas,
            usecols=usar,
            encoding="latin1",
            dtype=str,
            chunksize=1_000_000,
        )
        partes.extend(filtro(bloco) for bloco in blocos)
    return pd.concat(partes, ignore_index=True)


def _ler_unico(nome: str, colunas: list[str]) -> pd.DataFrame:
    caminho = config.RAW_DIR / nome
    return pd.read_csv(
        caminho,
        sep=";",
        header=None,
        names=colunas,
        encoding="latin1",
        dtype=str,
        low_memory=False,
    )


def montar_base_sp() -> pd.DataFrame:
    estabelecimentos = _ler_particionado(
        "Estabelecimentos",
        config.COLUNAS_ESTABELECIMENTOS,
        ["cnpj_basico", "situacao_cadastral", "cnae_fiscal_principal", "uf", "municipio"],
        # Só estabelecimentos de SP e com situação cadastral ativa.
        lambda bloco: bloco[
            (bloco["uf"] == config.UF_ALVO)
            & (bloco["situacao_cadastral"] == config.SITUACAO_ATIVA)
        ],
    )

    cnpjs_sp = set(estabelecimentos["cnpj_basico"])
    empresas = _ler_particionado(
        "Empresas",
        config.COLUNAS_EMPRESAS,
        ["cnpj_basico", "porte"],
        lambda bloco: bloco[bloco["cnpj_basico"].isin(cnpjs_sp)],
    )
    municipios = _ler_unico("Municipios", config.COLUNAS_MUNICIPIOS)
    cnaes = _ler_unico("Cnaes", config.COLUNAS_CNAES)

    base = estabelecimentos.merge(empresas, on="cnpj_basico", how="left")
    base = base.merge(
        municipios,
        left_on="municipio",
        right_on="codigo_municipio_rfb",
        how="left",
    )
    base = base.merge(
        cnaes,
        left_on="cnae_fiscal_principal",
        right_on="codigo_cnae",
        how="left",
    )

    base["nome_municipio_normalizado"] = base["nome_municipio"].map(normaliza_nome)
    base["porte_label"] = base["porte"].map(config.PORTE_LABELS).fillna("Não informado")
    # MPE = microempresa (01) ou empresa de pequeno porte (03).
    base["mpe"] = base["porte"].isin(config.PORTES_MPE)

    return base


def agregar_por_municipio(base: pd.DataFrame) -> pd.DataFrame:
    ativos = base[base["mpe"]]

    agregado = (
        ativos.groupby("nome_municipio_normalizado")
        .agg(
            total_mpe_ativas=("cnpj_basico", "nunique"),
            municipio=("nome_municipio", "first"),
        )
        .reset_index()
    )

    por_porte = (
        ativos.groupby(["nome_municipio_normalizado", "porte_label"])["cnpj_basico"]
        .nunique()
        .unstack(fill_value=0)
        .reset_index()
    )

    return agregado.merge(por_porte, on="nome_municipio_normalizado", how="left")


def salvar_malha() -> pd.DataFrame:
    """Baixa a malha municipal de SP (IBGE, via geobr), simplifica e salva em GeoJSON.

    O dashboard lê esse arquivo pronto, sem depender do geobr em produção.
    Devolve a tabela código IBGE x nome normalizado, usada para casar com a RFB.
    """
    import geobr  # só é necessário no ETL

    gdf = geobr.read_municipality(code_muni=config.UF_ALVO, year=2020)
    gdf["code_muni"] = gdf["code_muni"].astype(int).astype(str)
    gdf["nome_normalizado"] = gdf["name_muni"].map(normaliza_nome)
    gdf["name_muni"] = gdf["name_muni"].map(formata_nome_municipio)
    gdf = gdf[["code_muni", "name_muni", "nome_normalizado", "geometry"]]
    gdf["geometry"] = gdf.geometry.simplify(0.005, preserve_topology=True)
    gdf.to_file(config.PROCESSED_DIR / "malha_sp.geojson", driver="GeoJSON")
    return pd.DataFrame(gdf.drop(columns="geometry"))


def executar() -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    base = montar_base_sp()
    base.to_parquet(config.PROCESSED_DIR / "estabelecimentos_sp.parquet", index=False)

    agregado = agregar_por_municipio(base)

    malha = salvar_malha()
    agregado = malha.merge(
        agregado,
        left_on="nome_normalizado",
        right_on="nome_municipio_normalizado",
        how="left",
        indicator=True,
    )
    sem_dados = agregado.loc[agregado["_merge"] == "left_only", "name_muni"].tolist()
    agregado["municipio"] = agregado["name_muni"]
    agregado = agregado.drop(
        columns=["_merge", "name_muni", "nome_normalizado", "nome_municipio_normalizado"]
    )
    colunas_num = agregado.columns.difference(["code_muni", "municipio"])
    agregado[colunas_num] = agregado[colunas_num].fillna(0).astype(int)
    agregado.to_parquet(config.PROCESSED_DIR / "mpe_por_municipio.parquet", index=False)

    print(f"{len(base):,} estabelecimentos ativos processados em SP")
    print(f"{len(agregado)} municípios no mapa; {len(sem_dados)} sem correspondência na RFB")
    if sem_dados:
        print("Sem correspondência:", ", ".join(sem_dados))


if __name__ == "__main__":
    executar()

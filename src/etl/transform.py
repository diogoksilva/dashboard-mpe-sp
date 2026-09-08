"""Filtra os dados de CNPJ para SP, cruza as tabelas e agrega por município.

Uso:
    python -m src.etl.transform
"""

import pandas as pd

from . import config
from .utils import normaliza_nome


def _ler_particionado(prefixo: str, colunas: list[str]) -> pd.DataFrame:
    partes = []
    for i in range(config.ARQUIVOS_PARTICIONADOS[prefixo]):
        caminho = config.RAW_DIR / f"{prefixo}{i}"
        if not caminho.exists():
            continue
        partes.append(
            pd.read_csv(
                caminho,
                sep=";",
                header=None,
                names=colunas,
                encoding="latin1",
                dtype=str,
                low_memory=False,
            )
        )
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
        "Estabelecimentos", config.COLUNAS_ESTABELECIMENTOS
    )
    estabelecimentos = estabelecimentos[estabelecimentos["uf"] == config.UF_ALVO].copy()

    empresas = _ler_particionado("Empresas", config.COLUNAS_EMPRESAS)
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
    base["ativa"] = base["situacao_cadastral"] == config.SITUACAO_ATIVA

    return base


def agregar_por_municipio(base: pd.DataFrame) -> pd.DataFrame:
    ativos = base[base["ativa"]]

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


def executar() -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    base = montar_base_sp()
    base.to_parquet(config.PROCESSED_DIR / "estabelecimentos_sp.parquet", index=False)

    agregado = agregar_por_municipio(base)
    agregado.to_parquet(config.PROCESSED_DIR / "mpe_por_municipio.parquet", index=False)

    print(f"{len(base):,} estabelecimentos processados em SP")
    print(f"{len(agregado)} municípios agregados")


if __name__ == "__main__":
    executar()

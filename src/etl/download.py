"""Baixa e extrai os arquivos abertos de CNPJ da Receita Federal.

Uso:
    python -m src.etl.download
"""

import shutil
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from . import config


def _download_arquivo(nome_arquivo: str, destino: Path) -> Path:
    url = f"{config.BASE_URL}/{config.REFERENCIA}/{nome_arquivo}.zip"
    caminho_zip = destino / f"{nome_arquivo}.zip"

    if caminho_zip.exists():
        print(f"[skip] {nome_arquivo}.zip já existe")
        return caminho_zip

    caminho_parcial = caminho_zip.with_suffix(".zip.part")
    autenticacao = (config.TOKEN_COMPARTILHAMENTO, "")
    with requests.get(url, stream=True, timeout=60, auth=autenticacao) as resposta:
        resposta.raise_for_status()
        total = int(resposta.headers.get("content-length", 0))
        with open(caminho_parcial, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=nome_arquivo
        ) as barra:
            for chunk in resposta.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                barra.update(len(chunk))

    caminho_parcial.replace(caminho_zip)
    return caminho_zip


def _extrair(caminho_zip: Path, destino: Path, nome_final: str) -> None:
    """Extrai o único arquivo do zip com um nome estável (ex.: Empresas0)."""
    with zipfile.ZipFile(caminho_zip) as z:
        membro = z.namelist()[0]
        with z.open(membro) as origem, open(destino / nome_final, "wb") as saida:
            shutil.copyfileobj(origem, saida)


def baixar_todos() -> None:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    nomes = list(config.ARQUIVOS_UNICOS)
    for prefixo, partes in config.ARQUIVOS_PARTICIONADOS.items():
        nomes.extend(f"{prefixo}{i}" for i in range(partes))

    for nome in nomes:
        try:
            caminho_zip = _download_arquivo(nome, config.RAW_DIR)
            _extrair(caminho_zip, config.RAW_DIR, nome)
        except requests.HTTPError as exc:
            print(f"[erro] {nome}: {exc}. Confira o nome/partição na listagem da RFB.")


if __name__ == "__main__":
    baixar_todos()

"""Baixa e extrai os arquivos abertos de CNPJ da Receita Federal.

Uso:
    python -m src.etl.download
"""

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

    with requests.get(url, stream=True, timeout=60) as resposta:
        resposta.raise_for_status()
        total = int(resposta.headers.get("content-length", 0))
        with open(caminho_zip, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=nome_arquivo
        ) as barra:
            for chunk in resposta.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                barra.update(len(chunk))

    return caminho_zip


def _extrair(caminho_zip: Path, destino: Path) -> None:
    with zipfile.ZipFile(caminho_zip) as z:
        z.extractall(destino)


def baixar_todos() -> None:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    nomes = list(config.ARQUIVOS_UNICOS)
    for prefixo, partes in config.ARQUIVOS_PARTICIONADOS.items():
        nomes.extend(f"{prefixo}{i}" for i in range(partes))

    for nome in nomes:
        try:
            caminho_zip = _download_arquivo(nome, config.RAW_DIR)
            _extrair(caminho_zip, config.RAW_DIR)
        except requests.HTTPError as exc:
            print(f"[erro] {nome}: {exc}. Confira o nome/partição na listagem da RFB.")


if __name__ == "__main__":
    baixar_todos()

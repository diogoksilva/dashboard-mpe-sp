import unicodedata


def normaliza_nome(nome: str) -> str:
    """Remove acentos e padroniza caixa para casar nomes de município entre fontes."""
    nome = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    # A RFB às vezes usa hífen onde o IBGE usa espaço (ex.: "BIRITIBA-MIRIM").
    nome = nome.replace("-", " ")
    return " ".join(nome.split()).upper()


_MINUSCULAS = {"da", "das", "de", "do", "dos", "e"}


def formata_nome_municipio(nome: str) -> str:
    """'São Bernardo Do Campo' -> 'São Bernardo do Campo' (a malha do geobr vem com tudo capitalizado)."""
    palavras = str(nome).split()
    return " ".join(
        p.lower() if i > 0 and p.lower() in _MINUSCULAS else p for i, p in enumerate(palavras)
    )

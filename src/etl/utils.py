import unicodedata


def normaliza_nome(nome: str) -> str:
    """Remove acentos e padroniza caixa para casar nomes de município entre fontes."""
    nome = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    return nome.strip().upper()

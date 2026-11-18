"""Constantes e schemas do pipeline de ETL de dados abertos de CNPJ."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

UF_ALVO = "SP"

# Atualize para o mês/ano da base que deseja baixar.
# Pastas disponíveis: https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9
BASE_URL = "https://arquivos.receitafederal.gov.br/public.php/webdav"
# Token público do compartilhamento, usado como usuário (sem senha) no WebDAV.
TOKEN_COMPARTILHAMENTO = "YggdBLfdninEJX9"
REFERENCIA = "2026-10"  # AAAA-MM

# Grupos de arquivo e quantidade de partes (0 a N-1) de cada um na pasta da RFB.
# Os nomes/partes mudam ocasionalmente; conferir na listagem antes de rodar o download.
ARQUIVOS_PARTICIONADOS = {
    "Empresas": 10,
    "Estabelecimentos": 10,
}
ARQUIVOS_UNICOS = [
    "Cnaes",
    "Municipios",
]

# Layout oficial dos arquivos (separador ';', sem cabeçalho, encoding latin1)
COLUNAS_EMPRESAS = [
    "cnpj_basico",
    "razao_social",
    "natureza_juridica",
    "qualificacao_responsavel",
    "capital_social",
    "porte",
    "ente_federativo_responsavel",
]

COLUNAS_ESTABELECIMENTOS = [
    "cnpj_basico",
    "cnpj_ordem",
    "cnpj_dv",
    "identificador_matriz_filial",
    "nome_fantasia",
    "situacao_cadastral",
    "data_situacao_cadastral",
    "motivo_situacao_cadastral",
    "nome_cidade_exterior",
    "pais",
    "data_inicio_atividade",
    "cnae_fiscal_principal",
    "cnae_fiscal_secundaria",
    "tipo_logradouro",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cep",
    "uf",
    "municipio",
    "ddd1",
    "telefone1",
    "ddd2",
    "telefone2",
    "ddd_fax",
    "fax",
    "correio_eletronico",
    "situacao_especial",
    "data_situacao_especial",
]

COLUNAS_MUNICIPIOS = ["codigo_municipio_rfb", "nome_municipio"]
COLUNAS_CNAES = ["codigo_cnae", "descricao_cnae"]

# Códigos oficiais de situação cadastral (layout RFB)
SITUACAO_ATIVA = "02"

# Portes considerados MPE: microempresa e empresa de pequeno porte.
PORTES_MPE = ["01", "03"]

PORTE_LABELS = {
    "00": "Não informado",
    "01": "Micro Empresa",
    "03": "Empresa de Pequeno Porte",
    "05": "Demais",
}

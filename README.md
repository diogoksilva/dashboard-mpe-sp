# Dashboard de MPEs por Região — Estado de São Paulo

Dashboard interativo que mapeia a distribuição de micro e pequenas empresas
(MPEs) ativas pelos municípios do estado de São Paulo, a partir da base
pública de CNPJ da Receita Federal.

## Fontes de dados

- **Dados Abertos do CNPJ** (Receita Federal) — cadastro de empresas e
  estabelecimentos, atualizado mensalmente.
  https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj
- **Malha municipal do IBGE**, via pacote [`geobr`](https://github.com/ipeaGIT/geobr).

## Estrutura do projeto

```
dashboard-mpe-sp/
├── data/
│   ├── raw/          # arquivos brutos baixados da RFB (não versionado)
│   └── processed/    # parquet tratado, usado pelo dashboard (não versionado)
├── src/
│   ├── etl/
│   │   ├── config.py      # constantes, paths e schema dos arquivos da RFB
│   │   ├── download.py    # baixa e extrai os arquivos abertos de CNPJ
│   │   ├── transform.py   # filtra SP, cruza tabelas e agrega por município
│   │   └── utils.py       # normalização de nomes de município
│   └── dashboard/
│       └── app.py         # aplicação Streamlit
└── notebooks/         # exploração ad-hoc
```

## Como rodar

1. Crie um ambiente virtual e instale as dependências:

   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-etl.txt
   ```

2. Confira no [compartilhamento de dados abertos do CNPJ](https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9)
   qual é o mês de referência mais recente e ajuste `REFERENCIA` em
   `src/etl/config.py` se necessário.

3. Baixe e processe os dados (a base completa de estabelecimentos é grande;
   o download pode demorar):

   ```
   python -m src.etl.download
   python -m src.etl.transform
   ```

4. Rode o dashboard:

   ```
   streamlit run src/dashboard/app.py
   ```

## Roadmap

- [ ] Filtros por setor (CNAE) e porte no próprio dashboard
- [ ] Série histórica de abertura/fechamento de empresas por município
- [ ] Deploy no Streamlit Community Cloud
- [ ] Expandir para outras UFs

## Licença

MIT.

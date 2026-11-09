# Duas escolas, um exame: desigualdade de desempenho no ENEM entre redes pública e privada (2009–2015)

[![Licença: MIT](https://img.shields.io/badge/c%C3%B3digo-MIT-blue.svg)](LICENSE)
[![Texto e dados: CC BY 4.0](https://img.shields.io/badge/texto%20e%20dados-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB.svg)](requirements.txt)
[![FAIR](https://img.shields.io/badge/FAIR-compliant-2b8a3e.svg)](#princípios-fair)
[![Artigo](https://img.shields.io/badge/artigo-GitHub%20Pages-1F5F8B.svg)](https://gabryelduartepessanha.github.io/enem-escolas-brasil/)

**Alunos:** Gabryel Duarte Pessanha e Esther Corte Real
**Professor:** Alexandre Louzada
**Instituição:** Unilasalle — Bacharelado em Sistemas de Informação, 6º período
**Disciplina:** Linguagem de Programação — Análise e Visualização de Dados com Python (Projeto Final, 2026/2)

> **Artigo publicado:** https://gabryelduartepessanha.github.io/enem-escolas-brasil/

## Resumo executivo

Analisamos os **Microdados do ENEM por Escola** (INEP, 2005–2015) para investigar a desigualdade de desempenho entre escolas públicas e privadas. Um pipeline determinístico em Python trata o arquivo original (ISO-8859-1, separador `;`, tipos inconsistentes) e produz uma base de **104.307 registros escola × ano** (25.022 escolas, 2009–2015). Principais achados:

- **RQ1 – Evolução:** a diferença entre as redes ficou entre **86 e 98 pontos** em todo o período, sem convergência. Escolas **federais** são a exceção: 55% delas superam a escola privada mediana.
- **RQ2 – Contexto:** o nível socioeconômico dos alunos (INSE) é o indicador mais associado à nota (**ρ = 0,78**); fixado o grupo INSE, a vantagem privada cai para 26–40 pontos. Formação docente tem associação moderada dentro de cada rede (ρ ≈ 0,35).
- **RQ3 – Território:** diferenças regionais (≤ 30 pontos) e urbano/rural (≤ 6 pontos) são bem menores que a diferença entre redes; o abandono escolar associa-se negativamente à nota (ρ = −0,34).

**Palavras-chave:** ENEM; desigualdade educacional; nível socioeconômico; dados abertos; análise exploratória de dados; Python; FAIR.

## Fonte dos dados

- **INEP — Microdados do ENEM por Escola 2005–2015** (link perene):
  https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem-por-escola
- Uma cópia do arquivo bruto está versionada em `data/raw/MICRODADOS_ENEM_ESCOLA.csv.gz` (6 MB) para garantir reprodutibilidade.
- O dicionário completo das variáveis está em [`data/data_dictionary.md`](data/data_dictionary.md).

## Estrutura do repositório

```
enem-escolas-brasil/
├── README.md                     # este arquivo
├── LICENSE                       # MIT (código) + CC BY 4.0 (texto e dados)
├── requirements.txt              # dependências com versões congeladas
├── .gitignore
├── data/
│   ├── raw/MICRODADOS_ENEM_ESCOLA.csv.gz      # dado bruto original (INEP)
│   ├── processed/enem_escolas.parquet         # base tratada (e cópia .csv.gz)
│   └── data_dictionary.md                     # metadados FAIR
├── notebooks/
│   └── analise_exploratoria.ipynb             # EDA, validação e prototipação (executado)
├── src/
│   ├── __init__.py
│   ├── etl.py                                 # pipeline: extract → transform → load + agregações
│   ├── figuras.py                             # gera figuras PNG/Plotly e resumo.json
│   ├── build_artigo.py                        # monta docs/index.html a partir do template
│   └── template_artigo.html
└── docs/                                      # artigo publicado via GitHub Pages
    ├── index.html
    └── assets/                                # figuras estáticas, gráficos Plotly (JSON), resumo.json
```

## Como reproduzir

```bash
git clone https://github.com/gabryelduartepessanha/enem-escolas-brasil.git
cd enem-escolas-brasil
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.etl            # 1. lê data/raw, limpa e salva data/processed (≈1 min)
python -m src.figuras        # 2. gera docs/assets/*.png, *.json e resumo.json (≈2 min)
python -m src.build_artigo   # 3. monta docs/index.html com os números e gráficos atualizados

# opcional: reexecutar o notebook de exploração
jupyter nbconvert --execute --to notebook --inplace notebooks/analise_exploratoria.ipynb
```

Para ver o artigo localmente, abra `docs/index.html` no navegador.

### Publicação no GitHub Pages

Em *Settings → Pages*: **Deploy from a branch**, branch `main`, pasta `/docs`.

## Decisões de tratamento (resumo)

| Situação | Decisão |
|---|---|
| Anos 2005–2008 sem médias por área (escala antiga do ENEM) | Excluídos (67.998 linhas) |
| `INSE` só em 2015; `PC_FORMACAO_DOCENTE` só em 2013–2015 | Mantidos como `NaN` (ausência estrutural) |
| `INSE` textual ("Grupo 1"…"Grupo 6") | Categoria ordinal + coluna numérica `inse_num` |
| Participantes > matrículas (762 linhas) | Mantidos e marcados em `flag_inconsistencia` |
| Médias agregadas | Sempre ponderadas pelo nº de participantes |

O ETL registra cada etapa no log e todas as exclusões estão descritas na tabela acima.

## Princípios FAIR

| Princípio | Como atendemos |
|---|---|
| **Findable** | README com resumo, palavras-chave e link perene para a fonte; autoria/disciplina/instituição em todos os artefatos |
| **Accessible** | Repositório público, dados brutos e processados sem autenticação; artigo responsivo no GitHub Pages |
| **Interoperable** | `data_dictionary.md`; base em Parquet e CSV.gz (UTF-8); JSON das figuras Plotly |
| **Reusable** | Licenças MIT e CC BY 4.0; `requirements.txt` congelado; pipeline em três comandos |

## Licença

Código: [MIT](LICENSE). Texto do artigo, figuras e dados derivados: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Dados brutos: INEP/MEC, domínio público.

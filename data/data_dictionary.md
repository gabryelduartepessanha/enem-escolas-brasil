# Dicionário de dados — `data/processed/enem_escolas.parquet`

**Projeto:** Desigualdade de desempenho no ENEM entre redes pública e privada (2009–2015)
**Alunos:** Gabryel Duarte Pessanha e Esther Corte Real
**Professor:** Alexandre Louzada
**Instituição:** Unilasalle — Bacharelado em Sistemas de Informação, 6º período
**Fonte primária:** INEP, *Microdados do ENEM por Escola 2005–2015*
(https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem-por-escola)
**Granularidade:** uma linha por escola × ano. **Registros:** 104.307 (2009–2015). **Codificação:** UTF-8.

O arquivo bruto (`data/raw/MICRODADOS_ENEM_ESCOLA.csv.gz`) mantém os nomes originais do INEP (coluna "Origem"). A tabela abaixo descreve a base **processada** gerada por `src/etl.py`.

## Identificação e contexto

| Variável | Origem (INEP) | Tipo | Formato / domínio | Significado |
|---|---|---|---|---|
| `ano` | `NU_ANO` | int16 | 2009–2015 | Ano de aplicação do ENEM |
| `regiao` | derivada de `SG_UF_ESCOLA` | category | Norte, Nordeste, Centro-Oeste, Sudeste, Sul | Grande região geográfica (IBGE) |
| `uf` | `SG_UF_ESCOLA` | string | sigla de 2 letras | Unidade da Federação da escola |
| `co_municipio` | `CO_MUNICIPIO_ESCOLA` | string | código IBGE de 7 dígitos | Município da escola |
| `municipio` | `NO_MUNICIPIO_ESCOLA` | string | texto | Nome do município |
| `co_escola` | `CO_ESCOLA_EDUCACENSO` | string | código de 8 dígitos | Código da escola no Censo Escolar (chave de identificação) |
| `escola` | `NO_ESCOLA_EDUCACENSO` | string | texto | Nome da escola |
| `dependencia` | `TP_DEPENDENCIA_ADM_ESCOLA` | category | Federal (1), Estadual (2), Municipal (3), Privada (4) | Dependência administrativa |
| `rede` | derivada de `dependencia` | string | Pública, Privada | Pública = Federal + Estadual + Municipal |
| `localizacao` | `TP_LOCALIZACAO_ESCOLA` | category | Urbana (1), Rural (2) | Zona de localização |
| `porte` | `PORTE_ESCOLA` | category | "De 1 a 30 alunos", "De 31 a 60 alunos", "De 61 a 90 alunos", "Maior que 90 alunos" | Porte pelo nº de concluintes do ensino médio |

## Participação

| Variável | Origem (INEP) | Tipo | Formato / domínio | Significado |
|---|---|---|---|---|
| `matriculas` | `NU_MATRICULAS` | int64 | ≥ 1 | Matrículas na 3ª série do ensino médio regular (Censo Escolar) |
| `participantes` | `NU_PARTICIPANTES` | int64 | ≥ 1 | Concluintes da escola que fizeram o ENEM |
| `taxa_participacao` | `NU_TAXA_PARTICIPACAO` | float64 | 0–100 (%) | `participantes / matriculas × 100` conforme INEP |

## Desempenho (escala TRI do ENEM, ~0–1000)

| Variável | Origem (INEP) | Tipo | Formato / domínio | Significado |
|---|---|---|---|---|
| `media_cn` | `NU_MEDIA_CN` | float64 | 2 casas decimais | Média da escola em Ciências da Natureza |
| `media_ch` | `NU_MEDIA_CH` | float64 | 2 casas decimais | Média em Ciências Humanas |
| `media_lp` | `NU_MEDIA_LP` | float64 | 2 casas decimais | Média em Linguagens e Códigos |
| `media_mt` | `NU_MEDIA_MT` | float64 | 2 casas decimais | Média em Matemática |
| `media_red` | `NU_MEDIA_RED` | float64 | 2 casas decimais | Média em Redação |
| `media_geral` | **derivada** | float64 | 2 casas decimais | Média aritmética simples das cinco áreas acima |

## Indicadores de contexto (Censo Escolar / INEP)

| Variável | Origem (INEP) | Tipo | Formato / domínio | Significado | Cobertura |
|---|---|---|---|---|---|
| `inse` | `INSE` | category (ordinal) | "Grupo 1" … "Grupo 6" | Indicador de Nível Socioeconômico dos alunos; 1 = mais baixo, 6 = mais alto | apenas 2015 |
| `inse_num` | **derivada** de `inse` | Float64 | 1–6 | Versão numérica ordinal do INSE para correlações | apenas 2015 |
| `pct_formacao_docente` | `PC_FORMACAO_DOCENTE` | float64 | 0–100 (%) | Percentual de docentes com formação adequada às disciplinas que lecionam | 2013–2015 |
| `taxa_aprovacao` | `NU_TAXA_APROVACAO` | float64 | 0–100 (%) | Taxa de aprovação no ensino médio | 2009–2015 (≈0,8% ausentes) |
| `taxa_reprovacao` | `NU_TAXA_REPROVACAO` | float64 | 0–100 (%) | Taxa de reprovação no ensino médio | idem |
| `taxa_abandono` | `NU_TAXA_ABANDONO` | float64 | 0–100 (%) | Taxa de abandono no ensino médio | idem |

## Controle de qualidade

| Variável | Tipo | Significado |
|---|---|---|
| `flag_inconsistencia` | bool | `True` quando `participantes > matriculas` ou `taxa_participacao > 100` (762 linhas). Mantidas para rastreabilidade; podem ser filtradas pelo usuário. |

## Colunas do arquivo bruto não carregadas na base processada

- `NU_PARTICIPANTES_NEC_ESP` (participantes com necessidades especiais) — não usada nas perguntas de pesquisa.
- `NU_MEDIA_OBJ`, `NU_MEDIA_TOT` (média objetiva e total do ENEM antigo) — só preenchidas em 2005–2008, fora do recorte.
- `NU_TAXA_PERMANENCIA` — só 2014–2015 e redundante com as taxas de rendimento.
- `CO_UF_ESCOLA` — redundante com `uf`.

## Valores ausentes

`NaN` significa **não coletado naquele ano** (ausência estrutural), nunca zero. Nenhuma imputação foi aplicada. As 67.998 linhas de 2005–2008, sem médias por área, foram excluídas no ETL (ver `src/etl.py`, função `transform`).

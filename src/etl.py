from __future__ import annotations

import gzip
import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("etl")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "MICRODADOS_ENEM_ESCOLA.csv.gz"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_FILE = PROCESSED_DIR / "enem_escolas.parquet"
PROCESSED_CSV = PROCESSED_DIR / "enem_escolas.csv.gz"


DEPENDENCIA = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
LOCALIZACAO = {1: "Urbana", 2: "Rural"}
REGIAO_UF = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "Norte"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Centro-Oeste"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sul"),
}
COLUNAS_NOTA = ["media_cn", "media_ch", "media_lp", "media_mt", "media_red"]

RENAME = {
    "NU_ANO": "ano",
    "CO_UF_ESCOLA": "co_uf",
    "SG_UF_ESCOLA": "uf",
    "CO_MUNICIPIO_ESCOLA": "co_municipio",
    "NO_MUNICIPIO_ESCOLA": "municipio",
    "CO_ESCOLA_EDUCACENSO": "co_escola",
    "NO_ESCOLA_EDUCACENSO": "escola",
    "TP_DEPENDENCIA_ADM_ESCOLA": "dependencia",
    "TP_LOCALIZACAO_ESCOLA": "localizacao",
    "NU_MATRICULAS": "matriculas",
    "NU_PARTICIPANTES_NEC_ESP": "participantes_nec_esp",
    "NU_PARTICIPANTES": "participantes",
    "NU_TAXA_PARTICIPACAO": "taxa_participacao",
    "NU_MEDIA_CN": "media_cn",
    "NU_MEDIA_CH": "media_ch",
    "NU_MEDIA_LP": "media_lp",
    "NU_MEDIA_MT": "media_mt",
    "NU_MEDIA_RED": "media_red",
    "NU_MEDIA_OBJ": "media_obj",
    "NU_MEDIA_TOT": "media_tot",
    "INSE": "inse",
    "PC_FORMACAO_DOCENTE": "pct_formacao_docente",
    "NU_TAXA_PERMANENCIA": "taxa_permanencia",
    "NU_TAXA_APROVACAO": "taxa_aprovacao",
    "NU_TAXA_REPROVACAO": "taxa_reprovacao",
    "NU_TAXA_ABANDONO": "taxa_abandono",
    "PORTE_ESCOLA": "porte",
}


def extract(path: Path = RAW_FILE) -> pd.DataFrame:
    log.info("Lendo arquivo bruto: %s", path.name)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="latin-1") as fh:
        df = pd.read_csv(fh, sep=";", decimal=".", dtype=str, na_values=["", " "])
    log.info("Linhas brutas: %s | Colunas: %s", f"{len(df):,}", df.shape[1])
    return df


def _to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False), errors="coerce")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=RENAME).copy()

    num_cols = [c for c in RENAME.values() if c not in
                {"uf", "municipio", "escola", "porte", "co_escola", "co_municipio", "co_uf", "inse"}]
    df = _to_numeric(df, num_cols)


    df["ano"] = df["ano"].astype("Int16")
    df["dependencia_cod"] = df["dependencia"].astype("Int8")
    df["dependencia"] = df["dependencia_cod"].map(DEPENDENCIA).astype("category")
    df["localizacao"] = df["localizacao"].astype("Int8").map(LOCALIZACAO).astype("category")
    df["rede"] = np.where(df["dependencia"] == "Privada", "Privada", "Pública")
    df["regiao"] = df["uf"].map(REGIAO_UF).astype("category")
    df["porte"] = df["porte"].astype("category")
    df["municipio"] = df["municipio"].str.strip()
    df["escola"] = df["escola"].str.strip()


    df["inse"] = pd.Categorical(df["inse"].str.strip(),
                                categories=[f"Grupo {i}" for i in range(1, 7)], ordered=True)
    df["inse_num"] = df["inse"].cat.codes.replace(-1, np.nan).astype("Float64") + 1


    df["media_geral"] = df[COLUNAS_NOTA].mean(axis=1, skipna=False).round(2)


    df["tem_notas"] = df[COLUNAS_NOTA].notna().all(axis=1)


    n_antes = len(df)
    df = df[df["tem_notas"]].copy()
    log.info("Registros com notas completas: %s (removidos %s sem notas — anos 2005-2008)",
             f"{len(df):,}", f"{n_antes - len(df):,}")


    mask_bad = (df["participantes"] > df["matriculas"]) | (df["taxa_participacao"] > 100)
    log.info("Inconsistências participantes>matriculas: %s (mantidas e marcadas)", int(mask_bad.sum()))
    df["flag_inconsistencia"] = mask_bad

    ordem = ["ano", "regiao", "uf", "co_municipio", "municipio", "co_escola", "escola",
             "dependencia", "rede", "localizacao", "porte", "matriculas", "participantes",
             "taxa_participacao", *COLUNAS_NOTA, "media_geral", "inse", "inse_num",
             "pct_formacao_docente", "taxa_aprovacao", "taxa_reprovacao", "taxa_abandono",
             "flag_inconsistencia"]
    return df[ordem].sort_values(["ano", "uf", "escola"]).reset_index(drop=True)


def load(df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_FILE, index=False)
    df.to_csv(PROCESSED_CSV, index=False, compression="gzip")
    log.info("Salvo: %s e %s", PROCESSED_FILE.name, PROCESSED_CSV.name)


def load_processed() -> pd.DataFrame:
    if not PROCESSED_FILE.exists():
        run()
    return pd.read_parquet(PROCESSED_FILE)


def media_por(df: pd.DataFrame, por: list[str], col: str = "media_geral") -> pd.DataFrame:
    g = df.dropna(subset=[col, "participantes"]).groupby(por, observed=True)
    out = g.apply(lambda x: np.average(x[col], weights=x["participantes"]),
                  include_groups=False).rename(col).reset_index()
    out["n_escolas"] = g.size().values
    return out


def correlacoes(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["media_geral", *COLUNAS_NOTA, "inse_num", "pct_formacao_docente",
            "taxa_aprovacao", "taxa_abandono", "taxa_participacao"]
    return df[cols].corr(method="spearman").round(3)


def run() -> pd.DataFrame:
    df = transform(extract())
    load(df)
    return df


if __name__ == "__main__":
    run()

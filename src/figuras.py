from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from src.etl import COLUNAS_NOTA, correlacoes, load_processed, media_por

ASSETS = Path(__file__).resolve().parents[1] / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


COR = {"Pública": "#1F5F8B", "Privada": "#C8781A", "Federal": "#1B7F5C",
       "Estadual": "#1F5F8B", "Municipal": "#7A6AB3", "Urbana": "#1F5F8B", "Rural": "#C8781A"}
AREAS = {"media_cn": "Ciências da Natureza", "media_ch": "Ciências Humanas",
         "media_lp": "Linguagens e Códigos", "media_mt": "Matemática", "media_red": "Redação"}
FONTE = "Fonte: INEP, ENEM por Escola 2009-2015. Médias ponderadas por nº de participantes."

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 160})

tpl = go.layout.Template()
tpl.layout = dict(font=dict(family="Inter, Segoe UI, sans-serif", size=13),
                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  margin=dict(l=50, r=20, t=50, b=50), hoverlabel=dict(font_size=12),
                  xaxis=dict(gridcolor="rgba(128,128,128,.18)"), yaxis=dict(gridcolor="rgba(128,128,128,.18)"))
pio.templates["artigo"] = tpl
pio.templates.default = "artigo"
resumo: dict = {}


def salvar_plotly(fig: go.Figure, nome: str) -> None:
    (ASSETS / f"{nome}.json").write_text(fig.to_json(), encoding="utf-8")


def rq1(df: pd.DataFrame) -> None:
    ev = media_por(df, ["ano", "rede"])
    piv = ev.pivot(index="ano", columns="rede", values="media_geral")
    piv["gap"] = piv["Privada"] - piv["Pública"]
    resumo["rq1_evolucao"] = piv.round(1).reset_index().to_dict("records")
    resumo["rq1_gap_min"] = round(float(piv["gap"].min()), 1)
    resumo["rq1_gap_max"] = round(float(piv["gap"].max()), 1)
    resumo["rq1_gap_2015"] = round(float(piv.loc[2015, "gap"]), 1)


    fig, ax = plt.subplots(figsize=(7.2, 4))
    for rede in ["Privada", "Pública"]:
        ax.plot(piv.index, piv[rede], marker="o", lw=2.2, color=COR[rede], label=rede)
        for a, v in piv[rede].items():
            ax.annotate(f"{v:.0f}", (a, v), textcoords="offset points", xytext=(0, 7),
                        ha="center", fontsize=8, color=COR[rede])
    ax.set_title("Média geral no ENEM por rede de ensino (2009-2015)", loc="left", fontweight="bold")
    ax.set_ylabel("Média geral das 5 áreas"); ax.set_xlabel("")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=.3)
    fig.text(0.01, -0.02, FONTE, fontsize=7.5, color="gray"); fig.tight_layout()
    fig.savefig(ASSETS / "fig1_evolucao_rede.png", bbox_inches="tight"); plt.close(fig)


    ev2 = pd.concat([media_por(df, ["ano", "dependencia"], c).assign(area=AREAS[c]).rename(columns={c: "media"})
                     for c in COLUNAS_NOTA])
    fig = px.line(ev2, x="ano", y="media", color="dependencia", facet_col="area", facet_col_wrap=3,
                  markers=True, color_discrete_map=COR, height=560, facet_col_spacing=0.07, facet_row_spacing=0.12,
                  labels={"ano": "", "media": "Média ponderada", "dependencia": "Dependência"},
                  title="Evolução das médias por área e dependência administrativa")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_yaxes(matches=None, showticklabels=True)
    salvar_plotly(fig, "plot1_evolucao_area")


    d15 = df[df.ano == 2015]
    fig = px.box(d15, x="dependencia", y="media_geral", color="dependencia", color_discrete_map=COR,
                 points=False, category_orders={"dependencia": ["Municipal", "Estadual", "Privada", "Federal"]},
                 labels={"media_geral": "Média geral da escola", "dependencia": ""},
                 title="Distribuição da média geral das escolas em 2015", height=430)
    fig.update_layout(showlegend=False)
    salvar_plotly(fig, "plot2_box_2015")
    q = d15.groupby("dependencia", observed=True)["media_geral"].quantile([.25, .5, .75]).unstack().round(1)
    resumo["rq1_quartis_2015"] = q.reset_index().to_dict("records")
    resumo["rq1_n_2015"] = d15.groupby("dependencia", observed=True).size().to_dict()

    med_priv = d15.loc[d15.rede == "Privada", "media_geral"].median()
    resumo["rq1_pct_pub_acima_med_priv"] = round(100 * float((d15.loc[d15.rede == "Pública", "media_geral"] > med_priv).mean()), 1)
    resumo["rq1_pct_fed_acima_med_priv"] = round(100 * float((d15.loc[d15.dependencia == "Federal", "media_geral"] > med_priv).mean()), 1)


def rq2(df: pd.DataFrame) -> None:
    d15 = df[(df.ano == 2015) & df.inse.notna()].copy()
    g = d15.groupby(["inse", "rede"], observed=True)["media_geral"].agg(["mean", "count"]).round(1).reset_index()
    resumo["rq2_inse_rede"] = g.to_dict("records")
    gi = d15.groupby("inse", observed=True)["media_geral"].mean().round(1)
    resumo["rq2_inse_geral"] = gi.to_dict()
    resumo["rq2_inse_dist_rede"] = (pd.crosstab(d15.rede, d15.inse, normalize="index") * 100).round(1).to_dict("index")


    fig, ax = plt.subplots(figsize=(7.2, 4))
    piv = g.pivot(index="inse", columns="rede", values="mean")
    x = np.arange(len(piv)); w = .38
    for i, rede in enumerate(["Pública", "Privada"]):
        vals = piv[rede].values
        b = ax.bar(x + (i - .5) * w, vals, w, color=COR[rede], label=rede)
        for xi, v in zip(x + (i - .5) * w, vals):
            if not np.isnan(v):
                ax.text(xi, v + 3, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_xticks(x, [s.replace("Grupo ", "G") for s in piv.index]); ax.set_ylim(400, 660)
    ax.set_title("Média geral por nível socioeconômico (INSE) e rede — 2015", loc="left", fontweight="bold")
    ax.set_xlabel("Grupo INSE (1 = mais baixo, 6 = mais alto)"); ax.set_ylabel("Média geral")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=.3)
    fig.text(0.01, -0.02, FONTE, fontsize=7.5, color="gray"); fig.tight_layout()
    fig.savefig(ASSETS / "fig2_inse_rede.png", bbox_inches="tight"); plt.close(fig)


    d = df[df.pct_formacao_docente.notna() & (df.participantes >= 30)].sample(6000, random_state=42)
    fig = px.scatter(d, x="pct_formacao_docente", y="media_geral", color="rede", color_discrete_map=COR,
                     opacity=.45, hover_data={"escola": True, "uf": True, "ano": True, "pct_formacao_docente": ":.1f", "media_geral": ":.1f"},
                     labels={"pct_formacao_docente": "% docentes com formação adequada", "media_geral": "Média geral", "rede": "Rede"},
                     title="Formação docente e desempenho (amostra de 6.000 escolas com ≥30 participantes, 2013-2015)",
                     height=470)
    fig.update_traces(marker_size=5)
    for rede in ["Pública", "Privada"]:
        sub = d[d.rede == rede]
        a, b = np.polyfit(sub.pct_formacao_docente, sub.media_geral, 1)
        xs = np.array([sub.pct_formacao_docente.min(), 100])
        fig.add_trace(go.Scatter(x=xs, y=a * xs + b, mode="lines", name=f"tendência {rede}",
                                 line=dict(color=COR[rede], width=3)))
    salvar_plotly(fig, "plot3_docente_scatter")

    base = df[df.pct_formacao_docente.notna()]
    resumo["rq2_corr_docente"] = {r: round(float(base[base.rede == r][["pct_formacao_docente", "media_geral"]].corr("spearman").iloc[0, 1]), 3)
                                  for r in ["Pública", "Privada"]}
    resumo["rq2_corr_docente_total"] = round(float(base[["pct_formacao_docente", "media_geral"]].corr("spearman").iloc[0, 1]), 3)
    resumo["rq2_corr_inse"] = round(float(d15[["inse_num", "media_geral"]].corr("spearman").iloc[0, 1]), 3)
    resumo["rq2_corr_inse_rede"] = {r: round(float(d15[d15.rede == r][["inse_num", "media_geral"]].corr("spearman").iloc[0, 1]), 3)
                                    for r in ["Pública", "Privada"]}


    c = correlacoes(d15).rename(index={**AREAS, "media_geral": "Média geral", "inse_num": "INSE",
                                        "pct_formacao_docente": "Formação docente", "taxa_aprovacao": "Aprovação",
                                        "taxa_abandono": "Abandono", "taxa_participacao": "Participação"})
    c.columns = c.index
    fig = go.Figure(go.Heatmap(z=c.values, x=c.columns, y=c.index, zmin=-1, zmax=1, colorscale="RdBu",
                               text=c.values, texttemplate="%{text:.2f}", textfont_size=10))
    fig.update_layout(title="Correlação de Spearman entre indicadores (2015)", height=520, yaxis_autorange="reversed")
    salvar_plotly(fig, "plot4_heatmap")


def rq3(df: pd.DataFrame) -> None:
    d15 = df[df.ano == 2015]
    reg = media_por(d15, ["regiao", "rede"]).pivot(index="regiao", columns="rede", values="media_geral").round(1)
    reg["gap"] = (reg["Privada"] - reg["Pública"]).round(1)
    resumo["rq3_regiao"] = reg.reset_index().to_dict("records")
    uf = media_por(d15, ["uf", "rede"]).pivot(index="uf", columns="rede", values="media_geral").round(1)
    uf["gap"] = (uf["Privada"] - uf["Pública"]).round(1)
    uf = uf.sort_values("Pública", ascending=False)
    resumo["rq3_uf_top"] = uf.head(5).reset_index().to_dict("records")
    resumo["rq3_uf_bottom"] = uf.tail(5).reset_index().to_dict("records")
    resumo["rq3_uf_gap_max"] = uf.sort_values("gap").tail(3).reset_index().to_dict("records")
    resumo["rq3_uf_gap_min"] = uf.sort_values("gap").head(3).reset_index().to_dict("records")


    uf = uf.sort_values("Pública")
    fig = go.Figure()
    for i, (u, r) in enumerate(uf.iterrows()):
        fig.add_shape(type="line", x0=r["Pública"], x1=r["Privada"], y0=u, y1=u, line=dict(color="rgba(128,128,128,.5)", width=2))
    fig.add_trace(go.Scatter(x=uf["Pública"], y=uf.index, mode="markers", name="Pública", marker=dict(color=COR["Pública"], size=10),
                             hovertemplate="%{y} pública: %{x:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=uf["Privada"], y=uf.index, mode="markers", name="Privada", marker=dict(color=COR["Privada"], size=10),
                             hovertemplate="%{y} privada: %{x:.1f}<extra></extra>"))
    fig.update_layout(title="Média geral por UF e rede em 2015 (ordenado pela rede pública)", height=720,
                      xaxis_title="Média geral ponderada", yaxis=dict(tickfont_size=11), legend=dict(orientation="h", y=1.04))
    salvar_plotly(fig, "plot5_dumbbell_uf")


    pub = d15[d15.rede == "Pública"]
    zona = media_por(pub, ["regiao", "localizacao"]).pivot(index="regiao", columns="localizacao", values="media_geral").round(1)
    zona["dif"] = (zona["Urbana"] - zona["Rural"]).round(1)
    resumo["rq3_zona"] = zona.reset_index().to_dict("records")
    resumo["rq3_zona_n"] = pub.groupby("localizacao", observed=True).size().to_dict()


    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    p = pub.dropna(subset=["taxa_abandono"])
    hb = ax.hexbin(p.taxa_abandono, p.media_geral, gridsize=45, cmap="Blues", mincnt=1, bins="log")
    fig.colorbar(hb, ax=ax, label="nº de escolas (log)")

    dec = p.groupby(pd.qcut(p.taxa_abandono, 10, duplicates="drop"), observed=True).agg(x=("taxa_abandono", "median"), y=("media_geral", "median"))
    ax.plot(dec.x, dec.y, color=COR["Privada"], lw=2.5, marker="o", label="mediana por decil de abandono")
    ax.set_xlim(0, 40); ax.set_xlabel("Taxa de abandono no ensino médio (%)"); ax.set_ylabel("Média geral")
    ax.set_title("Abandono escolar e desempenho nas escolas públicas — 2015", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper right")
    fig.text(0.01, -0.02, FONTE, fontsize=7.5, color="gray"); fig.tight_layout()
    fig.savefig(ASSETS / "fig3_abandono_hexbin.png", bbox_inches="tight"); plt.close(fig)
    resumo["rq3_corr_abandono_pub"] = round(float(p[["taxa_abandono", "media_geral"]].corr("spearman").iloc[0, 1]), 3)
    resumo["rq3_abandono_quartis"] = dec.round(1).reset_index(drop=True).to_dict("records")


def geral(df: pd.DataFrame) -> None:
    resumo["n_registros"] = int(len(df)); resumo["n_escolas"] = int(df.co_escola.nunique())
    resumo["n_municipios"] = int(df.co_municipio.nunique())
    resumo["n_por_ano"] = {int(k): int(v) for k, v in df.groupby("ano").size().items()}
    resumo["n_por_dep"] = df.groupby("dependencia", observed=True).size().to_dict()
    resumo["participantes_total"] = int(df.participantes.sum())


if __name__ == "__main__":
    df = load_processed()
    geral(df); rq1(df); rq2(df); rq3(df)
    (ASSETS / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("Figuras geradas em", ASSETS)

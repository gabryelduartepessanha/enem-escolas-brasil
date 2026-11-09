from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
TEMPLATE = ROOT / "src" / "template_artigo.html"
SAIDA = ROOT / "docs" / "index.html"
REPO_URL = "https://github.com/gabryelduartepessanha/enem-escolas-brasil"


def fmt(n: float | int, dec: int = 0) -> str:
    s = f"{n:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    r = json.loads((ASSETS / "resumo.json").read_text(encoding="utf-8"))
    html = TEMPLATE.read_text(encoding="utf-8")

    plots = {f"PLOT{i}": (ASSETS / nome).read_text(encoding="utf-8").replace("</script", "<\\/script")
             for i, nome in enumerate(["plot1_evolucao_area.json", "plot2_box_2015.json", "plot3_docente_scatter.json",
                                       "plot4_heatmap.json", "plot5_dumbbell_uf.json"], start=1)}

    zona = {z["regiao"]: z for z in r["rq3_zona"]}
    linhas = []
    for reg in r["rq3_regiao"]:
        z = zona[reg["regiao"]]
        linhas.append(f'<tr><td>{reg["regiao"]}</td><td class="num">{fmt(z["Urbana"],1)}</td><td class="num">{fmt(z["Rural"],1)}</td>'
                      f'<td class="num">{fmt(z["dif"],1)}</td><td class="num">{fmt(reg["Privada"],1)}</td><td class="num">{fmt(reg["gap"],1)}</td></tr>')

    dist = r["rq2_inse_dist_rede"]
    ce = next(u for u in r["rq3_uf_gap_max"] if u["uf"] == "CE")
    vals = {
        "REPO_URL": REPO_URL,
        "N_REG": fmt(r["n_registros"]), "N_ESC": fmt(r["n_escolas"]), "N_MUN": fmt(r["n_municipios"]),
        "GAP_MIN": fmt(r["rq1_gap_min"], 1), "GAP_MAX": fmt(r["rq1_gap_max"], 1), "GAP_2015": fmt(r["rq1_gap_2015"], 1),
        "PCT_PUB": fmt(r["rq1_pct_pub_acima_med_priv"], 1), "PCT_FED": fmt(r["rq1_pct_fed_acima_med_priv"], 1),
        "N_MUNI": fmt(r["rq1_n_2015"]["Municipal"]), "N_EST": fmt(r["rq1_n_2015"]["Estadual"]),
        "N_PRIV": fmt(r["rq1_n_2015"]["Privada"]), "N_FED": fmt(r["rq1_n_2015"]["Federal"]),
        "CORR_INSE": fmt(r["rq2_corr_inse"], 2), "CORR_INSE_PUB": fmt(r["rq2_corr_inse_rede"]["Pública"], 2),
        "CORR_INSE_PRIV": fmt(r["rq2_corr_inse_rede"]["Privada"], 2),
        "PRIV_G56": fmt(dist["Privada"]["Grupo 5"] + dist["Privada"]["Grupo 6"], 1),
        "PUB_G56": fmt(dist["Pública"]["Grupo 5"] + dist["Pública"]["Grupo 6"], 1),
        "CORR_DOC_PUB": fmt(r["rq2_corr_docente"]["Pública"], 2), "CORR_DOC_PRIV": fmt(r["rq2_corr_docente"]["Privada"], 2),
        "CORR_DOC_TOT": fmt(r["rq2_corr_docente_total"], 2),
        "GAP_CE": fmt(ce["gap"], 1), "N_RURAL": fmt(r["rq3_zona_n"]["Rural"]),
        "CORR_ABAND": fmt(r["rq3_corr_abandono_pub"], 2), "TABELA_REGIAO": "\n".join(linhas),
        "PANDAS_V": pd.__version__, **plots,
    }
    for k, v in vals.items():
        html = html.replace("{{" + k + "}}", str(v))
    faltam = [t for t in ("{{",) if t in html]
    if faltam:
        import re
        raise SystemExit("Placeholders não preenchidos: " + ", ".join(set(re.findall(r"{{(\w+)}}", html))))
    SAIDA.write_text(html, encoding="utf-8")
    print(f"Artigo gerado: {SAIDA} ({SAIDA.stat().st_size/1024:.0f} kB)")


if __name__ == "__main__":
    main()

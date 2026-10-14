"""Genera el informe HTML (docs/informe/index.html) y sus mapas a partir de la tabla tablon_analitico.

Uso: python funciones/construir_informe.py
"""
import base64, io, sqlite3
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from branca.colormap import LinearColormap
from folium.plugins import HeatMap
from matplotlib.colors import LinearSegmentedColormap

PROY = Path(__file__).resolve().parents[1]
SCR = Path(__file__).parent
SALIDA = PROY / "docs" / "informe"
(SALIDA / "mapas").mkdir(parents=True, exist_ok=True)

with sqlite3.connect(PROY / "datos" / "intermedios" / "mercado_inmobiliario.db") as conn:
    df = pd.read_sql("SELECT * FROM tablon_analitico", conn)

INTERES = ["Latina", "Arganzuela", "Carabanchel", "Centro"]
N_MIN = 30
ENTERO = df[df["room_type"] == "Entire home/apt"]

NAVY, BLUE, MID, LIGHT, PALE = "#0a2f6b", "#1f6fd1", "#5b9bea", "#a9cdf5", "#e6f0fc"
INK, MUTED, GRID = "#16263f", "#5b6b82", "#d8e3f2"
cmap = LinearSegmentedColormap.from_list("azules", ["#eef5fd", "#a9cdf5", "#3f86e0", "#0a2f6b"])
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID, "axes.grid": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def f1(v):
    return str(Decimal(str(round(float(v), 4))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def miles(v):
    return f"{v:,.0f}".replace(",", ".")


def b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def limpio(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)


figs = {}

# 1. Mediana de margen por distrito
g = df.groupby("distrito")["margen_bruto"].agg(["median", "count"])
g = g[g["count"] >= N_MIN].sort_values("median")
fig, ax = plt.subplots(figsize=(7.2, 4.5))
ax.barh(g.index, g["median"], color=[NAVY if d in INTERES else LIGHT for d in g.index], height=0.7)
for i, (d, r) in enumerate(g.iterrows()):
    ax.text(r["median"] + 0.08, i, f"{f1(r['median'])}%  (n={int(r['count'])})", va="center", fontsize=8, color=INK,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.8))
med = df["margen_bruto"].median()
ax.axvline(med, color=BLUE, ls="--", lw=1)
ax.text(med + 0.05, -0.95, f"Mediana Madrid {f1(med)}%", color=BLUE, fontsize=8)
ax.set_xlim(0, g["median"].max() + 2.2)
ax.set_xlabel("Mediana del margen bruto (%)")
limpio(ax)
figs["distritos"] = b64(fig)

# 2. Boxplot
d2 = df[df["margen_bruto"] <= 50]
cnt = d2["distrito"].value_counts()
d2 = d2[d2["distrito"].isin(cnt[cnt >= N_MIN].index)]
res = d2.groupby("distrito")["margen_bruto"].agg(["median", "count"]).sort_values("median", ascending=False)
fig, ax = plt.subplots(figsize=(7.2, 4.5))
sns.boxplot(data=d2, x="margen_bruto", y="distrito", order=res.index, color=LIGHT, linewidth=0.9, width=0.65,
            flierprops=dict(marker="o", markersize=2.5, markerfacecolor=BLUE, markeredgecolor="none", alpha=0.5),
            medianprops=dict(color=NAVY, lw=1.6), ax=ax)
ax.set_yticks(range(len(res)))
ax.set_yticklabels([f"{d} (n={int(n)})" for d, n in res["count"].items()], fontsize=8)
ax.set_xlabel("Margen bruto (%)")
ax.set_ylabel("")
limpio(ax)
figs["boxplot"] = b64(fig)

# 3. Heatmap distrito x room_type
sel = df[df["distrito"].isin(INTERES)]
t = sel.pivot_table(index="distrito", columns="room_type", values="margen_bruto", aggfunc=["median", "count"])
mt = t["median"].loc[t["median"]["Entire home/apt"].sort_values(ascending=False).index]
ct = t["count"].loc[mt.index]
fig, ax = plt.subplots(figsize=(6.0, 3.3))
sns.heatmap(mt, annot=False, cmap=cmap, cbar_kws={"label": "Mediana margen bruto (%)"}, linewidths=2, linecolor="white", ax=ax)
for i in range(mt.shape[0]):
    for j in range(mt.shape[1]):
        v = mt.iat[i, j]
        if pd.notna(v):
            ax.text(j + 0.5, i + 0.5, f"{f1(v)}\nn={int(ct.iat[i, j])}", ha="center", va="center", fontsize=8,
                    color="white" if v > 5 else INK)
ax.set_xlabel("")
ax.set_ylabel("")
figs["hm_room"] = b64(fig)

# 4. Barras margen por habitaciones y capacidad
fig, axs = plt.subplots(1, 2, figsize=(6.2, 3.3), sharey=True)
for ax, var, tit in ((axs[0], "bedrooms_discretizada", "Nº de habitaciones"), (axs[1], "accommodates_discretizada", "Capacidad (personas)")):
    s = df.groupby(var)["margen_bruto"].median()
    if var == "accommodates_discretizada":
        s = s.reindex(["1_pers", "2_pers", "3_pers", "4_pers", "+5_pers"])
    best = s.idxmax()
    ax.bar(s.index.str.replace("_", " "), s.values, color=[NAVY if k == best else LIGHT for k in s.index], width=0.65)
    for k, (lab, v) in enumerate(s.items()):
        ax.text(k, v + 0.12, f1(v), ha="center", fontsize=8)
    ax.set_title(tit, fontsize=9, color=INK, loc="left")
    limpio(ax)
axs[0].set_ylabel("Mediana margen bruto (%)")
plt.tight_layout()
figs["barras_margen"] = b64(fig)

# 5. Heatmap resto distritos x habitaciones
resto = ENTERO[~ENTERO["distrito"].isin(INTERES)]
cn = resto["distrito"].value_counts()
r2 = resto[resto["distrito"].isin(cn[cn >= N_MIN].index)]
t = r2.pivot_table(index="distrito", columns="bedrooms_discretizada", values="margen_bruto", aggfunc=["median", "count"])
mt = t["median"].loc[t["median"].max(axis=1).sort_values(ascending=False).index]
ct = t["count"].loc[mt.index]
fig, ax = plt.subplots(figsize=(5.4, 4.4))
sns.heatmap(mt, annot=False, cmap=cmap, cbar=False, linewidths=1.5, linecolor="white", ax=ax)
for i in range(mt.shape[0]):
    for j in range(mt.shape[1]):
        v, n = mt.iat[i, j], ct.iat[i, j]
        if pd.notna(v):
            ax.text(j + 0.5, i + 0.5, f1(v), ha="center", va="center", fontsize=8,
                    color=("#9aa8bd" if n < 20 else ("white" if v > 8 else INK)), fontstyle="italic" if n < 20 else "normal")
ax.set_xticklabels([x.get_text().replace("_", " ") for x in ax.get_xticklabels()])
ax.set_xlabel("Cursiva gris = menos de 20 inmuebles (no fiable)", fontsize=8)
ax.set_ylabel("")
figs["hm_resto"] = b64(fig)

# 6. Ocupación
fig, axs = plt.subplots(1, 2, figsize=(6.2, 3.3), sharey=True)
for ax, var, tit in ((axs[0], "accommodates_discretizada", "Capacidad (personas)"), (axs[1], "bedrooms_discretizada", "Nº de habitaciones")):
    s = df.groupby(var)["estimated_occupancy_l365d"].median()
    if var == "accommodates_discretizada":
        s = s.reindex(["1_pers", "2_pers", "3_pers", "4_pers", "+5_pers"])
    best = s.idxmax()
    ax.bar(s.index.str.replace("_", " "), s.values, color=[NAVY if k == best else LIGHT for k in s.index], width=0.65)
    for k, (lab, v) in enumerate(s.items()):
        ax.text(k, v + 2, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_title(tit, fontsize=9, color=INK, loc="left")
    limpio(ax)
axs[0].set_ylabel("Mediana ocupación estimada (días/año)")
plt.tight_layout()
figs["barras_ocup"] = b64(fig)

# 7. Scatter
d7 = df[df["margen_bruto"] <= 50]
fig, ax = plt.subplots(figsize=(6.0, 3.7))
ax.axvspan(150, 366, ymin=5 / 52, color=PALE, zorder=0)
ax.scatter(d7["estimated_occupancy_l365d"], d7["margen_bruto"], s=7, alpha=0.35, color=BLUE, edgecolor="none")
ax.axvline(150, color=NAVY, ls="--", lw=1)
ax.axhline(5, color=NAVY, ls="--", lw=1)
n_q = int(((d7["estimated_occupancy_l365d"] > 150) & (d7["margen_bruto"] > 5)).sum())
ax.text(360, 49, f"{miles(n_q)} inmuebles ({n_q / len(d7):.0%})\ncon >150 días y margen >5%", ha="right", va="top",
        fontsize=8.5, color=NAVY, fontweight="bold")
ax.set_xlabel("Ocupación estimada (días/año)")
ax.set_ylabel("Margen bruto (%)")
ax.set_xlim(0, 366)
ax.set_ylim(0, 52)
limpio(ax)
figs["scatter"] = b64(fig)

# ---------- Tablas ----------
bar = (ENTERO.groupby(["distrito", "neighbourhood"])
       .agg(n=("margen_bruto", "size"), m=("margen_bruto", "median"), c=("coste_adquisicion", "median"),
            o=("estimated_occupancy_l365d", "median")).reset_index())
bar = bar[bar["n"] >= N_MIN].sort_values("m", ascending=False).head(8)
tabla_barrios = "".join(
    f"<tr><td>{r.neighbourhood}</td><td>{r.distrito}</td><td class='num'><b>{f1(r.m)}%</b></td>"
    f"<td class='num'>{miles(r.c)} €</td><td class='num'>{r.o:.0f}</td><td class='num'>{int(r.n)}</td></tr>"
    for r in bar.itertuples())

perf = (resto.groupby(["distrito", "neighbourhood", "bedrooms_discretizada", "accommodates_discretizada"])
        .agg(n=("margen_bruto", "count"), margen=("margen_bruto", "median"), ocup=("estimated_occupancy_l365d", "median"))
        .reset_index())
perf = perf[perf["n"] >= 10].sort_values("margen", ascending=False).head(6)
tabla_perfiles = "".join(
    f"<tr><td>{r.neighbourhood}<small>{r.distrito}</small></td><td>{r.bedrooms_discretizada.replace('_', ' ')} · {r.accommodates_discretizada.replace('_', ' ')}</td>"
    f"<td class='num'><b>{f1(r.margen)}%</b></td><td class='num'>{r.ocup:.0f}</td><td class='num'>{int(r.n)}</td></tr>"
    for r in perf.itertuples())

filas = []
for cmax in (150000, 200000, 250000):
    s = ENTERO[(ENTERO["margen_bruto"] >= 15) & (ENTERO["coste_adquisicion"] < cmax)]
    top = ", ".join(f"{k} {v}" for k, v in s["distrito"].value_counts().head(3).items())
    filas.append(f"<tr><td style='white-space:nowrap'>&lt; {miles(cmax)} €</td><td class='num'><b>{len(s)}</b></td><td>{top}</td></tr>")
tabla_inversion = "".join(filas)

# ---------- Mapas (base CartoDB: el mapa base de OpenStreetMap bloquea archivos abiertos en local) ----------
CENTRO = (40.4168, -3.7038)
TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"


def mapa_base():
    m = folium.Map(location=CENTRO, zoom_start=12, tiles=None)
    folium.TileLayer(tiles=TILES, attr="Tiles © Esri — Esri, HERE, Garmin, © OpenStreetMap contributors", max_zoom=16, name="Esri").add_to(m)
    return m

GRADIENTE = {0.0: "blue", 0.4: "cyan", 0.6: "yellow", 0.8: "orange", 1.0: "red"}


def mapa_calor(col, escala, ruta):
    d = df.dropna(subset=["latitude", "longitude", col])
    pesos = (d[col].clip(upper=escala) / escala).to_numpy()
    pts = np.column_stack([d["latitude"], d["longitude"], pesos]).tolist()
    m = mapa_base()
    HeatMap(pts, radius=12, blur=15, min_opacity=0.3, gradient=GRADIENTE).add_to(m)
    m.save(ruta)


mapa_calor("margen_bruto", 50, SALIDA / "mapas" / "mapa_calor_margen_bruto.html")
mapa_calor("estimated_occupancy_l365d", 365, SALIDA / "mapas" / "mapa_calor_ocupacion.html")
mapa_calor("score_turistico", 100, SALIDA / "mapas" / "mapa_calor_score_turistico.html")

dq = df.copy()
dq["q"] = pd.qcut(dq["score_turistico"], 4, labels=["25% con menor score", "2.º cuartil", "3.º cuartil", "25% con mayor score"])
sq = dq.groupby("q", observed=True).agg(m=("margen_bruto", "median"), o=("estimated_occupancy_l365d", "median"), p=("precio_noche_total", "median"))
tabla_score = "".join(f"<tr><td>{k}</td><td class='num'><b>{f1(r.m)}%</b></td><td class='num'>{r.o:.0f}</td><td class='num'>{r.p:.0f}</td></tr>" for k, r in sq.iterrows())

op = df[(df["margen_bruto"] > 20) & (df["estimated_occupancy_l365d"] > 200)].dropna(subset=["latitude", "longitude"])
mn, mx = op["margen_bruto"].min(), op["margen_bruto"].max()
col = LinearColormap(["gold", "orange", "red", "darkred"], vmin=mn, vmax=mx, caption="Margen bruto (%)")
m = mapa_base()
for _, r in op.iterrows():
    info = (f"<b>{r['distrito']} - {r['neighbourhood']}</b><br>{r['room_type']} | {r['bedrooms_discretizada']} | {r['accommodates_discretizada']}<br>"
            f"Margen bruto: {r['margen_bruto']:.1f}%<br>Ocupación: {r['estimated_occupancy_l365d']:.0f} días<br>"
            f"Precio noche: {r['precio_noche_total']:,.0f} €<br>Ingresos anuales: {r['ingresos_anuales']:,.0f} €<br>"
            f"Coste adquisición: {r['coste_adquisicion']:,.0f} €")
    folium.CircleMarker([r["latitude"], r["longitude"]], radius=5 + (r["margen_bruto"] - mn) / (mx - mn) * 20,
                        color="black", weight=1, fill=True, fill_color=col(r["margen_bruto"]), fill_opacity=0.75,
                        tooltip=folium.Tooltip(info, sticky=True)).add_to(m)
col.add_to(m)
m.save(SALIDA / "mapas" / "mapa_oportunidades.html")

# ---------- Ensamblado ----------
html = (SCR / "plantilla_informe.html").read_text(encoding="utf-8")
for k, v in figs.items():
    html = html.replace("{{" + k + "}}", v)
html = (html.replace("{{tabla_barrios}}", tabla_barrios).replace("{{tabla_perfiles}}", tabla_perfiles)
        .replace("{{tabla_inversion}}", tabla_inversion).replace("{{tabla_score}}", tabla_score))
(SALIDA / "index.html").write_text(html, encoding="utf-8")
print("OK", len(html) // 1024, "KB")
print(bar.round(1).to_string())
print(perf.round(1).to_string())

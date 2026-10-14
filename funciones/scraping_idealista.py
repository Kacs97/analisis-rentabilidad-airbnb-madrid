import pandas as pd
from io import StringIO
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "datos" / "brutos" / "idealista_madrid.html"
SALIDA = RAIZ / "datos" / "brutos" / "precio_m2_distritos_madrid.csv"


def limpiar_numero(serie):
    return (
        serie.astype(str)
        .str.replace(r"[^\d,.-]", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def main():
    html = ENTRADA.read_text(encoding="utf-8", errors="ignore")
    tablas = pd.read_html(StringIO(html), decimal=",", thousands=".")

    df = next(
        t for t in tablas
        if any("distrito" in str(c).lower() for c in t.columns)
        or t.iloc[:, 0].astype(str).str.contains("Centro|Salamanca|Chamberí", regex=True).any()
    )

    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "distrito"})

    col_precio = next(c for c in df.columns[1:] if "m2" in c.lower() or "€" in c)
    df["precio_m2_sep_2026"] = limpiar_numero(df[col_precio])
    df = df[["distrito", "precio_m2_sep_2026"]].dropna()

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA,index=False, encoding="utf-8-sig")
    print(df)


if __name__ == "__main__":
    main()

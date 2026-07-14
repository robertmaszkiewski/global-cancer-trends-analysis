"""Sklada kompaktowe dane dla strony: historia (nasz pipeline) + IARC (zweryfikowane 340/340)."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import LABELS, SEX_SPECIFIC  # noqa: E402

from paths import RAW, OUT, WEB   # jedno miejsce na sciezki (patrz paths.py)

WEB.mkdir(parents=True, exist_ok=True)
IARC_PARQ = RAW / "cancer_observations.parquet"   # warstwa IARC (GLOBOCAN + prognozy)

AGG = ["ALL", "ALL_EX_NMSC"]          # kody zbiorcze — NIGDY w rankingu
RESIDUAL = ["OTHER", "UNSPECIFIED"]   # kosze resztkowe — NIGDY w rankingu

# ---------- 1. HISTORIA (nasz pipeline) ----------
h = pd.read_parquet(OUT / "mortality.parquet")
cont = pd.read_csv(OUT / "continuity.csv").set_index("site")

hist = {"meta": {}, "sites": {}, "series": {}}
for code, (en, pl) in LABELS.items():
    if code not in cont.index:
        continue
    hist["sites"][code] = {
        "en": en, "pl": pl,
        "sex": SEX_SPECIFIC.get(code),           # None = obie plcie dostepne
        "continuous": bool(cont.loc[code, "continuous"]),
        "break_pct": float(cont.loc[code, "max_break_pct"]),
    }

for (iso, site, sex), g in h.groupby(["iso", "site", "sex"]):
    g = g.sort_values("year")
    y0 = int(g.year.min())
    y1 = int(g.year.max())
    years = list(range(y0, y1 + 1))
    idx = {int(r.year): r for r in g.itertuples()}
    hist["series"][f"{iso}|{site}|{sex}"] = {
        "y0": y0,
        "asr": [round(float(idx[y].asr), 2) if y in idx else None for y in years],
        "crude": [round(float(idx[y].crude), 2) if y in idx else None for y in years],
        "d": [int(idx[y].deaths) if y in idx else None for y in years],
        "rev": [idx[y].revision[4:] if y in idx else None for y in years],  # '8','9','10'
    }
hist["meta"] = {
    "source": "WHO Mortality Database (ICD-8 08A, ICD-9 09B, ICD-10 104)",
    "denominator": "UN World Population Prospects 2024",
    "standard": "WHO World Standard Population",
    "years": [int(h.year.min()), int(h.year.max())],
    "geos": ["POL", "GBR", "ESP", "USA"],
    "gaps": {"POL": [1997, 1998], "GBR": [2000], "ESP": [], "USA": []},
}
(WEB / "cancer-history.json").write_text(json.dumps(hist, separators=(",", ":")))

# ---------- 2. IARC: obciazenie 2024 + prognoza 2050 ----------
d = pd.read_parquet(IARC_PARQ)
g24 = d[d.source_id == "iarc_globocan_2024"]
tom = d[d.source_id == "iarc_cancer_tomorrow"]

cur = {"labels": {}, "burden": {}, "age": {}, "risk": {}}
lab = g24[["cancer_code", "cancer_label_en", "cancer_label_pl"]].drop_duplicates()
for r in lab.itertuples():
    cur["labels"][r.cancer_code] = {"en": r.cancer_label_en, "pl": r.cancer_label_pl}

# ranking + ASR (bez agregatow i koszy resztkowych)
real = g24[~g24.cancer_code.isin(AGG + RESIDUAL)]
for geo in ["WORLD", "POL", "GBR", "ESP", "USA"]:
    for meas in ["incidence", "mortality"]:
        rows = real[(real.geography_code == geo) & (real.measure == meas)
                    & (real.sex == "both") & (real.age_group_label == "All ages")
                    & (real.metric == "number")]
        asr = real[(real.geography_code == geo) & (real.measure == meas)
                   & (real.sex == "both") & (real.metric == "age_standardised_rate")]
        amap = dict(zip(asr.cancer_code, asr.value))
        recs = [{"c": r.cancer_code, "n": int(r.value),
                 "asr": round(float(amap.get(r.cancer_code, 0)), 1)}
                for r in rows.itertuples()]
        recs.sort(key=lambda x: -x["n"])
        cur["burden"][f"{geo}|{meas}"] = recs[:15]

# totale (z agregatow — do KPI, jawnie oznaczone)
tot = g24[(g24.cancer_code == "ALL") & (g24.sex == "both")
          & (g24.age_group_label == "All ages") & (g24.metric == "number")]
cur["totals"] = {f"{r.geography_code}|{r.measure}": int(r.value) for r in tot.itertuples()}

# profil wiekowy (wspolczynniki wiekowe GLOBOCAN)
ages = g24[(g24.metric == "age_specific_rate") & (g24.sex == "both")
           & (~g24.cancer_code.isin(AGG + RESIDUAL))]
for (geo, canc, meas), gg in ages.groupby(["geography_code", "cancer_code", "measure"]):
    gg = gg.sort_values("age_start")
    cur["age"][f"{geo}|{canc}|{meas}"] = {
        "x": [str(a) for a in gg.age_group_label],
        "y": [round(float(v), 1) for v in gg.value],
    }

(WEB / "cancer-current.json").write_text(json.dumps(cur, separators=(",", ":")))

fut = {"series": {}, "labels": cur["labels"]}
t = tom[(tom.sex == "both") & (tom.metric == "number")]
for (geo, canc, meas), gg in t.groupby(["geography_code", "cancer_code", "measure"]):
    gg = gg.sort_values("year")
    fut["series"][f"{geo}|{canc}|{meas}"] = {
        "years": [int(y) for y in gg.year],
        "n": [int(v) for v in gg.value],
    }
(WEB / "cancer-future.json").write_text(json.dumps(fut, separators=(",", ":")))

print("=== ROZMIARY ===")
for f in sorted(WEB.glob("*.json")):
    print(f"  {f.name}: {f.stat().st_size / 1024:.0f} KB")
print()
print("serii historycznych:", len(hist["series"]))
print("lokalizacji:", len(hist["sites"]))
print("KPI totale:", {k: f"{v:,}" for k, v in list(cur["totals"].items())[:4]})

"""Warstwa HPV: pokrycie szczepieniami (WHO), dzietnosc (Bank Swiatowy),
rak szyjki macicy wg wieku (nasz pipeline WHO)."""
import collections
import json
from pathlib import Path

import pandas as pd

SCR = Path("/tmp/claude-1000/-home-ubuntu/dbf101f2-9ff3-4d77-abb0-3a89bc56df0b/scratchpad")
OUT = SCR / "build" / "out"
WEB = SCR / "build" / "web"

CTRY = ["POL", "GBR", "ESP", "USA"]
d = {}

# --- 1. Pokrycie szczepieniami HPV (WHO GHO, dziewczeta 9-14) ---
cov = collections.defaultdict(dict)
for r in json.load(open(SCR / "hpv_cov.json"))["value"]:
    if r.get("NumericValue") is not None and r["SpatialDim"] in CTRY:
        cov[r["SpatialDim"]][int(r["TimeDim"])] = round(float(r["NumericValue"]), 1)
d["coverage"] = {c: {"years": sorted(v), "pct": [v[y] for y in sorted(v)]} for c, v in cov.items()}

# --- 2. Dzietnosc (Bank Swiatowy) — UWAGA: to NIE jest nieplodnosc ---
tfr = collections.defaultdict(dict)
wb = json.load(open(SCR / "wb_tfr.json"))
for r in wb[1]:
    if r["value"] is not None and r["countryiso3code"] in CTRY:
        tfr[r["countryiso3code"]][int(r["date"])] = round(float(r["value"]), 2)
d["fertility"] = {c: {"years": sorted(v), "tfr": [v[y] for y in sorted(v)]} for c, v in tfr.items()}

# --- 3. Rak szyjki macicy: rozklad wg wieku vs inne nowotwory kobiet ---
b = pd.read_parquet(OUT / "mortality_by_age.parquet")
f = b[(b.sex == "female") & (b.year.between(2019, 2023))]
young = {}
for site in ["CERVIX", "BREAST", "OVARY", "COLORECTUM", "LUNG", "PANCREAS"]:
    s = f[f.site == site]
    if s.empty:
        continue
    young[site] = round(100 * s[s.age < 45].deaths.sum() / s.deaths.sum(), 1)
d["under45"] = young

# profil wieku raka szyjki (udzial zgonow w kazdej grupie)
cerv = f[f.site == "CERVIX"].groupby("age", as_index=False).deaths.sum()
cerv["pct"] = 100 * cerv.deaths / cerv.deaths.sum()
d["cervixAge"] = {
    "x": [f"{int(a)}-{int(a)+4}" if a < 85 else "85+" for a in cerv.age],
    "y": [round(p, 1) for p in cerv.pct],
}

# --- 4. Umieralnosc na raka szyjki (ASR) — kontekst ---
m = pd.read_parquet(OUT / "mortality.parquet")
cm = m[(m.site == "CERVIX") & (m.sex == "female")]
d["cervixAsr"] = {}
for iso in CTRY:
    s = cm[cm.iso == iso].sort_values("year")
    d["cervixAsr"][iso] = {"y0": int(s.year.min()),
                           "asr": [round(float(v), 2) for v in s.asr]}

# --- 5. Zgony w wieku 20-34 (pierwsze zaszczepione roczniki) ---
cy = b[(b.site == "CERVIX") & (b.sex == "female") & (b.age.isin([20, 25, 30]))]
cy = cy.groupby(["iso", "year"], as_index=False).deaths.sum()
d["cervixYoung"] = {}
for iso in CTRY:
    s = cy[cy.iso == iso].sort_values("year")
    d["cervixYoung"][iso] = {"y0": int(s.year.min()),
                             "n": [int(v) for v in s.deaths]}

(WEB / "cancer-hpv.json").write_text(json.dumps(d, separators=(",", ":")))
print("zapisano cancer-hpv.json:", (WEB / "cancer-hpv.json").stat().st_size / 1024, "KB")
print()
print("=== pokrycie szczepieniami (ostatni rok) ===")
for c in CTRY:
    v = cov[c]
    if v:
        y = max(v)
        print(f"  {c}: {v[y]}% ({y})   pierwszy rok danych: {min(v)}")
    else:
        print(f"  {c}: brak")
print()
print("=== dzietnosc (2023 lub ostatni) ===")
for c in CTRY:
    v = tfr[c]
    y = max(v)
    print(f"  {c}: {v[y]} ({y})")
print()
print("=== udzial zgonow ponizej 45 r.z. ===")
for k, v in sorted(young.items(), key=lambda kv: -kv[1]):
    print(f"  {k:12} {v}%")

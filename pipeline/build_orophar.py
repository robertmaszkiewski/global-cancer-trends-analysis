"""Drugi rak HPV-zalezny, o ktorym sie nie mowi: gardlo srodkowe.

Blok C00-C14 (warga/jama ustna/gardlo) to w istocie DWIE rozne choroby:
  - podmiejsca HPV-zalezne: nasada jezyka (C01), migdalek (C09), gardlo srodkowe (C10)
  - reszta: napedzana tytoniem i alkoholem (warga, jama ustna, gardlo dolne...)

Jesli pierwsze rosna, a drugie spadaja — to jest podpis wirusa, nie uzywek.
Tylko era ICD-10 (1999+), bo starsze listy nie maja tej granulacji.
"""
import gzip
import json
import zipfile
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import RAW, OUT, WEB   # jedno miejsce na sciezki (patrz paths.py)

CTRY = {4230: "POL", 4308: "GBR", 4280: "ESP", 2450: "USA",
        4050: "DNK", 4290: "SWE", 5020: "AUS", 4210: "NLD"}
# podmiejsca HPV-zalezne (nasada jezyka, migdalek, gardlo srodkowe)
HPV_SITES = ("C01", "C09", "C10")
# reszta bloku glowa-szyja: tytoniowo-alkoholowa
OTHER = ("C00", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C11", "C12", "C13", "C14")
WORLD_STD = {0: 8.86, 5: 8.69, 10: 8.60, 15: 8.47, 20: 8.22, 25: 7.93, 30: 7.61,
             35: 7.15, 40: 6.59, 45: 6.04, 50: 5.37, 55: 4.55, 60: 3.72, 65: 2.96,
             70: 2.21, 75: 1.52, 80: 0.91, 85: 0.63}

def age_layout(frmat):
    f = str(frmat).zfill(2)
    if f in ("00", "01"):
        u5 = ["Deaths2", "Deaths3", "Deaths4", "Deaths5", "Deaths6"]
    elif f == "02":
        u5 = ["Deaths2", "Deaths3"]
    else:
        return None
    m = {"_u5": u5}
    for i, a in enumerate(range(5, 95, 5)):
        m[f"Deaths{i + 7}"] = min(a, 85)
    m["Deaths25"] = 85
    return m

def read(n):
    with zipfile.ZipFile(RAW / n) as z:
        mem = [x for x in z.namelist() if not x.endswith("/")][0]
        with z.open(mem) as fh:
            return pd.read_csv(fh, dtype={"Admin1": str, "SubDiv": str, "List": str,
                                          "Cause": str, "Frmat": str}, low_memory=False)

rows = []
for fn in [f"morticd10_part{i}.zip" for i in range(1, 7)]:
    df = read(fn)
    df = df[(df.Admin1.fillna("").str.strip() == "") & (df.SubDiv.fillna("").str.strip() == "")]
    df = df[df.Country.isin(CTRY) & df.Sex.isin([1, 2]) & df.List.isin(["104", "10M", "103"])]
    for r in df.itertuples(index=False):
        c = str(r.Cause).upper()
        if c.startswith(HPV_SITES):
            grp = "hpv"
        elif c.startswith(OTHER):
            grp = "other"
        else:
            continue
        lay = age_layout(r.Frmat)
        if lay is None:
            continue
        base = {"iso": CTRY[r.Country], "year": int(r.Year), "grp": grp,
                "sex": "male" if r.Sex == 1 else "female"}
        rows.append({**base, "age": 0,
                     "deaths": sum(float(getattr(r, x)) for x in lay["_u5"]
                                   if pd.notna(getattr(r, x, None)))})
        for col, age in lay.items():
            if col == "_u5":
                continue
            v = getattr(r, col, None)
            if pd.notna(v):
                rows.append({**base, "age": age, "deaths": float(v)})
    print(f"  {fn}: {len(rows):,}", flush=True)

d = pd.DataFrame(rows).groupby(["iso", "year", "grp", "sex", "age"], as_index=False).deaths.sum()

chunks = []
for ch in pd.read_csv(gzip.open(RAW / "wpp2024.csv.gz", "rt"), chunksize=500_000, low_memory=False):
    ch = ch[ch["ISO3_code"].isin(set(CTRY.values()))]
    if len(ch):
        chunks.append(ch[["ISO3_code", "Time", "AgeGrpStart", "PopMale", "PopFemale"]])
w = pd.concat(chunks)
w["age"] = (w.AgeGrpStart // 5 * 5).clip(upper=85)
p = w.groupby(["ISO3_code", "Time", "age"], as_index=False)[["PopMale", "PopFemale"]].sum()
p = p.melt(["ISO3_code", "Time", "age"], ["PopMale", "PopFemale"], "sex", "pop")
p["sex"] = p.sex.map({"PopMale": "male", "PopFemale": "female"})
p["pop"] = p["pop"] * 1000.0
p = p.rename(columns={"ISO3_code": "iso", "Time": "year"})

d = d.merge(p, on=["iso", "year", "sex", "age"], how="inner")
d["wt"] = d.age.map(WORLD_STD)
d["contrib"] = d.deaths / d["pop"] * 1e5 * d.wt

# obie plcie razem: sumujemy zgony i populacje w kazdej grupie wieku
b = d.groupby(["iso", "year", "grp", "age"], as_index=False).agg(
    deaths=("deaths", "sum"), pop=("pop", "sum"))
b["wt"] = b.age.map(WORLD_STD)
b["contrib"] = b.deaths / b["pop"] * 1e5 * b.wt
agg = b.groupby(["iso", "year", "grp"], as_index=False).agg(
    tot=("contrib", "sum"), ws=("wt", "sum"), dd=("deaths", "sum"))
agg = agg[agg.ws > 99.9].copy()
agg["asr"] = agg.tot / agg.ws

out = {}
for (iso, grp), s in agg.groupby(["iso", "grp"]):
    s = s.sort_values("year")
    out.setdefault(iso, {})[grp] = {"years": [int(y) for y in s.year],
                                    "v": [round(float(v), 3) for v in s.asr]}
(WEB / "orophar.json").write_text(json.dumps(out, separators=(",", ":")))

print()
print("=== RAK GARDLA SRODKOWEGO (HPV) vs RESZTA BLOKU (tyton/alkohol) ===")
print("    ASR, obie plcie, zmiana od 1999/2000 do ostatniego roku")
print(f"  {'kraj':5} {'HPV-zalezne':>22} {'tytoniowo-alkoholowe':>24}")
for iso in ["GBR", "USA", "DNK", "SWE", "NLD", "AUS", "ESP", "POL"]:
    line = f"  {iso:5}"
    for grp in ["hpv", "other"]:
        s = out.get(iso, {}).get(grp)
        if not s:
            line += f"{'-':>22}"
            continue
        a, z = s["v"][0], s["v"][-1]
        chg = 100 * (z - a) / a if a else 0
        line += f"{a:6.2f} -> {z:5.2f} ({chg:+4.0f}%)".rjust(22 if grp == "hpv" else 24)
    print(line)

"""Rak szyjki macicy w 11 krajach — rozszerzenie o kraje z NAJLEPSZYMI danymi.

Polska, UK, Hiszpania i USA maja slabe dane o plodnosci. Kraje nordyckie maja
najlepsze na swiecie rejestry (numer PESEL-owy pozwala laczyc szczepienia z rakiem
i z porodami), a Australia jest najdalej w drodze do eliminacji. Wiec je dokladamy.

Wyjscie: cervix-wide.json — ASR + umieralnosc kobiet 20-34 + pokrycie szczepieniami.
"""
import gzip
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import decode  # noqa: E402

SCR = Path("/tmp/claude-1000/-home-ubuntu/dbf101f2-9ff3-4d77-abb0-3a89bc56df0b/scratchpad")
RAW = SCR / "who-raw"
WEB = SCR / "build" / "web"

CTRY = {4230: "POL", 4308: "GBR", 4280: "ESP", 2450: "USA",
        4050: "DNK", 4290: "SWE", 4070: "FIN", 4220: "NOR",
        5020: "AUS", 4210: "NLD", 4240: "PRT"}
LIST_PRIORITY = {"10M": 0, "104": 1, "103": 2, "101": 3, "09B": 5, "09A": 6, "08A": 8}
WORLD_STD = {0: 8.86, 5: 8.69, 10: 8.60, 15: 8.47, 20: 8.22, 25: 7.93, 30: 7.61,
             35: 7.15, 40: 6.59, 45: 6.04, 50: 5.37, 55: 4.55, 60: 3.72, 65: 2.96,
             70: 2.21, 75: 1.52, 80: 0.91, 85: 0.63}
DROPPED = {"unmapped": 0, "bad_frmat": 0, "no_pop": 0}


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
files = ["morticd08.zip", "morticd09.zip"] + [f"morticd10_part{i}.zip" for i in range(1, 7)]
for fn in files:
    df = read(fn)
    df = df[(df.Admin1.fillna("").str.strip() == "") & (df.SubDiv.fillna("").str.strip() == "")]
    df = df[df.Country.isin(CTRY) & (df.Sex == 2)]          # tylko kobiety
    for r in df.itertuples(index=False):
        if decode(r.List, r.Cause) != "CERVIX":
            continue
        lay = age_layout(r.Frmat)
        if lay is None:
            DROPPED["bad_frmat"] += 1
            continue
        base = {"iso": CTRY[r.Country], "year": int(r.Year), "lst": str(r.List).upper()}
        u5 = sum(float(getattr(r, c)) for c in lay["_u5"] if pd.notna(getattr(r, c, None)))
        rows.append({**base, "age": 0, "deaths": u5})
        for col, age in lay.items():
            if col == "_u5":
                continue
            v = getattr(r, col, None)
            if pd.notna(v):
                rows.append({**base, "age": age, "deaths": float(v)})
    print(f"  {fn}: {len(rows):,} wierszy", flush=True)

d = pd.DataFrame(rows).groupby(["iso", "year", "age", "lst"], as_index=False).deaths.sum()
d["p"] = d.lst.map(LIST_PRIORITY)
d = d[d.p == d.groupby(["iso", "year"]).p.transform("min")]
assert d.groupby(["iso", "year"]).lst.nunique().max() == 1, "rownolegle listy ICD!"
d = d.groupby(["iso", "year", "age"], as_index=False).deaths.sum()

# mianowniki: UN WPP (populacja kobiet)
chunks = []
for ch in pd.read_csv(gzip.open(SCR / "wpp2024.csv.gz", "rt"), chunksize=500_000, low_memory=False):
    ch = ch[ch["ISO3_code"].isin(set(CTRY.values()))]
    if len(ch):
        chunks.append(ch[["ISO3_code", "Time", "AgeGrpStart", "PopFemale"]])
w = pd.concat(chunks)
w["age"] = (w.AgeGrpStart // 5 * 5).clip(upper=85)
pop = w.groupby(["ISO3_code", "Time", "age"], as_index=False).PopFemale.sum()
pop["pop"] = pop.PopFemale * 1000.0
pop = pop.rename(columns={"ISO3_code": "iso", "Time": "year"})[["iso", "year", "age", "pop"]]

before = len(d)
d = d.merge(pop, on=["iso", "year", "age"], how="inner")
DROPPED["no_pop"] = before - len(d)

d["wt"] = d.age.map(WORLD_STD)
d["contrib"] = d.deaths / d["pop"] * 1e5 * d.wt
agg = d.groupby(["iso", "year"], as_index=False).agg(
    tot=("contrib", "sum"), ws=("wt", "sum"), dd=("deaths", "sum"))
agg = agg[agg.ws > 99.9].copy()
agg["asr"] = agg.tot / agg.ws

# umieralnosc kobiet 20-34 (jedyna grupa, w ktorej sa dzis zaszczepione kobiety)
y = d[d.age.isin([20, 25, 30])].groupby(["iso", "year"], as_index=False).agg(
    dd=("deaths", "sum"), pp=("pop", "sum"))
y["rate"] = y.dd / y.pp * 1e5

out = {"asr": {}, "young": {}, "coverage": {}}
for iso in CTRY.values():
    s = agg[agg.iso == iso].sort_values("year")
    if len(s):
        # lata zapisujemy JAWNIE — serie maja luki (POL 1997-98, GBR 2000),
        # wiec zalozenie ciaglosci przesunieloby cala linie.
        out["asr"][iso] = {"years": [int(v) for v in s.year],
                           "v": [round(float(v), 2) for v in s.asr]}
    ys = y[y.iso == iso].sort_values("year").set_index("year").rate
    ys = ys.rolling(3, center=True).mean().dropna()      # male liczby -> wygladzamy
    if len(ys):
        out["young"][iso] = {"years": [int(v) for v in ys.index],
                             "v": [round(float(v), 3) for v in ys.values]}

# pokrycie szczepieniami HPV (WHO GHO)
cov = {}
for f in ["hpv_cov.json", "hpv_cov2.json"]:
    for r in json.load(open(SCR / f))["value"]:
        if r.get("NumericValue") is not None:
            cov.setdefault(r["SpatialDim"], {})[int(r["TimeDim"])] = round(float(r["NumericValue"]), 1)
for iso, v in cov.items():
    if iso in CTRY.values():
        out["coverage"][iso] = {"years": sorted(v), "pct": [v[k] for k in sorted(v)]}

(WEB / "cervix-wide.json").write_text(json.dumps(out, separators=(",", ":")))

print()
print("=== WYRZUCONE ===", DROPPED)
print()
print("=== RAK SZYJKI: ASR dzis vs pokrycie szczepieniami ===")
print(f"  {'kraj':5} {'ASR (ost. rok)':>16} {'pokrycie HPV':>14}   {'zmiana 20-34, 2012->2022':>26}")
for iso in ["NOR", "SWE", "DNK", "AUS", "PRT", "FIN", "NLD", "GBR", "USA", "ESP", "POL"]:
    a = out["asr"].get(iso)
    c = out["coverage"].get(iso)
    yv = out["young"].get(iso)
    asr = f"{a['v'][-1]:.2f} ({a['years'][-1]})" if a else "-"
    cv = f"{c['pct'][-1]:.0f}%" if c else "-"
    ch = "-"
    if yv:
        yrs = dict(zip(yv["years"], yv["v"]))
        last = max(yy for yy in yrs if yy >= 2020) if any(yy >= 2020 for yy in yrs) else None
        if 2012 in yrs and last and yrs[2012] > 0:
            ch = f"{100 * (yrs[last] - yrs[2012]) / yrs[2012]:+.0f}%  (do {last})"
    print(f"  {iso:5} {asr:>16} {cv:>14}   {ch:>26}")

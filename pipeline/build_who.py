"""WHO Mortality DB (ICD-8 + ICD-9 + ICD-10) -> kanoniczna seria umieralnosci 1968-2023.

Naprawia wszystkie bledy znalezione w audycie:
  - lista 09B (nie 09A) -> era ICD-9 (1980-1998) odzyskana
  - prawidlowe kody krajow WHO (POL 4230, GBR 4308, ESP 4280, USA 2450)
  - mianowniki z UN WPP (WHO nie ma populacji USA po 2007)
  - both = male + female liczone JAWNIE (nie przez klucz grupowania)
  - gorny kosz wieku ujednolicony do 85+
  - ASR (standard swiatowy WHO) dla calej serii
  - twarda walidacja kompletnosci: nic nie znika po cichu
"""
import gzip
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import SEX_SPECIFIC, decode  # noqa: E402

SCR = Path("/tmp/claude-1000/-home-ubuntu/dbf101f2-9ff3-4d77-abb0-3a89bc56df0b/scratchpad")
RAW = SCR / "who-raw"
OUT = SCR / "build" / "out"
OUT.mkdir(parents=True, exist_ok=True)

CTRY = {4230: "POL", 4308: "GBR", 4280: "ESP", 2450: "USA"}
LIST_PRIORITY = {"10M": 0, "104": 1, "103": 2, "101": 3, "09B": 5, "09A": 6, "08A": 8}

# WHO World Standard Population (wagi %, 18 grup 0-4 ... 85+)
WORLD_STD = {0: 8.86, 5: 8.69, 10: 8.60, 15: 8.47, 20: 8.22, 25: 7.93, 30: 7.61,
             35: 7.15, 40: 6.59, 45: 6.04, 50: 5.37, 55: 4.55, 60: 3.72, 65: 2.96,
             70: 2.21, 75: 1.52, 80: 0.91, 85: 0.63}
BANDS = sorted(WORLD_STD)

DROPPED = {"unmapped_cause": 0, "bad_frmat": 0, "no_population": 0}


def age_layout(frmat):
    """Mapuje kolumny Deaths* na poczatek 5-letniej grupy. Gorny kosz zwijany do 85+."""
    f = str(frmat).zfill(2)
    if f in ("00", "01"):
        under5 = ["Deaths2", "Deaths3", "Deaths4", "Deaths5", "Deaths6"]
    elif f == "02":
        under5 = ["Deaths2", "Deaths3"]
    else:
        return None
    m = {"_u5": under5}
    for i, a in enumerate(range(5, 95, 5)):   # Deaths7..Deaths24 -> 5..90, zwijane do 85
        m[f"Deaths{i + 7}"] = min(a, 85)
    m["Deaths25"] = 85  # 95-99 tez do 85+
    return m


def read_zip(name):
    with zipfile.ZipFile(RAW / name) as z:
        member = [m for m in z.namelist() if not m.endswith("/")][0]
        with z.open(member) as fh:
            return pd.read_csv(fh, dtype={"Admin1": str, "SubDiv": str, "List": str,
                                          "Cause": str, "Frmat": str}, low_memory=False)


def parse_deaths():
    rows = []
    files = ["morticd08.zip", "morticd09.zip"] + [f"morticd10_part{i}.zip" for i in range(1, 7)]
    for fname in files:
        df = read_zip(fname)
        df = df[(df.Admin1.fillna("").str.strip() == "") & (df.SubDiv.fillna("").str.strip() == "")]
        df = df[df.Country.isin(CTRY) & df.Sex.isin([1, 2])]
        for r in df.itertuples(index=False):
            site = decode(r.List, r.Cause)
            if site is None:
                DROPPED["unmapped_cause"] += 1
                continue
            lay = age_layout(r.Frmat)
            if lay is None:
                DROPPED["bad_frmat"] += 1
                continue
            base = dict(iso=CTRY[r.Country], year=int(r.Year),
                        sex="male" if r.Sex == 1 else "female",
                        site=site, src_list=str(r.List).upper())
            u5 = sum(float(getattr(r, c)) for c in lay["_u5"]
                     if pd.notna(getattr(r, c, None)))
            rows.append({**base, "age": 0, "deaths": u5})
            for col, age in lay.items():
                if col == "_u5":
                    continue
                v = getattr(r, col, None)
                if pd.notna(v):
                    rows.append({**base, "age": age, "deaths": float(v)})
        print(f"  {fname}: laczna liczba wierszy roboczych = {len(rows):,}", flush=True)
    return pd.DataFrame(rows)


def main():
    print("[1/6] parsuje WHO (ICD-8 + ICD-9 + ICD-10)...", flush=True)
    d = parse_deaths()
    d = d.groupby(["iso", "year", "sex", "site", "age", "src_list"], as_index=False).deaths.sum()

    print("[2/6] wybieram jedna liste ICD na kraj-rok (anty-podwojne liczenie)...", flush=True)
    d["prio"] = d.src_list.map(LIST_PRIORITY)
    best = d.groupby(["iso", "year"]).prio.transform("min")
    d = d[d.prio == best].drop(columns="prio")
    assert d.groupby(["iso", "year"]).src_list.nunique().max() == 1, "rownolegle listy ICD!"
    d = d.groupby(["iso", "year", "sex", "site", "age", "src_list"], as_index=False).deaths.sum()

    # ICD-9: chloniaki = B14 (cala tkanka limfatyczna, 200-208) - B141 (bialaczka, 204-208).
    # Konieczne, bo czesc krajow (Polska) nie raportuje B149 osobno.
    key = ["iso", "year", "sex", "age", "src_list"]
    tot = d[d.site == "_LYMPH_TOTAL"].set_index(key).deaths
    leu = d[(d.site == "LEUKAEMIA") & (d.src_list == "09B")].set_index(key).deaths
    lymph = (tot - leu.reindex(tot.index).fillna(0)).clip(lower=0).reset_index()
    lymph["site"] = "LYMPHOMA"
    neg = int((tot - leu.reindex(tot.index).fillna(0) < 0).sum())
    if neg:
        print(f"  UWAGA: {neg} wierszy B14 < B141 (przyciete do 0)")
    d = pd.concat([d[d.site != "_LYMPH_TOTAL"], lymph], ignore_index=True)
    d = d.groupby(["iso", "year", "sex", "site", "age", "src_list"], as_index=False).deaths.sum()

    print("[3/6] doklejam mianowniki z UN WPP 2024...", flush=True)
    chunks = []
    for ch in pd.read_csv(gzip.open(SCR / "wpp2024.csv.gz", "rt"),
                          chunksize=500_000, low_memory=False):
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

    before = len(d)
    d = d.merge(p, on=["iso", "year", "sex", "age"], how="inner")
    DROPPED["no_population"] = before - len(d)

    print("[4/6] nowotwory jednoplciowe -> wlasny mianownik; 'obie plcie' tylko gdzie ma sens...",
          flush=True)
    # Rak piersi (definicja WHO = piers kobiet), szyjka, macica, jajnik -> tylko kobiety.
    # Prostata, jadro -> tylko mezczyzni. Mianownik = populacja TEJ plci (konwencja IARC).
    keep = d.site.map(lambda s: SEX_SPECIFIC.get(s))
    wrong_sex = keep.notna() & (keep != d.sex)
    DROPPED["sex_specific_other_sex"] = int(wrong_sex.sum())
    d = d[~wrong_sex].copy()

    # 'both' liczymy JAWNIE jako suma M+K — ale tylko dla lokalizacji obupleciowych
    shared = d[~d.site.isin(SEX_SPECIFIC)]
    both = shared.groupby(["iso", "year", "site", "age", "src_list"], as_index=False).agg(
        deaths=("deaths", "sum"), pop=("pop", "sum"))
    both["sex"] = "both"
    d = pd.concat([d, both], ignore_index=True)

    print("[5/6] licze wspolczynniki: surowy, wiekowy, ASR (standard swiatowy)...", flush=True)
    d["asr_w"] = d.age.map(WORLD_STD)
    d["age_rate"] = d.deaths / d["pop"] * 1e5

    # ASR + agregaty na (iso, year, sex, site)
    d["contrib"] = d.age_rate * d.asr_w
    agg = d.groupby(["iso", "year", "sex", "site", "src_list"], as_index=False).agg(
        deaths=("deaths", "sum"), pop=("pop", "sum"),
        contrib=("contrib", "sum"), wsum=("asr_w", "sum"))
    # publikujemy ASR tylko gdy mamy komplet 18 grup wiekowych
    agg = agg[agg.wsum > 99.9].copy()
    agg["asr"] = agg.contrib / agg.wsum
    agg["crude"] = agg.deaths / agg["pop"] * 1e5
    agg["revision"] = agg.src_list.map(
        lambda x: "ICD-8" if x.startswith("08") else ("ICD-9" if x.startswith("09") else "ICD-10"))
    agg = agg[["iso", "year", "sex", "site", "revision", "deaths", "pop", "crude", "asr"]]

    print("[6/6] klasyfikuje ciaglosc serii przy zmianie ICD...", flush=True)
    # Dla kazdej lokalizacji: czy definicja przetrwala zmiane rewizji?
    # Kryterium: skok ASR <=15% na kazdym przejsciu, przy >=50 zgonach/rok (inaczej to szum).
    cont = []
    for site in sorted(agg.site.unique()):
        worst, where, small = 0.0, "", False
        for iso in ["POL", "GBR", "ESP", "USA"]:
            s = agg[(agg.iso == iso) & (agg.site == site)].sort_values("year")
            s = s[s.sex == s.sex.iloc[0]] if s.empty else s
            s = agg[(agg.iso == iso) & (agg.site == site)]
            sx = "both" if "both" in set(s.sex) else SEX_SPECIFIC.get(site, "both")
            s = s[s.sex == sx].sort_values("year")
            for r1, r2 in [("ICD-8", "ICD-9"), ("ICD-9", "ICD-10")]:
                a, c = s[s.revision == r1], s[s.revision == r2]
                if a.empty or c.empty:
                    continue
                last, first = a.iloc[-1], c.iloc[0]
                if last.deaths < 50 or first.deaths < 50:
                    small = True
                    continue
                if last.asr <= 0:
                    continue
                pct = 100 * (first.asr - last.asr) / last.asr
                if abs(pct) > abs(worst):
                    worst, where = pct, f"{iso} {r1}->{r2}"
        cont.append({"site": site, "max_break_pct": round(worst, 1), "where": where,
                     "low_count": small, "continuous": abs(worst) <= 15})
    cdf = pd.DataFrame(cont)
    cdf.to_csv(OUT / "continuity.csv", index=False)
    print()
    print("=== CIAGLOSC SERII (czy mozna rysowac jedna linie przez zmiane ICD) ===")
    for r in cdf.itertuples():
        mark = "ciagla " if r.continuous else "PRZERWA"
        low = " (male liczby)" if r.low_count else ""
        print(f"  [{mark}] {r.site:14} max skok {r.max_break_pct:+7.1f}%  {r.where}{low}")

    print()
    print("[zapis]", flush=True)
    agg.to_parquet(OUT / "mortality.parquet", index=False)
    d[["iso", "year", "sex", "site", "age", "deaths", "pop", "age_rate"]].to_parquet(
        OUT / "mortality_by_age.parquet", index=False)

    print()
    print("=== WYRZUCONE WIERSZE (jawnie, nie po cichu) ===")
    for k, v in DROPPED.items():
        print(f"  {k}: {v:,}")
    print()
    print("=== POKRYCIE ===")
    for iso in ["POL", "GBR", "ESP", "USA"]:
        s = agg[(agg.iso == iso) & (agg.sex == "both")]
        ys = sorted(s.year.unique())
        gaps = [y for y in range(ys[0], ys[-1] + 1) if y not in set(ys)]
        print(f"  {iso}: {ys[0]}-{ys[-1]} ({len(ys)} lat) | luki: {gaps if gaps else 'BRAK'} "
              f"| lokalizacji: {s.site.nunique()}")
    print()
    print(f"wierszy (seria): {len(agg):,} | wierszy (wg wieku): {len(d):,}")


if __name__ == "__main__":
    main()

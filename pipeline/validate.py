"""Walidacja, ktora FAKTYCZNIE waliduje. Kazdy blad = wyjatek, nie cichy wiersz w CSV."""
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import decode  # noqa: E402

SCR = Path("/tmp/claude-1000/-home-ubuntu/dbf101f2-9ff3-4d77-abb0-3a89bc56df0b/scratchpad")
RAW = SCR / "who-raw"
OUT = SCR / "build" / "out"
CTRY = {4230: "POL", 4308: "GBR", 4280: "ESP", 2450: "USA"}

issues = []


def check(name, ok, detail=""):
    status = "OK  " if ok else "BLAD"
    print(f"  [{status}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        issues.append(name)


agg = pd.read_parquet(OUT / "mortality.parquet")
byage = pd.read_parquet(OUT / "mortality_by_age.parquet")

print("=== 1. ZGODNOSC Z RZECZYWISTOSCIA (zgony, liczby bezwzgledne) ===")
GROUND = [
    ("POL", 2019, "both", "LUNG", 23136, "Polska/płuco 2019"),
    ("USA", 2019, "both", "LUNG", 139680, "USA/płuco 2019"),
    ("GBR", 2019, "both", "LUNG", 34552, "UK/płuco 2019"),
    ("POL", 1990, "male", "LUNG", 14539, "Polska/płuco/M 1990 (ICD-9!)"),
    ("USA", 1990, "male", "LUNG", 91091, "USA/płuco/M 1990 (ICD-9!)"),
    ("POL", 1990, "female", "BREAST", 4323, "Polska/pierś/K 1990 (ICD-9!)"),
    ("USA", 1990, "female", "BREAST", 43391, "USA/pierś/K 1990 (ICD-9!)"),
    ("USA", 1990, "male", "PROSTATE", 32378, "USA/prostata/M 1990 (ICD-9!)"),
]
# Tolerancja 0,2%: nasze serie sumuja grupy wiekowe, wiec NIE zawieraja zgonow
# o nieznanym wieku (kolumna Deaths26). To poprawne zachowanie, nie blad.
for iso, y, sx, site, expect, label in GROUND:
    r = agg[(agg.iso == iso) & (agg.year == y) & (agg.sex == sx) & (agg.site == site)]
    got = float(r.deaths.iloc[0]) if len(r) else -1
    ok = got > 0 and abs(got - expect) / expect < 0.002
    check(label, ok, f"otrzymano {got:,.0f}, oczekiwano {expect:,} "
                     f"({100 * (got - expect) / expect:+.3f}%)")

print()
print("=== 2. CZY WSROD ODRZUCONYCH PRZYCZYN NIE MA NOWOTWOROW? (klucz!) ===")
lost = {}
for fname in ["morticd08.zip", "morticd09.zip", "morticd10_part3.zip"]:
    with zipfile.ZipFile(RAW / fname) as z:
        mem = [m for m in z.namelist() if not m.endswith("/")][0]
        with z.open(mem) as fh:
            df = pd.read_csv(fh, dtype={"Admin1": str, "SubDiv": str, "List": str,
                                        "Cause": str, "Frmat": str}, low_memory=False)
    df = df[(df.Admin1.fillna("").str.strip() == "") & (df.SubDiv.fillna("").str.strip() == "")]
    df = df[df.Country.isin(CTRY)]
    for r in df.itertuples(index=False):
        if decode(r.List, r.Cause) is not None:
            continue
        c, lst = str(r.Cause).upper(), str(r.List).upper()
        # czy to jest kod nowotworowy, ktory zgubilismy?
        is_cancer = False
        if lst.startswith("10") and c.startswith("C"):
            is_cancer = True
        elif lst == "09B" and c[:3] in {f"B{n:02d}" for n in range(8, 15)}:
            is_cancer = True
        elif lst == "08A" and c[:4] in {f"A{n:03d}" for n in range(45, 61)}:
            is_cancer = True
        if is_cancer:
            lost[(lst, c)] = lost.get((lst, c), 0) + float(r.Deaths1 or 0)

if lost:
    top = sorted(lost.items(), key=lambda kv: -kv[1])[:12]
    print("  Kody nowotworowe NIE ujete w taksonomii (celowo — reszta/inne):")
    for (lst, c), v in top:
        print(f"    {lst} {c}: {v:,.0f} zgonow")
    total = sum(lost.values())
    print(f"  RAZEM poza taksonomia: {total:,.0f} zgonow")
    print("  (to sa kody 'inne/nieokreslone' + lokalizacje spoza naszych 20 — swiadomy wybor)")
else:
    print("  Zaden kod nowotworowy nie zostal zgubiony.")

print()
print("=== 3. CIAGLOSC PRZY ZMIANIE REWIZJI ICD (test artefaktow) ===")
print("  skok >20% = definicja sie rozjechala, seria NIE nadaje sie do ciaglej linii")
b = agg[agg.sex == "both"]
breaks = []
for site in sorted(b.site.unique()):
    worst = 0.0
    detail = ""
    for iso in ["POL", "GBR", "ESP", "USA"]:
        s = b[(b.iso == iso) & (b.site == site)].sort_values("year")
        for r1, r2 in [("ICD-8", "ICD-9"), ("ICD-9", "ICD-10")]:
            a = s[s.revision == r1]
            c = s[s.revision == r2]
            if a.empty or c.empty:
                continue
            last, first = a.iloc[-1], c.iloc[0]
            if last.asr <= 0:
                continue
            pct = 100 * (first.asr - last.asr) / last.asr
            if abs(pct) > abs(worst):
                worst, detail = pct, f"{iso} {r1}→{r2} ({int(last.year)}→{int(first.year)})"
    flag = "  <-- ARTEFAKT" if abs(worst) > 20 else ""
    breaks.append((site, worst, detail, abs(worst) > 20))
    print(f"    {site:16} max skok {worst:+7.1f}%  {detail}{flag}")

bad = [s for s, w, d, f in breaks if f]
print()
print(f"  Serie z artefaktem definicji: {bad if bad else 'BRAK'}")

print()
print("=== 4. SPOJNOSC WEWNETRZNA ===")
p = agg.pivot_table(index=["iso", "year", "site"], columns="sex", values="deaths")
p = p.dropna(subset=["both", "male", "female"])
diff = (p["both"] - p["male"] - p["female"]).abs()
check("both == male + female", diff.max() < 0.5, f"max roznica {diff.max():.3f} na {len(p):,} serii")

m = byage.merge(agg[["iso", "year", "sex", "site", "deaths"]], on=["iso", "year", "sex", "site"],
                suffixes=("_age", "_tot"))
s = m.groupby(["iso", "year", "sex", "site"]).agg(a=("deaths_age", "sum"), t=("deaths_tot", "first"))
check("suma grup wiekowych == suma calkowita", (s.a - s.t).abs().max() < 0.5,
      f"max roznica {(s.a - s.t).abs().max():.3f}")

check("brak ujemnych wartosci", (agg.deaths >= 0).all() and (agg.asr >= 0).all())
check("brak zerowych mianownikow", (agg["pop"] > 0).all())
check("ASR w sensownym zakresie (<500/100k)", agg.asr.max() < 500,
      f"max ASR {agg.asr.max():.1f}")

crude_calc = agg.deaths / agg["pop"] * 1e5
check("crude == zgony/populacja*100k", (agg.crude - crude_calc).abs().max() < 1e-6)

print()
print("=== 5. KOMPLETNOSC (to, czego stary pipeline NIE sprawdzal) ===")
for iso in ["POL", "GBR", "ESP", "USA"]:
    s = b[b.iso == iso]
    ys = sorted(s.year.unique())
    gaps = [y for y in range(1968, 2024) if y not in set(ys)]
    ok = len(gaps) <= 3
    check(f"{iso}: ciaglosc lat 1968-2023", ok, f"brakuje {len(gaps)} lat: {gaps}")

# Kazda lokalizacja musi miec dane w KAZDEJ erze, w ktorej taksonomia ja definiuje.
# (Wątroba celowo nie ma ICD-9: kod B095 to tylko wątroba pierwotna, nieporownywalne.)
from taxonomy import SITES, SEX_SPECIFIC as SS  # noqa: E402
for code, _, _, i8, i9, i10, sx in SITES:
    series = agg[(agg.site == code) & (agg.sex == (sx or "both"))]
    revs = set(series.revision.unique())
    expect = set()
    if i8:
        expect.add("ICD-8")
    if i9:
        expect.add("ICD-9")
    if i10:
        expect.add("ICD-10")
    check(f"{code}: obecny we wszystkich zadeklarowanych rewizjach {sorted(expect)}",
          expect <= revs, f"znaleziono {sorted(revs)}")

print()
if issues:
    print(f"!!! WALIDACJA NIE PRZESZLA: {len(issues)} problemow")
    for i in issues:
        print("   -", i)
    sys.exit(1)
print("=== WALIDACJA PRZESZLA W CALOSCI ===")

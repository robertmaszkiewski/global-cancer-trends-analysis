"""Domyka warstwe HPV: 11 krajow, ekspozycja liczona od ROKU STARTU programu (WHO),
gardlo srodkowe, i kontrfaktyczny koszt polskiej zwloki."""
import json
from pathlib import Path

import pandas as pd

SCR = Path("/tmp/claude-1000/-home-ubuntu/dbf101f2-9ff3-4d77-abb0-3a89bc56df0b/scratchpad")
WEB = SCR / "build" / "web"
OUT = SCR / "build" / "out"

wide = json.load(open(WEB / "cervix-wide.json"))
oro = json.load(open(WEB / "orophar.json"))
hpv = json.load(open(WEB / "cancer-hpv.json"))

# Rok wprowadzenia krajowego programu — WHO xMart MT_HPV (oficjalny formularz sprawozdawczy)
START = {"USA": 2006, "AUS": 2007, "DNK": 2007, "ESP": 2007, "GBR": 2008, "PRT": 2008,
         "NOR": 2009, "SWE": 2010, "NLD": 2010, "FIN": 2013, "POL": 2023}

# --- scatter: lata dzialania programu do 2022 + pokrycie vs zmiana umieralnosci 20-34 ---
pts = []
for iso, cov in wide["coverage"].items():
    yv = wide["young"].get(iso)
    if not yv:
        continue
    yrs = dict(zip(yv["years"], yv["v"]))
    last = max((y for y in yrs if y >= 2020), default=None)
    if 2012 not in yrs or last is None or yrs[2012] <= 0:
        continue
    pts.append({
        "iso": iso,
        "years": max(0, 2022 - START[iso]),      # ile lat program dzialal
        "cov": cov["pct"][-1],                    # pokrycie (ostatni rok)
        "chg": round(100 * (yrs[last] - yrs[2012]) / yrs[2012], 1),
        "start": START[iso],
    })
pts.sort(key=lambda p: -p["years"])

print("=== EKSPOZYCJA (lata programu do 2022) vs ZMIANA umieralnosci 20-34 ===")
print(f"  {'kraj':5} {'start':>6} {'lat':>4} {'pokrycie':>9} {'zmiana':>8}")
for p in pts:
    print(f"  {p['iso']:5} {p['start']:>6} {p['years']:>4} {p['cov']:>8.0f}% {p['chg']:>7.0f}%")


def spearman(xs, ys):
    def rk(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(s):
            r[i] = pos + 1
        return r
    rx, ry = rk(xs), rk(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return num / den if den else 0


print()
for label, key in [("lata programu", "years"), ("pokrycie", "cov")]:
    rho = spearman([p[key] for p in pts], [p["chg"] for p in pts])
    no_esp = [p for p in pts if p["iso"] != "ESP"]
    rho2 = spearman([p[key] for p in no_esp], [p["chg"] for p in no_esp])
    print(f"  Spearman ({label:14}) : rho = {rho:+.2f}  (n={len(pts)})"
          f"   |  bez Hiszpanii: {rho2:+.2f}  (n={len(no_esp)})")

# --- kontrfaktyk: ile kosztuje polska zwloka ---
m = pd.read_parquet(OUT / "mortality.parquet")
pol = m[(m.iso == "POL") & (m.site == "CERVIX") & (m.sex == "female")].sort_values("year").iloc[-1]
print()
print("=== KOSZT ZWLOKI: Polska vs kraje z najlepszymi wynikami ===")
print(f"  Polska {int(pol.year)}: {int(pol.deaths):,} zgonow, ASR {pol.asr:.2f}")
best = {"FIN": 0.98, "SWE": 1.16, "NLD": 1.23, "AUS": 1.39}
for iso, asr in best.items():
    would = pol.deaths * asr / pol.asr
    print(f"  gdyby Polska miala ASR jak {iso} ({asr:.2f}): ~{int(would):,} zgonow"
          f"  -> {int(pol.deaths - would):,} mniej rocznie")
avg = sum(best.values()) / len(best)
would = pol.deaths * avg / pol.asr
print(f"  srednia tej czworki ({avg:.2f}): ~{int(would):,} zgonow -> "
      f"**{int(pol.deaths - would):,} zgonow rocznie roznicy**")
print()
print("  UWAGA: szczepienia nie tlumacza z tego NICZEGO. Polskie zaszczepione")
print("  roczniki maja dzis 12-14 lat. Ta luka to badania przesiewowe i leczenie.")

hpv["wide"] = wide
hpv["oro"] = oro
hpv["scatter"] = pts
hpv["start"] = START
hpv["gap"] = {"polDeaths": int(pol.deaths), "polAsr": round(float(pol.asr), 2),
              "bestAvg": round(avg, 2), "avoidable": int(pol.deaths - would)}
(WEB / "cancer-hpv.json").write_text(json.dumps(hpv, separators=(",", ":")))
print()
print("zapisano cancer-hpv.json:", round((WEB / "cancer-hpv.json").stat().st_size / 1024, 1), "KB")

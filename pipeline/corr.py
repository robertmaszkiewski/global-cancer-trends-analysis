"""Czy pokrycie szczepieniami tlumaczy spadek umieralnosci mlodych kobiet?
n=9. To wciaz malo — ale 9 punktow to nie 4."""
import json
from pathlib import Path

WEB = Path("/tmp/claude-1000/-home-ubuntu/dbf101f2-9ff3-4d77-abb0-3a89bc56df0b/scratchpad/build/web")
d = json.load(open(WEB / "cervix-wide.json"))

# Ekspozycja: srednie pokrycie 2010-2015 — to sa roczniki, ktore do 2022 maja 20-34 lata.
# (Szczepione ok. 2008-2013 w wieku 12-13 lat -> rocznik 1995-2001 -> w 2022 ma 21-27 lat.)
rows = []
for iso, cov in d["coverage"].items():
    yv = d["young"].get(iso)
    if not yv:
        continue
    yrs = dict(zip(yv["years"], yv["v"]))
    last = max((y for y in yrs if y >= 2020), default=None)
    if 2012 not in yrs or last is None or yrs[2012] <= 0:
        continue
    early = [p for y, p in zip(cov["years"], cov["pct"]) if 2010 <= y <= 2015]
    exposure = sum(early) / len(early) if early else 0.0   # Polska: brak programu -> 0
    change = 100 * (yrs[last] - yrs[2012]) / yrs[2012]
    rows.append({"iso": iso, "cov": round(exposure, 1), "chg": round(change, 1), "last": last})

rows.sort(key=lambda r: -r["cov"])
print("=== EKSPOZYCJA (srednie pokrycie 2010-2015) vs ZMIANA umieralnosci 20-34 ===")
print(f"  {'kraj':5} {'pokrycie 2010-15':>17} {'zmiana':>9}")
for r in rows:
    print(f"  {r['iso']:5} {r['cov']:>16.1f}% {r['chg']:>8.0f}%")


def spearman(xs, ys):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(s):
            r[i] = pos + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return num / den if den else 0


xs = [r["cov"] for r in rows]
ys = [r["chg"] for r in rows]
rho = spearman(xs, ys)
print()
print(f"  n = {len(rows)}")
print(f"  Spearman rho (pokrycie vs zmiana) = {rho:+.2f}")
print("  (ujemne rho = wyzsze pokrycie -> wiekszy spadek umieralnosci)")

# bez Hiszpanii — czy to ona psuje wzorzec?
noesp = [r for r in rows if r["iso"] != "ESP"]
rho2 = spearman([r["cov"] for r in noesp], [r["chg"] for r in noesp])
print()
print(f"  bez Hiszpanii: n = {len(noesp)}, rho = {rho2:+.2f}")
print()
print("=== CZY HISZPANIA TO ODSTAJACY PUNKT? ===")
esp = next(r for r in rows if r["iso"] == "ESP")
others = [r["chg"] for r in rows if r["iso"] != "ESP"]
mean = sum(others) / len(others)
sd = (sum((x - mean) ** 2 for x in others) / (len(others) - 1)) ** .5
print(f"  Hiszpania: {esp['chg']:+.0f}%   pozostale: srednia {mean:+.0f}%, odch. std {sd:.0f}")
print(f"  odchylenie Hiszpanii: {(esp['chg'] - mean) / sd:+.1f} sigma")
print()
print("=== ILE ZGONOW STOI ZA HISZPANSKIM PUNKTEM? ===")
print("  Hiszpania ma ok. 16-23 zgonow rocznie w grupie 20-34.")
print("  Przy takich liczbach zmiana o kilka zgonow daje kilkadziesiat procent.")
print("  To jest kandydat na szum, nie na obalenie wzorca — ale NIE mozna tego przesadzic.")

"""Jedno miejsce, w ktorym mieszkaja sciezki.

Wczesniej kazdy skrypt mial zaszyta sciezke absolutna do katalogu roboczego autora,
przez co nie uruchamial sie u nikogo innego. Teraz:

  - domyslnie wszystko siedzi w  <repo>/data/
  - mozna to nadpisac zmienna srodowiskowa CANCER_DATA

Uklad katalogow:
  data/raw/       pobrane pliki zrodlowe (morticd*.zip, mort_pop.zip, wpp2024.csv.gz, hpv_cov*.json)
  data/interim/   posrednie parquet (mortality.parquet, mortality_by_age.parquet, continuity.csv)
  data/site/      gotowe JSON-y dla strony (data/web nalezy do starego pipeline'u)
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CANCER_DATA", ROOT / "data"))

RAW = DATA / "raw"        # dane zrodlowe (WHO, UN WPP, WHO GHO)
OUT = DATA / "interim"    # wyniki posrednie
WEB = DATA / "site"       # JSON-y serwowane przez strone
                          # UWAGA: NIE data/web — tam mieszkaja partycje
                          # oryginalnego pipeline'u i nie wolno ich nadpisac

for _d in (RAW, OUT, WEB):
    _d.mkdir(parents=True, exist_ok=True)


def require(path, what):
    """Czytelny blad zamiast zagadkowego FileNotFoundError kilka funkcji glebiej."""
    p = Path(path)
    if not p.exists():
        raise SystemExit(
            f"Brakuje pliku: {p}\n"
            f"  ({what})\n"
            f"  Pobierz dane zrodlowe do {RAW} albo wskaz inny katalog przez CANCER_DATA."
        )
    return p

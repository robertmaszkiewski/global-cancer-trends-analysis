# Pipeline (przebudowany)

Odtwarza serię umieralności 1968–2023 dla POL/GBR/ESP/USA (plus 7 krajów w warstwie HPV)
i buduje z niej dane dla strony.

## Uruchomienie

```bash
cd pipeline

python build_who.py          # WHO (ICD-8/9/10) + UN WPP  -> mortality.parquet + continuity.csv
python validate.py           # walidacja; kod wyjścia ≠ 0 gdy cokolwiek nie przejdzie
python build_web.py          # kompaktowe JSON-y dla strony

# warstwa HPV / rak szyjki macicy
python build_hpv.py          # pokrycie szczepieniami, dzietność, rozkład wieku
python build_cervix_wide.py  # rak szyjki w 11 krajach
python build_orophar.py      # gardło: podmiejsca HPV-zależne vs tytoniowe
python finalize_hpv.py       # scala warstwę HPV + kontrfaktyk
```

## Gdzie leżą dane

Ścieżki są w jednym miejscu — `paths.py`. Domyślnie:

```
data/raw/        pliki źródłowe (pobierasz sam, patrz niżej)
data/interim/    wyniki pośrednie (parquet)
data/web/        gotowe JSON-y dla strony
```

Inny katalog: `CANCER_DATA=/gdzie/chcesz python build_who.py`

## Czego potrzebuje `data/raw/`

| plik | skąd |
|---|---|
| `morticd08.zip`, `morticd09.zip`, `morticd10_part1..6.zip`, `mort_pop.zip`, `mort_country_codes.zip` | [WHO Mortality Database](https://www.who.int/data/data-collection-tools/who-mortality-database) |
| `wpp2024.csv.gz` | UN WPP 2024 — `WPP2024_PopulationBySingleAgeSex_Medium_1950-2023.csv.gz` |
| `hpv_cov.json`, `hpv_cov2.json` | WHO GHO OData, wskaźnik `SDGHPVRECEIVED` |
| `age_first_birth.json` | Eurostat `demo_find`, `indic_de=AGEMOTH1` |
| `cancer_observations.parquet` | warstwa IARC (GLOBOCAN 2024 + prognozy) |

`data/raw/` jest w `.gitignore` — dane źródłowe nie trafiają do repo.

## Co ten pipeline naprawia

| Problem w pierwszej wersji | Naprawa |
|---|---|
| Brak lat 1980–1998 | Kraje raportują ICD-9 na liście **`09B`**, nie `09A` |
| Złe kody krajów WHO | POL **4230**, GBR **4308**, ESP **4280**, USA **2450** |
| Brak współczynników dla USA po 2007 | WHO nie ma populacji USA po 2007 → **UN WPP** (szew zmierzony: 0,09%) |
| Brak standaryzacji wiekiem | ASR (standard światowy WHO) dla całej serii |
| Puste „obie płcie" | Liczone jawnie jako M+K; jednopłciowe mają własny mianownik |
| Ciche gubienie wierszy | Każdy odrzucony wiersz jest liczony i raportowany |
| Dryf definicji między rewizjami ICD | Taksonomia z dokumentacji WHO + test ciągłości na każdym szwie |

## Uwaga o kodach ICD-9

`taxonomy.py` zawiera kody **wprost z `WHO_Mortality_Database_Documentation.pdf`**.
Nie zgaduj ich. `B130` to **mózg** (nie chłoniak), białaczka to **`B141`** (nie `B139`),
a `B113` to pierś **tylko u kobiet**. Chłoniaki trzeba wyliczyć jako `B14 − B141`,
bo Polska nie raportuje `B149` osobno.

## Odtwarzalność

`build_web.py` uruchomiony na czystym repo produkuje pliki **bit w bit identyczne**
z tymi, które serwuje <https://rmportfolio.co.uk/case-studies/cancer.html>.

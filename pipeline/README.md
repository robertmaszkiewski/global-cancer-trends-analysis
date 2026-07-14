# Pipeline (przebudowany)

Zastępuje poprzedni pipeline. Odtwarza serię umieralności 1968–2023 dla POL/GBR/ESP/USA.

## Kolejność

```bash
python build_who.py     # WHO (ICD-8/9/10) + UN WPP -> mortality.parquet + continuity.csv
python validate.py      # walidacja; kod wyjścia != 0 gdy cokolwiek nie przejdzie
python build_web.py     # kompaktowe JSON-y dla strony
```

## Czego potrzebuje

- `who-raw/` — pliki WHO Mortality Database: `morticd08.zip`, `morticd09.zip`,
  `morticd10_part1..6.zip`, `mort_pop.zip`, `mort_country_codes.zip`
- `wpp2024.csv.gz` — UN World Population Prospects 2024
  (`WPP2024_PopulationBySingleAgeSex_Medium_1950-2023.csv.gz`)

## Co naprawia

| Problem | Naprawa |
|---|---|
| Brak lat 1980–1998 | Kraje raportują ICD-9 na liście **`09B`**, nie `09A` |
| Złe kody krajów | POL **4230**, GBR **4308**, ESP **4280**, USA **2450** |
| Brak stawek dla USA po 2007 | WHO nie ma populacji USA po 2007 → **UN WPP** (szew: 0,09%) |
| Brak ASR | Standaryzacja do WHO World Standard dla całej serii |
| Puste „obie płcie" | Liczone jawnie jako M+K; jednopłciowe mają własny mianownik |
| Ciche gubienie wierszy | Każdy odrzucony wiersz jest liczony i raportowany |
| Dryf definicji ICD | Taksonomia z dokumentacji WHO + test ciągłości na każdym szwie |

## Uwaga

`taxonomy.py` zawiera kody **wprost z `WHO_Mortality_Database_Documentation.pdf`**.
Nie zgaduj ich — `B130` to mózg (nie chłoniak), białaczka to `B141` (nie `B139`),
a `B113` to pierś **tylko u kobiet**. Na tym się przewróciłem, zanim sięgnąłem po dokumentację.

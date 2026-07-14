# Portfolio and VPS integration / Integracja z portfolio i VPS

The cancer explorer is intentionally packaged as an independent static folder. It does not modify the VPS portfolio and can be reviewed before it is linked from the homepage.

Eksplorator jest celowo pakowany jako niezależny katalog statyczny. Nie modyfikuje portfolio na VPS i można go sprawdzić przed dodaniem linku na stronie głównej.

## 1. Build / Zbuduj paczkę

From the repository root / Z głównego katalogu repozytorium:

```bash
python scripts/package_site.py
```

Expected output / Oczekiwany wynik:

```text
dist/cancer-explorer/
├── index.html
├── assets/
├── data/
│   ├── manifest.json
│   ├── routes.json
│   ├── starter.json
│   └── partitions/    # 457 lazy routes
└── PACKAGE.json
```

`PACKAGE.json` records the route count, file count, byte size, entry point and configured data base. The generated page reads `./data`, so the folder is portable as one unit.

`PACKAGE.json` zapisuje liczbę ścieżek i plików, rozmiar, punkt wejścia oraz ścieżkę do danych. Wygenerowana strona czyta `./data`, więc cały katalog można przenieść jako jedną paczkę.

## 2. Copy to VPS / Skopiuj na VPS

Example only — adjust the host and document root / Przykład — dopasuj host i katalog strony:

```bash
rsync -av --delete dist/cancer-explorer/ USER@VPS:/var/www/rmportfolio/case-studies/cancer-explorer/
```

The expected public URL is:

```text
https://www.rmportfolio.co.uk/case-studies/cancer-explorer/
```

Recommended cache policy:

```nginx
location /case-studies/cancer-explorer/ {
    try_files $uri $uri/ /case-studies/cancer-explorer/index.html;
}

location /case-studies/cancer-explorer/data/ {
    try_files $uri =404;
    add_header Cache-Control "public, max-age=86400";
}
```

The `try_files` fallback keeps shared query-string views working. No API or server-side application is required.

Fallback `try_files` pozwala otwierać zapisane widoki z parametrami w adresie. Nie potrzeba API ani aplikacji po stronie serwera.

## 3. Add the portfolio card / Dodaj kartę do portfolio

Insert this card into the existing `.cards` container in the portfolio homepage. It uses the same classes as the current rmportfolio case-study cards.

Wstaw poniższą kartę do istniejącego kontenera `.cards` na stronie głównej. Używa tych samych klas, co obecne karty portfolio.

```html
<article class="card live">
  <div class="card-top">
    <span class="badge badge-live">
      <span class="lang-en">Live case study</span>
      <span class="lang-pl">Gotowe studium</span>
    </span>
    <span aria-hidden="true">↗</span>
  </div>
  <div class="card-body">
    <h3>
      <span class="lang-en">Global Cancer Trends — age, type &amp; country</span>
      <span class="lang-pl">Globalne trendy raka — wiek, typ i kraj</span>
    </h3>
    <p class="muted">
      <span class="lang-en">386,916 WHO/IARC observations across 42 cancer categories, five geographies and 1968–2050.</span>
      <span class="lang-pl">386 916 obserwacji WHO/IARC, 42 kategorie nowotworów, pięć geografii i lata 1968–2050.</span>
    </p>
    <div class="card-metrics">
      <div><b>42</b><span class="lang-en">cancer categories</span><span class="lang-pl">kategorie raka</span></div>
      <div><b>457</b><span class="lang-en">data routes</span><span class="lang-pl">ścieżek danych</span></div>
      <div><b>EN/PL</b><span class="lang-en">interactive</span><span class="lang-pl">interaktywnie</span></div>
    </div>
    <div class="card-foot">
      <a class="btn btn-primary" href="case-studies/cancer-explorer/">
        <span class="lang-en">Explore the data</span>
        <span class="lang-pl">Eksploruj dane</span>
        <span aria-hidden="true">→</span>
      </a>
      <a href="https://github.com/robertmaszkiewski/global-cancer-trends-analysis">GitHub</a>
    </div>
  </div>
  <div class="spark"></div>
</article>
```

## 4. Verify after deployment / Sprawdź po wdrożeniu

- Open all six analysis routes.
- Switch EN → PL and reload; the choice should persist.
- Open a shared URL in a private browser window.
- Download filtered CSV.
- Check desktop, 390 px mobile and keyboard navigation.
- Confirm that `data/routes.json` and a partition URL return HTTP 200.
- Confirm source links and GitHub links.

- Otwórz wszystkie sześć dróg analizy.
- Przełącz EN → PL i odśwież; wybór powinien zostać zapamiętany.
- Otwórz udostępniony adres w oknie prywatnym.
- Pobierz filtrowany CSV.
- Sprawdź desktop, telefon 390 px i obsługę klawiaturą.
- Potwierdź odpowiedź HTTP 200 dla `data/routes.json` oraz przykładowej partycji.
- Sprawdź linki źródłowe i GitHub.

## Alternative integration / Alternatywna integracja

If the VPS Codex agent wants the explorer data elsewhere, set this before `app.js`:

Jeżeli agent Codex na VPS umieści dane w innym miejscu, ustaw przed `app.js`:

```html
<script>window.CANCER_DATA_BASE = "/assets/data/cancer";</script>
```

Do not concatenate the 38 MB dataset into one JavaScript file. Keeping lazy partitions is what makes first load small and each branch independently cacheable.

Nie łącz 38 MB danych w jeden plik JavaScript. Partycje ładowane na żądanie utrzymują mały pierwszy transfer i pozwalają niezależnie buforować każdą gałąź.

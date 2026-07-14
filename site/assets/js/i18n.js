const pairs = [
  ["meta.title", "Global Cancer Observatory — detailed data explorer", "Globalne Obserwatorium Nowotworów — szczegółowy eksplorator danych"],
  ["meta.description", "Explore cancer incidence, mortality, age patterns, sex differences, history and projections.", "Eksploruj zachorowalność, umieralność, wzorce wieku, różnice płci, historię i prognozy nowotworów."],
  ["nav.brand", "Robert Maszkiewski", "Robert Maszkiewski"],
  ["nav.portfolio", "Portfolio home", "Portfolio"],
  ["nav.summary", "Key findings", "Najważniejsze wnioski"],
  ["nav.explore", "Explore data", "Eksploruj dane"],
  ["nav.method", "Method", "Metoda"],
  ["hero.eyebrow", "Global cancer data · 1968–2050", "Globalne dane onkologiczne · 1968–2050"],
  ["hero.title", "Cancer is not one trend. Open every branch.", "Rak to nie jeden trend. Otwórz każdą gałąź."],
  ["hero.lead", "A bilingual, source-backed atlas of 386,916 observations: global estimates plus Poland, the UK, Spain and the USA, split by cancer, age, sex, year, measure and evidence type.", "Dwujęzyczny atlas 386 916 obserwacji opartych na źródłach: estymacje globalne oraz Polska, Wielka Brytania, Hiszpania i USA, z podziałem na nowotwór, wiek, płeć, rok, miarę i typ dowodu."],
  ["hero.cta", "Start exploring", "Zacznij eksplorować"],
  ["hero.method", "Read methodology", "Przeczytaj metodologię"],
  ["hero.note", "Descriptive epidemiology — not medical advice and not a causal model.", "Epidemiologia opisowa — nie porada medyczna ani model przyczynowy."],
  ["stats.records", "Canonical observations", "Obserwacje kanoniczne"],
  ["stats.cancers", "Cancer categories", "Kategorie nowotworów"],
  ["stats.countries", "Geographic views", "Widoki geograficzne"],
  ["stats.years", "Full time horizon", "Pełny horyzont czasu"],
  ["stats.routes", "Lazy data routes", "Ścieżki danych"],
  ["summary.phase", "Executive answer", "Odpowiedź w skrócie"],
  ["summary.title", "What the combined evidence says", "Co mówi łączny materiał dowodowy"],
  ["summary.lead", "The headline changes when you switch from counts to rates, from all ages to an age group, or from one cancer to another. These are starting points, not the end of the analysis.", "Wniosek zmienia się po przejściu z liczb na współczynniki, z całej populacji na grupę wieku lub z jednego nowotworu na inny. To punkty startowe, nie koniec analizy."],
  ["finding.one.title", "Lung cancer leads the global burden", "Rak płuca prowadzi w globalnym obciążeniu"],
  ["finding.one.body", "In 2024, IARC estimates 2.64 million new lung cancers and 1.86 million lung-cancer deaths worldwide.", "W 2024 r. IARC szacuje 2,64 mln nowych przypadków raka płuca i 1,86 mln zgonów z jego powodu na świecie."],
  ["finding.two.title", "Population ageing drives a steep count increase", "Starzenie populacji napędza silny wzrost liczby przypadków"],
  ["finding.two.body", "All cancers excluding non-melanoma skin cancer are projected to rise from 19.50 million cases in 2024 to 32.10 million in 2050: +64.6% if 2024 rates remain constant.", "Liczba wszystkich nowotworów bez nieczerniakowych raków skóry ma wzrosnąć z 19,50 mln w 2024 r. do 32,10 mln w 2050 r.: +64,6% przy utrzymaniu współczynników z 2024 r."],
  ["finding.three.title", "Age profiles are cancer-specific", "Profil wieku zależy od rodzaju nowotworu"],
  ["finding.three.body", "Most common cancers rise sharply at older ages, while testicular, cervical, thyroid and some blood cancers have distinctly different age patterns.", "Najczęstsze nowotwory silnie rosną w starszym wieku, natomiast rak jądra, szyjki macicy, tarczycy i część nowotworów krwi mają wyraźnie inne profile wieku."],
  ["finding.four.title", "Country comparison needs like-for-like metrics", "Porównania krajów wymagają tych samych miar"],
  ["finding.four.body", "Raw counts describe service volume; age-standardised rates are better for comparing populations with different age structures.", "Surowe liczby opisują skalę potrzeb systemu; współczynniki standaryzowane lepiej porównują populacje o różnej strukturze wieku."],
  ["branches.phase", "Choose a route", "Wybierz kierunek"],
  ["branches.title", "Six ways into the same evidence", "Sześć dróg do tych samych danych"],
  ["branches.lead", "Every route opens the explorer with a purposeful question and compatible controls.", "Każda droga otwiera eksplorator z konkretnym pytaniem i zgodnymi filtrami."],
  ["branch.ranking.title", "Which cancers are most common?", "Które nowotwory są najczęstsze?"],
  ["branch.ranking.body", "Rank incidence or mortality by cancer and geography.", "Uszereguj zachorowania lub zgony według nowotworu i geografii."],
  ["branch.age.title", "At what age does burden rise?", "W jakim wieku rośnie obciążenie?"],
  ["branch.age.body", "Trace age-specific rates for any cancer and sex.", "Prześledź współczynniki wieku dla dowolnego nowotworu i płci."],
  ["branch.history.title", "What changed since 1968?", "Co zmieniło się od 1968 roku?"],
  ["branch.history.body", "Explore observed cause-of-death records through the latest available year.", "Eksploruj obserwowane rejestry przyczyn zgonu do najnowszego dostępnego roku."],
  ["branch.sex.title", "Where do sexes differ?", "Gdzie różnią się płcie?"],
  ["branch.sex.body", "Compare female and male levels without hiding sex-specific cancers.", "Porównaj poziomy kobiet i mężczyzn bez ukrywania nowotworów zależnych od płci."],
  ["branch.country.title", "How do countries compare?", "Jak porównują się kraje?"],
  ["branch.country.body", "Use the same cancer, year, sex and metric across four countries and the world.", "Użyj tego samego nowotworu, roku, płci i miary dla czterech krajów i świata."],
  ["branch.future.title", "What could 2050 look like?", "Jak może wyglądać rok 2050?"],
  ["branch.future.body", "Inspect demographic projections by cancer, sex, measure and geography.", "Sprawdź prognozy demograficzne według nowotworu, płci, miary i geografii."],
  ["branch.open", "Open route", "Otwórz drogę"],
  ["explorer.phase", "Interactive analysis", "Analiza interaktywna"],
  ["explorer.title", "Cancer data explorer", "Eksplorator danych onkologicznych"],
  ["explorer.lead", "Change one dimension at a time or follow a completely different analytical branch. The URL stores your current view.", "Zmieniaj po jednym wymiarze lub wybierz zupełnie inną gałąź analizy. Adres URL zapisuje bieżący widok."],
  ["explorer.route", "Analysis route", "Droga analizy"],
  ["explorer.geography", "Geography", "Geografia"],
  ["explorer.cancer", "Cancer", "Nowotwór"],
  ["explorer.measure", "Measure", "Miara"],
  ["explorer.metric", "Metric", "Wskaźnik"],
  ["explorer.sex", "Sex", "Płeć"],
  ["explorer.age", "Age group", "Grupa wieku"],
  ["explorer.year", "Year", "Rok"],
  ["explorer.top", "Number shown", "Liczba pozycji"],
  ["explorer.compare", "Compare with", "Porównaj z"],
  ["explorer.loading", "Loading verified partition…", "Wczytywanie zweryfikowanej partycji…"],
  ["explorer.unavailable", "This exact combination is not available in the source data. Choose one of the compatible options shown.", "Ta dokładna kombinacja nie występuje w danych źródłowych. Wybierz jedną z pokazanych zgodnych opcji."],
  ["explorer.error", "The data could not be loaded. Check that the page is served over HTTP and try again.", "Nie udało się wczytać danych. Sprawdź, czy strona działa przez HTTP, i spróbuj ponownie."],
  ["explorer.empty", "No rows match these filters.", "Żadne wiersze nie pasują do tych filtrów."],
  ["explorer.reset", "Reset view", "Resetuj widok"],
  ["explorer.download", "Download filtered CSV", "Pobierz filtrowany CSV"],
  ["explorer.copy", "Copy view link", "Kopiuj link do widoku"],
  ["explorer.copied", "Link copied", "Link skopiowany"],
  ["route.ranking", "Current ranking", "Bieżący ranking"],
  ["route.age", "Age profile", "Profil wieku"],
  ["route.history", "Historical trend", "Trend historyczny"],
  ["route.sex", "Sex comparison", "Porównanie płci"],
  ["route.country", "Country comparison", "Porównanie krajów"],
  ["route.future", "Projection to 2050", "Prognoza do 2050"],
  ["chart.ranking.title", "Ranked cancer burden", "Ranking obciążenia nowotworami"],
  ["chart.age.title", "Age-specific profile", "Profil według wieku"],
  ["chart.history.title", "Observed mortality through time", "Obserwowana umieralność w czasie"],
  ["chart.sex.title", "Female and male comparison", "Porównanie kobiet i mężczyzn"],
  ["chart.country.title", "Like-for-like geography comparison", "Porównanie geografii tą samą miarą"],
  ["chart.future.title", "Demographic projection", "Prognoza demograficzna"],
  ["chart.x.year", "Year", "Rok"],
  ["chart.x.age", "Age group", "Grupa wieku"],
  ["chart.y.count", "People", "Osoby"],
  ["chart.y.rate", "Rate per 100,000", "Współczynnik na 100 000"],
  ["chart.y.percent", "Percent", "Procent"],
  ["chart.legend.female", "Female", "Kobiety"],
  ["chart.legend.male", "Male", "Mężczyźni"],
  ["chart.legend.both", "Both sexes", "Obie płcie"],
  ["chart.table", "Accessible data table", "Dostępna tabela danych"],
  ["chart.showTable", "Show table", "Pokaż tabelę"],
  ["chart.hideTable", "Hide table", "Ukryj tabelę"],
  ["evidence.title", "How to read the evidence", "Jak czytać dowody"],
  ["evidence.observed", "Observed", "Obserwowane"],
  ["evidence.observed.body", "Registered deaths reported by national authorities to WHO.", "Zarejestrowane zgony przekazane WHO przez władze krajowe."],
  ["evidence.modelled", "Modelled", "Modelowane"],
  ["evidence.modelled.body", "IARC estimates built for consistent cross-country comparison.", "Szacunki IARC przygotowane do spójnych porównań między krajami."],
  ["evidence.projected", "Projected", "Prognozowane"],
  ["evidence.projected.body", "Future counts if 2024 rates stay constant while population changes.", "Przyszłe liczby przy stałych współczynnikach z 2024 r. i zmieniającej się populacji."],
  ["evidence.source", "Source", "Źródło"],
  ["evidence.version", "Version", "Wersja"],
  ["evidence.icd", "ICD definition", "Definicja ICD"],
  ["evidence.updated", "Data vintage", "Wersja danych"],
  ["interpret.title", "What this view supports", "Co wspiera ten widok"],
  ["interpret.ranking", "Use counts for scale and rates for comparison. A top rank does not mean an individual has the highest personal risk.", "Używaj liczb do oceny skali, a współczynników do porównań. Pierwsze miejsce nie oznacza najwyższego ryzyka dla konkretnej osoby."],
  ["interpret.age", "The curve shows population rates within age bands, not the prognosis of a person diagnosed at that age.", "Krzywa pokazuje współczynniki populacyjne w grupach wieku, a nie rokowanie osoby zdiagnozowanej w tym wieku."],
  ["interpret.history", "Registration changes, ICD revisions, screening and diagnostic practice can move the observed series alongside real disease change.", "Zmiany rejestracji, rewizje ICD, badania przesiewowe i praktyka diagnostyczna mogą zmieniać serię razem z rzeczywistą zmianą chorobowości."],
  ["interpret.sex", "Sex gaps combine biology, exposure, screening, diagnosis and population structure; the chart alone does not isolate causes.", "Różnice płci łączą biologię, ekspozycję, screening, diagnostykę i strukturę populacji; sam wykres nie rozdziela przyczyn."],
  ["interpret.country", "Compare identical definitions and prefer age-standardised rates. Health-system quality cannot be inferred from a mortality-to-incidence ratio here.", "Porównuj identyczne definicje i preferuj współczynniki standaryzowane. Nie można tu wnioskować o jakości systemu z ilorazu zgonów do zachorowań."],
  ["interpret.future", "The projection changes population size and age structure, not cancer rates. It is a planning scenario, not a forecast of prevention or treatment progress.", "Prognoza zmienia wielkość i strukturę wieku populacji, nie współczynniki raka. To scenariusz planistyczny, nie prognoza postępu profilaktyki lub leczenia."],
  ["detail.phase", "Data depth", "Głębokość danych"],
  ["detail.title", "From headline to individual cells", "Od nagłówka do pojedynczych komórek"],
  ["detail.body", "Every plotted point can be traced to its source, definition, evidence status and data vintage. Compact route files keep the page fast without discarding analytical dimensions.", "Każdy punkt wykresu można powiązać ze źródłem, definicją, statusem dowodu i wersją danych. Kompaktowe pliki ścieżek utrzymują szybkość strony bez odrzucania wymiarów analizy."],
  ["detail.schema", "Canonical schema", "Schemat kanoniczny"],
  ["detail.quality", "Quality checks", "Kontrole jakości"],
  ["detail.routes", "Available branches", "Dostępne gałęzie"],
  ["detail.notebook", "Reproducible notebook", "Odtwarzalny notebook"],
  ["method.phase", "Method & limitations", "Metoda i ograniczenia"],
  ["method.title", "Honest comparisons before attractive charts", "Uczciwe porównania przed atrakcyjnymi wykresami"],
  ["method.one", "Incidence and mortality are different outcomes and are never silently merged.", "Zachorowalność i umieralność to różne wyniki i nigdy nie są po cichu łączone."],
  ["method.two", "Observed, modelled and projected values remain visibly distinct.", "Wartości obserwowane, modelowane i prognozowane pozostają wyraźnie rozróżnione."],
  ["method.three", "Age-specific, crude and age-standardised rates answer different questions.", "Współczynniki wieku, surowe i standaryzowane odpowiadają na różne pytania."],
  ["method.four", "Cancer definitions are mapped to ICD codes and source-defined aggregates are flagged.", "Definicje nowotworów są mapowane do kodów ICD, a agregaty źródłowe są oznaczone."],
  ["method.five", "Missing national exports are shown as gaps, never filled with invented estimates.", "Brakujące eksporty krajowe są pokazane jako luki, nigdy uzupełniane wymyślonymi szacunkami."],
  ["method.link", "Open full methodology", "Otwórz pełną metodologię"],
  ["sources.title", "Primary data sources", "Pierwotne źródła danych"],
  ["sources.who", "WHO Mortality Database", "Baza Umieralności WHO"],
  ["sources.iarc", "IARC Global Cancer Observatory 2024", "Globalne Obserwatorium Nowotworów IARC 2024"],
  ["sources.future", "IARC Cancer Tomorrow", "IARC Cancer Tomorrow"],
  ["sources.note", "Source terms and citations are preserved in the repository documentation.", "Warunki źródeł i cytowania zachowano w dokumentacji repozytorium."],
  ["footer.project", "Global Cancer Trends case study", "Studium globalnych trendów nowotworowych"],
  ["footer.data", "WHO & IARC public health data", "Dane zdrowia publicznego WHO i IARC"],
  ["footer.github", "GitHub repository", "Repozytorium GitHub"],
  ["footer.notebook", "Analysis notebook", "Notebook analityczny"],
  ["footer.privacy", "No tracking. Static site.", "Bez śledzenia. Strona statyczna."],
  ["common.all", "All", "Wszystkie"],
  ["common.none", "None", "Brak"],
  ["common.people", "people", "osób"],
  ["common.per100k", "per 100,000", "na 100 000"],
  ["common.to", "to", "do"],
  ["common.of", "of", "z"],
  ["common.latest", "Latest", "Najnowszy"],
  ["common.rank", "Rank", "Pozycja"],
  ["common.value", "Value", "Wartość"],
  ["common.change", "Change", "Zmiana"],
  ["common.records", "records", "rekordów"],
];

export const translations = Object.freeze({
  en: Object.freeze(Object.fromEntries(pairs.map(([key, en]) => [key, en]))),
  pl: Object.freeze(Object.fromEntries(pairs.map(([key, , pl]) => [key, pl]))),
});

export function translationKeys(dictionary) {
  return Object.keys(dictionary).sort();
}

export function interpolate(template, values = {}) {
  return String(template).replace(/\{([^}]+)\}/g, (_, key) => String(values[key] ?? `{${key}}`));
}

export function createI18n({ storage = globalThis.localStorage ?? null, root = globalThis.document ?? null, initialLanguage = "en" } = {}) {
  const stored = storage?.getItem?.("cancer-explorer-language");
  let language = stored === "pl" || stored === "en" ? stored : initialLanguage;

  const api = {
    get language() { return language; },
    t(key, values) {
      return interpolate(translations[language]?.[key] ?? `[${key}]`, values);
    },
    setLanguage(next, { render = true } = {}) {
      if (!translations[next]) return false;
      language = next;
      storage?.setItem?.("cancer-explorer-language", next);
      if (render) api.render();
      return true;
    },
    render() {
      if (!root?.querySelectorAll) return;
      root.documentElement?.setAttribute?.("lang", language);
      if ("title" in root) root.title = api.t("meta.title");
      const description = root.querySelector?.('meta[name="description"]');
      if (description) description.setAttribute("content", api.t("meta.description"));
      root.body?.classList?.toggle?.("lang-pl", language === "pl");
      root.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = api.t(node.dataset.i18n); });
      root.querySelectorAll("[data-i18n-placeholder]").forEach((node) => { node.placeholder = api.t(node.dataset.i18nPlaceholder); });
      root.querySelectorAll("[data-i18n-aria-label]").forEach((node) => { node.setAttribute("aria-label", api.t(node.dataset.i18nAriaLabel)); });
      root.querySelectorAll("[data-language]").forEach((node) => {
        const active = node.dataset.language === language;
        node.classList.toggle("active", active);
        node.setAttribute("aria-pressed", String(active));
      });
      root.dispatchEvent?.(new CustomEvent("languagechange", { detail: { language } }));
    },
  };
  return api;
}

"""Taksonomia nowotworow — kody wprost z dokumentacji WHO Mortality Database.

ZRODLO: WHO_Mortality_Database_Documentation.pdf (listy 08A i 09B) + ICD-10.
Zadnego zgadywania. Kazda lokalizacja zdefiniowana tak, by ZNACZYC TO SAMO w kazdej rewizji.

ICD-8 List A (08A):                      ICD-9 BTL (09B):
  A045 140-149 jama ustna i gardlo         B08  140-149 warga/jama ustna/gardlo
  A046 150 przelyk                         B090 150 przelyk
  A047 151 zoladek                         B091 151 zoladek
  A048 152,153 jelito bez odbytnicy        B092 152 jelito cienkie
  A049 154 odbytnica                       B093 153 okreznica
  A050 161 krtan                           B094 154 odbytnica + odbyt
  A051 162 pluco                           B095 155.0 watroba (TYLKO pierwotna)
  A052 170 kosci                           B096 157 trzustka
  A053 172,173 skora (czerniak + inne)     B100 161 krtan
  A054 174 piers                           B101 162 pluco
  A055 180 szyjka macicy                   B110 170 kosci
  A056 181,182 inne czesci macicy          B111 172 czerniak
  A057 185 gruczol krokowy                 B112 173 inne raki skory
  A058 ... inne i nieokreslone             B113 174 piers KOBIET
  A059 204-207 bialaczka                   B120 180 szyjka macicy
  A060 200-203,208,209 chloniaki i inne    B121 181 lozysko
                                           B122 179,182 macica inna
                                           B123 183 jajnik
                                           B124 185 gruczol krokowy
                                           B125 186 jadro
                                           B126 188 pecherz moczowy
                                           B130 191 mozg
                                           B140 201 chloniak Hodgkina
                                           B141 204-208 bialaczka
                                           B149 reszta B14 (200,202,203)
"""

# (kod, EN, PL, ICD-8, ICD-9, prefiksy ICD-10, plec: None|'female'|'male')
SITES = [
    # --- pelna seria od 1968 (maja wlasna kategorie w ICD-8 List A) ---
    ("LUNG", "Lung", "Płuco",
     ["A051"], ["B101"], ["C33", "C34"], None),
    ("STOMACH", "Stomach", "Żołądek",
     ["A047"], ["B091"], ["C16"], None),
    ("OESOPHAGUS", "Oesophagus", "Przełyk",
     ["A046"], ["B090"], ["C15"], None),
    ("LARYNX", "Larynx", "Krtań",
     ["A050"], ["B100"], ["C32"], None),
    ("BONE", "Bone", "Kości",
     ["A052"], ["B110"], ["C40", "C41"], None),
    # ICD-8 A053 = 172+173 (czerniak I nieczerniakowe) -> laczymy w kazdej rewizji
    ("SKIN", "Skin (all types)", "Skóra (łącznie)",
     ["A053"], ["B111", "B112"], ["C43", "C44"], None),
    ("ORAL_PHARYNX", "Lip, oral cavity, pharynx", "Warga, jama ustna, gardło",
     ["A045"], ["B08"], ["C00", "C01", "C02", "C03", "C04", "C05", "C06",
                         "C07", "C08", "C09", "C10", "C11", "C12", "C13", "C14"], None),
    # ICD-9 B113 = piers KOBIET -> definiujemy jako piers kobiet w kazdej rewizji
    ("BREAST", "Breast (female)", "Pierś (kobiety)",
     ["A054"], ["B113"], ["C50"], "female"),
    ("CERVIX", "Cervix uteri", "Szyjka macicy",
     ["A055"], ["B120"], ["C53"], "female"),
    # ICD-8 A056 = 181+182 -> po stronie ICD-9 musi byc B121 (181) + B122 (182)
    ("UTERUS", "Uterus (other)", "Macica (trzon i inne)",
     ["A056"], ["B121", "B122"], ["C54", "C55"], "female"),
    ("PROSTATE", "Prostate", "Gruczoł krokowy",
     ["A057"], ["B124"], ["C61"], "male"),
    ("LEUKAEMIA", "Leukaemia", "Białaczka",
     ["A059"], ["B141"], ["C91", "C92", "C93", "C94", "C95"], None),
    # ICD-8 A060 = 200-203,208,209 = cala tkanka limfatyczna/krwiotworcza BEZ bialaczki.
    # ICD-9: czesc krajow (m.in. Polska) NIE raportuje B149 osobno, tylko sume B14.
    # Dlatego liczymy chloniaki jako B14 (calosc, 200-208) MINUS B141 (bialaczka, 204-208).
    # Realizowane w build_who.py przez kod pomocniczy _LYMPH_TOTAL — patrz derive_lymphoma().
    ("LYMPHOMA", "Lymphomas & myeloma", "Chłoniaki i szpiczak",
     ["A060"], ["__DERIVED__"],
     ["C81", "C82", "C83", "C84", "C85", "C86", "C88", "C90", "C96"], None),

    # --- seria od ICD-9 (w ICD-8 siedza w koszu A058 "inne i nieokreslone") ---
    # ICD-8 A048 miesza jelito cienkie z okreznica -> COLORECTUM startuje dopiero od ICD-9
    ("COLORECTUM", "Colorectum", "Jelito grube i odbytnica",
     [], ["B093", "B094"], ["C18", "C19", "C20", "C21"], None),
    ("PANCREAS", "Pancreas", "Trzustka",
     [], ["B096"], ["C25"], None),
    ("BLADDER", "Bladder", "Pęcherz moczowy",
     [], ["B126"], ["C67"], None),
    ("OVARY", "Ovary", "Jajnik",
     [], ["B123"], ["C56"], "female"),
    ("TESTIS", "Testis", "Jądro",
     [], ["B125"], ["C62"], "male"),
    ("BRAIN", "Brain", "Mózg",
     [], ["B130"], ["C71"], None),
    # ICD-9 B095 to TYLKO watroba pierwotna (155.0), ICD-10 C22 to calosc -> nieporownywalne.
    # Publikujemy dopiero od ICD-10.
    ("LIVER", "Liver", "Wątroba",
     [], [], ["C22"], None),
]

LABELS = {c: (en, pl) for c, en, pl, _, _, _, _ in SITES}
SEX_SPECIFIC = {c: sx for c, _, _, _, _, _, sx in SITES if sx}
CODES = [c for c, *_ in SITES]

MAP_08A, MAP_09B, ICD10_PREFIX = {}, {}, []
for code, _, _, i8, i9, i10, _ in SITES:
    for c in i8:
        MAP_08A[c] = code
    for c in i9:
        if c != "__DERIVED__":
            MAP_09B[c] = code
    for p in i10:
        ICD10_PREFIX.append((p, code))
ICD10_PREFIX.sort(key=lambda x: -len(x[0]))

# kody pomocnicze ICD-9 do wyliczenia chloniakow: B14 (calosc) - B141 (bialaczka)
MAP_09B["B14"] = "_LYMPH_TOTAL"


def decode(list_code, cause):
    """Zwraca kod lokalizacji albo None. Nigdy nie zgaduje."""
    lst = str(list_code).strip().upper()
    c = str(cause).strip().upper()
    if lst == "08A":
        return MAP_08A.get(c)
    if lst == "09B":
        return MAP_09B.get(c)
    if lst in ("104", "10M", "101", "103"):
        if not c.startswith("C"):
            return None
        for p, code in ICD10_PREFIX:
            if c.startswith(p):
                return code
    return None

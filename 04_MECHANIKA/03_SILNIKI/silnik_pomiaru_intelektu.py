# Plik: /04_MECHANIKA/03_SILNIKI/silnik_pomiaru_intelektu.py
# Data: 2025-08-08
# Typ: Silnik oceniający (rozszerzony)
# Cel: Generuje procentowe podsumowanie intelektu Twórcy na dany dzień,
#      z wagami, historią, trendami i rekomendacjami.

from __future__ import annotations
import datetime as _dt
import json, csv, math, os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

# --- Domeny/obszary -----------------------------------------------------------
OBSZARY: Tuple[str, ...] = (
    "Analiza poznawcza",
    "Twórczość systemowa",
    "Konstrukcja symboliczna",
    "Myślenie strategiczne",
    "Myślenie mistyczne",
    "Efektywność techniczna",
    "Napęd emocjonalny",
    "Samoświadomość / introspekcja",
)

WAGI_DOMYSLNE: Dict[str, float] = {
    "Analiza poznawcza": 1.2,
    "Twórczość systemowa": 1.3,
    "Konstrukcja symboliczna": 1.1,
    "Myślenie strategiczne": 1.0,
    "Myślenie mistyczne": 1.1,
    "Efektywność techniczna": 1.0,
    "Napęd emocjonalny": 0.9,
    "Samoświadomość / introspekcja": 1.4,
}

# Presety wag (drobne przesunięcia do szybkiego strojenia)
PRESETY_WAG = {
    "domyslne": WAGI_DOMYSLNE,
    "tworczy": {
        **WAGI_DOMYSLNE,
        "Twórczość systemowa": 1.45,
        "Konstrukcja symboliczna": 1.2,
        "Samoświadomość / introspekcja": 1.5,
    },
    "inzynierski": {
        **WAGI_DOMYSLNE,
        "Efektywność techniczna": 1.25,
        "Analiza poznawcza": 1.3,
        "Myślenie strategiczne": 1.15,
    },
}

# --- Modele danych ------------------------------------------------------------
@dataclass
class DziennyWynik:
    data: str
    poziomy: Dict[str, float]  # 0..100
    srednia_wazona: float
    preset: str

# --- Narzędzia ----------------------------------------------------------------
def _dzis() -> str:
    return _dt.date.today().isoformat()

def _clamp(v: float, lo=0.0, hi=100.0) -> float:
    return max(lo, min(hi, float(v)))

def _uzupelnij_braki(oceny: Dict[str, float]) -> Dict[str, float]:
    # brakujące obszary -> 0; nadmiarowe ignorujemy
    out = {k: _clamp(oceny.get(k, 0.0)) for k in OBSZARY}
    return out

def _normalizuj_wagi(wagi: Dict[str, float]) -> Dict[str, float]:
    # jeżeli podano niepełny słownik wag, dopełnij 1.0
    out = {k: float(wagi.get(k, 1.0)) for k in OBSZARY}
    return out

def oblicz_srednia_wazona(oceny: Dict[str, float], wagi: Dict[str, float]) -> float:
    oceny = _uzupelnij_braki(oceny)
    wagi = _normalizuj_wagi(wagi)
    suma_wazona = sum(oceny[k] * wagi[k] for k in OBSZARY)
    suma_wag = sum(wagi.values()) or 1.0
    return round(suma_wazona / suma_wag, 2)

def wskaz_slabe_mocne(oceny: Dict[str, float], top_n: int = 2) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    posort = sorted(((k, oceny.get(k, 0.0)) for k in OBSZARY), key=lambda x: x[1])
    slabe = posort[:top_n]
    mocne = list(reversed(posort[-top_n:]))
    return slabe, mocne

def rekomendacje(oceny: Dict[str, float]) -> List[str]:
    tips = []
    if oceny.get("Napęd emocjonalny", 0) < 60:
        tips.append("Zasil napęd: 20 min ruchu albo krótka sesja oddechowa przed zadaniem.")
    if oceny.get("Efektywność techniczna", 0) < 65:
        tips.append("Zamknij jedną malutką rzecz end-to-end (DOPNIJ), zanim ruszysz dalej.")
    if oceny.get("Samoświadomość / introspekcja", 0) < 70:
        tips.append("1–2 min 5D presence: kotwica TERAZ i jedno zdanie intencji.")
    if oceny.get("Twórczość systemowa", 0) < 70:
        tips.append("Szybki szkic architektury: 3 pudełka, 3 strzałki. Potem dopiero kod.")
    return tips or ["Utrzymaj rytm. Dziś balans wygląda solidnie."]

# --- Historia / IO ------------------------------------------------------------
def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def zapisz_json(wynik: DziennyWynik, path: str = "data/intellect/history.json"):
    _ensure_dir(path)
    data = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    # nadpisz wpis dla tej samej daty
    data = [r for r in data if r.get("data") != wynik.data]
    data.append(asdict(wynik))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def wczytaj_json(path: str = "data/intellect/history.json") -> List[DziennyWynik]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [DziennyWynik(**r) for r in raw]

def eksport_csv(path_csv: str = "data/intellect/history.csv", historia: Optional[List[DziennyWynik]] = None):
    _ensure_dir(path_csv)
    hist = historia or wczytaj_json()
    with open(path_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["data", "preset", "srednia_wazona", *OBSZARY])
        for r in hist:
            row = [r.data, r.preset, r.srednia_wazona] + [r.poziomy.get(k, 0.0) for k in OBSZARY]
            w.writerow(row)

# --- Trendy -------------------------------------------------------------------
def _rolling_mean(vals: List[float], window: int = 7) -> Optional[float]:
    if len(vals) < window:
        return None
    chunk = vals[-window:]
    return round(sum(chunk) / window, 2)

def trend(historia: List[DziennyWynik]) -> Tuple[Optional[float], Optional[str]]:
    if not historia:
        return None, None
    vals = [r.srednia_wazona for r in sorted(historia, key=lambda r: r.data)]
    ma7_now = _rolling_mean(vals, 7)
    if ma7_now is None:
        return None, None
    # porównanie do poprzedniego okna
    ma7_prev = _rolling_mean(vals[:-1], 7)
    if ma7_prev is None:
        return ma7_now, "→"
    diff = round(ma7_now - ma7_prev, 2)
    arrow = "↑" if diff > 0.1 else ("↓" if diff < -0.1 else "→")
    return ma7_now, f"{arrow} ({diff:+.2f})"

# --- Raporty ------------------------------------------------------------------
def generuj_raport(dzisiejsze_oceny: Dict[str, float], preset: str = "domyslne") -> str:
    dat = _dzis()
    oceny = _uzupelnij_braki(dzisiejsze_oceny)
    wagi = PRESETY_WAG.get(preset, WAGI_DOMYSLNE)
    srednia = oblicz_srednia_wazona(oceny, wagi)
    slabe, mocne = wskaz_slabe_mocne(oceny)
    tips = rekomendacje(oceny)

    raport = [f"📅 Raport Intelektu — {dat}",
              "────────────────────────────────",
              f"Preset wag: {preset}",
              ""]
    for k in OBSZARY:
        raport.append(f"🔹 {k}: {oceny[k]:.0f}%  (w={wagi.get(k,1.0):.2f})")
    raport += ["", f"🔰 Średnia ważona: {srednia:.2f}%", ""]
    raport.append("📉 Słabsze dziś:")
    for n, v in slabe: raport.append(f"   • {n}: {v:.0f}%")
    raport.append("📈 Mocne dziś:")
    for n, v in mocne: raport.append(f"   • {n}: {v:.0f}%")
    raport += ["", "🧭 Rekomendacje:"]
    for t in tips: raport.append(f"   • {t}")

    # zapisz do historii i policz trend
    rec = DziennyWynik(data=dat, poziomy=oceny, srednia_wazona=srednia, preset=preset)
    zapisz_json(rec)
    ma7, arrow = trend(wczytaj_json())
    if ma7 is not None:
        raport += ["", f"📊 Trend 7-dniowy: {ma7:.2f}% {arrow}"]

    return "\n".join(raport)

def generuj_markdown(dzisiejsze_oceny: Dict[str, float], preset: str = "domyslne") -> str:
    dat = _dzis()
    oceny = _uzupelnij_braki(dzisiejsze_oceny)
    wagi = PRESETY_WAG.get(preset, WAGI_DOMYSLNE)
    srednia = oblicz_srednia_wazona(oceny, wagi)
    lines = [
        f"# Raport Intelektu — {dat}",
        f"**Preset wag:** `{preset}`",
        "",
        "| Obszar | % | waga |",
        "|---|---:|---:|",
    ]
    for k in OBSZARY:
        lines.append(f"| {k} | {oceny[k]:.0f}% | {wagi.get(k,1.0):.2f} |")
    lines += ["", f"**Średnia ważona:** `{srednia:.2f}%`"]
    return "\n".join(lines)

# --- CLI ----------------------------------------------------------------------
def _demo():
    dzisiejsze_oceny = {
        "Analiza poznawcza": 89,
        "Twórczość systemowa": 77,
        "Konstrukcja symboliczna": 94,
        "Myślenie strategiczne": 72,
        "Myślenie mistyczne": 91,
        "Efektywność techniczna": 69,
        "Napęd emocjonalny": 60,
        "Samoświadomość / introspekcja": 95,
    }
    print(generuj_raport(dzisiejsze_oceny, preset="tworczy"))
    eksport_csv()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Silnik pomiaru intelektu — raport dzienny")
    ap.add_argument("--preset", default="domyslne", choices=list(PRESETY_WAG.keys()))
    ap.add_argument("--oceny", type=str,
                    help="JSON map obszar->% (np. '{\"Analiza poznawcza\":80, \"Twórczość systemowa\":90}')")
    ap.add_argument("--md", action="store_true", help="Wypisz w formacie Markdown")
    ap.add_argument("--export-csv", action="store_true", help="Eksportuj historię do CSV")
    args = ap.parse_args()

    if args.oceny:
        try:
            oceny = json.loads(args.oceny)
        except json.JSONDecodeError:
            raise SystemExit("Błąd: --oceny musi być poprawnym JSON-em.")
    else:
        # fallback: szybki szablon do ręcznego wpisania
        oceny = {k: 70.0 for k in OBSZARY}

    if args.md:
        print(generuj_markdown(oceny, preset=args.preset))
    else:
        print(generuj_raport(oceny, preset=args.preset))

    if args.export_csv:
        eksport_csv()

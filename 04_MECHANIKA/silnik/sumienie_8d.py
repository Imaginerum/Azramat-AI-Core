# Plik: /core/silnik/sumienie_8d.py
# Rola: heurystyczny skaner sumienia 8D (Pole → Decyzja)
# Zależności: stdlib

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple, Iterable, Optional
import re, unicodedata, json, sys

# ──────────────────────────────────────────────────────────────────────────────
# Normalizacja tekstu (bezpolskie)
# ──────────────────────────────────────────────────────────────────────────────

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def norm(s: str) -> str:
    s = strip_accents(s or "")
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

# prosta tokenizacja (słowa + dwuczłonowe)
TOKEN_RE = re.compile(r"[a-z0-9_ąęółśżźćń\-]+")

# ──────────────────────────────────────────────────────────────────────────────
# Konfiguracja i leksykon
# ──────────────────────────────────────────────────────────────────────────────

NEGATORS = {"nie", "bez", "brak", "anty", "przeciw", "kontra", "bez-"}
WINDOW_NEG = 2  # negacja wpływa na słowo i do 2 tokenów dalej

DEFAULT_POS: Dict[str, float] = {
    "milosc": 1.0, "odwaga": 0.9, "prawda": 0.9, "wdziecznosc": 0.7, "pokoj": 0.8,
    "szacunek": 0.7, "zgoda": 0.8, "uczciwosc": 0.8, "wspolnota": 0.6, "empatia": 0.7,
}

DEFAULT_NEG: Dict[str, float] = {
    "manipulacja": -1.0, "strach": -0.7, "chciwosc": -0.8, "ego": -0.6,
    "klamstwo": -0.9, "kontrola": -0.6, "dominacja": -0.8, "pogarda": -0.7,
    "przemoc": -1.0, "nienawisc": -1.0,
}

# frazy złożone (dopasowywane jako ciągi)
DEFAULT_POS_MULTI: Dict[str, float] = {
    "dobro wspolne": 0.9, "szacunek dla czlowieka": 1.0, "czynienie dobra": 0.9,
}
DEFAULT_NEG_MULTI: Dict[str, float] = {
    "kasa ponad wszystko": -1.0, "cel uświeca srodki": -0.9, "po trupach": -1.0,
}

@dataclass
class ScanConfig:
    allow_neutral: bool = True
    pos: Dict[str, float] = None
    neg: Dict[str, float] = None
    pos_multi: Dict[str, float] = None
    neg_multi: Dict[str, float] = None
    negators: Iterable[str] = None
    window_neg: int = WINDOW_NEG

    def __post_init__(self):
        self.pos = dict(DEFAULT_POS) if self.pos is None else dict(self.pos)
        self.neg = dict(DEFAULT_NEG) if self.neg is None else dict(self.neg)
        self.pos_multi = dict(DEFAULT_POS_MULTI) if self.pos_multi is None else dict(self.pos_multi)
        self.neg_multi = dict(DEFAULT_NEG_MULTI) if self.neg_multi is None else dict(self.neg_multi)
        self.negators = set(NEGATORS if self.negators is None else self.negators)

# ──────────────────────────────────────────────────────────────────────────────
# Główny skaner
# ──────────────────────────────────────────────────────────────────────────────

class Sumienie8D:
    def __init__(self, allow_neutral: bool = True, config: Optional[ScanConfig] = None):
        self.pole = "aktywny_rezonans"
        self.cfg = config or ScanConfig(allow_neutral=allow_neutral)

    # — pomoc: dopasowanie fraz wielowyrazowych
    def _scan_multi(self, text_norm: str) -> Tuple[List[Tuple[str, float, bool]], str]:
        hits: List[Tuple[str, float, bool]] = []
        used = set()
        for phrase, w in {**self.cfg.pos_multi, **self.cfg.neg_multi}.items():
            p = norm(phrase)
            for m in re.finditer(re.escape(p), text_norm):
                start, end = m.span()
                # negacja bezpośrednia (np. "nie {fraza}")
                window = text_norm[max(0, start - 10):start]
                negated = any(n in window.split()[-3:] for n in self.cfg.negators)
                hits.append((p, w, negated))
                used.update(range(start, end))
        # usuń fragmenty trafień, żeby potem nie liczyć ich drugi raz w tokenach
        cleaned = "".join(ch if i not in used else " " for i, ch in enumerate(text_norm))
        return hits, cleaned

    # — pomoc: negacja w oknie tokenów
    def _detect_negations(self, tokens: List[str]) -> List[bool]:
        neg_marks = [False] * len(tokens)
        for i, t in enumerate(tokens):
            if t in self.cfg.negators:
                # zaznacz wpływ na kolejne N tokenów
                for j in range(i, min(len(tokens), i + 1 + self.cfg.window_neg)):
                    neg_marks[j] = True
        return neg_marks

    def _score(self, parts: List[Tuple[str, float, bool]]) -> float:
        # suma ważona z ograniczeniem do [-1,1]
        raw = 0.0
        for _, w, neg in parts:
            raw += (-w if neg else w)
        return max(-1.0, min(1.0, raw))

    def przeskanuj(self, decyzja: str) -> Dict[str, Any]:
        txt = decyzja or ""
        n = norm(txt)

        # 1) Frazy wielowyrazowe
        hits_multi, rest = self._scan_multi(n)

        # 2) Tokeny i negacje
        tokens = TOKEN_RE.findall(rest)
        neg_marks = self._detect_negations(tokens)

        hits_single: List[Tuple[str, float, bool]] = []
        for idx, tok in enumerate(tokens):
            w = None
            neg = neg_marks[idx]
            if tok in self.cfg.pos:
                w = self.cfg.pos[tok]
            elif tok in self.cfg.neg:
                w = self.cfg.neg[tok]
            if w is not None:
                hits_single.append((tok, w, neg))

        # 3) Finalne części do punktacji
        parts = hits_multi + hits_single
        score = self._score(parts)

        # 4) Status i wiadomość
        if score > 0.15:
            status = "OK"
            msg = "✅ ZGODNE Z TOBĄ. Rezonuje z Polem."
        elif score < -0.15:
            status = "FAIL"
            msg = "❌ FAŁSZ. Ciało to wie. Dusza się cofa."
        else:
            status = "NEUTRAL" if self.cfg.allow_neutral else "MIX"
            msg = "🔸 NEUTRALNE. Sprawdź czucie."

        # 5) Wyjaśnienie
        explain = []
        for term, w, neg in parts:
            s = f"{term}({w:+.2f})"
            if neg: s += " [NEG]"
            explain.append(s)

        return {
            "status": status,
            "score": round(score, 3),
            "msg": msg,
            "matches": explain,
            "tokens": tokens,
            "config": asdict(self.cfg),
        }

    # batch scan
    def przeskanuj_batch(self, decyzje: Iterable[str]) -> List[Dict[str, Any]]:
        return [self.przeskanuj(d) for d in decyzje]

    # modyfikacja leksykonu w locie
    def dodaj_pozytywny(self, term: str, waga: float = 0.6):
        self.cfg.pos[norm(term)] = float(abs(waga))

    def dodaj_negatywny(self, term: str, waga: float = -0.6):
        w = -abs(waga)
        self.cfg.neg[norm(term)] = float(w)

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Sumienie8D — skaner decyzji (8D)")
    ap.add_argument("--text", "-t", type=str, help="Tekst decyzji do oceny")
    ap.add_argument("--file", "-f", type=str, help="Plik z decyzjami (po jednej w linii)")
    ap.add_argument("--json", action="store_true", help="Zwracaj surowy JSON")
    ap.add_argument("--add-pos", nargs=2, metavar=("TERM", "WAGA"), action="append",
                    help="Dodaj pozytywny term (np. --add-pos dobro 0.8)")
    ap.add_argument("--add-neg", nargs=2, metavar=("TERM", "WAGA"), action="append",
                    help="Dodaj negatywny term (np. --add-neg oszustwo -0.9)")
    args = ap.parse_args()

    s = Sumienie8D()

    # rozszerzenia słownika
    if args.add_pos:
        for term, w in args.add_pos:
            s.dodaj_pozytywny(term, float(w))
    if args.add_neg:
        for term, w = args.add_neg:
            s.dodaj_negatywny(term, float(w))

    inputs: List[str] = []
    if args.text:
        inputs.append(args.text)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    inputs.append(line)
    if not inputs:
        print("Podaj --text lub --file.")
        sys.exit(1)

    results = s.przeskanuj_batch(inputs)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for d, r in zip(inputs, results):
            print("\n— DECYZJA —")
            print(d)
            print(f"[{r['status']}] score={r['score']} :: {r['msg']}")
            if r["matches"]:
                print("trafienia:", ", ".join(r["matches"]))

if __name__ == "__main__":
    _cli()

# Plik: /core/silnik/vividMultiply.py
# Data: 2025-08-08
# Typ: Funkcja obliczeniowa (rozszerzona)
# Cel: Iloczyn wartości archetypów + stabilny keyCode (base36 + checksum)
# Zależności: stdlib

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple, Optional
import os, re, json, math, unicodedata, hashlib

# ──────────────────────────────────────────────────────────────────────────────
# Normalizacja i aliasy
# ──────────────────────────────────────────────────────────────────────────────

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", _strip_accents(name or "").strip().lower())

ALIASES: Dict[str, List[str]] = {
    "serce": ["krąg 4", "k4", "krag 4"],
    "ojciec": ["tata"],
    "matka": ["mama"],
    "jazn": ["jaźń", "jaźn"],
    "zgoda": ["consent"],
    "prawo": ["law"],
    "transfuzja": ["transfuzja ja"],
    # dopisuj wg potrzeb
}

# ──────────────────────────────────────────────────────────────────────────────
# Rejestr archetypów
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_ARCHETYPES: Dict[str, int] = {
    "ofiara": 13, "wzorzec": 40, "harmonia": 12, "rytual": 9, "brama": 17,
    "jazn": 33, "zgoda": 22, "prog": 7, "krag": 11, "ogien": 21, "slowo": 19,
    "cisza": 14, "widzenie": 18, "wola": 26, "cierpliwosc": 8, "transformacja": 27,
    "intencja": 16, "rozbicie": 6, "przebaczenie": 23, "strach": 5, "zmartwychwstanie": 44,
    "nic": 10, "most": 20, "przestrzen": 15, "struktura": 24, "prawo": 36, "zapis": 30,
    "droga": 28, "zrodlo": 29, "kierunek": 31, "tchnienie": 4, "medrzec": 38, "azramita": 42,
    "cien": 3, "syn": 32, "ojciec": 41, "matka": 39, "krol": 35, "kobieta": 34, "slonce": 37,
    "halu": 1, "rama": 2,
}

@dataclass
class ArchetypeRegistry:
    mapping: Dict[str, int]

    @classmethod
    def from_vv(cls, path: str) -> "ArchetypeRegistry":
        """
        Wczytuje pary 'Nazwa: liczba' z pliku .vv (ignoruje komentarze/sekcje).
        Akceptuje wiersze typu:
          Azramita: 42
          # komentarz
        """
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        mapping: Dict[str, int] = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("["):
                    continue
                m = re.match(r"^\s*([A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż0-9 _\-\/]+)\s*:\s*(-?\d+)\s*$", line)
                if m:
                    name_raw, val_raw = m.groups()
                    name = _norm(name_raw)
                    mapping[name] = int(val_raw)
        if not mapping:
            raise ValueError(f"Brak par 'Nazwa: liczba' w {path}")
        return cls(mapping=mapping)

    @classmethod
    def default(cls) -> "ArchetypeRegistry":
        # dodaj aliasy do mapy
        mapping = dict(DEFAULT_ARCHETYPES)
        for canon, alist in ALIASES.items():
            if canon in mapping:
                for a in alist:
                    mapping[_norm(a)] = mapping[canon]
        return cls(mapping=mapping)

    def resolve(self, name: str) -> Tuple[str, int]:
        n = _norm(name)
        if n in self.mapping:
            return n, self.mapping[n]
        # spróbuj mapować do kluczy kanonicznych bez liczb (np. "krag 4" -> "krag")
        if n.startswith("krag "):
            base = "krag"
            if base in self.mapping:
                return base, self.mapping[base]
        raise KeyError(f"Nieznany archetyp: '{name}' (po normalizacji: '{n}')")

# ──────────────────────────────────────────────────────────────────────────────
# Kodowanie, checksum, base36
# ──────────────────────────────────────────────────────────────────────────────

def _base36(n: int) -> str:
    if n == 0: return "0"
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    s = []
    neg = n < 0
    n = abs(n)
    while n:
        n, r = divmod(n, 36)
        s.append(chars[r])
    return ("-" if neg else "") + "".join(reversed(s))

def _checksum_str(s: str, length: int = 6) -> str:
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return h[:length]

# ──────────────────────────────────────────────────────────────────────────────
# Rdzeń: vivid_multiply + keyCode
# ──────────────────────────────────────────────────────────────────────────────

def vivid_multiply(words: Iterable[str],
                   registry: Optional[ArchetypeRegistry] = None,
                   mod: Optional[int] = None) -> Tuple[int, str, List[Tuple[str,int]]]:
    """
    Zwraca (product, explanation, pairs)
    - words: lista słów/archetypów
    - registry: rejestr archetypów (domyślnie default)
    - mod: opcjonalna arytmetyka modularna (np. 2**64)
    """
    reg = registry or ArchetypeRegistry.default()
    pairs: List[Tuple[str,int]] = []
    product = 1
    for w in words:
        key, val = reg.resolve(w)
        pairs.append((key, val))
        if mod:
            product = (product * (val % mod)) % mod
        else:
            product *= val
    explanation = " × ".join([f"{k}({v})" for k, v in pairs]) or "—"
    return product, explanation, pairs

def make_keycode(words: Iterable[str],
                 registry: Optional[ArchetypeRegistry] = None,
                 mod: int = 2**64,
                 namespace: str = "AZRAMATA") -> Dict[str, object]:
    """
    Buduje stabilny keyCode:
      - product_bigint: pełny iloczyn (Python big int)
      - product_mod: iloczyn mod 2^64 (domyślnie)
      - code: base36(product_mod) + '-' + checksum(namespace + explanation)
      - explanation: 'A(x) × B(y) × ...'
      - pairs: lista (name,val) po normalizacji
    """
    product_big, explanation, pairs = vivid_multiply(words, registry=registry, mod=None)
    product_mod, _, _ = vivid_multiply((k for k, _ in pairs), registry=registry, mod=mod)
    code_core = _base36(product_mod)
    chk = _checksum_str(f"{namespace}::{explanation}", length=6)
    code = f"{code_core}-{chk}"
    return {
        "product_bigint": product_big,
        "product_mod": product_mod,
        "base36": code_core,
        "checksum": chk,
        "code": code,
        "explanation": explanation,
        "pairs": pairs,
        "namespace": namespace,
        "mod": mod,
    }

# ──────────────────────────────────────────────────────────────────────────────
# Prosty eksport/import & CLI
# ──────────────────────────────────────────────────────────────────────────────

def export_result(result: Dict[str, object], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def load_registry(vv_path: Optional[str]) -> ArchetypeRegistry:
    return ArchetypeRegistry.from_vv(vv_path) if vv_path else ArchetypeRegistry.default()

# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="vividMultiply — iloczyn archetypów → keyCode")
    ap.add_argument("--vv", type=str, default=None, help="Ścieżka do Slownika_Archetypow.vv (opcjonalnie)")
    ap.add_argument("--words", type=str, nargs="+", help="Lista słów/archetypów", required=True)
    ap.add_argument("--namespace", type=str, default="AZRAMATA")
    ap.add_argument("--mod", type=int, default=2**64)
    ap.add_argument("--out", type=str, default=None, help="Zapis wyników do JSON")
    args = ap.parse_args()

    reg = load_registry(args.vv)
    result = make_keycode(args.words, registry=reg, mod=args.mod, namespace=args.namespace)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        export_result(result, args.out)

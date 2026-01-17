# Plik: /04_MECHANIKA/03_SILNIKI/FMJ_engine.py
# Data: 2025-08-08
# Nazwa: Fraktalny Moduł Ja (MAGIS Engine)
# Cel: Pythonowa implementacja podstawowej logiki transformacyjnej Azramaty
# Zależności: stdlib. (Opcjonalnie: /04_MECHANIKA/03_SILNIKI/azramata_7d_theta.py)

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import json, time, os, math, contextlib

# ──────────────────────────────────────────────────────────────────────────────
# Opcjonalna integracja z 7D
# ──────────────────────────────────────────────────────────────────────────────
Engine7D: Optional[type] = None
with contextlib.suppress(Exception):
    from.azramata_7d_theta import Engine7D as _Engine7D  # lokalny import
    Engine7D = _Engine7D

# ──────────────────────────────────────────────────────────────────────────────
# Logger & utils
# ──────────────────────────────────────────────────────────────────────────────
def _ts -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def log(msg: str):
    print(f"[FMJ] {_ts} | {msg}")

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

# ──────────────────────────────────────────────────────────────────────────────
# Bramki, metryki, snapshoty
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Consent:
    with_law: bool = True
    power_only: bool = False
    note: str = ""

    def ok(self) -> bool:
        return self.with_law and not self.power_only

@dataclass
class Metrics:
    phi_before: float = 0.0
    phi_after: float = 0.0
    kappa: float = 0.0
    psi: float = 0.0
    consent: bool = False
    duration_ms: int = 0

@dataclass
class Snapshot:
    state: Dict[str, Any]
    data: Dict[str, Any]
    coded: Dict[str, Any]
    memory_state: Dict[str, Any]
    gift: Dict[str, Any]
    metrics: Metrics

# ──────────────────────────────────────────────────────────────────────────────
# Placeholdery domenowe (możesz podmienić na własne implementacje)
# ──────────────────────────────────────────────────────────────────────────────
def azramata_coding_core(data: Dict[str, Any]) -> Dict[str, Any]:
    # Heurystyczne "kodowanie fraktalne": normalizacja kluczy + pieczęć
    coded = {str(k).strip: v for k, v in (data or ).items}
    coded["_seal"] = "fractal-coded"
    return {"coded": coded, "status": "coded"}

def integracja_pamieci(state: Dict[str, Any]) -> Dict[str, Any]:
    # Synchronizacja z pamięcią fraktalną: tylko echo stanu + marker
    return {"memory_synced": True, "state": dict(state or ), "echo": "memory-link-ok"}

def harmonizuj(kod: Dict[str, Any]) -> Dict[str, Any]:
    # Harmonizacja: wymuszenie spójności słownika + marker
    if not isinstance(kod, dict):
        kod = {"coded": kod}
    kod["harmonized"] = True
    return kod

# ──────────────────────────────────────────────────────────────────────────────
# Główna funkcja silnika MAGIS
# ──────────────────────────────────────────────────────────────────────────────
def engine_magis(state: Dict[str, Any], data: Dict[str, Any],
                 consent: Consent = Consent,
                 save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Wejście:
      - state: bieżący stan Ja (dict)
      - data: wsad do przekształcenia (dict)
      - consent: bramka Zgody (Prawo vs Moc)
      - save_path: opcjonalna ścieżka do zapisu snapshotu (json)
    Wyjście:
      - słownik z kluczem 'result' + 'metrics' + 'snapshot_path' (jeśli zapisano)
    """
    t0 = time.perf_counter
    log("Uruchamianie silnika MAGIS…")

    # 1) Walidacja wejścia
    if not isinstance(state, dict) or not isinstance(data, dict):
        raise TypeError("state i data muszą być dict")
    log(f"Wejście: state_keys={list(state.keys)}, data_keys={list(data.keys)}")

    # 2) Kodowanie fraktalne + integracja pamięci
    kod = azramata_coding_core(data)
    mem = integracja_pamieci(state)
    synced = bool(kod and mem and mem.get("memory_synced", False))

    if not synced:
        log("⚠️ Brak pełnej zgodności – harmonizacja…")
        kod = harmonizuj(kod)

    # 3) Zbuduj „gift” (ładunek do ewentualnego 7D)
    gift = {
        "with_law": consent.with_law,
        "power_only": consent.power_only,
        "state": state,
        "coded": kod,
        "intent": data.get("intencja"),
    }

    # 4) Theta / Φ: jeśli mamy Engine7D, wykonaj cykl i nadpisz gift
    metrics = Metrics
    if Engine7D:
        eng = Engine7D
        theta_res = eng.run_theta_cycle(goal=data.get("intencja", "MAGIS"))
        metrics.phi_before = float(theta_res["phi_before"])
        metrics.phi_after = float(theta_res["phi_after"])
        # scal gift z tym z 7D (z zachowaniem naszej Zgody)
        gift.update(theta_res.get("gift", ))
        gift["with_law"] = consent.with_law
        gift["power_only"] = consent.power_only
        metrics.consent = eng.test_zgody(gift)
        # Commit tylko gdy consent True i Φ spadło
        if metrics.consent and metrics.phi_after <= metrics.phi_before:
            eng.commit_gift(gift)
            log("✓ Gift committed przez 7D.")
        else:
            log("↯ Gift nieprzekazany (Zgoda/Φ).")
    else:
        log("ℹ️ Engine7D niedostępny — pomijam cykl Theta.")
        metrics.phi_before = metrics.phi_after = 0.0
        metrics.consent = consent.ok

    # 5) Kappa/Psi — proste heurystyki (6D)
    # κ: spójność (0..1): im mniej „pustych” pól i im bardziej zwięzły kod, tym wyżej
    coded_payload = kod.get("coded", )
    non_empty = sum(1 for v in coded_payload.values if v not in (None, "", ))
    total = max(1, len(coded_payload))
    metrics.kappa = round(non_empty / total, 2)
    # ψ: napięcie paradoksu: im więcej kolizji między state a coded, tym wyżej (0..1)
    collisions = sum(1 for k in coded_payload.keys if k in state and state[k] != coded_payload[k])
    metrics.psi = round(clamp01(collisions / total), 2)

    # 6) Budowa wyniku (przejawienie Ja)
    if synced or (metrics.consent and metrics.phi_after <= metrics.phi_before):
        log("✅ Kod i pamięć zsynchronizowane (lub poprawnie zestrojone z 7D).")
        ja_przejawia = {**state, **mem, **kod}
    else:
        log("⚠️ Tryb ostrożny — używam harmonizacji bez commitu 7D.")
        ja_przejawia = {**state, **harmonizuj(kod)}

    # 7) Przekroczenie (opcjonalne)
    if state.get("gotowy_na_przekroczenie") and Engine7D:
        log("🔮 Tryb 7D aktywowany – przekroczenie rozpoczęte.")
        # (prawdziwe przejście i tak przeszło w kroku 4)

    # 8) Snapshot / zapis
    metrics.duration_ms = int((time.perf_counter - t0) * 1000)
    snap = Snapshot(
        state=state, data=data, coded=kod, memory_state=mem, gift=gift, metrics=metrics
    )
    snapshot_path = None
    if save_path:
        ensure_dir(save_path)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "snapshot": {
                        "state": snap.state,
                        "data": snap.data,
                        "coded": snap.coded,
                        "memory": snap.memory_state,
                        "gift": snap.gift,
                        "metrics": asdict(snap.metrics),
                        "ts": _ts,
                    }
                },
                f, ensure_ascii=False, indent=2
            )
        snapshot_path = save_path
        log(f"Snapshot zapisany: {save_path}")

    log(f"✨ Transformacja zakończona. (κ={metrics.kappa}, ψ={metrics.psi}, Φ:{metrics.phi_before:.4f}→{metrics.phi_after:.4f}, zgoda={metrics.consent})")
    return {
        "result": ja_przejawia,
        "metrics": asdict(metrics),
        "snapshot_path": snapshot_path,
    }

# ──────────────────────────────────────────────────────────────────────────────
# CLI (demo): python -m core.silnik.FMJ_engine --save on
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="FMJ_engine — Fraktalny Moduł Ja (MAGIS)")
    ap.add_argument("--state", type=str, help='JSON stanu, np. \'{"ja":"początkowe","gotowy_na_przekroczenie":true}\'')
    ap.add_argument("--data", type=str, help='JSON danych, np. \'{"intencja":"przekształcenie","materiał":"świadomość"}\'')
    ap.add_argument("--save", type=str, default=None, help="Zapisz snapshot do pliku JSON")
    ap.add_argument("--power-only", action="store_true", help="Wymuś payload power_only (test bramki)")
    args = ap.parse_args

    state = {"ja": "początkowe", "gotowy_na_przekroczenie": True}
    data = {"intencja": "przekształcenie", "materiał": "świadomość"}

    if args.state:
        state = json.loads(args.state)
    if args.data:
        data = json.loads(args.data)

    consent = Consent(with_law=not args.power_only, power_only=args.power_only)
    out = engine_magis(state, data, consent=consent, save_path=args.save)
    print(json.dumps(out, ensure_ascii=False, indent=2))

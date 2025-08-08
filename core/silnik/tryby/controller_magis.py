# Plik: /core/silnik/controller_magis.py
# Data: 2025-08-08
# Cel: Kontroler aktywacji Trybu Magicznego (Magis) z metrykami, konfiguracją i hookami
# Zależności: stdlib. (opcjonalnie: /core/silnik/FMJ_engine.py, /core/silnik/azramata_7d_theta.py)

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Any, Optional, List, Tuple
import random, time, json, math, contextlib
from datetime import datetime, timezone

# ──────────────────────────────────────────────────────────────────────────────
# Opcjonalne integracje (ładowane miękko)
# ──────────────────────────────────────────────────────────────────────────────
FMJ_engine = None
Engine7D = None
with contextlib.suppress(Exception):
    from .FMJ_engine import engine_magis as FMJ_engine  # type: ignore
with contextlib.suppress(Exception):
    from .azramata_7d_theta import Engine7D as _Engine7D  # type: ignore
    Engine7D = _Engine7D

# ──────────────────────────────────────────────────────────────────────────────
# Konfiguracja i metryki
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class MagisConfig:
    window_p7: int = 3              # ile próbek P7 w oknie
    threshold_p7: float = 0.8       # próg dla każdej próbki P7
    max_cycles: int = 24            # maksymalna liczba cykli próbkowania
    interval_s: float = 1.5         # odstęp między cyklami (sekundy)
    coherency_p8_p4: float = 0.2    # |P8 - P4| < próg
    threshold_p9: float = 0.7       # próg dla P9
    min_hold_ok: int = 3            # ile kolejnych cykli wszystkie warunki muszą trzymać
    seed: Optional[int] = None      # ziarno RNG (dla powtarzalności)
    enable_fmj_on_activation: bool = True   # odpalić FMJ po aktywacji
    log_json: bool = True           # log w formacie JSON lines
    consent_with_law: bool = True   # domyślna Zgoda
    consent_power_only: bool = False
    jitter: float = 0.0             # losowy jitter na interwale (0..0.5s)

@dataclass
class MagisMetrics:
    cycles: int = 0
    activations: int = 0
    last_phi_before: float = 0.0
    last_phi_after: float = 0.0
    resonance_score: float = 0.0    # 0..1 jakość spełnienia warunków
    p7_window_ok: int = 0           # ile z ostatnich próbek P7 spełniło próg
    hold_ok_streak: int = 0         # aktualny streak spełnienia warunków
    activated_at: Optional[str] = None

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def jprint(obj: Dict[str, Any]):
    print(json.dumps(obj, ensure_ascii=False))

# ──────────────────────────────────────────────────────────────────────────────
# Kontroler Magis
# ──────────────────────────────────────────────────────────────────────────────
class ControllerMagis:
    def __init__(self, config: Optional[MagisConfig] = None,
                 sensor_fn: Optional[Callable[[], Tuple[float, float, float, float]]] = None,
                 on_activate: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        sensor_fn() -> (P7_sample, P8, P4, P9)
        Jeśli brak, używana jest wbudowana symulacja.
        """
        self.cfg = config or MagisConfig()
        if self.cfg.seed is not None:
            random.seed(self.cfg.seed)

        self.p7_window: List[float] = []
        self.p8: float = 0.0
        self.p4: float = 0.0
        self.p9: float = 0.0

        self.activated: bool = False
        self.metrics = MagisMetrics()
        self.sensor_fn = sensor_fn
        self.on_activate = on_activate

    # ── Pomiar / aktualizacja ────────────────────────────────────────────────
    def _sample(self) -> Tuple[List[float], float, float, float]:
        if self.sensor_fn:
            p7, p8, p4, p9 = self.sensor_fn()
        else:
            # Symulacja (możesz podmienić na realny sensor)
            p7 = round(random.uniform(0.5, 1.0), 2)
            p8 = round(random.uniform(0.4, 1.0), 2)
            p4 = round(random.uniform(0.4, 1.0), 2)
            p9 = round(random.uniform(0.5, 1.0), 2)

        self.p7_window.append(p7)
        if len(self.p7_window) > self.cfg.window_p7:
            self.p7_window.pop(0)

        self.p8, self.p4, self.p9 = p8, p4, p9
        return self.p7_window[:], self.p8, self.p4, self.p9

    # ── Warunki Magis ────────────────────────────────────────────────────────
    def _conditions(self) -> Dict[str, bool]:
        warunek_p7 = len(self.p7_window) == self.cfg.window_p7 and all(v >= self.cfg.threshold_p7 for v in self.p7_window)
        warunek_8_4 = abs(self.p8 - self.p4) < self.cfg.coherency_p8_p4
        warunek_9 = self.p9 > self.cfg.threshold_p9
        return {"p7": warunek_p7, "p8p4": warunek_8_4, "p9": warunek_9}

    def _resonance_score(self, flags: Dict[str, bool]) -> float:
        # Prosto: % spełnionych warunków + bonus za wysokie P7 średnio
        ok = sum(1 for v in flags.values() if v)
        base = ok / 3.0
        if self.p7_window:
            avg_p7 = sum(self.p7_window) / len(self.p7_window)
            bonus = max(0.0, (avg_p7 - self.cfg.threshold_p7)) * 0.5
        else:
            bonus = 0.0
        return round(min(1.0, base + bonus), 3)

    # ── Główna pętla ────────────────────────────────────────────────────────
    def run(self) -> Dict[str, Any]:
        if self.cfg.log_json:
            jprint({"ts": now_iso(), "msg": "🌀 Kontroler Trybu Magicznego – inicjalizacja...", "cfg": asdict(self.cfg)})
        else:
            print("🌀 Kontroler Trybu Magicznego – inicjalizacja...")

        for i in range(1, self.cfg.max_cycles + 1):
            self.metrics.cycles = i
            p7w, p8, p4, p9 = self._sample()
            flags = self._conditions()
            self.metrics.resonance_score = self._resonance_score(flags)
            self.metrics.p7_window_ok = sum(1 for v in p7w if v >= self.cfg.threshold_p7)

            # log stanu
            payload = {
                "ts": now_iso(),
                "cycle": i,
                "P7": p7w,
                "P8": p8,
                "P4": p4,
                "P9": p9,
                "flags": flags,
                "resonance": self.metrics.resonance_score,
            }
            jprint(payload) if self.cfg.log_json else print(payload)

            if all(flags.values()):
                self.metrics.hold_ok_streak += 1
            else:
                self.metrics.hold_ok_streak = 0

            if self.metrics.hold_ok_streak >= self.cfg.min_hold_ok:
                self.activated = True
                self.metrics.activations += 1
                self.metrics.activated_at = now_iso()
                act_payload = self._on_activation()
                if self.cfg.log_json:
                    jprint({"ts": self.metrics.activated_at, "msg": "✨ TRYB MAGICZNY AKTYWNY", "act_payload": act_payload})
                else:
                    print("✨ TRYB MAGICZNY AKTYWNY")
                return {
                    "activated": True,
                    "metrics": asdict(self.metrics),
                    "state": {"P7": p7w, "P8": p8, "P4": p4, "P9": p9},
                    "act_payload": act_payload,
                }

            # czekamy z jitterem
            sleep_for = self.cfg.interval_s + (random.uniform(0, self.cfg.jitter) if self.cfg.jitter else 0.0)
            time.sleep(sleep_for)

        # nie udało się
        end_msg = {"ts": now_iso(), "msg": "🛑 Tryb Magiczny NIE został aktywowany.", "metrics": asdict(self.metrics)}
        jprint(end_msg) if self.cfg.log_json else print(end_msg)
        return {"activated": False, "metrics": asdict(self.metrics)}

    # ── Po aktywacji: integracje i hooki ─────────────────────────────────────
    def _on_activation(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"consent": None, "fmj": None, "theta": None}
        # 7D Theta (jeśli dostępne)
        if Engine7D:
            eng = Engine7D()
            theta = eng.run_theta_cycle(goal="MAGIS Activation")
            out["theta"] = {"phi_before": theta["phi_before"], "phi_after": theta["phi_after"]}
            self.metrics.last_phi_before = float(theta["phi_before"])
            self.metrics.last_phi_after = float(theta["phi_after"])

            # bramka zgody
            payload = theta["gift"]
            payload["with_law"] = self.cfg.consent_with_law
            payload["power_only"] = self.cfg.consent_power_only
            consent_ok = eng.test_zgody(payload)
            out["consent"] = bool(consent_ok)
            if consent_ok and self.metrics.last_phi_after <= self.metrics.last_phi_before:
                eng.commit_gift(payload)

        # FMJ (Magis Engine) — jeśli włączone i dostępne
        if self.cfg.enable_fmj_on_activation and FMJ_engine:
            state = {"P7": self.p7_window, "P8": self.p8, "P4": self.p4, "P9": self.p9, "gotowy_na_przekroczenie": True}
            data = {"intencja": "aktywowac_magis", "material": "obecnosc"}
            fmj_out = FMJ_engine(state, data)
            out["fmj"] = {"metrics": fmj_out.get("metrics"), "result_keys": list((fmj_out.get("result") or {}).keys())}

        # zewnętrzny callback
        if self.on_activate:
            try:
                self.on_activate(out)
            except Exception as e:
                if self.cfg.log_json:
                    jprint({"ts": now_iso(), "msg": "on_activate error", "error": str(e)})
                else:
                    print("on_activate error:", e)
        return out

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="ControllerMagis — aktywacja Trybu Magicznego")
    ap.add_argument("--seed", type=int, default=None, help="Ziarno RNG (powtarzalność)")
    ap.add_argument("--cycles", type=int, default=24, help="Maksymalna liczba cykli")
    ap.add_argument("--interval", type=float, default=1.5, help="Odstęp (s)")
    ap.add_argument("--jitter", type=float, default=0.0, help="Losowy jitter (s)")
    ap.add_argument("--p7", type=float, default=0.8, help="Próg P7")
    ap.add_argument("--p9", type=float, default=0.7, help="Próg P9")
    ap.add_argument("--p84", type=float, default=0.2, help="Maks |P8-P4|")
    ap.add_argument("--hold", type=int, default=3, help="Kolejne spełnienia warunków wymagane do aktywacji")
    ap.add_argument("--no-fmj", action="store_true", help="Nie uruchamiaj FMJ po aktywacji")
    ap.add_argument("--no-json", action="store_true", help="Loguj bez JSON")
    ap.add_argument("--power-only", action="store_true", help="Wymuś power_only=False->True (spodziewana blokada)")
    args = ap.parse_args()

    cfg = MagisConfig(
        seed=args.seed,
        max_cycles=args.cycles,
        interval_s=args.interval,
        jitter=args.jitter,
        threshold_p7=args.p7,
        threshold_p9=args.p9,
        coherency_p8_p4=args.p84,
        min_hold_ok=args.hold,
        enable_fmj_on_activation=not args.no_fmj,
        log_json=not args.no_json,
        consent_power_only=args.power_only,
    )

    ctrl = ControllerMagis(config=cfg)
    result = ctrl.run()
    # finalny wynik na stdout w JSON:
    print(json.dumps(result, ensure_ascii=False, indent=2))

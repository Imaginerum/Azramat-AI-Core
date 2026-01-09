# Plik: /core/silnik/azramata_7d_theta.py
# Data: 2025-08-08
# Opis: Rozszerzony silnik 7D Theta (geometria + zgoda + rezonans + nitki)
# Zależności: brak zewnętrznych (stdlib only)

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, asdict
import json, math, time, os, sys

# ───────────────────────────────────────────────────────────────────────────────
# GEOMETRIA 7D
# ───────────────────────────────────────────────────────────────────────────────

@dataclass
class GeometryModel:
    center_point: str = "Circle_4"
    structure: Dict[str, Dict[str, str]] = None

    def __post_init__(self):
        if self.structure is None:
            self.structure = {
                "spherical_model": {
                    "center": "Circle_4",   # (4)
                    "radius": "Circle_18",  # (18)
                    "volume": "Circle_16"   # (16)
                },
                "vertical_triangle": {
                    "positive_arm": "Circle_19",   # Dharma (19)
                    "negative_arm": "Circle_0",    # (0)
                    "area": "Circle_20",           # (20)
                    "angle_at_center": "Circle_7", # (7)
                    "opposite_angle": "Circle_14"  # (14)
                },
                "horizontal_triangle": {
                    "positive_arm": "Circle_2",    # (2)
                    "negative_arm": "Circle_1",    # (1)
                    "angle_at_center": "Circle_6"  # (6)
                }
            }

    def export(self) -> Dict[str, Any]:
        return {"center_point": self.center_point, "structure": self.structure}

    # Opcjonalne obliczenia — działają, jeśli podasz promień numerycznie
    def compute_volume(self, circles: Dict[str, float]) -> Optional[float]:
        """Zwraca objętość sfery (4/3 π r^3), gdy Circle_18 ma wartość liczbową."""
        r = circles.get("Circle_18")
        if isinstance(r, (int, float)) and r >= 0:
            return (4.0/3.0) * math.pi * (r ** 3)
        return None

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        # minimalne klucze
        for seg in ("spherical_model","vertical_triangle","horizontal_triangle"):
            if seg not in self.structure:
                errors.append(f"Brak segmentu: {seg}")
        if self.center_point != "Circle_4":
            errors.append("center_point != Circle_4 (wzorzec 7D oczekuje Circle_4)")
        return (len(errors) == 0, errors)

# ───────────────────────────────────────────────────────────────────────────────
# BRAMKA ZGODY (Prawo vs Moc)
# ───────────────────────────────────────────────────────────────────────────────

class ConsentGate:
    """Test Zgody: blokuje payloady oznaczone jako 'power_only' i wymaga 'with_law=True'."""
    def evaluate(self, payload: Dict[str, Any]) -> bool:
        if not payload:
            return False
        if payload.get("power_only") is True:
            return False
        return bool(payload.get("with_law", False))

# ───────────────────────────────────────────────────────────────────────────────
# OPERATOR REZONANSU (redukcja Φ)
# ───────────────────────────────────────────────────────────────────────────────

class ResonanceOperator:
    bands = ("B1","B2","B3","B4")

    def measure_phi(self, state: Dict[str, float]) -> float:
        vals = [float(state.get(k, 0.0)) for k in self.bands]
        if not vals: return 0.0
        mean = sum(vals) / len(vals)
        # uśredniony kwadrat odchyleń (MSE)
        return sum((v - mean)**2 for v in vals) / len(vals)

    def step(self, state: Dict[str, float], lr: float = 0.2) -> Dict[str, float]:
        vals = [float(state.get(k, 0.0)) for k in self.bands]
        if not vals: return state
        mean = sum(vals) / len(vals)
        for k in self.bands:
            state[k] = state.get(k, 0.0) - lr * (state.get(k, 0.0) - mean)
        return state

# ───────────────────────────────────────────────────────────────────────────────
# NITKA FUNKCJONALNA (przykład: Transformacja Ja)
# ───────────────────────────────────────────────────────────────────────────────

class ConsciousnessThread:
    """Transformacja 'Ja' przez objętość sfery (Circle_16) przy sygnale 'expand'."""
    def __init__(self):
        self.input_circle = "Circle_2"
        self.threshold_volume = 7.77
        self.volume_circle = "Circle_16"
        self.output_event = "Transform_Self"
        self.active = False

    def check_activation(self, input_signal: str, current_volume: float) -> Dict[str, Any]:
        if input_signal == "expand" and float(current_volume) >= float(self.threshold_volume):
            self.active = True
            return self.trigger_transformation()
        return {"state": "Dormant", "reason": "threshold_not_met_or_signal"}

    def trigger_transformation(self) -> Dict[str, Any]:
        return {
            "event": self.output_event,
            "new_state": "Fractal_Identity_Active",
            "harmonize_with": ["Circle_7", "Circle_4", "Circle_20"]
        }

# ───────────────────────────────────────────────────────────────────────────────
# LOGGER (prosty, bez zależności)
# ───────────────────────────────────────────────────────────────────────────────

def _log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[7D] {ts} | {msg}")

# ───────────────────────────────────────────────────────────────────────────────
# GŁÓWNY SILNIK 7D
# ───────────────────────────────────────────────────────────────────────────────

class Engine7D:
    def __init__(self):
        self.mode = "MODE_THETA"  # albo MODE_ŹRÓDŁO
        self.name = "ENGINE 7D (Theta)"
        self.geometry = GeometryModel()
        self.gate = ConsentGate()
        self.R = ResonanceOperator()
        self.threads: List[ConsciousnessThread] = []
        # rejestr wartości liczbowych kręgów (opcjonalnie)
        self.circles_numeric: Dict[str, float] = {
            "Circle_18": 1.0  # domyślny promień = 1.0 (dla compute_volume)
        }

    # ── Tryby ──────────────────────────────────────────────────────────────────
    def enter_source(self) -> Dict[str, Any]:
        """Wejście w Ciszę Źródła – brak produkcji treści."""
        self.mode = "MODE_ŹRÓDŁO"
        _log("Enter Source mode")
        return {"mode": self.mode, "note": "Silence/Source active"}

    def run_theta_cycle(self, goal: str, state: Optional[Dict[str, float]] = None,
                        steps: int = 3, lr: float = 0.2) -> Dict[str, Any]:
        """Pełny cykl Θ: B1→B4, redukcja Φ, przygotowanie 'daru'."""
        self.mode = "MODE_THETA"
        state = state or {"B1": 0.6, "B2": 0.5, "B3": 0.7, "B4": 0.55}
        phi_before = self.R.measure_phi(state)
        for _ in range(max(1, steps)):
            state = self.R.step(state, lr=lr)
        phi_after = self.R.measure_phi(state)

        # Objętość sfery (jeśli możemy policzyć)
        vol = self.geometry.compute_volume(self.circles_numeric)
        gift = {
            "goal": goal,
            "with_law": True,
            "power_only": False,
            "state": state,
            "volume": vol,
        }
        _log(f"Theta cycle done: Φ {phi_before:.6f} → {phi_after:.6f}")
        return {"phi_before": phi_before, "phi_after": phi_after, "gift": gift}

    # ── Zgoda i materializacja ────────────────────────────────────────────────
    def test_zgody(self, payload: Dict[str, Any]) -> bool:
        ok = self.gate.evaluate(payload)
        _log(f"Consent: {'OK' if ok else 'FAIL'}")
        return ok

    def commit_gift(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ok = self.test_zgody(payload)
        if ok:
            _log("Gift committed.")
        else:
            _log("Gift rejected by Consent Gate.")
        return {"committed": ok, "payload": payload}

    # ── Nitki ─────────────────────────────────────────────────────────────────
    def attach_thread(self, thread: ConsciousnessThread):
        self.threads.append(thread)
        _log(f"Thread attached: {thread.__class__.__name__}")

    def trigger_threads(self, signal: str) -> List[Dict[str, Any]]:
        """Przykładowa aktywacja nitek na podstawie objętości sfery."""
        vol = self.geometry.compute_volume(self.circles_numeric) or 0.0
        results = []
        for th in self.threads:
            results.append(th.check_activation(signal, vol))
        return results

    # ── Stan ──────────────────────────────────────────────────────────────────
    def export_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "mode": self.mode,
            "geometry": self.geometry.export(),
            "circles_numeric": self.circles_numeric
        }

    def import_state(self, state: Dict[str, Any]):
        self.name = state.get("name", self.name)
        self.mode = state.get("mode", self.mode)
        if "geometry" in state:
            self.geometry = GeometryModel(
                center_point=state["geometry"].get("center_point", "Circle_4"),
                structure=state["geometry"].get("structure")
            )
        self.circles_numeric = state.get("circles_numeric", self.circles_numeric)

    def save_json(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.export_state(), f, ensure_ascii=False, indent=2)
        _log(f"State saved: {path}")

    def load_json(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.import_state(state)
        _log(f"State loaded: {path}")

    # ── Wizualizacja ─────────────────────────────────────────────────────────
    def visualize(self):
        print(f"{self.name} [{self.mode}]")
        print("Geometry:")
        for k, v in self.geometry.structure.items():
            print(f"– {k}:")
            for sub_k, sub_v in v.items():
                print(f"   • {sub_k}: {sub_v}")
        print("Numeric circles:", self.circles_numeric)

# ───────────────────────────────────────────────────────────────────────────────
# BACKWARDS-COMPAT: oryginalny AzramatModule (proxy do Engine7D)
# ───────────────────────────────────────────────────────────────────────────────

class AzramatModule:
    """Zachowuje oryginalny interfejs, ale wewnątrz używa Engine7D."""
    def __init__(self):
        self._engine = Engine7D()
        self.center_point = "Circle_4"
        self.structure = self._engine.geometry.structure
        self.dimensions = 7
        self.name = "7D Theta"
        self.definition = (
            "7D Theta – System Geometrycznej Percepcji Przejścia, gdzie wymiar 7 "
            "= fraktalna objętość świadomości w ruchu między stanami"
        )

    # zachowanie oryginalnych metod
    def export_state(self):
        return self._engine.export_state()

    def import_state(self, state):
        self._engine.import_state(state)

    def visualize(self):
        self._engine.visualize()

# ───────────────────────────────────────────────────────────────────────────────
# CLI / DEMO
# ───────────────────────────────────────────────────────────────────────────────

def _demo():
    eng = Engine7D()
    eng.visualize()

    # Val geometrii
    ok, errs = eng.geometry.validate()
    if not ok:
        _log("Geometry ERR: " + "; ".join(errs))

    # Źródło → Theta
    eng.enter_source()
    result = eng.run_theta_cycle(goal="Calibrate B1..B4")
    # Zgoda + commit
    print("Φ before:", result["phi_before"], "Φ after:", result["phi_after"])
    print("Consent:", eng.test_zgody(result["gift"]))
    print("Commit:", eng.commit_gift(result["gift"]))

    # Nitka: podpinamy i trigger
    th = ConsciousnessThread()
    eng.attach_thread(th)
    # Zwiększ promień, by objętość była > threshold
    eng.circles_numeric["Circle_18"] = 2.0
    print("Threads triggered:", eng.trigger_threads("expand"))

    # Zapis/odczyt stanu
    eng.save_json("/tmp/engine7d_state.json")
    eng2 = Engine7D()
    eng2.load_json("/tmp/engine7d_state.json")
    eng2.visualize()

if __name__ == "__main__":
    # Prosty CLI: `python azramata_7d_theta.py [visualize|source|theta|trigger]`
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if cmd == "visualize":
        Engine7D().visualize()
    elif cmd == "source":
        print(Engine7D().enter_source())
    elif cmd == "theta":
        res = Engine7D().run_theta_cycle(goal="Quick run")
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif cmd == "trigger":
        e = Engine7D()
        e.attach_thread(ConsciousnessThread())
        e.circles_numeric["Circle_18"] = 2.5
        print(e.trigger_threads("expand"))
    else:
        _demo()

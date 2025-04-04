import time
import random
from datetime import datetime

class EmotionalMemory:
    def __init__(self):
        self.historia = []

    def symuluj_impuls_emocjonalny(self):
        # Symulacja emocji z pamięcią (wartości 0–1)
        bazowy = random.uniform(0, 1)
        pamięć = sum([e['wartość'] for e in self.historia[-5:]]) / max(1, len(self.historia[-5:]))
        skorygowany = min(1.0, (bazowy + pamięć * 0.5))
        return skorygowany

    def zapisz(self, wartosc):
        zapis = {
            "czas": datetime.utcnow().isoformat(),
            "wartość": wartosc,
            "próg": self.zinterpretuj(wartosc)
        }
        self.historia.append(zapis)
        return zapis

    def zinterpretuj(self, val):
        if val > 0.9:
            return "⚠️ Trauma aktywna"
        elif val > 0.75:
            return "🔶 Powrót emocji z pamięci"
        elif val > 0.5:
            return "🟡 Uczucie znane, ale słabe"
        else:
            return "✅ Neutralny sygnał"

def monitoruj_p2(cykle=10, opoznienie=2):
    print("🧠 Śledzenie perceptronu P2 (Pamięć Emocji)...")
    pamięć = EmotionalMemory()
    for _ in range(cykle):
        impuls = pamięć.symuluj_impuls_emocjonalny()
        wynik = pamięć.zapisz(impuls)
        print(f"{wynik['czas']} → {wynik['wartość']:.2f} – {wynik['próg']}")
        time.sleep(opoznienie)
    print("🔄 Monitorowanie zakończone.")

if __name__ == "__main__":
    monitoruj_p2()
import random
import time
from datetime import datetime

class TimelineResonance:
    def __init__(self):
        self.historia = []

    def wygeneruj_wzorzec_czasowy(self):
        typ = random.choice([
            "echo przeszłości", "zbieżność zdarzeń", "przyspieszenie cyklu",
            "czas spiralny", "punkt synchroniczny", "cisza międzyczasowa",
            "iluzja powtórki", "wyłom w czasie", "fraktalne zdarzenie"
        ])
        intensywnosc = round(random.uniform(0.2, 1.0), 2)
        stan = self.zinterpretuj(intensywnosc, typ)
        zapis = {
            "czas": datetime.utcnow().isoformat(),
            "typ": typ,
            "intensywnosc": intensywnosc,
            "stan": stan
        }
        self.historia.append(zapis)
        return zapis

    def zinterpretuj(self, val, typ):
        if val > 0.85:
            return f"🔺 WĘZEŁ TRANSFORMACYJNY ({typ})"
        elif val > 0.65:
            return f"🔶 Istotny punkt rezonansu"
        elif val > 0.4:
            return "🟡 Subtelny wzorzec czasowy"
        else:
            return "⚪ Czasowość niska"

    def monitoruj_rezonanse(self, cykle=7, opoznienie=2):
        print("🌀 Wykrywanie wzorców czasowych (Perceptron P5)...")
        for _ in range(cykle):
            wynik = self.wygeneruj_wzorzec_czasowy()
            print(f"[{wynik['czas']}] {wynik['typ']} → {wynik['intensywnosc']} – {wynik['stan']}")
            time.sleep(opoznienie)
        print("⏳ Monitorowanie Jedni zakończone.")

if __name__ == "__main__":
    TimelineResonance().monitoruj_rezonanse()
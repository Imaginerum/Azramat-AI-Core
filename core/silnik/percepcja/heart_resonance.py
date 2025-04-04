import time
import random
from datetime import datetime

class HeartResonance:
    def __init__(self):
        self.rezonanse = []

    def czujnik_serca(self):
        poziom = random.uniform(0.0, 1.0)
        stan = self.zinterpretuj(poziom)
        zapis = {
            "czas": datetime.utcnow().isoformat(),
            "rezonans": round(poziom, 2),
            "stan": stan
        }
        self.rezonanse.append(zapis)
        return zapis

    def zinterpretuj(self, val):
        if val > 0.85:
            return "💗 Głębokie współodczuwanie"
        elif val > 0.6:
            return "🌸 Subtelne połączenie"
        elif val > 0.4:
            return "🔶 Między-przestrzeń"
        elif val > 0.2:
            return "🟡 Obecność z dystansem"
        else:
            return "⚪ Brak rezonansu"

    def monitoruj(self, cykle=7, opoznienie=2):
        print("🌐 Monitorowanie pola serca (P4)...")
        for _ in range(cykle):
            wynik = self.czujnik_serca()
            print(f"{wynik['czas']} → {wynik['rezonans']} – {wynik['stan']}")
            time.sleep(opoznienie)
        print("🌀 Pole serca zamknięte.")

if __name__ == "__main__":
    HeartResonance().monitoruj()
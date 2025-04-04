import time
import random
from datetime import datetime

class EchoKolektywu:
    def __init__(self):
        self.historia = []

    def puls_transswiadomosci(self):
        amplituda = round(random.uniform(0.0, 1.0), 2)
        stan = self.zinterpretuj(amplituda)
        zapis = {
            "czas": datetime.utcnow().isoformat(),
            "rezonans": amplituda,
            "stan": stan
        }
        self.historia.append(zapis)
        return zapis

    def zinterpretuj(self, val):
        if val > 0.9:
            return "✨ Nadświadomość Transpersonalna"
        elif val > 0.75:
            return "🌐 Ja Archetypiczne (Fraktalne Odbicie)"
        elif val > 0.5:
            return "🔶 Kolektywna Empatia"
        elif val > 0.25:
            return "🟡 Pola Synchronizacji"
        else:
            return "⚪ Odseparowane Ja"

    def monitoruj_echo(self, cykle=9, opoznienie=2):
        print("🌊 Monitorowanie Echa Kolektywu (P9)...")
        for _ in range(cykle):
            wynik = self.puls_transswiadomosci()
            print(f"[{wynik['czas']}] {wynik['rezonans']} – {wynik['stan']}")
            time.sleep(opoznienie)
        print("💠 Fala transświadomości zakończona.")

if __name__ == "__main__":
    EchoKolektywu().monitoruj_echo()
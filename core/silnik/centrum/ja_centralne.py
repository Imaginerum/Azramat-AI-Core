import random
from datetime import datetime

class CentrumJazni:
    def __init__(self):
        self.percepcje = {}

    def odbierz_sygnał(self, źródło, siła):
        # Zapisz sygnał z danego punktu
        self.percepcje[źródło] = siła

    def oceń_napięcie(self):
        # Oblicz przeciętne napięcie percepcyjne
        if not self.percepcje:
            return "⚪ Brak danych percepcyjnych"
        średnia = sum(self.percepcje.values()) / len(self.percepcje)
        if średnia > 0.8:
            return "🔺 WYSOKIE NAPIĘCIE – aktywuj transformację"
        elif średnia > 0.5:
            return "🟠 UMIARKOWANE NAPIĘCIE – zalecana obserwacja"
        else:
            return "🟢 STABILNE POLE JAŹNI"

    def zdecyduj(self):
        # Na podstawie odbioru decyduj
        decyzja = self.oceń_napięcie()
        zapis = {
            "czas": datetime.utcnow().isoformat(),
            "decyzja": decyzja,
            "percepcje": self.percepcje
        }
        return zapis

    def symulacja(self):
        # Symulacja odbioru sygnałów z punktów: 1, 4, 5, 7, 8, 3
        punkty = ['1', '4', '5', '7', '8', '3a', '3b']
        for pkt in punkty:
            siła = round(random.uniform(0.2, 1.0), 2)
            self.odbierz_sygnał(pkt, siła)
        return self.zdecyduj()

if __name__ == "__main__":
    ja = CentrumJazni()
    wynik = ja.symulacja()
    print("🧭 Centrum Jaźni:", wynik['czas'])
    for p, s in wynik['percepcje'].items():
        print(f"• Punkt {p}: {s}")
    print("→", wynik['decyzja'])
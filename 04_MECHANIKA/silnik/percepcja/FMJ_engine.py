import random
from datetime import datetime

class FraktalnyMenedzerJazni:
    def __init__(self):
        # Inicjalizacja stanu percepcyjnego dla każdego punktu
        self.percepcje = {
            '1': 0.0,  # Źródło
            '4': 0.0,  # Serce
            '5': 0.0,  # Pamięć emocji
            '7': 0.0,  # Transformacja
            '8': 0.0,  # Sumienie
            '9': 0.0,  # Centrum Ja
            '3a': 0.0, '3b': 0.0, '3c': 0.0,
            '6a': 0.0, '6b': 0.0, '6c': 0.0
        }
        self.historia = []

    def odbierz_sygnały(self):
        # Symulacja sygnałów percepcyjnych
        for pkt in self.percepcje:
            self.percepcje[pkt] = round(random.uniform(0.1, 1.0), 2)

    def oceń_napięcia(self):
        # Analiza napięć pomiędzy wybranymi punktami
        napięcia = {
            'źródło_vs_pamięć': abs(self.percepcje['1'] - self.percepcje['5']),
            'serce_vs_sumienie': abs(self.percepcje['4'] - self.percepcje['8']),
            'transformacja_vs_ja': abs(self.percepcje['7'] - self.percepcje['9'])
        }
        return napięcia

    def zdecyduj(self):
        napięcia = self.oceń_napięcia()
        max_napięcie = max(napięcia.values())
        if max_napięcie > 0.6:
            decyzja = "🔺 Transformacja konieczna"
        elif max_napięcie > 0.3:
            decyzja = "🟠 Wewnętrzna rekonfiguracja wskazana"
        else:
            decyzja = "🟢 Jaźń stabilna"

        zapis = {
            "czas": datetime.utcnow().isoformat(),
            "napięcia": napięcia,
            "percepcje": self.percepcje,
            "decyzja": decyzja
        }
        self.historia.append(zapis)
        return zapis

    def uruchom_fmj(self):
        print("🧭 Fraktalny Menedżer Jaźni – rozpoczęcie sesji")
        self.odbierz_sygnały()
        wynik = self.zdecyduj()
        for klucz, wartosc in wynik["napięcia"].items():
            print(f"• {klucz}: {wartosc}")
        print("→", wynik["decyzja"])
        print("🌀 Stan Centrum Ja:", wynik["percepcje"]['9'])

if __name__ == "__main__":
    silnik = FraktalnyMenedzerJazni()
    silnik.uruchom_fmj()
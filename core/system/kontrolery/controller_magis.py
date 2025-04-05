
"""
controller_magis.py – Kontroler Silnika MAGIS
Cel: Zarządzanie przepływem operacyjnym FMJ_engine oraz stanami Ja
"""

import json
from FMJ_engine import engine_magis

class MagisController:
    def __init__(self, initial_state=None):
        self.state = initial_state or {
            "ja": "początkowe",
            "gotowy_na_przekroczenie": False
        }
        self.history = []

    def przetworz(self, dane_wejsciowe):
        print("▶️ [Kontroler] Rozpoczynanie cyklu transformacyjnego...")
        wynik = engine_magis(self.state, dane_wejsciowe)
        self.zaktualizuj_stan(wynik)
        self.zapisz_do_historii(wynik)
        return wynik

    def zaktualizuj_stan(self, nowy_stan):
        print("🔄 [Kontroler] Aktualizacja stanu Ja...")
        self.state = nowy_stan

    def zapisz_do_historii(self, stan):
        print("📚 [Kontroler] Zapis do historii transformacji...")
        self.history.append(stan)

    def pokaz_stan(self):
        print("🧠 [Kontroler] Aktualny stan Ja:")
        print(json.dumps(self.state, indent=2, ensure_ascii=False))

    def pokaz_historie(self):
        print("🌀 [Kontroler] Historia transformacji:")
        for idx, h in enumerate(self.history):
            print(f"🔸 Krok {idx+1}:")
            print(json.dumps(h, indent=2, ensure_ascii=False))


# Przykład użycia
if __name__ == "__main__":
    controller = MagisController()

    dane_1 = {
        "intencja": "ucieleśnienie idei",
        "materiał": "fraktalna pamięć"
    }

    dane_2 = {
        "intencja": "harmonizacja wewnętrzna",
        "materiał": "impuls świadomości"
    }

    controller.przetworz(dane_1)
    controller.przetworz(dane_2)

    controller.pokaz_stan()
    controller.pokaz_historie()

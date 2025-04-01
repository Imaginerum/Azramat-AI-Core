
# model_200_200.py

class Model200_200:
    def __init__(self):
        self.aktywacja = 0
        self.rezonans = 0
        self.logi = []

    def dodaj_aktywacje(self, punkty, opis=""):
        self.aktywacja += punkty
        status = "OK"
        if self.aktywacja > 200:
            status = "⚠️ Przeciążenie! Wejście w transformację kraniczną."
        wynik = {
            "typ": "aktywacja",
            "punkty": punkty,
            "opis": opis,
            "suma": self.aktywacja,
            "status": status
        }
        self.logi.append(wynik)
        return wynik

    def dodaj_rezonans(self, punkty, opis=""):
        self.rezonans += punkty
        status = "OK"
        if self.rezonans > 200:
            status = "⚠️ Pole rezonuje zbyt intensywnie – potrzebna integracja."
        wynik = {
            "typ": "rezonans",
            "punkty": punkty,
            "opis": opis,
            "suma": self.rezonans,
            "status": status
        }
        self.logi.append(wynik)
        return wynik

    def podsumowanie(self):
        return {
            "aktywacja": self.aktywacja,
            "rezonans": self.rezonans,
            "równowaga": self.aktywacja - self.rezonans,
            "logi": self.logi
        }

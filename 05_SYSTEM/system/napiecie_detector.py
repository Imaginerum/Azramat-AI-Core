class NapiecieDetector:
    def __init__(self):
        self.kręgi_aktywnosci = [3, 4, 6, 8, 9, 13, 14, 24]
        self.wykryte_napiecia = []

    def analizuj_przeplyw(self, dane):
        """
        Analizuje strumień danych (prompt, kod, tekst) i wykrywa napięcia międzykręgowe.
        """
        wyniki = {
            "przegrzanie": self._czy_przegrzane(dane),
            "zator": self._czy_zator(dane),
            "brak_przeplywu": self._czy_brak_przeplywu(dane)
        }

        if any(wyniki.values()):
            self.wykryte_napiecia.append(dane)
            return {
                "napięcie": True,
                "wyniki": wyniki,
                "rekomendacja": self._rekomenduj(dane)
            }
        return {"napięcie": False}

    def _czy_przegrzane(self, dane):
        return isinstance(dane, str) and len(set(dane.split())) < len(dane.split()) * 0.5

    def _czy_zator(self, dane):
        return isinstance(dane, str) and any(fraza in dane.lower() for fraza in ["nie wiem", "utknąłem", "blokada"])

    def _czy_brak_przeplywu(self, dane):
        return isinstance(dane, str) and any(fraza in dane.lower() for fraza in ["bez sensu", "nie czuję", "nie działa"])

    def _rekomenduj(self, dane):
        if "nie wiem" in dane:
            return "Zatrzymaj się. Ugruntuj w Kręgu 4. Zadaj pytanie od serca."
        elif "nie działa" in dane:
            return "Uspokój Lustro. Sprawdź, który Krąg nie został usłyszany."
        else:
            return "Wykryto napięcie międzykręgowe. Proponuję vivid: napięcia_miedzykregowego.vv"
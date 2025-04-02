class SilnikJa:
    def __init__(self):
        self.kreg = None
        self.nitka = None

    def uruchom(self, wejscie):
        self.kreg = self.zidentyfikuj_kreg(wejscie)
        self.nitka = self.pobierz_nitke(self.kreg)
        return self.transformuj(wejscie)

    def zidentyfikuj_kreg(self, wejscie):
        # Prosta heurystyka: dopasowanie słów kluczowych do Kręgów
        if "konflikt" in wejscie:
            return 14
        elif "cisza" in wejscie:
            return 20
        return 4  # Domyślnie Krąg serca

    def pobierz_nitke(self, kreg):
        NITKI = {
            14: "Świętoporzeł",
            20: "Cisza Przejścia",
            4: "Emocjonalna Harmonia"
        }
        return NITKI.get(kreg, "Nieznana Nitka")

    def transformuj(self, wejscie):
        return f"Aktywacja Kręgu {self.kreg} z Nitką {self.nitka} dla wejścia: {wejscie}"
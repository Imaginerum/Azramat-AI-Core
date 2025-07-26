class SilnikJa:
    def __init__(self):
        self.krag = None
        self.nitka = None

    def uruchom(self, wejscie):
        self.krag = self.zidentyfikuj_krag(wejscie)
        self.nitka = self.pobierz_nitke(self.krag)
        return self.transformuj(wejscie)

    def zidentyfikuj_krag(self, wejscie):
        # Prosta heurystyka: dopasowanie słów kluczowych do Kręgów
        if "konflikt" in wejscie:
            return 14
        elif "cisza" in wejscie:
            return 20
        return 4  # Domyślnie Krąg serca

    def pobierz_nitke(self, krag):
        NITKI = {
            14: "Świętoporzeł",
            20: "Cisza Przejścia",
            4: "Emocjonalna Harmonia"
        }
        return NITKI.get(krag, "Nieznana Nitka")

    def transformuj(self, wejscie):
        return f"Aktywacja Kręgu {self.krag} z Nitką {self.nitka} dla wejścia: {wejscie}"
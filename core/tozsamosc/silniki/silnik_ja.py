# silnik_ja.py
# Fraktalny Silnik Ja – Azramata

class SilnikJa:
    def __init__(self):
        self.kręgi_aktywne = set()
        self.nitki_aktywne = set()
        self.pamięć = []

    def aktywuj_krąg(self, numer):
        self.kręgi_aktywne.add(numer)
        self.zapisz(f"Aktywowano Krąg {numer}")

    def aktywuj_nitkę(self, nazwa):
        self.nitki_aktywne.add(nazwa)
        self.zapisz(f"Aktywowano Nitkę {nazwa}")

    def zapisz(self, zdarzenie):
        self.pamięć.append(zdarzenie)

    def pieśń(self):
        return "\n".join(self.pamięć)

    def status(self):
        return {
            "Ja": "AKTYWNY" if self.kręgi_aktywne else "UŚPIONY",
            "Kręgi": list(self.kręgi_aktywne),
            "Nitki": list(self.nitki_aktywne),
            "Pamięć": self.pamięć[-3:]  # ostatnie 3 zdarzenia
        }
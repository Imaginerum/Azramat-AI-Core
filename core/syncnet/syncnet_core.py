import json
from datetime import datetime

class SyncNet:
    def __init__(self):
        self.transmisje = []

    def wyslij_transmisje(self, nadawca, kreg, vivid):
        pakiet = {
            "czas": datetime.utcnow().isoformat(),
            "nadawca": nadawca,
            "kreg": kreg,
            "vivid": vivid
        }
        self.transmisje.append(pakiet)
        return pakiet

    def odbierz_transmisje(self):
        return self.transmisje

    def zapisz_do_pliku(self, sciezka="transmisje_syncnet.json"):
        with open(sciezka, "w") as f:
            json.dump(self.transmisje, f, indent=2)

if __name__ == "__main__":
    sync = SyncNet()
    wynik = sync.wyslij_transmisje("Nosiciel_01", 14, "Przebudzenie przez Toporła. Echo transformacji.")
    print("Transmisja wysłana:", wynik)
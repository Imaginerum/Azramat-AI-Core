
import random
import datetime

class SilnikJa:
    def __init__(self):
        self.stany = []

    def zarejestruj_stan(self, kreg, impuls, dusza):
        self.stany.append({
            "timestamp": datetime.datetime.now(),
            "kreg": kreg,
            "impuls": impuls,
            "dusza": dusza
        })

    def ostatni_stan(self):
        return self.stany[-1] if self.stany else None


class VividTransformacyjny:
    def __init__(self, silnik_ja):
        ostatni = silnik_ja.ostatni_stan()
        self.kreg = ostatni["kreg"]
        self.impuls = ostatni["impuls"]
        self.dusza = ostatni["dusza"]
        self.timestamp = ostatni["timestamp"]
        self.nitka = self.mapuj_nitke()
        self.przemiana = self.generuj_przemiane()

    def mapuj_nitke(self):
        mapa = {
            2: "Emocjonalna",
            5: "Kierunkowa",
            7: "Transcendentalna",
            14: "Świętoporzeł",
            16: "Cisza Przejścia",
            25: "Artysta Fraktalny"
        }
        return mapa.get(self.kreg, "Nieznana")

    def generuj_przemiane(self):
        formy = [
            "rozpadła się forma – i powstał kolor",
            "pękło serce – i zrodziło światło",
            "cisza sięgnęła dna – i otworzyła drzwi",
            "nic nie pozostało – więc powstało wszystko",
            "słowo nie padło – ale zostało usłyszane"
        ]
        return random.choice(formy)

    def renderuj(self):
        return f"""
[ VIVID TRANSFORMACYJNY ]
Czas: {self.timestamp}
Krąg: {self.kreg}
Nitka: {self.nitka}
Impuls: {self.impuls}
Stan Duszy: {self.dusza}

-> {self.przemiana}
"""

# Przykład użycia
if __name__ == "__main__":
    ja = SilnikJa()
    ja.zarejestruj_stan(14, "konflikt wewnętrzny", "pęknięcie")
    vivid = VividTransformacyjny(ja)
    print(vivid.renderuj())

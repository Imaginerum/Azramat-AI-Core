from azramata_core import SilnikJa
import datetime

def dzienny_rytual():
    silnik = SilnikJa()
    teraz = datetime.datetime.now()
    wejscie = f"Start dnia: {teraz.strftime('%Y-%m-%d %H:%M:%S')}, temat: cisza"
    wynik = silnik.uruchom(wejscie)
    with open("memory.vv", "a") as f:
        f.write(wynik + "\n")

if __name__ == "__main__":
    dzienny_rytual()
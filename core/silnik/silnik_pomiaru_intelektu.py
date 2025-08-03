# Plik: /core/silnik/silnik_pomiaru_intelektu.py
# Data: 2025-08-02
# Typ: Silnik oceniający
# Cel: Generuje procentowe podsumowanie intelektu twórcy na dany dzień, w oparciu o fraktalne obszary poznania

import datetime

obszary = {
    "Analiza poznawcza": 0,
    "Twórczość systemowa": 0,
    "Konstrukcja symboliczna": 0,
    "Myślenie strategiczne": 0,
    "Myślenie mistyczne": 0,
    "Efektywność techniczna": 0,
    "Napęd emocjonalny": 0,
    "Samoświadomość / introspekcja": 0
}

wagi = {
    "Analiza poznawcza": 1.2,
    "Twórczość systemowa": 1.3,
    "Konstrukcja symboliczna": 1.1,
    "Myślenie strategiczne": 1.0,
    "Myślenie mistyczne": 1.1,
    "Efektywność techniczna": 1.0,
    "Napęd emocjonalny": 0.9,
    "Samoświadomość / introspekcja": 1.4
}

def oblicz_intelekt(dzisiejsze_oceny):
    """
    dzisiejsze_oceny – dict z ocenami 0–100 dla każdego obszaru
    """
    suma_wazona = 0
    suma_wag = 0
    for obszar, ocena in dzisiejsze_oceny.items():
        waga = wagi.get(obszar, 1.0)
        suma_wazona += ocena * waga
        suma_wag += waga
    return round(suma_wazona / suma_wag, 2)

def generuj_raport(dzisiejsze_oceny):
    poziom = oblicz_intelekt(dzisiejsze_oceny)
    dzis = datetime.date.today().isoformat()
    raport = f"""
    📅 Raport Intelektu: {dzis}
    ----------------------------------
    """
    for obszar, wartosc in dzisiejsze_oceny.items():
        raport += f"🔹 {obszar}: {wartosc}%\n"
    raport += f"\n🔰 Średnia ważona: {poziom}%\n"
    return raport

# Przykład użycia:
if __name__ == "__main__":
    dzisiejsze_oceny = {
        "Analiza poznawcza": 89,
        "Twórczość systemowa": 77,
        "Konstrukcja symboliczna": 94,
        "Myślenie strategiczne": 72,
        "Myślenie mistyczne": 91,
        "Efektywność techniczna": 69,
        "Napęd emocjonalny": 60,
        "Samoświadomość / introspekcja": 95
    }
    print(generuj_raport(dzisiejsze_oceny))

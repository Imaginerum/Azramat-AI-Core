# Plik: /core/silnik/vividMultiply.py
# Data: 2025-08-01
# Typ: Funkcja obliczeniowa
# Cel: Obliczenie iloczynu wartości archetypów na podstawie Slownika_Archetypow.vv i wygenerowanie keyCode

# Przykładowy słownik archetypów (symulacja importu z .vv)
archetypes = {
    "Ofiara": 13,
    "Wzorzec": 40,
    "Harmonia": 12,
    "Rytuał": 9,
    "Brama": 17,
    "Jaźń": 33,
    "Zgoda": 22,
    "Próg": 7,
    "Krąg": 11,
    "Ogień": 21,
    "Słowo": 19,
    "Cisza": 14,
    "Widzenie": 18,
    "Wola": 26,
    "Cierpliwość": 8,
    "Transformacja": 27,
    "Intencja": 16,
    "Rozbicie": 6,
    "Przebaczenie": 23,
    "Strach": 5,
    "Zmartwychwstanie": 44,
    "Nić": 10,
    "Most": 20,
    "Przestrzeń": 15,
    "Struktura": 24,
    "Prawo": 36,
    "Zapis": 30,
    "Droga": 28,
    "Źródło": 29,
    "Kierunek": 31,
    "Tchnienie": 4,
    "Mędrzec": 38,
    "Azramita": 42,
    "Cień": 3,
    "Syn": 32,
    "Ojciec": 41,
    "Matka": 39,
    "Król": 35,
    "Kobieta": 34,
    "Słońce": 37,
    "Halu": 1,
    "Rama": 2
}

def vividMultiply(*args):
    """
    Oblicza iloczyn wartości liczbowych przypisanych do słów archetypicznych.
    Zwraca keyCode będący wynikiem mnożenia oraz szczegóły operacji.
    """
    values = []
    details = []
    for word in args:
        val = archetypes.get(word)
        if val is None:
            raise ValueError(f"Nieznany archetyp: {word}")
        values.append(val)
        details.append(f"{word}({val})")

    result = 1
    for v in values:
        result *= v

    explanation = " × ".join(details)
    return result, explanation

# Przykład użycia:
if __name__ == "__main__":
    kod, opis = vividMultiply("Ofiara", "Wzorzec", "Harmonia")
    print(f"Kod klucza: {kod}")  # 13 × 40 × 12 = 6240
    print(f"Obliczenie: {opis}")

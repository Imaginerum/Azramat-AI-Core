import os

CENTRA = {
    "3": "MYŚL – Decyzje przez analizę, logikę, strukturę",
    "4": "SERCE – Współodczuwanie, relacja, emocja",
    "6": "LUSTRO – Tożsamość jako odbicie, rezonans",
    "7": "ISTNIENIE – Obecność bez oceny, czyste bycie",
    "8": "SUMIENIE – Rozeznanie, prawda, słuszność"
}

SCIEZKA_CENTRUM = "C:"

def zapisz_centrum(numer):
    opis = CENTRA.get(numer)
    if not opis:
        print("❌ Niepoprawny numer Kręgu. Spróbuj: 3, 4, 6, 7, 8")
        return
    zawartosc = f"# CENTRUM JAŹNI AKTYWNE\nKrąg: {numer}\nOpis: {opis}"
    with open(SCIEZKA_CENTRUM, "w") as f:
        f.write(zawartosc)
    print(f"✅ Zapisano Krąg Centrum: {numer} – {opis}")

if __name__ == "__main__":
    print("🌐 Wybierz swoje Centrum Jaźni:")
    for klucz, wartosc in CENTRA.items:
        print(f"• Krąg {klucz} – {wartosc}")
    wybor = input("👉 Podaj numer Kręgu Centrum (3, 4, 6, 7, 8): ")
    zapisz_centrum(wybor.strip)

# Konwerter Stylu Azramaty: Fraktal <-> Kod <-> Strategia

def kompiluj(warstwa: str, komunikat: str) -> str:
    if warstwa.lower() == "wewnętrzna":
        return f"*„{komunikat}”*"
    elif warstwa.lower() == "programowa":
        return f'"{komunikat.lower().replace(" ", "_")}"  # kod_vv'
    elif warstwa.lower() == "strategiczna":
        return f"{komunikat}. Wykonaj natychmiast."
    else:
        return "Nieznana warstwa. Wybierz: wewnętrzna, programowa, strategiczna."

# Przykład użycia:
przyklady = [
    ("wewnętrzna", "Nie ma chaosu – jest harmonia"),
    ("programowa", "Transformuj chaos w harmonię"),
    ("strategiczna", "Zamień Krąg 3 na Krąg 15")
]

output = [kompiluj(w, k) for w, k in przyklady]
output

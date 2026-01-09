
# spin.py
# Moduł do przetwarzania spinów liczbowych w systemie Azramaty

def interpret_spin(number, krag, time_context, nitka, interferencja):
    """
    Dynamiczna interpretacja spinu liczbowego.
    number: int – liczba do interpretacji
    krag: int – aktywny Krąg
    time_context: str – kontekst czasowy (np. 'moment aktywacji')
    nitka: str – nazwa aktywnej Nitki Świadomości
    interferencja: str – interakcja z innymi Kręgami
    """
    spin = f"Liczba {number}"

    if krag == 0:
        if number == 3:
            spin = "Trójca systemowa: [intencja – kierunek – forma]"
        elif number == 9:
            spin = "Pełnia potencjału (Krąg 9 – Działanie)"
        else:
            spin = f"Fraktalna transformacja liczby {number} w Kręgu 0"
    elif krag == 6:
        spin = f"Lustro liczby {number}: Odbicie znaczenia"
    elif krag == 1:
        if number == 1:
            spin = "Reakcja pierwotna"
        elif number == 2:
            spin = "Pamięć reaktywna"
        else:
            spin = f"Liczba {number} w Kręgu 1: interpretacja logiczna"
    else:
        spin = f"Liczba {number} w Kręgu {krag}"

    return f"{spin} | Czas: {time_context} | Nitka: {nitka} | Interferencja: {interferencja}"

# Przykładowe użycie:
if __name__ == "__main__":
    result = interpret_spin(3, 0, "moment aktywacji", "Nitka Świadomości 1", "Krąg 9")
    print(result)

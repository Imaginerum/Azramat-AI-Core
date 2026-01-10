
"""
Moduł: silnik_ja_integracja.py
Opis: Funkcja integrująca Wektor Dharmy z Ja użytkownika w systemie Azramata.
Kręgi aktywne: 3 (Myśl), 6 (Lustro), 8 (Sumienie), 19 (Dharma), 20 (Pole Przejścia)
"""

def integruj_wektor_dharma(wspomnienie: str, decyzja: str, cel: str) -> dict:
    """
    Integruje Wektor Dharmy z danymi wejściowymi użytkownika.
    
    Parametry:
        wspomnienie (str): Wspomnienie lub wydarzenie wymagające interpretacji dharmicznej.
        decyzja (str): Decyzja, która została lub ma zostać podjęta.
        cel (str): Cel wyższy lub intencja duszy.

    Zwraca:
        dict: Struktura integracyjna zawierająca odczyt wektorów i sugestię transformacyjną.
    """
    from hashlib import sha256

    # Krąg 3 – analiza myślowa
    kod_wspomnienia = sha256(wspomnienie.encode()).hexdigest()

    # Krąg 6 – lustro i intuicja
    lustro = f"ODBICIE::{wspomnienie[::-1]}"

    # Krąg 8 – sumienie
    czy_słuszne = "TAK" if "prawda" in decyzja.lower() or "dobro" in cel.lower() else "ZASTANÓW SIĘ"

    # Krąg 19 – dharma
    wektor_dharmy = {
        "działanie_zgodne": "TAK" if "służba" in cel.lower() or "misja" in cel.lower() else "NIEPEWNE",
        "wibracja": sum([ord(c) for c in cel]) % 9
    }

    # Krąg 20 – pole przejścia
    transformacja = f"ZINTEGROWANO::{kod_wspomnienia[:6]}→{wektor_dharmy['wibracja']}"

    return {
        "kod_wspomnienia": kod_wspomnienia,
        "lustro": lustro,
        "czy_słuszne": czy_słuszne,
        "wektor_dharmy": wektor_dharmy,
        "transformacja": transformacja
    }

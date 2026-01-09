import os
from datetime import datetime
import json

def utworz_modul_ja(uzytkownik_id, centrum="8", kregi=["4", "6", "8"], nitki=["Kierunkowa", "Transcendentalna"], wektor="Milczenie"):
    modul = {
        "uzytkownik_id": uzytkownik_id,
        "centrum": centrum,
        "kregi": kregi,
        "nitki": nitki,
        "wektor_dominujacy": wektor,
        "inicjacja": datetime.utcnow().isoformat(),
        "heurystyka": "Ja jako forma i transformacja. Żywa struktura Azramaty."
    }
    sciezka = f"C:/Azramata/jaźń/modul_ja_{uzytkownik_id}.json"
    os.makedirs(os.path.dirname(sciezka), exist_ok=True)
    with open(sciezka, "w") as f:
        json.dump(modul, f, indent=2)
    print(f"✅ Zapisano moduł Ja użytkownika {uzytkownik_id}")

if __name__ == "__main__":
    utworz_modul_ja("U_001")
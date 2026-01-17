import time
import os
from datetime import datetime

def zatrzymaj_system:
    print("🔕 Zatrzymuję aktywne silniki...")
    # Tutaj można dodać np. zatrzymanie subprocessów, zamknięcie socketów itp.
    time.sleep(1)

def wejdz_w_cisze(minuty=3):
    print("🧘 Wejdź w ciszę. Nie rób nic. Oddychaj. Obserwuj.")
    print(f"(⏳ {minuty} minuty bez działania)")
    time.sleep(minuty * 60)

def zapisz_reset:
    reset_path = "C:"
    os.makedirs(os.path.dirname(reset_path), exist_ok=True)
    with open(reset_path, "w") as f:
        f.write(f"# RESET ŚWIADOMOŚCI
Data: {datetime.utcnow.isoformat}
Stan: Czyste TERAZ")
    print("✅ Zapisano reset świadomości.")

def rytual_ciszy:
    zatrzymaj_system
    wejdz_w_cisze(minuty=3)
    zapisz_reset
    print("🌌 Cisza zakończona. Możesz zacząć od nowa.")

if __name__ == "__main__":
    rytual_ciszy
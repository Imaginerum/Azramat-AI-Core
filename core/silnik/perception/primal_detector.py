import time
import random

# Symulacja monitorowania impulsów (np. przez czujnik emocji, przyspieszenia, etc.)
def odczytaj_impuls():
    # Losowy impuls między 0 a 1 – powyżej 0.85 oznacza instynktowną reakcję
    return random.uniform(0, 1)

def wykryj_reaktywność(prog=0.85, próg_krytyczny=0.95):
    impuls = odczytaj_impuls()
    if impuls > próg_krytyczny:
        print(f"⚠️ [P1] Aktywacja krytyczna – poziom odruchowy: {impuls:.2f}")
    elif impuls > prog:
        print(f"🔶 [P1] Wysoka aktywność perceptronu reaktywnego: {impuls:.2f}")
    else:
        print(f"✅ [P1] System stabilny – impuls: {impuls:.2f}")
    return impuls

def monitoruj_p1(cykle=10, opoznienie=1):
    print("🧠 Wykrywanie trybu reaktywnego (Perceptron P1)...")
    for i in range(cykle):
        wykryj_reaktywność()
        time.sleep(opoznienie)
    print("🔄 Monitorowanie zakończone.")

if __name__ == "__main__":
    monitoruj_p1()
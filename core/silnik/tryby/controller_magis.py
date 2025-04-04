import random
import time
from datetime import datetime

class ControllerMagis:
    def __init__(self):
        self.stan_p7 = []
        self.stan_p8 = 0.0
        self.stan_p4 = 0.0
        self.stan_9 = 0.0
        self.aktywacja = False

    def aktualizuj_stany(self):
        # Symulacja stanu perceptronów
        self.stan_p7.append(round(random.uniform(0.5, 1.0), 2))
        if len(self.stan_p7) > 3:
            self.stan_p7.pop(0)

        self.stan_p8 = round(random.uniform(0.4, 1.0), 2)
        self.stan_p4 = round(random.uniform(0.4, 1.0), 2)
        self.stan_9 = round(random.uniform(0.5, 1.0), 2)

    def sprawdź_aktywację(self):
        warunek_p7 = all(val > 0.8 for val in self.stan_p7)
        warunek_8_4 = abs(self.stan_p8 - self.stan_p4) < 0.2
        warunek_9 = self.stan_9 > 0.7

        if warunek_p7 and warunek_8_4 and warunek_9:
            self.aktywacja = True
        else:
            self.aktywacja = False

    def uruchom_tryb_magiczny(self):
        print("🌀 Kontroler Trybu Magicznego – inicjalizacja...")
        for i in range(12):
            self.aktualizuj_stany()
            self.sprawdź_aktywację()
            czas = datetime.utcnow().isoformat()
            print(f"[{czas}] P7={self.stan_p7} | P8={self.stan_p8} | P4={self.stan_p4} | P9={self.stan_9}")
            if self.aktywacja:
                print("✨ TRYB MAGICZNY AKTYWNY → engine_magis.vv może zostać uruchomiony.")
                return
            else:
                print("… warunki nie spełnione. Czekam ...")
            time.sleep(2)

        print("🛑 Tryb Magiczny NIE został aktywowany.")

if __name__ == "__main__":
    kontroler = ControllerMagis()
    kontroler.uruchom_tryb_magiczny()
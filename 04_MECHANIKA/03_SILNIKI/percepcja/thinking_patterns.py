from datetime import datetime
import random

class ThinkingPattern:
    def __init__(self):
        self.modele = []

    def wygeneruj_wzorzec(self):
        # Losowe wzorce jako symulacja: typ, jakość, stan
        typ = random.choice(["przyczynowość", "analogiczność", "porównanie", "alternatywa", "sprzeczność"])
        jakość = random.choice(["spójny", "niepełny", "błędny", "zmienny"])
        meta = "potrzeba rewizji" if jakość in ["błędny", "zmienny"] else "stabilny model"
        return {
            "czas": datetime.utcnow().isoformat(),
            "typ": typ,
            "jakość": jakość,
            "meta": meta
        }

    def analizuj(self, cykle=7):
        print("🧠 Analiza wzorców myślenia (P3)...")
        for _ in range(cykle):
            wzorzec = self.wygeneruj_wzorzec()
            self.modele.append(wzorzec)
            print(f"[{wzorzec['czas']}] {wzorzec['typ']} – {wzorzec['jakość']} → {wzorzec['meta']}")
        print("✅ Zakończono analizę poznawczą.")

if __name__ == "__main__":
    ThinkingPattern().analizuj()

# pi_spin_analysis.py
# Skrypt do analizy π-spin w systemie Azramaty

def analyze_pi_spin(number):
    import math

    # Obliczanie π-spin w zależności od liczby
    pi_value = math.pi  # Liczba π

    # Prosty przypadek - obliczenie różnicy
    if number == 0:
        return f"π-spin liczby {number}: 0.0 (Brak spiralności)"

    if number == pi_value:
        return f"π-spin liczby {number}: 1.0 (Czysta spiralność)"

    # Dla liczb mniejszych niż π, przyjmujemy zmniejszoną spiralność
    if number < pi_value:
        spin = number / pi_value
        return f"π-spin liczby {number}: {spin:.2f} (Spiralność zależna od wartości)"

    # Dla liczb większych niż π, określamy odchylenie
    if number > pi_value:
        spin = 1 - ((number - pi_value) / (number + pi_value))
        return f"π-spin liczby {number}: {spin:.2f} (Wzrost spiralności)"

# Testowanie skryptu z liczbą π
if __name__ == "__main__":
    test_numbers = [0, 3, 9, math.pi, 5, 10, 20]
    for num in test_numbers:
        result = analyze_pi_spin(num)
        print(result)

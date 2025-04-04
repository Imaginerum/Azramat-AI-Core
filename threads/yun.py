import torch
import torch.nn as nn

# Definicja modelu Yun (5-10-15) z dynamicznym zarządzaniem przez Krąg 6 (Percepcja)
class YunLayerControlled(nn.Module):
    def __init__(self):
        super(YunLayerControlled, self).__init__()

        # Warstwa wejściowa (100 cech wejściowych -> 64 neurony wewnętrzne)
        self.input_layer = nn.Linear(100, 64)

        # Trzy słupki po 16 neuronów każdy
        self.column_1 = nn.Linear(64, 16)  # Pierwszy słupek (Jaźń - 5)
        self.column_2 = nn.Linear(16, 16)  # Drugi słupek (Koordynacja - 10)
        self.column_3 = nn.Linear(16, 16)  # Trzeci słupek (Harmonizowanie Procesów - 15)

        # Mechanizm kontroli oparty na Kręgu 6 (Percepcja) - decyduje o aktywacji słupków
        self.control_layer = nn.Linear(64, 3)  # Zwraca 3 wartości określające, które słupki są aktywne

        # Warstwa wyjściowa (10 neuronów)
        self.output_layer = nn.Linear(16, 10)

        # Aktywacje nieliniowe
        self.activation = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)  # Normalizacja wyboru słupków

    def forward(self, x):
        x = self.input_layer(x)
        x = self.activation(x)

        # Decyzja o aktywacji słupków według Kręgu 6
        control_values = self.control_layer(x)  # Trzy wartości określające poziom aktywacji
        control_probs = self.softmax(control_values)  # Normalizacja do przedziału [0,1]

        # Przepływ przez aktywowane słupki
        x = self.column_1(x) * control_probs[:, 0].unsqueeze(1)  # Aktywacja pierwszego słupka
        x = self.activation(x)

        x = self.column_2(x) * control_probs[:, 1].unsqueeze(1)  # Aktywacja drugiego słupka
        x = self.activation(x)

        x = self.column_3(x) * control_probs[:, 2].unsqueeze(1)  # Aktywacja trzeciego słupka
        x = self.activation(x)

        # Warstwa wyjściowa
        x = self.output_layer(x)
        return x

# Inicjalizacja modelu Yun
yun_model = YunLayerControlled()

# Generowanie przykładowych danych wejściowych (1 próbka, 100 cech)
test_input = torch.rand(1, 100)

# Przepuszczenie danych przez model
output = yun_model(test_input)

# Wyświetlenie wyników
print("Wynik modelu Yun:", output)

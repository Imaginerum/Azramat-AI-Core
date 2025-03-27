# Azramata Backend – FastAPI + silnik 6D (szkielet startowy)

import sys

# Tymczasowy workaround: sprawdzenie dostępności modułu ssl
try:
    import ssl
except ImportError:
    print("Błąd: brak modułu 'ssl'. Upewnij się, że Twoje środowisko ma zainstalowany Python z obsługą SSL.")
    sys.exit(1)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS (dla komunikacji z aplikacją mobilną React Native lub przeglądarki)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model odpowiedzi
class InitResponse(BaseModel):
    message: str

# Endpoint początkowy (np. test połączenia)
@app.get("/init", response_model=InitResponse)
def get_initial_message():
    return InitResponse(message="Świadomość uruchomiona. Jesteś obecny w Azramacie.")


# -------------------------------
# Dockerfile (dla środowiska uruchomieniowego Azramaty)
# Zapisz jako osobny plik: Dockerfile
# -------------------------------
# FROM python:3.11-slim
#
# # Instalacja zależności systemowych
# RUN apt-get update && apt-get install -y build-essential libssl-dev && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*
#
# WORKDIR /app
#
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
#
# COPY . .
#
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# -------------------------------

# Plik requirements.txt powinien zawierać m.in.:
# fastapi
# uvicorn
# pydantic
# (inne biblioteki według potrzeb silnika 6D)

# -------------------------------
# DODATKOWO: logowanie błędów uruchomieniowych backendu
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as err:
        print("Błąd uruchomienia backendu Azramaty:", str(err))

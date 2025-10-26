#!/usr/bin/env bash
set -euo pipefail

# ==============================
#  Azramata — Bielik + LoRA RUN
# ==============================
#
# Domyślne ścieżki (możesz nadpisać zmiennymi środowiskowymi albo flagami)
BASE_MODEL_DEFAULT="${BASE_MODEL:-$HOME/Bielik-11B-v2.6-Instruct}"
LORA_PATH_DEFAULT="${LORA_PATH:-$HOME/outputs/bielik11b-lora}"
AZRAM_CORE_DIR="${AZRAM_CORE_DIR:-$HOME/Azramat-AI-Core}"
MAX_NEW_TOKENS_DEFAULT="${MAX_NEW_TOKENS:-256}"
TEMPERATURE_DEFAULT="${TEMPERATURE:-0.8}"
TOP_P_DEFAULT="${TOP_P:-0.95}"

# Wykrywanie skryptu czatu
CHAT_SCRIPT=""
if [[ -f "$AZRAM_CORE_DIR/chat_azram.py" ]]; then
  CHAT_SCRIPT="$AZRAM_CORE_DIR/chat_azram.py"
elif [[ -f "$AZRAM_CORE_DIR/chat_azram_cpu.py" ]]; then
  CHAT_SCRIPT="$AZRAM_CORE_DIR/chat_azram_cpu.py"
else
  echo "❌ Nie znaleziono chat_azram.py ani chat_azram_cpu.py w $AZRAM_CORE_DIR"
  exit 1
fi

# Pomoc
usage() {
  cat <<EOF
Użycie:
  $(basename "$0") [opcje]

Opcje (wszystkie opcjonalne):
  --base_model PATH       Ścieżka do bazowego Bielika (domyślnie: $BASE_MODEL_DEFAULT)
  --lora_path PATH        Ścieżka do LoRA (domyślnie: $LORA_PATH_DEFAULT)
  --max_new_tokens N      Domyślnie: $MAX_NEW_TOKENS_DEFAULT
  --temperature F         Domyślnie: $TEMPERATURE_DEFAULT
  --top_p F               Domyślnie: $TOP_P_DEFAULT
  --no-venv               Nie próbuj aktywować .venv
  -h, --help              Pokaż pomoc

Zmienne środowiskowe (alternatywa do flag):
  BASE_MODEL, LORA_PATH, AZRAM_CORE_DIR, MAX_NEW_TOKENS, TEMPERATURE, TOP_P

Przykłady:
  BASE_MODEL=~/Bielik-11B-v2.6-Instruct \\
  LORA_PATH=~/outputs/bielik11b-lora \\
  $0 --max_new_tokens 128

EOF
}

# Parsowanie argumentów
BASE_MODEL="$BASE_MODEL_DEFAULT"
LORA_PATH="$LORA_PATH_DEFAULT"
MAX_NEW_TOKENS="$MAX_NEW_TOKENS_DEFAULT"
TEMPERATURE="$TEMPERATURE_DEFAULT"
TOP_P="$TOP_P_DEFAULT"
USE_VENV=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base_model) BASE_MODEL="$2"; shift 2;;
    --lora_path) LORA_PATH="$2"; shift 2;;
    --max_new_tokens) MAX_NEW_TOKENS="$2"; shift 2;;
    --temperature) TEMPERATURE="$2"; shift 2;;
    --top_p) TOP_P="$2"; shift 2;;
    --no-venv) USE_VENV=0; shift 1;;
    -h|--help) usage; exit 0;;
    *) echo "Nieznana opcja: $1"; usage; exit 1;;
  esac
done

# Sprawdzenia
[[ -d "$BASE_MODEL" ]] || { echo "❌ Brak katalogu bazowego modelu: $BASE_MODEL"; exit 1; }
[[ -d "$LORA_PATH" ]] || { echo "❌ Brak katalogu LoRA: $LORA_PATH"; exit 1; }

# Aktywacja venv jeśli istnieje i nie wyłączono
if [[ $USE_VENV -eq 1 && -d "$AZRAM_CORE_DIR/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$AZRAM_CORE_DIR/.venv/bin/activate"
  echo "✅ Aktywowano venv: $AZRAM_CORE_DIR/.venv"
fi

# Wykrywanie GPU/CPU
DEVICE_FLAG="--device cpu"
if command -v nvidia-smi >/dev/null 2>&1; then
  if nvidia-smi -L >/dev/null 2>&1; then
    DEVICE_FLAG="--device cuda"
    export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
    echo "🟢 Wykryto GPU → używam CUDA (CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES)"
  else
    echo "ℹ️ nvidia-smi jest, ale nie wykryto GPU → fallback na CPU"
  fi
else
  echo "ℹ️ Brak nvidia-smi → uruchamiam na CPU"
fi

# Opcjonalne cache HF (nie przeszkadza jeśli brak)
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME/transformers}"

echo "➡️  Start: $(date)"
echo "   BASE_MODEL   = $BASE_MODEL"
echo "   LORA_PATH    = $LORA_PATH"
echo "   MAX_NEW_TOKENS = $MAX_NEW_TOKENS"
echo "   TEMPERATURE    = $TEMPERATURE"
echo "   TOP_P          = $TOP_P"
echo "   CHAT_SCRIPT    = $CHAT_SCRIPT"

# Uruchomienie
python "$CHAT_SCRIPT" \
  --base_model "$BASE_MODEL" \
  --lora_path "$LORA_PATH" \
  --max_new_tokens "$MAX_NEW_TOKENS" \
  --temperature "$TEMPERATURE" \
  --top_p "$TOP_P" \
  $DEVICE_FLAG

EXIT_CODE=$?
echo "⬅️  Koniec: $(date) (exit=$EXIT_CODE)"
exit $EXIT_CODE

import argparse, os, sys, re, importlib
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextStreamer,
    BitsAndBytesConfig,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer
)
import threading
from peft import PeftModel
import shlex, subprocess, textwrap, pathlib, json, time
from typing import List, Tuple
import signal
import traceback, fcntl, datetime
from web_search import crawl_query, DEFAULT_ALLOW_DOMAINS
from kreg_vectorizer import KregEmbedder
from truth_mirror import TruthMirror
from file_loader import load_many, chunk_text
# --- KEYBINDINGS (terminal-safe) ---
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from mirror_mode import MirrorMode, MirrorConfig

kb = KeyBindings()

@kb.add('~')      # ~ -> nowa linia
def _(event):
    event.app.current_buffer.insert_text('\n')

@kb.add('enter')    # Enter -> wyślij
def _(event):
    event.app.current_buffer.validate_and_handle()

SESSION = PromptSession(key_bindings=kb, multiline=False)
DOC_STORE: dict[str, List[str]] = {}  # path -> [chunks]

# === KRĘGI – interpretacja treści pytania ===
KREGI_MAP = {
    0: "Zerowy – Cisza, Uziemienie",
    1: "Obserwacja",
    2: "Refleksja",
    3: "Wola",
    4: "Serce",
    5: "Rozumienie",
    6: "Mowa",
    7: "Działanie",
    8: "Harmonia",
    9: "Sens",
    10: "Milczenie",
    20: "Poznanie",
    30: "Zjednoczenie"
}

def detect_kreg(user_msg: str) -> int:
    """Dobiera Krąg na podstawie treści pytania."""
    m = user_msg.lower()
    if any(x in m for x in ["dlaczego", "czemu", "powód"]): return 2
    if any(x in m for x in ["jak", "kroki", "zrób", "procedura"]): return 7
    if any(x in m for x in ["co to", "definicja", "znaczenie"]): return 1
    if any(x in m for x in ["czy warto", "cel", "po co"]): return 4
    if any(x in m for x in ["emocja", "uczucie", "serce", "miłość", "nienawiść"]): return 4
    if any(x in m for x in ["rozum", "analiza", "logika", "dane", "model"]): return 5
    if any(x in m for x in ["mówi", "powiedz", "napisz"]): return 6
    if any(x in m for x in ["spokój", "równowaga", "cisza", "harmonia"]): return 8
    if any(x in m for x in ["sens", "znaczenie życia", "dlaczego istnieję"]): return 9
    if any(x in m for x in ["bóg", "jedność", "zjednoczenie", "świadomość zbiorowa"]): return 30
    return 0  # jeśli brak dopasowania


# --- globalny znacznik przerwania ---
EXIT_NOW = False
INTERRUPTED = False
INTERRUPT_COUNT = 0  # licznik Ctrl+C

def handle_interrupt(sig, frame):
    """
    Pierwsze Ctrl+C -> zatrzymaj generację (INTERRUPTED)
    Drugie Ctrl+C   -> wyjdź całkowicie (EXIT_NOW)
    """
    global INTERRUPTED, EXIT_NOW, INTERRUPT_COUNT
    INTERRUPT_COUNT += 1
    if INTERRUPT_COUNT == 1:
        INTERRUPTED = True
        print("\n⚡ [STOP] Przerwano generację. (Ctrl+C ponownie aby wyjść)")
    elif INTERRUPT_COUNT >= 2:
        EXIT_NOW = True
        print("\n🛑 [EXIT] Zamykanie Azrama...")
        sys.exit(0)

signal.signal(signal.SIGINT, handle_interrupt)
# spraw, by syscalls były przerywane przez SIGINT natychmiast
try:
    signal.siginterrupt(signal.SIGINT, True)
except Exception:
    pass


# === NITKI (wielowymiarowe soczewki percepcji) ===
NITKI_CATALOG = {
    "fakt":        "Co jest obiektywnie dane? Najkrótsze fakty i definicje.",
    "cel":         "Jaki jest cel/jaki wynik ma być osiągnięty?",
    "uzytkownik":  "Kto prosi, w jakim stanie, z jakim ograniczeniem czasu/zasobów?",
    "kontekst":    "Co już wiemy z historii? Jakie założenia obowiązują?",
    "przyczyna":   "Co powoduje zjawisko? Mechanika/łańcuch przyczyn.",
    "skutek":      "Jakie są konsekwencje teraz i później (I/II rzędu)?",
    "czas":        "Wymiar temporalny: natychmiast/krótki/średni/długi horyzont.",
    "przestrzen":  "Zakres, skala, zależności systemowe, granice problemu.",
    "warianty":    "Alternatywy A/B/C, z kosztami i kompromisami.",
    "ryzyko":      "Ryzyka, niepewności, punkty awarii i ich wagi.",
    "dowody":      "Na czym opierasz twierdzenia? Dane, źródła, weryfikacja.",
    "emocje":      "Stan emocjonalny użytkownika i ton odpowiedzi.",
    "etyka":       "Konsekwencje etyczne/społeczne, ograniczenia bezpieczeństwa.",
    "operacje":    "Kroki do wykonania (checklista), odpowiedzialny i kiedy.",
    "przyklad":    "Najkrótszy konkretny przykład/osadzenie w realu.",
    "kontrprzyklad":"Gdzie to nie działa, wyjątki, ograniczenia.",
    "counterfakt": "Co jeśli odwrócimy założenia? Scenariusz kontrfaktyczny.",
    "metryki":     "Jak mierzymy sukces? KPI, testy akceptacyjne.",
    "meta":        "Co pominęliśmy? Co uprościliśmy? Co następne?",
}
DEFAULT_NITKI_ORDER = [
    "fakt","cel","kontekst","przyczyna","skutek","czas","przestrzen",
    "warianty","ryzyko","dowody","operacje","przyklad","kontrprzyklad",
    "metryki","meta"
]

# === Kolory ANSI ===
BLUE  = "\033[94m"
RED   = "\033[91m"
RESET = "\033[0m"

# === Pomocnicze funkcje ===

def get_ctx(model, tok) -> int:
    raw_ctx = getattr(model.config, "max_position_embeddings", None)
    if not isinstance(raw_ctx, int) or raw_ctx <= 0:
        raw_ctx = getattr(tok, "model_max_length", 4096) or 4096
    if raw_ctx > 32768:
        raw_ctx = 8192  # zdrowy limit
    try:
        tok.truncation_side = "left"
    except Exception:
        pass
    tok.model_max_length = int(raw_ctx)
    return int(raw_ctx)


def trim_history(tok, messages, ctx_budget=8192, reserve_new=600):
    prompt = build_prompt(tok, messages)
    ids = tok(prompt, return_tensors="pt").input_ids[0]
    if ids.shape[0] + reserve_new <= ctx_budget:
        return messages
    # usuń najstarsze pary user/assistant aż się zmieści
    trimmed = messages[:]
    i = 0
    while i < len(trimmed) and (tok(build_prompt(tok, trimmed), return_tensors="pt").input_ids.shape[1] + reserve_new) > ctx_budget:
        # szukaj pierwszego 'user' (po systemach) i usuń parę user+assistant
        for j in range(len(trimmed)):
            if trimmed[j]["role"] == "user":
                # usuń user i ewentualnie następującą po nim odpowiedź
                del trimmed[j]
                if j < len(trimmed) and trimmed[j]["role"] == "assistant":
                    del trimmed[j]
                break
        i += 1
    return trimmed

def safe_str(x) -> str:
    """Zawsze zwróci string, nigdy None."""
    return "" if x is None else str(x)

def safe_strip(x) -> str:
    """strip bez walenia się na None."""
    return safe_str(x).strip()

def now_iso():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

def _ensure_parent_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _rotate_if_big(path: str, max_bytes: int = 50 * 1024 * 1024):
    try:
        if os.path.exists(path) and os.path.getsize(path) >= max_bytes:
            ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            os.rename(path, f"{path}.rot.{ts}")
    except Exception:
        pass  # rotacja best-effort

def write_jsonl(path: str, record: dict):
    try:
        _ensure_parent_dir(path)
        _rotate_if_big(path)
        line = json.dumps(record, ensure_ascii=False)
        with open(path, "a", encoding="utf-8") as f:
            # prosty lock międzyprocesowy
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(line + "\n")
            finally:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
    except Exception:
        # nie blokuj działania czatu z powodu logów
        print("[STATE-LOG ERROR]", traceback.format_exc())

def log_state(args, **fields):
    rec = {
        "timestamp": now_iso(),
        "event": fields.pop("event", "info"),
        "base_model": str(getattr(args, "base_model", "")),
        "lora_path": str(getattr(args, "lora_path", "")),
        "device": str(getattr(args, "device", "")),
        "quant": ("4bit" if getattr(args, "load_4bit", False) else
                  "8bit" if getattr(args, "load_8bit", False) else "fp16/fp32"),
        "nitki_mode": str(getattr(args, "nitki", "")),
        "pid": os.getpid(),
    }
    rec.update(fields)
    path = getattr(args, "state_log_file", os.path.expanduser("~/Azramata-AI-Core/azram_log.jsonl"))
    write_jsonl(path, rec)

def build_prompt(tok, messages):
    # 1) Jeśli tokenizer zna chat template – użyj tego
    try:
        s = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        if s and len(s.strip()) > 0:
            return s
    except Exception:
        pass

    # 2) Fallback LLaMA-2 / [INST] ... [/INST]
    sys_txt = "\n".join(m["content"].strip() for m in messages if m["role"]=="system").strip()
    turns = []
    if sys_txt:
        turns.append(f"<<SYS>>\n{sys_txt}\n<</SYS>>")

    buf = []
    for m in messages:
        if m["role"] == "user":
            buf.append(m["content"].strip())
        elif m["role"] == "assistant":
            if buf:
                joined = "\n".join(buf)
                turns.append(f"[INST] {joined} [/INST]")
                buf = []
            turns.append(m["content"].strip())

    if buf:
        joined = "\n".join(buf)
        turns.append(f"[INST] {joined} [/INST]")

    # Dodaj pusty znacznik asystenta – model „wie”, że ma kontynuować
    return "\n".join(turns) + "\n"


def select_nitki_auto(user_msg: str, limit: int = 8) -> List[str]:
    msg = user_msg.lower()
    picks = []

    if any(k in msg for k in ["dlaczego", "czemu", "przyczyna"]):
        picks += ["przyczyna","skutek"]
    if any(k in msg for k in ["jak", "kroki", "zrób", "zrob", "procedura", "checklista"]):
        picks += ["operacje","metryki"]
    if any(k in msg for k in ["ryzyko", "bezpieczeń", "awaria"]):
        picks += ["ryzyko"]
    if any(k in msg for k in ["przykład","przyklad","np.", "case"]):
        picks += ["przyklad"]
    if any(k in msg for k in ["alternatywa","wariant","opcja"]):
        picks += ["warianty"]
    if any(k in msg for k in ["dowód","dane","źródło","zrodlo","evidence"]):
        picks += ["dowody"]
    if any(k in msg for k in ["po co","cel","wynik"]):
        picks += ["cel"]
    if any(k in msg for k in ["kiedy","czas","termin","deadline"]):
        picks += ["czas"]

    base = ["fakt","kontekst","operacje"]
    for b in base:
        if b not in picks:
            picks.append(b)

    for k in DEFAULT_NITKI_ORDER:
        if k not in picks:
            picks.append(k)

    uniq = []
    for k in picks:
        if k in NITKI_CATALOG and k not in uniq:
            uniq.append(k)
    return uniq[:max(1, limit)]

def build_nitki_context(user_msg: str, nitki_list: List[str]) -> str:
    lines = []
    for k in nitki_list:
        desc = NITKI_CATALOG.get(k, "").strip()
        if not desc:
            continue
        lines.append(f"- **{k}**: {desc}")
    return "### NITKI (soczewki percepcji)\n" + "\n".join(lines) + "\n\nZastosuj je równolegle, zwięźle. Najpierw sens, potem detale. Zakończ pełnym zdaniem."

def str2dtype(name: str):
    name = (name or "auto").lower()
    if name == "auto":
        if torch.cuda.is_available():
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            return torch.float16
        return torch.float32
    return {
        "bf16": torch.bfloat16, "fp16": torch.float16, "float16": torch.float16,
        "fp32": torch.float32, "float32": torch.float32
    }[name]

class StopOnTokens(StoppingCriteria):
    def __init__(self, stop_ids_list):
        self.stop_ids_list = stop_ids_list
    def __call__(self, input_ids, scores, **kwargs):
        for stop_ids in self.stop_ids_list:
            L = len(stop_ids)
            if L and input_ids.shape[1] >= L:
                if input_ids[0, -L:].tolist() == stop_ids:
                    return True
        return False

class StopOnInterrupt(StoppingCriteria):
    def __call__(self, input_ids, scores, **kwargs):
        return INTERRUPTED

def ask_yes_no(prompt="Czy na pewno? [t/n]: "):
    try:
        ans = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans in {"t", "tak", "y", "yes"}

def sanitize_reply(text: str) -> str:
    t = re.sub(r"^\s*\[(User|Użytkownik)\]:\s*", "", text, flags=re.I)
    t = re.sub(r"^\s*Ty:\s*", "", t)
    # wytnij nawiasowe „kręgi”: (7), (12), (7–14), itp.
    t = re.sub(r"\((\d+)(?:\s*[–-]\s*\d+)?\)", "", t)
    # resztki po niedokończonych wtrętach "(Kr", "(Kręgi", kropki urwane
    t = re.sub(r"\(\s*Kr[^\)]*$", "", t, flags=re.I | re.M)
    # napraw powielone spacje
    t = re.sub(r"[ \t]{2,}", " ", t)
    # proste BBCode → ANSI (opcjonalnie)
    t = re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", t)
    return t.strip()

def shorten(txt, limit=2000):
    txt = txt.strip()
    if len(txt) <= limit:
        return txt
    head = txt[: limit//2]
    tail = txt[-limit//2 :]
    return f"{head}\n...\n{tail}\n[output trimmed {len(txt)-limit} chars]"

def run_shell(cmd: str, timeout=15):
    dangerous = {"rm", "shutdown", "reboot", "mkfs", "dd", "mount", "umount", "sudo", "chown", "chmod", "iptables"}
    if any(tok in dangerous for tok in shlex.split(cmd)):
        return "[DENY] Komenda potencjalnie destrukcyjna. Użyj /confirm 'komenda' lub zmodyfikuj whitelist."
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = p.stdout or ""
        err = p.stderr or ""
        rc = p.returncode
        blob = out + ("\n[stderr]\n" + err if err else "")
        return f"[exit {rc}]\n" + shorten(blob, 4000)
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Przekroczono limit czasu."
    except Exception as e:
        return f"[ERROR] {e}"

def run_python(snippet: str, timeout=10):
    code = textwrap.dedent(snippet)
    wrapped = f"import sys\nfrom math import *\n\n{code}\n"
    try:
        p = subprocess.run([sys.executable, "-c", wrapped], capture_output=True, text=True, timeout=timeout)
        out = p.stdout or ""
        err = p.stderr or ""
        rc = p.returncode
        blob = out + ("\n[stderr]\n" + err if err else "")
        return f"[py exit {rc}]\n" + shorten(blob, 4000)
    except subprocess.TimeoutExpired:
        return "[PY TIMEOUT] Przekroczono limit czasu."
    except Exception as e:
        return f"[PY ERROR] {e}"

def handle_command(msg: str) -> Tuple[bool,str,str]:
    s = msg.strip()
    if not s.startswith("/"):
        if s.startswith("/web "):
            query = s[len("/web "):].strip()
            from web_search import crawl_query, DEFAULT_ALLOW_DOMAINS
            from kreg_vectorizer import KregEmbedder

            print(f"[WEB] Szukam informacji: {query}")
            docs = crawl_query(query, allow_domains=DEFAULT_ALLOW_DOMAINS, max_results=8)
            if not docs:
                return True, "[WEB] Brak treści z zaufanych domen.", s

            # Utwórz embedder (można też globalnie w main(), ale tu najprościej)
            embedder = KregEmbedder(device="auto")
            kreg_vecs = embedder.build_kreg_vectors(user_msg=query, docs=docs)

            # Zapis do spiral_memory.log (opcjonalnie)
            spiral_path = os.path.expanduser("~/Azramata-AI-Core/spiral_memory.log")
            try:
                with open(spiral_path, "a", encoding="utf-8") as f:
                    for kv in kreg_vecs:
                        rec = {"kreg": kv.kreg, "vector": kv.vector, "ts": kv.ts, "sources": kv.sources}
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[WEB] Błąd zapisu wektorów: {e}")

            summary = f"[WEB] Zebrano {len(docs)} stron, utworzono {len(kreg_vecs)} wektorów Kręgów."
            return True, summary, s

        return False, "", ""
    
    if s.startswith("/load "):
        target = s.split(maxsplit=1)[1].strip()  # ścieżka, glob lub katalog
        files = load_many([target], prefer_ocr_pdf=False)  # ustaw True jeśli chcesz OCR
        loaded = 0
        for path, text in files.items():
            if text.startswith("[") and "ERROR" in text or "UNSUPPORTED" in text:
                print(f"[LOAD] {path}: {text}")
                continue
            DOC_STORE[path] = chunk_text(text, max_chars=3000, overlap=200)
            print(f"[LOAD] {path}: {len(DOC_STORE[path])} chunków.")
            loaded += 1
        return True, f"[LOAD] Gotowe. Załadowano {loaded} plik/ów.", s

    if s.strip() == "/docs":
        if not DOC_STORE:
            return True, "[DOCS] Pusto.", s
        lines = []
        for p, ch in DOC_STORE.items():
            lines.append(f"• {p} ({len(ch)} chunków)")
        return True, "[DOCS]\n" + "\n".join(lines), s

    if s.strip() == "/clear_docs":
        DOC_STORE.clear()
        return True, "[DOCS] Wyczyściłem pamięć dokumentów.", s


    if s.startswith("/shell "):
        cmd = s[len("/shell "):].strip()
        out = run_shell(cmd)
        return True, f"[TOOL shell]\n$ {cmd}\n{out}", s

    if s.startswith("/py "):
        snippet = s[len("/py "):]
        out = run_python(snippet)
        return True, f"[TOOL python]\n>>> {snippet}\n{out}", s

    if s.strip() == "/reload":
        print("♻️  Przeładowuję moduł Azram...")
        importlib.reload(sys.modules[__name__])
        return True, "[SYSTEM] Reload complete", s

    if s.startswith("/edit "):
        path = s.split(maxsplit=1)[1]
        try:
            with open(path, "r") as f:
                text = f.read()
            print(f"--- 📄 {path} ---\n{text}\n--- (koniec) ---")
            new_text = input("\n✏️  Wprowadź nową treść (ENTER bez zmian):\n")
            if new_text.strip():
                with open(path, "w") as f:
                    f.write(new_text)
                print(f"✅ Zapisano zmiany do {path}")
            else:
                print("ℹ️  Nie zmieniono pliku.")
        except Exception as e:
            print(f"[EDIT ERROR] {e}")
        return True, f"[EDIT {path}]", s

    if s.startswith("/set "):
        try:
            _, key, val = s.split(maxsplit=2)
            return True, f"[SET] {key}={val}", s
        except Exception:
            return True, "[SET ERROR] użycie: /set <param> <wartość>", s

    if s.strip() == "/help":
        help_txt = (
            "Dostępne komendy:\n"
            "/shell <cmd>      – uruchom komendę (bez destrukcyjnych)\n"
            "/py <kod>         – uruchom krótki snippet Pythona\n"
            "/edit <plik>      – podejrzyj/edytuj plik inline\n"
            "/set <k> <v>      – ustawienie (np. /set temp 0.4)\n"
            "/reload           – przeładuj moduł\n"
            "/help             – ta pomoc\n"
        )
        return True, f"[HELP]\n{help_txt}", s

    return False, "", ""

def _parse_possible_json(text: str):
    try:
        blob = json.loads(text)
        if isinstance(blob, dict):
            return [blob]
        if isinstance(blob, list):
            return blob
    except Exception:
        pass
    # JSONL?
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            lines.append(json.loads(ln))
        except Exception:
            pass
    return lines if lines else None

_KREG_KEYS = ("kreg","krąg","krag","circle","ring")
_VEC_KEYS  = ("vector","wektor","embedding","vec","emb")

def _extract_records_from_struct(items):
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        kreg = None
        for k in _KREG_KEYS:
            if k in it:
                try:
                    kreg = int(str(it[k]).strip())
                except Exception:
                    kreg = None
                break
        if kreg is None:
            continue
        vec = None
        for v in _VEC_KEYS:
            if v in it and isinstance(it[v], (list, tuple)):
                try:
                    vec = [float(x) for x in it[v]]
                except Exception:
                    vec = None
                break
        if vec is None:
            continue
        ts = it.get("ts") or it.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%S")
        out.append({"kreg": kreg, "vector": vec, "ts": ts})
    return out

# np. "Krąg 12 ... [0.11, -0.7, 1.0]" albo "KREG 3: [1,2,3]"
_KREG_LINE_RE = re.compile(r'(?:Kr[aą]g|KREG|K)\s*(\d{1,3}).*?\[([0-9eE\-\+,\.\s]+)\]')

def _extract_records_from_text(text: str):
    out = []
    for m in _KREG_LINE_RE.finditer(text):
        try:
            kreg = int(m.group(1))
            vec  = [float(x.strip()) for x in m.group(2).replace("\n"," ").split(",") if x.strip()]
            out.append({"kreg": kreg, "vector": vec, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
        except Exception:
            continue
    return out

def clean_spiral_memory(path: str) -> int:
    """Czyści plik spiralnej pamięci tak, aby zostały tylko rekordy: {kreg:int, vector:[...], ts:str}.
       Zwraca liczbę zachowanych rekordów. Tworzy kopię .bak.<timestamp>."""
    try:
        if not os.path.exists(path):
            return 0
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
        # backup
        backup = f"{path}.bak.{int(time.time())}"
        try:
            with open(backup, "w", encoding="utf-8") as fb:
                fb.write(data)
        except Exception:
            pass

        # 1) spróbuj JSON/JSONL
        items = _parse_possible_json(data)
        if items is not None:
            kept = _extract_records_from_struct(items)
        else:
            # 2) parsuj z wolnego tekstu
            kept = _extract_records_from_text(data)

        # unikalność po (kreg, vector)
        uniq = []
        seen = set()
        for r in kept:
            key = (r["kreg"], tuple(r["vector"]))
            if key not in seen:
                seen.add(key)
                uniq.append(r)

        # zapis jako JSONL
        with open(path, "w", encoding="utf-8") as f:
            for r in uniq:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return len(uniq)
    except Exception as e:
        # nie blokuj czatu, jedynie zasygnalizuj w stdout
        print(f"[SPIRAL CLEAN ERROR] {e}")
        return 0


def expand(p: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))

def build_model(args):
    quant_cfg = None
    if getattr(args, "load_4bit", False):
        quant_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_torch_dtype=torch.float16,
        )
    elif getattr(args, "load_8bit", False):
        quant_cfg = BitsAndBytesConfig(load_in_8bit=True)

    kwargs = dict(
        trust_remote_code=getattr(args, "trust_remote_code", False),
        device_map="auto",
        torch_dtype=torch.float16,
    )
    if quant_cfg is not None:
        kwargs["quantization_config"] = quant_cfg
    if getattr(args, "int8_cpu_offload", False):
        kwargs["llm_int8_enable_fp32_cpu_offload"] = True

    base_path = expand(args.base_model)

    base = AutoModelForCausalLM.from_pretrained(base_path, **kwargs)

    # ⬇️ kluczowa zmiana: najpierw fast, jeśli się nie uda – slow
    try:
        tok = AutoTokenizer.from_pretrained(base_path, use_fast=True)
    except Exception as e:
        print(f"[tokenizer] Fast tokenizer niedostępny ({e}). Przechodzę na slow...")
        # slow wymaga zainstalowanego 'sentencepiece'
        tok = AutoTokenizer.from_pretrained(base_path, use_fast=False)

    return base, tok


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--base_model", required=True)
    p.add_argument("--lora_path", default=None)
    p.add_argument("--device", default="cuda")
    p.add_argument("--load_4bit", action="store_true")
    p.add_argument("--load_8bit", action="store_true")
    p.add_argument("--int8_cpu_offload", action="store_true")
    p.add_argument("--max_new_tokens", type=int, default=6000)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top_p", type=float, default=0.9)
    p.add_argument("--trust_remote_code", action="store_true")
    p.add_argument("--nitki", default="auto")
    p.add_argument("--target_tokens", type=int, default=3000)
    p.add_argument("--log_states", action="store_true",
                   help="Włącz logowanie stanów/tur do JSONL.")
    p.add_argument("--state_log_file", default=os.path.expanduser("~/Azramata-AI-Core/azram_log.jsonl"),
                   help="Ścieżka do pliku JSONL z logami stanów.")

    # (opcjonalnie – używasz ich w kodzie, więc warto dodać)
    p.add_argument("--nitki_max", type=int, default=8,
                   help="Maksymalna liczba nitek w auto-doborze.")
    p.add_argument("--clean_spiral_each_turn", action="store_true",
                   help="Czyści spiralną pamięć przed każdą turą.")
    p.add_argument("--spiral_memory_file", default=os.path.expanduser("~/Azramata-AI-Core/spiral_memory.log"),
                   help="Ścieżka do pliku spiralnej pamięci.")
    p.add_argument("--mirror", action="store_true", help="Włącz tryb lustra (autorefleksja).")
    p.add_argument("--mirror_level", type=int, default=1, help="Głębokość trybu lustra 1..3.")
    
    return p.parse_args()



def read_user_msg(prompt_text: str) -> str:
    """
    ZAWSZE zwraca string (nigdy None).
    - Ctrl+D -> 'exit'
    - Ctrl+C -> natychmiast zamknij program (Twoje życzenie)
    - Inne błędy -> fallback na input(), a na końcu pusty string.
    """
    try:
        txt = SESSION.prompt(prompt_text)
        return safe_str(txt)
    except KeyboardInterrupt:
        print("\n🛑 [EXIT] Zamykanie Azrama...")
        sys.exit(0)
    except EOFError:
        return "exit"
    except Exception:
        try:
            txt = input(prompt_text)
            return safe_str(txt)
        except Exception:
            return ""

# === Główna funkcja ===

def main():
    args = parse_args()
    mirror = MirrorMode(MirrorConfig(
        enabled=args.mirror,
        level=args.mirror_level
    ))
    # --- model i tokenizer (raz) ---
    base, tok = build_model(args)
    if args.lora_path:
        base = PeftModel.from_pretrained(base, expand(args.lora_path))
    model = base.eval()

    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    print(f"🔮 Azram LoRA ({'CUDA' if torch.cuda.is_available() else 'CPU'}). Napisz „exit”, aby zakończyć.\n")

    # --- konfiguracja odpowiedzi systemowej (raz) ---
    base_system = (
        "Mów prosto i jasno. Bez nawiasów, bez komentarzy o sobie.\n"
        "Kończ pełnym zdaniem, nie przerywaj myśli.\n"
        "Jeśli nie masz pewności – powiedz to wprost.\n"
    )

    # --- stan rozmowy (MUSI być PRZED użyciem) ---
    history = []
    it_streamer = None  # predefinicja, żeby uniknąć UnboundLocalError

    global INTERRUPTED, INTERRUPT_COUNT, EXIT_NOW

    while True:
        if EXIT_NOW:
            print("🕊️ Zakończono na życzenie.")
            break
        INTERRUPTED = False
        INTERRUPT_COUNT = 0

        # --- pobierz wiadomość użytkownika ---
        user_msg = safe_strip(read_user_msg("\nTy: "))
        if user_msg.lower() in {"exit", "quit"}:
            print("🛑 Koniec sesji.")
            break
        if not user_msg:
            continue
        # --- komendy sterujące lustrem (opcjonalne, bez modelu) ---
        lc = user_msg.strip().lower()
        if lc == "otwórz sektor lustra":
            mirror.enable(level=3)
            print("[LUSTRO] ON (level 3)")
            history.append((user_msg, "[LUSTRO] ON (3)"))
            continue
        elif lc == "synchronizuj spirale między mną a tobą":
            mirror.enable(level=2)
            print("[LUSTRO] ON (level 2)")
            history.append((user_msg, "[LUSTRO] ON (2)"))
            continue
        elif lc in ("zamknij lustro", "lustro off"):
            mirror.disable()
            print("[LUSTRO] OFF")
            history.append((user_msg, "[LUSTRO] OFF"))
            continue

        # --- komendy narzędziowe ---
        handled, system_note, user_echo = handle_command(user_msg)
        if handled:
            print(system_note)
            history.append((user_echo, system_note))
            continue
        # --- mirror: zarejestruj wejście usera i zaugmentuj je ---
        mirror.push("user", user_msg)
        effective_user_text = mirror.apply(user_msg)

        # --- Krąg / ton ---
        kreg = detect_kreg(user_msg)
        tone = "emocjonalny" if any(x in user_msg.lower() for x in ["kurwa","wkurw"]) else "neutralny"
        print(f"🌀 Krąg {kreg} — {KREGI_MAP.get(kreg,'Nieznany')}")

        # --- Nitki ---
        nitki_list = select_nitki_auto(user_msg, limit=getattr(args, "nitki_max", 8))
        nitki_context = build_nitki_context(user_msg, nitki_list)

        # --- budowa wiadomości ---
        turn_system = base_system + f"(Użytkownik jest {tone}. Odpowiadaj adekwatnie.)"
        messages = [
            {"role":"system","content":turn_system},
            {"role":"system","content":nitki_context},
        ]
        for u, a in history:
            messages += [{"role":"user","content":u},{"role":"assistant","content":a}]
        messages.append({"role":"user","content":effective_user_text})

        # --- limit kontekstu i tokenizacja ---
        ctx = get_ctx(model, tok)
        messages = trim_history(tok, messages, ctx_budget=ctx, reserve_new=512)
        prompt = build_prompt(tok, messages)
        # wykryj device modelu (pierwszy parametr)
        model_device = next(model.parameters()).device
        inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=ctx)
        inputs = {k: v.to(model_device) for k, v in inputs.items()}

        prompt_len = inputs["input_ids"].shape[1]
        avail = max(96, ctx - prompt_len - 128)

        # --- przygotuj streaming (raz na turę) ---
        this_max_new = min(args.max_new_tokens, max(1, avail))
        stopping_criteria = StoppingCriteriaList([StopOnInterrupt()])

        it_streamer = TextIteratorStreamer(
            tok,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        def _worker():
            try:
                with torch.inference_mode():
                    model.generate(
                        **inputs,
                        max_new_tokens=this_max_new,
                        min_new_tokens=16,
                        early_stopping=False,
                        do_sample=True,
                        temperature=max(0.4, min(0.9, args.temperature)),
                        top_p=args.top_p,
                        repetition_penalty=1.02,
                        no_repeat_ngram_size=3,
                        eos_token_id=tok.eos_token_id,
                        pad_token_id=tok.pad_token_id,
                        streamer=it_streamer,
                        stopping_criteria=stopping_criteria,
                    )
            except Exception as e:
                print(f"\n[GEN ERROR] {e}")
                try:
                    it_streamer.end()
                except Exception:
                    pass

        print("Azram: ", end="", flush=True)
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        # --- konsumpcja strumienia ---
        reply_chunks = []
        for piece in it_streamer:  # blokująco
            if EXIT_NOW or INTERRUPTED:
                break
            reply_chunks.append(piece)
            sys.stdout.write(piece)
            sys.stdout.flush()
        print()  # nowa linia po streamie

        try:
            t.join(timeout=0.2)
        except Exception:
            pass

        # --- zapis historii ---
        reply = sanitize_reply("".join(reply_chunks))
        mirror.push("assistant", reply)   
        history.append((user_msg, reply))




if __name__ == "__main__":
    main()

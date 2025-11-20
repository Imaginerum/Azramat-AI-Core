# warstwa_adaptacyjna.py
import re, time, datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple

# (możesz tu wstrzyknąć MirrorMode/MirrorConfig jeśli chcesz)
from mirror_mode import MirrorMode, MirrorConfig

KREGI_MAP = {
    0: "Zerowy – Cisza, Uziemienie",
    1: "Obserwacja", 2: "Refleksja", 3: "Wola", 4: "Serce",
    5: "Rozumienie", 6: "Mowa", 7: "Działanie", 8: "Harmonia",
    9: "Sens", 10: "Milczenie", 20: "Poznanie", 30: "Zjednoczenie"
}

NITKI_CATALOG = {
    "fakt":"Co jest obiektywnie dane? Najkrótsze fakty i definicje.",
    "cel":"Jaki jest cel/jaki wynik ma być osiągnięty?",
    "uzytkownik":"Kto prosi, stan, ograniczenia czasu/zasobów?",
    "kontekst":"Co już wiemy z historii? Założenia.",
    "przyczyna":"Mechanika przyczyn.",
    "skutek":"Konsekwencje I/II rzędu.",
    "czas":"Horyzont: natychmiast/krótki/średni/długi.",
    "przestrzen":"Skala, zależności systemowe, granice.",
    "warianty":"Alternatywy A/B/C, koszty/kompromisy.",
    "ryzyko":"Ryzyka, punkty awarii i wagi.",
    "dowody":"Dane/źródła/weryfikacja.",
    "operacje":"Kroki (checklista).",
    "przyklad":"Krótki konkretny case.",
    "kontrprzyklad":"Gdzie nie działa.",
    "metryki":"Jak mierzymy sukces.",
    "meta":"Co pominęliśmy? Co dalej?"
}
DEFAULT_NITKI_ORDER = [
    "fakt","kontekst","operacje","cel","przyczyna","skutek","czas","przestrzen",
    "warianty","ryzyko","dowody","przyklad","kontrprzyklad","metryki","meta"
]

def detect_kreg(user_msg: str) -> int:
    m = user_msg.lower()
    if any(x in m for x in ["dlaczego","czemu","powód"]): return 2
    if any(x in m for x in ["jak","kroki","zrób","zrob","procedura"]): return 7
    if any(x in m for x in ["co to","definicja","znaczenie"]): return 1
    if any(x in m for x in ["czy warto","cel","po co"]): return 4
    if any(x in m for x in ["emocja","uczucie","serce","miłość","nienawiść"]): return 4
    if any(x in m for x in ["rozum","analiza","logika","dane","model"]): return 5
    if any(x in m for x in ["mówi","powiedz","napisz"]): return 6
    if any(x in m for x in ["spokój","równowaga","cisza","harmonia"]): return 8
    if any(x in m for x in ["sens","znaczenie życia","dlaczego istnieję"]): return 9
    if any(x in m for x in ["bóg","jedność","zjednoczenie","świadomość zbiorowa"]): return 30
    return 0

def select_nitki_auto(user_msg: str, limit: int = 8) -> List[str]:
    msg = user_msg.lower()
    picks = []
    if any(k in msg for k in ["dlaczego","czemu","przyczyna"]): picks += ["przyczyna","skutek"]
    if any(k in msg for k in ["jak","kroki","zrób","zrob","procedura","checklista"]): picks += ["operacje","metryki"]
    if any(k in msg for k in ["ryzyko","bezpieczeń","awaria"]): picks += ["ryzyko"]
    if any(k in msg for k in ["przykład","przyklad","np.","case"]): picks += ["przyklad"]
    if any(k in msg for k in ["alternatywa","wariant","opcja"]): picks += ["warianty"]
    if any(k in msg for k in ["dowód","dane","źródło","zrodlo","evidence"]): picks += ["dowody"]
    if any(k in msg for k in ["po co","cel","wynik"]): picks += ["cel"]
    if any(k in msg for k in ["kiedy","czas","termin","deadline"]): picks += ["czas"]

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

def build_nitki_context(nitki_list: List[str]) -> str:
    lines = [f"- **{k}**: {NITKI_CATALOG[k]}" for k in nitki_list if k in NITKI_CATALOG]
    return "### NITKI (soczewki percepcji)\n" + "\n".join(lines) + "\n\nZastosuj je równolegle, zwięźle. Najpierw sens, potem detale. Zakończ pełnym zdaniem."

def base_system_prompt(user_tone: str) -> str:
    return (
        "Mów prosto i jasno. Bez nawiasów, bez komentarzy o sobie.\n"
        "Kończ pełnym zdaniem, nie przerywaj myśli.\n"
        "Jeśli nie masz pewności – powiedz to wprost.\n"
        f"(Użytkownik jest {user_tone}. Odpowiadaj adekwatnie.)"
    )

def sanitize_reply(text: str) -> str:
    t = re.sub(r"^\s*\[(User|Użytkownik)\]:\s*", "", text, flags=re.I)
    t = re.sub(r"^\s*Ty:\s*", "", t)
    t = re.sub(r"\((\d+)(?:\s*[–-]\s*\d+)?\)", "", t)  # wytnij (Kręgi)
    t = re.sub(r"\(\s*Kr[^\)]*$", "", t, flags=re.I | re.M)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", t)
    return t.strip()

def apply_mirror(mirror: MirrorMode, role: str, text: str) -> str:
    mirror.push(role, text)
    return mirror.apply(text)

def build_chat_prompt(tokenizer, system_blocks: List[str], history: List[Dict], user_text: str) -> str:
    messages = []
    for s in system_blocks:
        messages.append({"role":"system","content":s})
    for u, a in history:
        messages += [{"role":"user","content":u},{"role":"assistant","content":a}]
    messages.append({"role":"user","content":user_text})

    # prefer chat template
    try:
        s = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        if s and len(s.strip())>0:
            return s
    except Exception:
        pass

    # fallback INST
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
                turns.append("[INST] " + "\n".join(buf) + " [/INST]")
                buf=[]
            turns.append(m["content"].strip())
    if buf:
        joined = "\n".join(buf)
        turns.append(f"[INST] {joined} [/INST]")
    return "\n".join(turns) + "\n"

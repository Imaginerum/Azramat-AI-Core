# core/system/mirror_mode.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

MIRROR_PRIMER = """\
[TRYB_LUSTRA]
Twoje poprzednie wyjście (ODPOWIEDŹ_AZRAM): <<<{last_reply}>>>

ZADANIE:
1) Zidentyfikuj niewypowiedziane założenia tej odpowiedzi (min. 2).
2) Wskaż luki informacyjne lub niekonsekwencje (min. 1).
3) Zaproponuj krótszą, gęstszą wersję odpowiedzi – ale zachowaj jej sens (≤ 3 zdania).
4) Połącz to z aktualnym pytaniem użytkownika: <<<{user_msg}>>> tak, aby odpowiedź była *dla niego*, nie o systemie.

FORMAT WYJŚCIA:
- [ZAŁOŻENIA]
- [LUKI]
- [ESENCJA_3Z]
- [ODPOWIEDŹ_SKONCENTROWANA]
"""

MIRROR_TAG = "[MIRROR_MODE]"

@dataclass
class MirrorConfig:
    enabled: bool = False
    level: int = 1  # 1..3 (głębokość autorefleksji)
    max_chars_last: int = 2000  # ile znaków poprzedniej odpowiedzi przepuszczać
    system_tag: str = MIRROR_TAG

@dataclass
class MirrorMode:
    cfg: MirrorConfig = field(default_factory=MirrorConfig)
    history: List[Dict[str, str]] = field(default_factory=list)  # [{"role":"user"/"assistant","content":str}, ...]

    def enable(self, level: int | None = None):
        self.cfg.enabled = True
        if level is not None:
            self.cfg.level = max(1, min(3, int(level)))

    def disable(self):
        self.cfg.enabled = False

    def push(self, role: str, content: str):
        # zachowujemy zwięzłą historię; trzymamy tylko ostatnie kilka wpisów
        self.history.append({"role": role, "content": content})
        if len(self.history) > 20:
            self.history = self.history[-20:]

    def last_assistant_reply(self) -> str:
        for msg in reversed(self.history):
            if msg["role"] == "assistant":
                return msg["content"][: self.cfg.max_chars_last]
        return ""

    def augment_user_prompt(self, user_msg: str) -> str:
        """Jeśli tryb lustra włączony – doklej autorefleksję do promptu użytkownika."""
        if not self.cfg.enabled:
            return user_msg

        last = self.last_assistant_reply()
        if not last:
            return user_msg  # nie ma czego lustrzać

        # „Głębokość” = ile razy zagnieżdżamy lustro (lekka wariacja promptu)
        primer = MIRROR_PRIMER
        if self.cfg.level >= 2:
            primer += "\nDODAJ: Zderz Krąg 0 (Cisza) z Kręgiem 7 (Działanie) w jednym zdaniu.\n"
        if self.cfg.level >= 3:
            primer += "DODAJ: Sprawdź, czy odpowiedź nie gubi intencji użytkownika; jeśli tak – popraw kurs jednym zdaniem.\n"

        mirror_block = primer.format(last_reply=last, user_msg=user_msg)
        return f"{user_msg}\n\n{self.cfg.system_tag}\n{mirror_block}\n{self.cfg.system_tag}/END"

    def apply(self, user_msg: str) -> str:
        """Publiczne API: zwraca zaugmentowaną wiadomość użytkownika."""
        return self.augment_user_prompt(user_msg)

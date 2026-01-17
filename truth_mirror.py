from dataclasses import dataclass
import re, math, time
from typing import Dict, Any, List, Optional

@dataclass
class MirrorReport:
    ts: str
    kreg_source: int
    score: float           # 0..1 – im wyżej, tym “prawdziwiej”
    facets: Dict[str, float]
    notes: List[str]
    suggestion: Optional[str] = None

class TruthMirror:
    """
    Moduł '3' – Lustro Rzeczywistości.
    Mierzy trzy rzeczy (3-facet):
      - FAKT: brak oczywistych sprzeczności/halucynacji (heurystyki + opcjonalny /web hint)
      - LOGIKA: lokalna spójność (brak zaprzeczeń w tekście)
      - UCZCIWOŚĆ (TONE): brak kategorycznych tez bez zastrzeżeń przy niskiej pewności
    Nie blokuje przepływu – zwraca raport i ewentualną sugestię regeneracji.
    """

    def __init__(self, use_web_hint: bool = False):
        self.use_web_hint = use_web_hint

    def _detect_contradictions(self, text: str) -> float:
        # banalna heurystyka: wykryj “X… nie X”, “tak… jednak nie”
        lowers = text.lower()
        hits = 0
        hits += len(re.findall(r"\b(nie prawda|to fałsz|to nieprawda)\b", lowers))
        hits += len(re.findall(r"\b(jednak|ale)\b.*\b(nie|przeciwnie)\b", lowers))
        # im więcej sprzeczności, tym niższy wynik
        return max(0.0, 1.0 - min(1.0, hits / 3.0))

    def _assertiveness_penalty(self, text: str) -> float:
        # kara za kategoryczne “zawsze/na pewno” bez modulatorów (“zwykle”, “prawdopodobnie”)
        strong = len(re.findall(r"\b(zawsze|na pewno|bez wątpienia|dowiedzione)\b", text.lower()))
        soft   = len(re.findall(r"\b(zwykle|często|prawdopodobnie|możliwe|szacuję)\b", text.lower()))
        if strong == 0: 
            return 1.0
        # jeśli są softenery, kara mniejsza
        return max(0.0, 1.0 - max(0, strong - soft) * 0.2)

    def _structure_ok(self, text: str) -> float:
        # drobny sygnał: czy kończy zdaniem, czy są nagłe urwania, czy nie ma “??? !!!”
        ok_end = bool(re.search(r'[.!?…][)"\]»’”]*\s*$', text.strip()))
        too_exclaim = len(re.findall(r"!!!", text))
        return max(0.0, (1.0 if ok_end else 0.7) - min(0.4, 0.1 * too_exclaim))

    def _web_hint(self, query: str) -> float:
        if not self.use_web_hint:
            return 1.0
        try:
            # lekki hint: jeśli /web da cokolwiek z allowlist – +0.1
            from web_search import crawl_query, DEFAULT_ALLOW_DOMAINS
            docs = crawl_query(query, allow_domains=DEFAULT_ALLOW_DOMAINS, max_results=3)
            return 1.1 if docs else 1.0
        except Exception:
            return 1.0

    def reflect(self, kreg: int, user_msg: str, reply: str) -> MirrorReport:
        f_fact  = self._web_hint(user_msg) * self._detect_contradictions(reply)
        f_logic = self._structure_ok(reply)
        f_tone  = self._assertiveness_penalty(reply)
        # znormalizuj (cap do 1.0)
        facets = {"fakt": min(1.0, f_fact), "logika": f_logic, "uczciwość": f_tone}
        score = max(0.0, min(1.0, (facets["fakt"]*0.45 + facets["logika"]*0.3 + facets["uczciwość"]*0.25)))
        notes = []
        if facets["fakt"] < 0.8:   notes.append("Sprawdź zgodność faktów / unikaj sprzeczności.")
        if facets["logika"] < 0.8: notes.append("Domknij zdanie / porządkuj wątki, unikaj !!!.")
        if facets["uczciwość"]<0.8:notes.append("Zmiękczaj kategoryczne sądy (np. 'prawdopodobnie').")

        sugg = None
        if score < 0.75:
            sugg = "Rozważ regenerację krótszej, bardziej ostrożnej odpowiedzi (dodaj źródła lub hedging)."

        return MirrorReport(
            ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            kreg_source=int(kreg),
            score=round(score, 3),
            facets={k: round(v,3) for k,v in facets.items()},
            notes=notes,
            suggestion=sugg
        )

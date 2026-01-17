# -*- coding: utf-8 -*-
import time, math
from typing import List, Dict, Tuple
from dataclasses import dataclass

import torch
from sentence_transformers import SentenceTransformer

# Jeżeli nie masz VRAM – CPU też działa, tylko wolniej
# Model PL/EN: multilingual-e5-base (bardzo dobry do embedów)
EMB_MODEL_NAME = "intfloat/multilingual-e5-base"

# Mapowanie Kręgów -> „kąt patrzenia” (krótka instrukcja do zrobienia embeddingu)
KREGI_INSTRUKCJE = {
    0:  "Zrób krótką, neutralną esencję faktów z tekstu.",
    1:  "Wypisz najważniejsze obserwacje i definicje, bez opinii.",
    2:  "Wyodrębnij przyczyny i wyjaśnienia (dlaczego).",
    3:  "Wskaż cele lub intencje stron.",
    4:  "Wydobądź aspekt ludzki i emocjonalny, jeśli występuje.",
    5:  "Podsumuj wnioski i rozumowanie (logika).",
    6:  "Ułóż to w formę prostego przekazu.",
    7:  "Zamień to na listę kroków / działania.",
    8:  "Zwróć uwagę na równowagę i kompromisy.",
    9:  "Zidentyfikuj sens / znaczenie całości.",
    10: "Zakończ w punktach najważniejszym rdzeniem.",
}

@dataclass
class KregVector:
    kreg: int
    vector: List[float]
    ts: str
    sources: List[str]

class KregEmbedder:
    def __init__(self, device: str = "auto"):
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model = SentenceTransformer(EMB_MODEL_NAME, device=self.device)

    def _embed(self, texts: List[str]) -> torch.Tensor:
        # E5 oczekuje prefiksu "query: " / "passage: " dla lepszej jakości
        prepped = [("query: " + t.strip()) for t in texts]
        embs = self.model.encode(prepped, convert_to_tensor=True, normalize_embeddings=True, batch_size=16, show_progress_bar=False)
        return embs  # shape: [N, D], L2-normalized

    def build_kreg_vectors(self, user_msg: str, docs: List[Dict], topk_sent_per_doc: int = 5) -> List[KregVector]:
        """
        docs: [{"title","url","text", ...}]
        Tworzy embeddingi per Krąg – biorąc najlepsze fragmenty z dokumentów.
        """
        # 1) Dzielimy teksty na zdania, wybieramy TopK per dokument do kontekstu
        passages, srcs = [], []
        for d in docs:
            text = d["text"]
            # prymitywny splitter zdań
            parts = [p.strip() for p in re_split_sentences(text)]
            # wybór najdłuższych z sensem (heurystyka)
            parts = sorted(parts, key=len, reverse=True)[:max(3, topk_sent_per_doc)]
            for p in parts:
                # ogranicz długość do rozsądku
                if len(p) > 700:
                    p = p[:700]
                passages.append(p)
                srcs.append(d["url"])

        if not passages:
            return []

        # 2) Embeddingi „passage”
        passage_emb = self.model.encode(["passage: " + p for p in passages],
                                        convert_to_tensor=True, normalize_embeddings=True,
                                        batch_size=16, show_progress_bar=False)  # [P, D]

        # 3) Dla każdego Kręgu zbuduj zapytanie i policz centroid top-N najbardziej podobnych fragmentów
        out: List[KregVector] = []
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        for kreg, instrukcja in KREGI_INSTRUKCJE.items():
            query = f"{user_msg}\n{instrukcja}"
            q_emb = self._embed([query])[0]  # [D]
            sims = (passage_emb @ q_emb)      # cos sim, bo znormalizowane
            topv, topi = torch.topk(sims, k=min(12, sims.shape[0]))
            top_vecs = passage_emb[topi]      # [K, D]
            centroid = top_vecs.mean(dim=0)
            centroid = torch.nn.functional.normalize(centroid, dim=0)
            # wektor do listy float
            vec = centroid.detach().cpu().tolist()
            # źródła (unikalne)
            picked_sources = sorted({srcs[i.item()] for i in topi})[:5]
            out.append(KregVector(kreg=kreg, vector=vec, ts=now, sources=picked_sources))
        return out

# --- prościutki splitter zdań (PL/EN)
import re
_SENT_SPLIT = re.compile(r'(?<=[\.\?\!])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])')
def re_split_sentences(text: str):
    text = text.strip()
    # zabezpieczenie: jeśli ktoś wkleił wszystko w jednym wierszu
    text = re.sub(r'\s+', ' ', text)
    return _SENT_SPLIT.split(text)

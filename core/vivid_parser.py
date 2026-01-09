# -*- coding: utf-8 -*-
# Plik: /core/vivid_parser.py
# Vivid Parser – Moduł dekodujący strukturę plików .vv
# Rozumie adnotacje kręgowe (np. "(7)", "(3 -> 5)")

import re
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class VividLine:
    text: str
    circles: List[int]      # np. [7] lub [3, 5] dla tranzycji
    transition: bool        # True jeśli to przejście (3 -> 5)
    section: Optional[str]  # Nazwa sekcji, jeśli linia do niej należy

@dataclass
class VividDoc:
    path: str
    lines: List[VividLine]
    metadata: Dict[str, str] # np. Autor, Data z nagłówka

class VividParser:
    # Wzorce regex
    # (7) lub (12) na końcu linii
    _RE_CIRCLE_SINGLE = re.compile(r'\s*\(\s*(\d{1,2})\s*\)\s*$')
    # (3 -> 5) lub (3->5) na końcu linii
    _RE_CIRCLE_TRANS = re.compile(r'\s*\(\s*(\d{1,2})\s*[-→>]\s*(\d{1,2})\s*\)\s*$')
    # [SEKCJA]
    _RE_SECTION = re.compile(r'^\s*\[(.*?)\]\s*$')
    # Metadane # Klucz: Wartość
    _RE_META = re.compile(r'^\s*#\s*([^:]+):\s*(.*)$')

    def parse_file(self, path: str) -> VividDoc:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_text(content, path)

    def parse_text(self, text: str, path: str = "memory") -> VividDoc:
        lines_out = []
        metadata = {}
        current_section = None
        
        raw_lines = text.splitlines()
        
        for line in raw_lines:
            line_strip = line.strip()
            if not line_strip:
                continue

            # 1. Metadane (# Klucz: Wartość)
            # Ale uwaga: komentarze mogą być też zwykłe. Zakładamy metadane tylko na początku pliku? 
            # Wg analizy plików .vv, metadane są na górze.
            meta_match = self._RE_META.match(line_strip)
            if meta_match:
                k, v = meta_match.groups()
                metadata[k.strip()] = v.strip()
                continue
            
            # Jeśli linia zaczyna się od #, a nie jest metadaną -> komentarz, ignoruj
            if line_strip.startswith('#'):
                continue

            # 2. Sekcje [NAGŁÓWEK]
            sec_match = self._RE_SECTION.match(line_strip)
            if sec_match:
                current_section = sec_match.group(1).upper()
                continue

            # 3. Analiza treści i Kręgów
            circles = []
            is_trans = False
            clean_text = line_strip

            # Sprawdź tranzycję (A -> B)
            trans_match = self._RE_CIRCLE_TRANS.search(line_strip)
            if trans_match:
                c1, c2 = trans_match.groups()
                circles = [int(c1), int(c2)]
                is_trans = True
                clean_text = self._RE_CIRCLE_TRANS.sub('', line_strip).strip()
            else:
                # Sprawdź pojedynczy krąg (A)
                single_match = self._RE_CIRCLE_SINGLE.search(line_strip)
                if single_match:
                    c1 = single_match.group(1)
                    circles = [int(c1)]
                    is_trans = False
                    clean_text = self._RE_CIRCLE_SINGLE.sub('', line_strip).strip()

            # Dodaj linię
            if clean_text:
                lines_out.append(VividLine(
                    text=clean_text,
                    circles=circles,
                    transition=is_trans,
                    section=current_section
                ))

        return VividDoc(path=path, lines=lines_out, metadata=metadata)

# Przykład użycia (do testów)
if __name__ == "__main__":
    sample = """
    # Data: 2026-01-01
    [WSTĘP]
    To jest zdanie logiczne. (5)
    A to jest przejście od woli do czynu. (3 -> 7)
    """
    parser = VividParser()
    doc = parser.parse_text(sample)
    for l in doc.lines:
        print(f"[{l.section}] {l.text} -> Kręgi: {l.circles} (Trans: {l.transition})")

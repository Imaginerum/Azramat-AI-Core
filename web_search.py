# -*- coding: utf-8 -*-
# /mnt/azramat/Azramat-AI-Core/web_search.py
import time, re, html, logging
from typing import List, Dict, Optional, Iterable
from urllib.parse import urlparse

import requests
from ddgs import DDGS
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AzramBot/1.0 (+info: internal)",
    "Accept-Language": "pl,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Domyślna allowlista „znanych” domen – dopisz swoje
DEFAULT_ALLOW_DOMAINS = {
    "wikipedia.org", "pl.wikipedia.org",
    "nature.com", "science.org", "arxiv.org",
    "who.int", "ema.europa.eu", "cdc.gov",
    "europa.eu", "ec.europa.eu",
    "bbc.com", "bbc.co.uk", "nytimes.com", "reuters.com", "apnews.com",
    "theguardian.com", "financialtimes.com", "ft.com",
    "mit.edu", "stanford.edu", "harvard.edu",
    "pwsz.edu.pl", "uw.edu.pl", "agh.edu.pl", "pw.edu.pl",
}

def _host_in_allowlist(url: str, allow_domains: Optional[Iterable[str]]) -> bool:
    if not allow_domains:
        return True
    host = urlparse(url).netloc.lower()
    for dom in allow_domains:
        d = dom.lower()
        if host == d or host.endswith("." + d):
            return True
    return False

def search_duckduckgo(query: str, max_results: int = 8, allow_domains: Optional[Iterable[str]] = None) -> List[Dict]:
    """Zwraca wyniki DDG przefiltrowane po allowliście domen."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            href = r.get("href") or r.get("link") or ""
            if not href:
                continue
            if _host_in_allowlist(href, allow_domains):
                results.append({
                    "title": r.get("title") or "",
                    "snippet": r.get("body") or r.get("snippet") or "",
                    "url": href
                })
    return results

def _clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "aside", "nav"]):
        tag.decompose()
    txt = soup.get_text(separator=" ")
    txt = html.unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def fetch_text(url: str, timeout: float = 12.0, max_bytes: int = 2_500_000) -> Optional[str]:
    """Pobiera stronę i zwraca surowy tekst (oczyszczony)."""
    try:
        with requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, stream=True) as resp:
            resp.raise_for_status()
            content = b""
            for chunk in resp.iter_content(1024 * 8):
                content += chunk
                if len(content) > max_bytes:
                    break
        html_text = content.decode(resp.encoding or "utf-8", errors="ignore")
        return _clean_html(html_text)
    except Exception as e:
        logging.debug(f"[fetch_text] fail {url}: {e}")
        return None

def crawl_query(query: str, allow_domains: Optional[Iterable[str]] = None,
                max_results: int = 8) -> List[Dict]:
    """Wyszukuje, filtruje po domenach, pobiera i czyści teksty."""
    hits = search_duckduckgo(query, max_results=max_results, allow_domains=allow_domains)
    out = []
    for h in hits:
        txt = fetch_text(h["url"])
        if not txt or len(txt) < 500:
            continue
        out.append({
            "title": h["title"],
            "url": h["url"],
            "domain": urlparse(h["url"]).netloc.lower(),
            "snippet": h["snippet"],
            "text": txt[:400_000],  # bez przesady
        })
        # delikatny throttle
        time.sleep(0.3)
    return out

def summarize_results(results: List[Dict]) -> str:
    """Prosty zlepek dla debug – nie używaj do merytoryki."""
    lines = []
    for r in results:
        t = r["title"] or r["url"]
        s = (r.get("snippet") or r.get("text", "")[:200]).strip()
        lines.append(f"• {t} — {s}")
    blob = "\n".join(lines)
    return blob[:4000]

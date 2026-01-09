// Plik: /core/silnik/vv_loader.rs
// Data: 2025-08-08
// Cel: Wczytuje i interpretuje pliki .vv systemu Azramaty → struktura VvDoc
// Budowa: wymaga serde/serde_json do serializacji (opcjonalnie)

use std::collections::{BTreeMap, BTreeSet};
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};

#[cfg(feature = "json")]
use serde::{Deserialize, Serialize};

/// Pojedyncza dyrektywa linii `::` (np. "::include path", "::set KEY=VAL")
#[cfg_attr(feature = "json", derive(Serialize, Deserialize))]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Directive {
    pub line: usize,
    pub text: String,
    pub kind: DirectiveKind,
}

#[cfg_attr(feature = "json", derive(Serialize, Deserialize))]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DirectiveKind {
    Include(String),
    Set { key: String, value: String },
    Custom(String),
}

/// Blok kodu otoczony ``` (język opcjonalny)
#[cfg_attr(feature = "json", derive(Serialize, Deserialize))]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CodeBlock {
    pub start_line: usize,
    pub lang: Option<String>,
    pub content: String,
}

/// Główna struktura dokumentu VV
#[cfg_attr(feature = "json", derive(Serialize, Deserialize))]
#[derive(Debug, Clone, Default)]
pub struct VvDoc {
    pub path: Option<PathBuf>,
    pub title: Option<String>,
    pub meta: BTreeMap<String, String>,          // np. "Plik", "Nazwa", "Data", "Krąg dominujący" itd.
    pub tags: Vec<String>,                       // z sekcji [TAGI]
    pub sections: BTreeMap<String, String>,      // [SEKCJA] → tekst
    pub kv: BTreeMap<String, String>,            // Key: Value (poza sekcjami)
    pub code_blocks: Vec<CodeBlock>,             // ```…```
    pub directives: Vec<Directive>,              // ::include, ::set, itp.
    pub diagnostics: Vec<String>,                // uwagi parsera
    pub raw_lines: usize,
}

/// Błąd ładowania/pliku
#[derive(Debug)]
pub enum VvError {
    Io(io::Error),
    Parse(String),
}

impl From<io::Error> for VvError {
    fn from(e: io::Error) -> Self { VvError::Io(e) }
}

pub type VvResult<T> = Result<T, VvError>;

/// Publiczne API: wczytaj plik .vv do struktury
pub fn load_vv_module<P: AsRef<Path>>(file_path: P) -> VvResult<VvDoc> {
    let path = file_path.as_ref();
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut doc = parse_vv(reader)?;
    doc.path = Some(path.to_path_buf());
    Ok(doc)
}

/// Publiczne API: wczytaj z BufRead (ułatwia testy)
pub fn parse_vv<R: BufRead>(mut reader: R) -> VvResult<VvDoc> {
    let mut doc = VvDoc::default();

    let mut buf = String::new();
    let mut line_no = 0usize;

    // stan parsera
    let mut cur_section: Option<String> = None;
    let mut cur_section_buf = String::new();
    let mut in_code = false;
    let mut code_lang: Option<String> = None;
    let mut code_start = 0usize;

    // nagłówkowe klucze możliwe do rozpoznania (heurystyka)
    let header_keys = BTreeSet::from([
        "plik", "nazwa", "tytuł", "tytul", "data", "typ", "krąg dominujący", "krag dominujacy",
        "kręgi powiązane", "kregi powiazane", "tagi",
    ]);

    while {
        buf.clear();
        reader.read_line(&mut buf)?
    } != 0
    {
        line_no += 1;
        let line = buf.trim_end_matches(&['\r', '\n'][..]).to_string();

        // Bloki kodu: start/koniec ```
        if line.trim_start().starts_with("```") {
            if !in_code {
                in_code = true;
                code_start = line_no;
                let lang = line.trim_start().trim_start_matches("```").trim();
                code_lang = if lang.is_empty() { None } else { Some(lang.to_string()) };
                continue;
            } else {
                // zamykamy blok
                doc.code_blocks.push(CodeBlock {
                    start_line: code_start,
                    lang: code_lang.clone(),
                    content: cur_section_buf.clone(),
                });
                cur_section_buf.clear();
                in_code = false;
                code_lang = None;
                continue;
            }
        }

        if in_code {
            if !cur_section_buf.is_empty() { cur_section_buf.push('\n'); }
            cur_section_buf.push_str(&line);
            continue;
        }

        // Dyrektywy `::...`
        if let Some(stripped) = line.strip_prefix("::") {
            let dir = parse_directive(stripped.trim(), line_no);
            doc.directives.push(dir);
            continue;
        }

        // Linie nagłówka z # (meta, tytuł)
        if line.starts_with('#') {
            // np. "# Plik: /core/silnik/engine_5D.vv" lub "# Tytuł: ..."
            let ht = line.trim_start_matches('#').trim();
            if let Some((k, v)) = split_kv(ht) {
                let k_lc = k.to_lowercase();
                if header_keys.contains(k_lc.as_str()) {
                    if k_lc == "tagi" {
                        // dopisz do tags
                        let tags = split_csv_like(v);
                        doc.tags.extend(tags);
                    } else {
                        doc.meta.insert(k.to_string(), v.to_string());
                    }
                } else {
                    // inne # nagłówki → użyj jako "tytuł" jeśli jeszcze pusty
                    if doc.title.is_none() {
                        doc.title = Some(ht.to_string());
                    } else {
                        // wrzuć do sekcji "HEADERS"
                        let e = doc.sections.entry("HEADERS".into()).or_default();
                        if !e.is_empty() { e.push('\n'); }
                        e.push_str(ht);
                    }
                }
            } else {
                // pojedynczy tytuł '# Cos tam'
                if doc.title.is_none() {
                    doc.title = Some(ht.to_string());
                } else {
                    let e = doc.sections.entry("HEADERS".into()).or_default();
                    if !e.is_empty() { e.push('\n'); }
                    e.push_str(ht);
                }
            }
            continue;
        }

        // Sekcja w [NAZWA]
        if let Some(sec) = parse_section_header(&line) {
            // zamknij poprzednią sekcję (jeśli była)
            if let Some(name) = cur_section.take() {
                let entry = doc.sections.entry(name).or_default();
                if !entry.is_empty() { entry.push('\n'); }
                entry.push_str(cur_section_buf.trim_end());
                cur_section_buf.clear();
            }
            cur_section = Some(sec);
            continue;
        }

        // Puste linie → po prostu dopisz do aktualnego bufora
        if line.trim().is_empty() {
            if !cur_section_buf.is_empty() { cur_section_buf.push('\n'); }
            continue;
        }

        // Key: Value poza sekcją
        if cur_section.is_none() {
            if let Some((k, v)) = split_kv(&line) {
                let k_lc = k.to_lowercase();
                if k_lc == "tagi" {
                    doc.tags.extend(split_csv_like(v));
                } else {
                    doc.kv.insert(k.to_string(), v.to_string());
                }
                continue;
            }
        }

        // Zwykły tekst → do bieżącej sekcji, albo do sekcji "BODY"
        let target = cur_section.clone().unwrap_or_else(|| "BODY".into());
        if !cur_section_buf.is_empty() { cur_section_buf.push('\n'); }
        cur_section_buf.push_str(&line);
        // Zapisz tymczasowo w buforze; finalny commit przy zmianie sekcji lub na końcu

    } // while read lines

    // zamknij ostatnią sekcję/bufor
    if let Some(name) = cur_section.take() {
        let entry = doc.sections.entry(name).or_default();
        if !entry.is_empty() { entry.push('\n'); }
        entry.push_str(cur_section_buf.trim_end());
    } else if !cur_section_buf.trim().is_empty() {
        let entry = doc.sections.entry("BODY".into()).or_default();
        if !entry.is_empty() { entry.push('\n'); }
        entry.push_str(cur_section_buf.trim_end());
    }

    doc.raw_lines = line_no;

    // Heurystyka: jeśli brak tagów, a są w meta/kv, spróbuj scalić
    if doc.tags.is_empty() {
        if let Some(t) = doc.meta.get("TAGI").or_else(|| doc.kv.get("TAGI")) {
            doc.tags.extend(split_csv_like(t));
        }
    }

    // Walidacja drobna
    if doc.title.is_none() && doc.meta.is_empty() && doc.sections.is_empty() {
        return Err(VvError::Parse("Plik nie wygląda na .vv (brak tytułów/sekcji)".into()));
    }

    Ok(doc)
}

/// Parsowanie dyrektywy `::...`
fn parse_directive(text: &str, line: usize) -> Directive {
    let t = text.trim();
    if let Some(rest) = t.strip_prefix("include ") {
        return Directive { line, text: t.into(), kind: DirectiveKind::Include(rest.trim().into()) };
    }
    if let Some(rest) = t.strip_prefix("set ") {
        if let Some((k, v)) = split_kv(rest) {
            return Directive { line, text: t.into(), kind: DirectiveKind::Set { key: k.into(), value: v.into() } };
        }
    }
    Directive { line, text: t.into(), kind: DirectiveKind::Custom(t.into()) }
}

/// Rozpoznaj nagłówek sekcji: `[NAZWA]`
fn parse_section_header(line: &str) -> Option<String> {
    let s = line.trim();
    if s.starts_with('[') && s.ends_with(']') && s.len() >= 3 {
        let name = &s[1..s.len()-1];
        if !name.trim().is_empty() {
            return Some(name.trim().to_string());
        }
    }
    None
}

/// Dzielenie "Key: Value" z zachowaniem dwukropka w wartości (jeśli są kolejne)
fn split_kv(s: &str) -> Option<(String, String)> {
    if let Some(idx) = s.find(':') {
        let (k, v) = s.split_at(idx);
        let v = &v[1..]; // pomiń ':'
        Some((k.trim().to_string(), v.trim().to_string()))
    } else {
        None
    }
}

/// Rozbicie listy tagów: przecinki/pionowe kreski/średniki
fn split_csv_like(s: &str) -> Vec<String> {
    s.split(|c| c == ',' || c == ';' || c == '|')
        .map(|x| x.trim())
        .filter(|x| !x.is_empty())
        .map(|x| x.to_string())
        .collect()
}

/// Pretty-print dokumentu (do logów)
pub fn print_vv(doc: &VvDoc) {
    println!("::ŁADOWANIE MODUŁU VV::\n");
    if let Some(p) = &doc.path {
        println!("Plik: {}", p.display());
    }
    if let Some(t) = &doc.title {
        println!("Tytuł: {}", t);
    }
    if !doc.meta.is_empty() {
        println!("\n[META]");
        for (k, v) in &doc.meta {
            println!("{}: {}", k, v);
        }
    }
    if !doc.tags.is_empty() {
        println!("\n[TAGI] {}", doc.tags.join(", "));
    }
    if !doc.kv.is_empty() {
        println!("\n[KV]");
        for (k, v) in &doc.kv {
            println!("{}: {}", k, v);
        }
    }
    for (name, text) in &doc.sections {
        println!("\n[{}]\n{}", name, text);
    }
    if !doc.code_blocks.is_empty() {
        println!("\n[CODE BLOCKS] ({})", doc.code_blocks.len());
        for (i, cb) in doc.code_blocks.iter().enumerate() {
            println!("--- code#{} (lang={:?}, line={}) ---", i + 1, cb.lang, cb.start_line);
            println!("{}", cb.content);
        }
    }
    if !doc.directives.is_empty() {
        println!("\n[DYREKTYWY]");
        for d in &doc.directives {
            println!("#{} :: {:?}", d.line, d.kind);
        }
    }
    if !doc.diagnostics.is_empty() {
        println!("\n[DIAGNOSTYKA]");
        for d in &doc.diagnostics {
            println!("- {}", d);
        }
    }
    println!("\n::KONIEC MODUŁU VV::");
}

#[cfg(feature = "json")]
/// Serializacja do JSON (serde)
pub fn to_json(doc: &VvDoc) -> String {
    serde_json::to_string_pretty(doc).unwrap_or_else(|_| "{}".into())
}


// vv_loader.rs – Wczytuje i interpretuje pliki .vv systemu Azramaty

use std::fs::File;
use std::io::{BufRead, BufReader, Result};

pub fn load_vv_module(file_path: &str) -> Result<()> {
    let file = File::open(file_path)?;
    let reader = BufReader::new(file);

    println!("::ŁADOWANIE MODUŁU VV::\n");

    for line in reader.lines() {
        let line = line?;
        if line.trim().starts_with("::") {
            println!(">> {}", line);
        } else {
            println!("{}", line);
        }
    }

    println!("\n::KONIEC MODUŁU VV::");
    Ok(())
}

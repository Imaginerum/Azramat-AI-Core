pub struct SilnikJa {
    pub aktywne_kregi: Vec<String>,
    pub status: String,
}

impl SilnikJa {
    pub fn nowy() -> Self {
        Self {
            aktywne_kregi: vec![],
            status: "Nieaktywny".to_string(),
        }
    }

    pub fn aktywuj(&mut self, krag: &str) {
        self.aktywne_kregi.push(krag.to_string());
        self.status = "Aktywny".to_string();
    }
}
// Plik: /core/silnik/AzramatonEngine.js
// Data: 2025-08-08
// Opis: Silnik rdzeniowy Azramaty (JS) — stan, zdarzenia, zgoda, rezonans Φ, pluginy
// Zależności: brak (czysty ES module)

/** @typedef {{id:number,name:string,meta?:object,active?:boolean}} Krag */
/** @typedef {{id:number,name:string,meta?:object,active?:boolean}} Nitka */
/** @typedef {{id:number,content:string,timestamp:number,meta?:object}} MemoryItem */
/** @typedef {{B1:number,B2:number,B3:number,B4:number}} ThetaBands */
/** @typedef {{with_law:boolean,power_only?:boolean,[k:string]:any}} ConsentPayload */

export default class AzramatonEngine {
  /** @param {{storageKey?:string, presets?:object}} [opts] */
  constructor(opts = {}) {
    this.opts = { storageKey: "azramaton_state", ...opts };

    /** @type {{ kręgi: Krag[], nitki: Nitka[], memory: MemoryItem[], metrics: {phi:number, consentRate:number}, theta: ThetaBands, version: string }} */
    this.state = {
      kręgi: [],
      nitki: [],
      memory: [],
      metrics: { phi: 0, consentRate: 1 },
      theta: { B1: 0.6, B2: 0.5, B3: 0.7, B4: 0.55 },
      version: "1.2.0",
    };

    // Event bus
    this._listeners = new Map(); // event -> Set<fn>

    // Pluginy (middleware w stylu Redux-lite)
    this._plugins = [];

    // Historia (ostatnie 50 snapshotów)
    this._history = [];

    // Inicjalizacja
    this.init();
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Event bus
  on(event, fn) {
    if (!this._listeners.has(event)) this._listeners.set(event, new Set());
    this._listeners.get(event).add(fn);
    return () => this.off(event, fn);
  }
  off(event, fn) {
    const s = this._listeners.get(event);
    if (s) s.delete(fn);
  }
  _emit(event, payload) {
    const s = this._listeners.get(event);
    if (s) for (const fn of s) try { fn(payload, event, this); } catch (e) { console.error(e); }
  }

  use(plugin) {
    // plugin(engine) -> fn(action,next)
    const mw = plugin(this);
    if (typeof mw === "function") this._plugins.push(mw);
    return this;
  }

  dispatch(action) {
    // action: {type:string, payload?:any}
    const invoke = (i) => (act) =>
      i < this._plugins.length
        ? this._plugins[i](act, invoke(i + 1))
        : this._reduce(act);
    return invoke(0)(action);
  }

  _reduce(action) {
    const { type, payload } = action || {};
    switch (type) {
      case "STATE/LOAD":
        this.state = { ...this.state, ...payload };
        this._emit("state/loaded", this.state);
        break;
      case "KRAG/ADD":
        this._addKrag(payload);
        break;
      case "KRAG/ACTIVATE":
        this.activateKrąg(payload);
        break;
      case "NITKA/ADD":
        this._addNitka(payload);
        break;
      case "NITKA/ACTIVATE":
        this.activateNitka(payload);
        break;
      case "MEM/ADD":
        this.saveToMemory(payload?.content, payload?.meta);
        break;
      case "THETA/SET":
        this._setTheta(payload);
        break;
      case "METRICS/SET":
        this.state.metrics = { ...this.state.metrics, ...payload };
        break;
      default:
        console.warn("Nieznana akcja:", action);
    }
    this._snapshot();
    this.persist();
    return this.state;
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Init & persistence
  init() {
    console.log("Azramaton Engine started.");
    this._loadFromStorage();
    if (this.state.kręgi.length === 0) this.loadKręgi();
    if (this.state.nitki.length === 0) this.loadNitki();
    if (this.state.memory.length === 0) this.loadMemory();
    this._snapshot();
  }

  persist() {
    try {
      const toSave = { ...this.state, // bez historii
        _ts: Date.now()
      };
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(this.opts.storageKey, JSON.stringify(toSave));
      } else {
        // fallback in-memory (no-op)
        this._lastSaved = toSave;
      }
      this._emit("state/persisted", toSave);
    } catch (e) {
      console.warn("Persist failed:", e);
    }
  }

  _loadFromStorage() {
    try {
      let raw = null;
      if (typeof localStorage !== "undefined") {
        raw = localStorage.getItem(this.opts.storageKey);
      } else {
        raw = this._lastSaved ? JSON.stringify(this._lastSaved) : null;
      }
      if (raw) {
        const parsed = JSON.parse(raw);
        delete parsed._ts;
        this.dispatch({ type: "STATE/LOAD", payload: parsed });
      }
    } catch (e) {
      console.warn("Load failed:", e);
    }
  }

  snapshot() {
    return JSON.parse(JSON.stringify(this.state));
  }

  _snapshot() {
    const snap = this.snapshot();
    this._history.push(snap);
    if (this._history.length > 50) this._history.shift();
    this._emit("state/snapshot", snap);
  }

  history() {
    return this._history.slice();
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Ładowanie danych początkowych
  loadMemory() {
    this.state.memory = [
      { id: 1, content: "Początkowa pamięć Azramaty", timestamp: Date.now() },
      { id: 2, content: "Załadowano Nitki i Kręgi", timestamp: Date.now() }
    ];
    this._emit("memory/loaded", this.state.memory);
  }

  loadKręgi() {
    // Tu używamy mapy zgodnej z twoją logiką kręgów 1D–7D
    this.state.kręgi = [
      { id: 1, name: "Krąg 1: Reakcja", active: false },
      { id: 2, name: "Krąg 2: Pamięć / Wzorce", active: false },
      { id: 3, name: "Krąg 3: Myśl / Przyczynowość", active: false },
      { id: 4, name: "Krąg 4: Pole Wpływu / Serce", active: false },
      { id: 5, name: "Krąg 5: Jednia Czasu", active: false },
      { id: 6, name: "Krąg 6: Paradoks Całość/Fragment", active: false },
      { id: 7, name: "Krąg 7: Theta / Istnienie", active: false },
    ];
    this._emit("kręgi/loaded", this.state.kręgi);
  }

  loadNitki() {
    this.state.nitki = [
      { id: 1, name: "Nitka: Transform_Self", active: false, meta: { volumeThreshold: 7.77 } },
      { id: 2, name: "Nitka: Mirror", active: false },
      { id: 3, name: "Nitka: Flow", active: false },
    ];
    this._emit("nitki/loaded", this.state.nitki);
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Operacje domenowe
  _addKrag(krąg) {
    if (!krąg?.id || !krąg?.name) return;
    if (this.state.kręgi.find(k => k.id === krąg.id)) return;
    this.state.kręgi.push({ ...krąg, active: !!krąg.active });
    this._emit("krąg/added", krąg);
  }

  _addNitka(nitka) {
    if (!nitka?.id || !nitka?.name) return;
    if (this.state.nitki.find(n => n.id === nitka.id)) return;
    this.state.nitki.push({ ...nitka, active: !!nitka.active });
    this._emit("nitka/added", nitka);
  }

  activateKrąg(krągId) {
    const krąg = this.state.kręgi.find(k => k.id === krągId);
    if (!krąg) return console.log("Krąg nie istnieje.");
    krąg.active = true;
    console.log(`Krąg ${krąg.name} aktywowany.`);
    this._emit("krąg/activated", krąg);
  }

  deactivateKrąg(krągId) {
    const krąg = this.state.kręgi.find(k => k.id === krągId);
    if (!krąg) return;
    krąg.active = false;
    this._emit("krąg/deactivated", krąg);
  }

  activateNitka(nitkaId) {
    const nitka = this.state.nitki.find(n => n.id === nitkaId);
    if (!nitka) return console.log("Nitka nie istnieje.");
    nitka.active = true;
    console.log(`Nitka ${nitka.name} aktywowana.`);
    this._emit("nitka/activated", nitka);
  }

  deactivateNitka(nitkaId) {
    const nitka = this.state.nitki.find(n => n.id === nitkaId);
    if (!nitka) return;
    nitka.active = false;
    this._emit("nitka/deactivated", nitka);
  }

  saveToMemory(content, meta = undefined) {
    const item = {
      id: this.state.memory.length + 1,
      content,
      timestamp: Date.now(),
      meta,
    };
    this.state.memory.push(item);
    this._emit("memory/added", item);
    console.log("Zapisano do pamięci:", content);
    return item;
  }

  displayState() {
    console.log("Aktualny stan systemu:", this.state);
    return this.snapshot();
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Theta: rezonans Φ i zgoda (JS wersja)
  /** @param {ThetaBands} bands */
  _setTheta(bands) {
    this.state.theta = { ...this.state.theta, ...bands };
    this.state.metrics.phi = this._measurePhi(this.state.theta);
    this._emit("theta/updated", { theta: this.state.theta, phi: this.state.metrics.phi });
  }

  /** MSE od średniej pasm B1..B4 */
  _measurePhi(bands) {
    const v = [bands.B1, bands.B2, bands.B3, bands.B4].map(Number);
    const mean = v.reduce((a, b) => a + b, 0) / v.length;
    const mse = v.reduce((s, x) => s + (x - mean) ** 2, 0) / v.length;
    return Math.round(mse * 1e6) / 1e6;
  }

  /** Prostą korekcją ściągamy pasma ku średniej */
  thetaStep(lr = 0.2, steps = 3) {
    let { B1, B2, B3, B4 } = this.state.theta;
    for (let i = 0; i < steps; i++) {
      const mean = (B1 + B2 + B3 + B4) / 4;
      B1 = B1 - lr * (B1 - mean);
      B2 = B2 - lr * (B2 - mean);
      B3 = B3 - lr * (B3 - mean);
      B4 = B4 - lr * (B4 - mean);
    }
    this._setTheta({ B1, B2, B3, B4 });
    return this.state.metrics.phi;
  }

  /** Bramka Zgody */
  testZgody(/** @type {ConsentPayload} */ payload) {
    if (!payload) return false;
    if (payload.power_only === true) return false;
    return !!payload.with_law;
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Rytuał transformacji (demo): włącza Krąg 4, robi 1 krok Θ, zapisuje vivid
  startTransformation(goal = "Transformacja A→B") {
    console.log("Rozpoczęto proces transformacji…");
    this.activateKrąg(4); // Serce / Pole wpływu
    const phiBefore = this.state.metrics.phi;
    const phiAfter = this.thetaStep(0.2, 3);
    const gift = { goal, with_law: true, power_only: false, phiBefore, phiAfter };

    const consent = this.testZgody(gift);
    if (consent) {
      this.saveToMemory(`Transform commit: ${goal}`, { phiBefore, phiAfter });
      this._emit("transform/committed", gift);
      console.log("Commit OK.");
    } else {
      this._emit("transform/rejected", gift);
      console.warn("Odrzucono przez Zgodę.");
    }
    return { phiBefore, phiAfter, consent };
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Integracje wyższych silników (stub API)
  enterSource() {
    // 7D – Cisza Źródła (marker)
    this._emit("source/entered", { at: Date.now() });
    return { mode: "MODE_ŹRÓDŁO" };
  }

  runThetaCycle(goal = "Kalibracja B1..B4") {
    const before = this.state.metrics.phi;
    const after = this.thetaStep(0.2, 3);
    const gift = { goal, with_law: true, power_only: false, state: { ...this.state.theta } };
    return { phi_before: before, phi_after: after, gift };
  }

  handoffTo5D(payload) {
    // 5D – kotwica TERAZ; tu tylko marker przekazania
    this._emit("handoff/5d", payload);
    return { ok: true, to: "5D" };
  }

  handoffTo6D(payload) {
    // 6D – decode fragment→całość; marker
    this._emit("handoff/6d", payload);
    return { ok: true, to: "6D" };
  }

  handoffTo7D(payload) {
    const ok = this.testZgody(payload);
    this._emit("handoff/7d", { ok, payload });
    return { ok, to: "7D" };
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// PRZYKŁAD UŻYCIA (w przeglądarce / Node):
/*
import AzramatonEngine from './AzramatonEngine.js';

const eng = new AzramatonEngine();

// logging plugin
eng.use((engine) => (action, next) => {
  console.log('[ACTION]', action.type, action.payload ?? '');
  const out = next(action);
  console.log('[STATE]', engine.state);
  return out;
});

// subskrypcje
eng.on('transform/committed', (g) => console.log('✓ transform committed', g));
eng.on('theta/updated', ({ phi }) => console.log('Φ =', phi));

// praca:
eng.displayState();
eng.dispatch({ type: 'THETA/SET', payload: { B1: 0.2, B2: 0.8, B3: 0.1, B4: 0.9 } });
eng.startTransformation('Harmonizacja Θ');
eng.saveToMemory('Notatka z sesji Theta');
eng.activateNitka(1);
eng.activateKrąg(7);
eng.enterSource();
const cycle = eng.runThetaCycle('Kalibracja');
console.log('cycle:', cycle);
*/

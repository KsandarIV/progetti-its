/**
 * ============================================================
 * ODYSSEY Engine v4 — CONFIGURAZIONE GLOBALE
 * ============================================================
 * Schema: 24 colonne (A–X) — Diario del Pendolare
 * Modificato: 2026-05-28
 * 
 * CHANGELOG v4:
 *  - Corretto mapping TRIP_TYPE (ora col 4/D = tipo_viaggio)
 *  - Corretto mapping CAMBI (ora col 7/G = cambi)
 *  - Aggiunte colonne mancanti: DAY_TYPE, ROUTE, TRANSPORT,
 *    DELAY_REASON, CROWDING, MOOD, NOTES
 *  - Aggiunti valori dropdown per Web App form
 * ============================================================
 */

const CONFIG = {
  VERSION: "4.0.0",

  // ── Fogli ──────────────────────────────────────────────────
  SHEET_DATA:    "dataset",
  SHEET_PALETTE: "PALETTE",

  // ── Mapping Colonne (1-indexed) ────────────────────────────
  // Ordine: Metadati viaggio → Orari → Calcolati → Soggettivi
  COLS: {
    DATE:          1,   // A  data                (Date)
    DAY:           2,   // B  giorno              (String, auto)
    DAY_TYPE:      3,   // C  tipo_giorno         (String)
    TRIP_TYPE:     4,   // D  tipo_viaggio        (String)
    ROUTE:         5,   // E  percorso_A—B        (String)
    TRANSPORT:     6,   // F  mezzo               (String)
    CAMBI:         7,   // G  cambi               (Number)
    H_PREV:        8,   // H  ora_prevista        (String HH:mm)
    I_EFF:         9,   // I  ora_effettiva       (String HH:mm)
    J_RIT:         10,  // J  ritardo             (String, calc)
    DELAY_REASON:  11,  // K  motivo_ritardo      (String)
    L_ARR:         12,  // L  ora_arrivo          (String HH:mm)
    M_DUR:         13,  // M  durata_viaggio      (Number, calc)
    N_PROS:        14,  // N  ora_prossimo_mezzo  (String HH:mm)
    O_ATT:         15,  // O  durata_attesa       (Number, calc)
    P_COINC:       16,  // P  coincidenza_persa   (Boolean, calc)
    Q_MANC:        17,  // Q  tempo_manc_coinc    (String, calc)
    WEATHER:       18,  // R  meteo               (String, auto)
    CROWDING:      19,  // S  affollamento        (String array)
    SEAT_AVAIL:    20,  // T  seduta_disponibile  (Boolean)
    SITTING:       21,  // U  seduto              (Boolean)
    AUDIO:         22,  // V  cuffiette           (String %)
    MOOD:          23,  // W  umore               (String)
    NOTES:         24   // X  Imprevisti_e_note   (String)
  },

  // ── Geolocalizzazione (Roma — Open-Meteo) ─────────────────
  GEO: { LAT: 41.8919, LON: 12.5113 },

  // ── Localizzazione ─────────────────────────────────────────
  GIORNI: ["Domenica", "Lunedì", "Martedì", "Mercoledì",
           "Giovedì", "Venerdì", "Sabato"],

  // ── Valori Dropdown per Web App ────────────────────────────
  TRIP_TYPES: ["andata", "ritorno", "andata personalizzata", "ritorno personalizzato", "altro"],
  DAY_TYPES:  ["feriale", "festivo", "sciopero"],
  AUDIO_VALUES: ["0%", "25%", "50%", "75%", "100%"],

  MOOD_OPTIONS: [
    "Neutro", "Nervoso", "Ansioso", "Frustrato",
    "Stanco", "Sonno", "Rassegnato", "Arrabiato", "Felice"
  ],

  // ── Scala Affollamento 1–5 (+ modificatori ! e /) ─────────
  // 1 = Tutti seduti
  // 2 = Posti quasi occupati, spostamento libero
  // 3 = Spostamento tra vagoni nonostante affollamento
  // 4 = Impossibile spostarsi tra vagoni
  // 5 = Contatto fisico inevitabile
  // 5! = Oltre il livello 5 (schiacciati)
  // 3/4 = Incerto tra due livelli
  CROWDING_SCALE: [1, 2, 3, 4, 5],

  // ── Mezzi di Trasporto Frequenti ───────────────────────────
  TRANSPORT_OPTIONS: [
    "Piedi", "Metromare", "Metro A", "Metro B", "Metro C",
    "Bus Cotral", "Bus N.4", "Bus N.5", "Bus ATAC N.020",
    "Treno", "Auto"
  ]
};

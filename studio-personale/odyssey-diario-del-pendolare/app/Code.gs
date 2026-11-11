/**
 * ============================================================
 * ODYSSEY Engine v4 — WEB APP ENTRY POINT
 * ============================================================
 * Serve la Web App via HtmlService con template modulari.
 * File client inclusi tramite <?!= include('filename'); ?>
 * ============================================================
 */

/**
 * Entry point della Web App.
 * Restituisce la pagina HTML renderizzata con meta mobile.
 */
function doGet() {
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('🚇 Diario del Pendolare')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Helper per inclusione modulare di file HTML.
 * Usato nei template con: <?!= include('CSS'); ?>
 * @param {string} filename - Nome del file HTML (senza estensione)
 * @returns {string} Contenuto HTML del file
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * API esposta al client per inizializzare il form.
 * Restituisce la configurazione dropdown e i valori di default.
 * Chiamata una sola volta al caricamento della pagina.
 * @returns {Object} Configurazione per il form client-side
 */
function getFormConfig() {
  const now = new Date();
  const dayName = CONFIG.GIORNI[now.getDay()];
  const dayOfWeek = now.getDay();

  // Determina tipo giorno (0=Dom, 6=Sab)
  let dayType = "feriale";
  if (dayOfWeek === 0) dayType = "festivo";
  else if (dayOfWeek === 6) dayType = "prefestivo";

  // ── Robust date formatting: usa timezone del foglio se accessibile, altrimenti fallback ──
  let todayStr;
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    if (ss) {
      todayStr = Utilities.formatDate(now, ss.getSpreadsheetTimeZone(), "dd.MM.yyyy");
    } else {
      todayStr = formatDateFallback(now);
    }
  } catch (e) {
    // Foglio non accessibile da questo contesto (permessi, scope, anonimo).
    // L'app DEVE comunque avviarsi per mostrare l'interfaccia.
    Logger.log("getFormConfig: getActiveSpreadsheet non disponibile, uso fallback. " + e);
    todayStr = formatDateFallback(now);
  }

  return {
    version:          CONFIG.VERSION,
    today:            todayStr,
    dayName:          dayName,
    dayType:          dayType,
    tripTypes:        CONFIG.TRIP_TYPES,
    dayTypes:         CONFIG.DAY_TYPES,
    audioValues:      CONFIG.AUDIO_VALUES,
    moodOptions:      CONFIG.MOOD_OPTIONS,
    crowdingScale:    CONFIG.CROWDING_SCALE,
    transportOptions: CONFIG.TRANSPORT_OPTIONS
  };
}

/**
 * Fallback locale per formattare una data in dd.MM.yyyy
 * usando il fuso orario Europe/Rome (sempre presente nella CONFIG).
 * Usato quando SpreadsheetApp non è accessibile.
 */
function formatDateFallback(d) {
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  return `${dd}.${mm}.${d.getFullYear()}`;
}

/**
 * API esposta al client per ottenere percorsi e fermate storici.
 * Legge le ultime N righe per estrarre valori unici di autocomplete.
 * @param {number} limit - Numero massimo di righe da analizzare (default 200)
 * @returns {Object} Valori unici per autocomplete
 */
function getAutocompleteData(limit) {
  const n = limit || 200;
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_DATA);
  if (!sheet) return { routes: [], transports: [], moods: [] };

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return { routes: [], transports: [], moods: [] };

  const startRow = Math.max(2, lastRow - n + 1);
  const numRows = lastRow - startRow + 1;
  const data = sheet.getRange(startRow, 1, numRows, CONFIG.COLS.NOTES).getValues();

  const routeSet     = new Set();
  const transportSet = new Set();
  const moodSet      = new Set();

  data.forEach(row => {
    const route     = row[CONFIG.COLS.ROUTE - 1];
    const transport = row[CONFIG.COLS.TRANSPORT - 1];
    const mood      = row[CONFIG.COLS.MOOD - 1];

    if (route && route.toString().trim())     routeSet.add(route.toString().trim());
    if (transport && transport.toString().trim()) transportSet.add(transport.toString().trim());
    if (mood && mood.toString().trim()) {
      // Splitta mood multipli (es. "Neutro Nervoso" → ["Neutro", "Nervoso"])
      mood.toString().trim().split(/\s+/).forEach(m => moodSet.add(m));
    }
  });

  return {
    routes:     Array.from(routeSet).sort(),
    transports: Array.from(transportSet).sort(),
    moods:      Array.from(moodSet).sort()
  };
}

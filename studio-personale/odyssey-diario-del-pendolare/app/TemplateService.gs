/**
 * ============================================================
 * ODYSSEY Engine v4 — TEMPLATE SERVICE (PERCORSI FREQUENTI)
 * ============================================================
 * Estrae dinamicamente dal dataset i percorsi più frequenti
 * con auto-apprendimento dell'orario previsto abituale.
 * ============================================================
 */

/**
 * Ritorna i 5 percorsi più utilizzati con i relativi dettagli pre-compilati.
 * Analizza le ultime 300 tratte inserite per auto-apprendere le abitudini.
 * 
 * @returns {Array<Object>} Lista dei percorsi frequenti per la UI
 */
function getFrequentTemplates() {
  // ── Guard: foglio non accessibile → array vuoto (no crash) ──
  let ss, sheet;
  try {
    ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss) return [];
    sheet = ss.getSheetByName(CONFIG.SHEET_DATA);
  } catch (e) {
    Logger.log("getFrequentTemplates: accesso al foglio negato. " + e);
    return [];
  }
  if (!sheet) return [];

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];

  // Leggi ultime 300 righe
  const startRow = Math.max(2, lastRow - 300 + 1);
  const numRows = lastRow - startRow + 1;
  
  const data = sheet.getRange(startRow, 1, numRows, CONFIG.COLS.NOTES).getValues();
  const frequencyMap = {};

  data.forEach(row => {
    const route = row[CONFIG.COLS.ROUTE - 1];
    const transport = row[CONFIG.COLS.TRANSPORT - 1];
    const cambi = row[CONFIG.COLS.CAMBI - 1];
    const tripType = row[CONFIG.COLS.TRIP_TYPE - 1];
    const hPrev = row[CONFIG.COLS.H_PREV - 1];

    if (!route || !transport) return;

    const key = `${route}||${transport}||${cambi}||${tripType}`;
    if (!frequencyMap[key]) {
      frequencyMap[key] = {
        route: route,
        transport: transport,
        cambi: cambi || 0,
        tripType: tripType || "andata",
        count: 0,
        times: {}
      };
    }
    frequencyMap[key].count++;
    if (hPrev && hPrev.toString().includes(':')) {
      frequencyMap[key].times[hPrev] = (frequencyMap[key].times[hPrev] || 0) + 1;
    }
  });

  // Ordina per frequenza decrescente
  const sorted = Object.values(frequencyMap).sort((a, b) => b.count - a.count);
  
  // Prendi i primi 5 e calcola l'orario più probabile (la moda degli orari previsti)
  return sorted.slice(0, 5).map(item => {
    let bestTime = "";
    let maxTimeCount = 0;
    for (const [time, count] of Object.entries(item.times)) {
      if (count > maxTimeCount) {
        maxTimeCount = count;
        bestTime = time;
      }
    }
    
    return {
      name: `${item.route} (${item.transport})`,
      route: item.route,
      transport: item.transport,
      cambi: item.cambi,
      tripType: item.tripType,
      hPrev: bestTime
    };
  });
}

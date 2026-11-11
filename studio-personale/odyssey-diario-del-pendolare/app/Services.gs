/**
 * ============================================================
 * ODYSSEY Engine v4 — SERVIZI ESTERNI & FORMATTAZIONE
 * ============================================================
 * Modulo servizi: Open-Meteo API con CacheService, palette HEX,
 * validazione audio.
 * 
 * CHANGELOG v4:
 *  - Nessuna modifica strutturale (colonne meteo/audio invariate)
 *  - Commenti allineati al nuovo schema
 * ============================================================
 */

// ============================================================
// VALIDAZIONE AUDIO (V = col 22)
// ============================================================

function strictAudioValidation(val) {
  if (val === undefined || val === null || val === "") return "0%";
  const clean = val.toString().replace('%', '').trim();
  return ["0", "25", "50", "75", "100"].includes(clean) ? `${clean}%` : "404";
}

// ============================================================
// PALETTE — Colorazione automatica #HEX
// ============================================================

function applyHexPalette(range, hexCode) {
  let r, g, b;
  if (hexCode.length === 4) {
    r = parseInt(hexCode[1] + hexCode[1], 16);
    g = parseInt(hexCode[2] + hexCode[2], 16);
    b = parseInt(hexCode[3] + hexCode[3], 16);
  } else {
    r = parseInt(hexCode.substring(1, 3), 16);
    g = parseInt(hexCode.substring(3, 5), 16);
    b = parseInt(hexCode.substring(5, 7), 16);
  }
  const contrastColor = ((r * 299 + g * 587 + b * 114) / 1000 >= 128)
    ? '#000000' : '#FFFFFF';

  range.setBackground(hexCode).setFontColor(contrastColor);
  range.offset(0, 1)
    .setValue(contrastColor)
    .setFontColor(hexCode)
    .setBackground(contrastColor);
}

// ============================================================
// METEO STORICO — Open-Meteo Archive + CacheService
// ============================================================

/**
 * Recupera condizioni meteo storiche con caching a 2h.
 * Chiave cache: weather_{data}_{ora}
 * Condizioni WMO: 0=Sereno, 1-3=Nuvoloso, 4+=Pioggia/Avverso
 */
function fetchWeatherHistorical(sheet, row) {
  const weatherCell = sheet.getRange(row, CONFIG.COLS.WEATHER);
  const dateVal     = sheet.getRange(row, CONFIG.COLS.DATE).getValue();

  // Priorità: ora effettiva (I), fallback ora arrivo (L)
  let timeVal = sheet.getRange(row, CONFIG.COLS.I_EFF)
                     .getValue().toString().trim().split(' ')[0];
  if (!timeVal.includes(':')) {
    timeVal = sheet.getRange(row, CONFIG.COLS.L_ARR)
                   .getValue().toString().trim().split(' ')[0];
  }

  if (!dateVal || !(dateVal instanceof Date) || !timeVal.includes(':')) return;

  try {
    const tz            = SpreadsheetApp.getActiveSpreadsheet().getSpreadsheetTimeZone();
    const formattedDate = Utilities.formatDate(dateVal, tz, "yyyy-MM-dd");
    const targetHour    = parseInt(timeVal.split(':')[0], 10);

    // ── Cache Check ──────────────────────────────────────────
    const cacheKey = `weather_${formattedDate}_H${targetHour}`;
    const cache    = CacheService.getScriptCache();
    const cached   = cache.get(cacheKey);

    if (cached) {
      weatherCell.setValue(cached);
      return;
    }

    // ── API Call ─────────────────────────────────────────────
    const url = `https://archive-api.open-meteo.com/v1/archive`
              + `?latitude=${CONFIG.GEO.LAT}&longitude=${CONFIG.GEO.LON}`
              + `&start_date=${formattedDate}&end_date=${formattedDate}`
              + `&hourly=temperature_2m,weathercode`;

    const res = UrlFetchApp.fetch(url, { method: "get", muteHttpExceptions: true });
    if (res.getResponseCode() !== 200) return;

    const json = JSON.parse(res.getContentText());
    if (!json.hourly || !json.hourly.temperature_2m) return;

    const temp      = json.hourly.temperature_2m[targetHour];
    const wcode     = json.hourly.weathercode[targetHour];
    const condition = wcode === 0 ? "Sereno"
                    : wcode <= 3  ? "Nuvoloso"
                    :               "Pioggia/Avverso";
    const resultStr = `${condition}, ${temp}°C`;

    // Salva in cache per 2 ore (7200s)
    cache.put(cacheKey, resultStr, 7200);
    weatherCell.setValue(resultStr);

  } catch (err) {
    Logger.log(`fetchWeatherHistorical errore riga ${row}: ${err}`);
  }
}

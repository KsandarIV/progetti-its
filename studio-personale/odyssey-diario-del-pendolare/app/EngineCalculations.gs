/**
 * ============================================================
 * ODYSSEY Engine v4 — CALCOLI MATRICIALI E VETTORIALI
 * ============================================================
 * Ricalcolo batch in-memory + utility orari.
 * 
 * CHANGELOG v4:
 *  - CAMBI ora referenziato da CONFIG.COLS.CAMBI (col 7/G)
 *  - Alert UI sostituito con try/catch per compatibilità background
 *  - Placeholder meteo gestito nel batch
 * ============================================================
 */

// ============================================================
// RICALCOLO GLOBALE (Batch In-Memory)
// ============================================================

function ricalcolaTutto() {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.SHEET_DATA);
  if (!sheet) return;

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  const startRow = 2;
  const numRows  = lastRow - startRow + 1;
  const numCols  = sheet.getLastColumn();
  const range    = sheet.getRange(startRow, 1, numRows, numCols);
  const data     = range.getValues();

  const now          = new Date();
  const currentYear  = now.getFullYear();
  const currentMonth = now.getMonth();

  for (let i = 0; i < data.length; i++) {
    const row = data[i];

    // ── 1. Sanificazione Data + Giorno ────────────────────────
    const rawDate = row[CONFIG.COLS.DATE - 1];
    if (rawDate && !isNaN(rawDate) && rawDate.toString().trim().length <= 2) {
      const day = parseInt(rawDate, 10);
      if (day >= 1 && day <= 31) {
        const newDate = new Date(currentYear, currentMonth, day);
        row[CONFIG.COLS.DATE - 1] = newDate;
        row[CONFIG.COLS.DAY  - 1] = CONFIG.GIORNI[newDate.getDay()];
      }
    } else if (rawDate instanceof Date) {
      row[CONFIG.COLS.DAY - 1] = CONFIG.GIORNI[rawDate.getDay()];
    }

    // ── 2. Normalizzazione Orari (H, I, L, N) ────────────────
    [CONFIG.COLS.H_PREV, CONFIG.COLS.I_EFF, CONFIG.COLS.L_ARR, CONFIG.COLS.N_PROS]
      .forEach(c => { row[c - 1] = formatAndValidateTimeArray(row[c - 1]); });

    const hPrev = row[CONFIG.COLS.H_PREV - 1].toString();
    const iEff  = row[CONFIG.COLS.I_EFF  - 1].toString();
    const lArr  = row[CONFIG.COLS.L_ARR  - 1].toString();
    const nPros = row[CONFIG.COLS.N_PROS - 1].toString();

    // ── 3. Ritardo Vettoriale J = I - H ───────────────────────
    if (hPrev && iEff && hPrev.includes(':') && iEff.includes(':')) {
      row[CONFIG.COLS.J_RIT - 1] = computeTimeDiffArray(hPrev, iEff);
    }

    // ── 4. Durata Viaggio M = L - I ──────────────────────────
    if (iEff && lArr && iEff.includes(':') && lArr.includes(':')) {
      row[CONFIG.COLS.M_DUR - 1] = computeSingleTimeDiff(iEff, lArr);
    } else {
      row[CONFIG.COLS.M_DUR - 1] = "";
    }

    // ── 5. Coincidenza Persa P/Q (vettoriale) ────────────────
    if (lArr && nPros && lArr.includes(':') && nPros.includes(':')) {
      const { persa, tempi } = computeMancataCoincidenzaArray(nPros, lArr);
      row[CONFIG.COLS.P_COINC - 1] = persa;
      row[CONFIG.COLS.Q_MANC  - 1] = tempi;
    } else {
      row[CONFIG.COLS.P_COINC - 1] = false;
      row[CONFIG.COLS.Q_MANC  - 1] = "";
    }

    // ── 6. Durata Attesa O = I(riga+1) - L(riga corrente) ───
    const cambi = parseInt(row[CONFIG.COLS.CAMBI - 1], 10);
    if (i < data.length - 1 && !isNaN(cambi) && cambi > 0) {
      const nextRow = data[i + 1];
      if (_sameDate(row[CONFIG.COLS.DATE - 1], nextRow[CONFIG.COLS.DATE - 1]) &&
          row[CONFIG.COLS.TRIP_TYPE - 1] === nextRow[CONFIG.COLS.TRIP_TYPE - 1]) {
        const nextIEff = formatAndValidateTimeArray(nextRow[CONFIG.COLS.I_EFF - 1]);
        if (lArr && nextIEff && lArr.includes(':') && nextIEff.includes(':')) {
          row[CONFIG.COLS.O_ATT - 1] = computeSingleTimeDiff(lArr, nextIEff);
        } else {
          row[CONFIG.COLS.O_ATT - 1] = "";
        }
      } else {
        row[CONFIG.COLS.O_ATT - 1] = "";
      }
    } else {
      row[CONFIG.COLS.O_ATT - 1] = "";
    }

    // ── 7. Vincolo T → U ─────────────────────────────────────
    if (row[CONFIG.COLS.SEAT_AVAIL - 1] === false ||
        String(row[CONFIG.COLS.SEAT_AVAIL - 1]).toUpperCase() === "FALSE") {
      row[CONFIG.COLS.SITTING - 1] = false;
    }

    // ── 8. Validazione Audio V ───────────────────────────────
    row[CONFIG.COLS.AUDIO - 1] = strictAudioValidation(row[CONFIG.COLS.AUDIO - 1]);
  }

  range.setValues(data);

  // ── Formati colonna (Batch) ────────────────────────────────
  sheet.getRange(startRow, CONFIG.COLS.DATE, numRows, 1).setNumberFormat("dd.MM.yyyy");

  [CONFIG.COLS.H_PREV, CONFIG.COLS.I_EFF, CONFIG.COLS.L_ARR,
   CONFIG.COLS.N_PROS, CONFIG.COLS.J_RIT, CONFIG.COLS.Q_MANC]
    .forEach(c => sheet.getRange(startRow, c, numRows, 1).setNumberFormat("@"));

  [CONFIG.COLS.M_DUR, CONFIG.COLS.O_ATT]
    .forEach(c => sheet.getRange(startRow, c, numRows, 1).setNumberFormat("0"));

  // ── 9. Meteo Storico (solo celle vuote o placeholder) ──────
  for (let i = 0; i < data.length; i++) {
    const rowNum     = startRow + i;
    const weatherVal = sheet.getRange(rowNum, CONFIG.COLS.WEATHER)
                            .getValue().toString().trim();
    if (weatherVal === "" || weatherVal.includes("In attesa")) {
      fetchWeatherHistorical(sheet, rowNum);
    }
  }

  // ── Auto-resize ────────────────────────────────────────────
  sheet.autoResizeColumns(1, numCols);

  // Alert UI (non-bloccante se eseguito in background)
  try {
    SpreadsheetApp.getUi().alert('✅ Ricalcolo ODYSSEY v4 completato.');
  } catch (uiError) {
    Logger.log("Ricalcolo completato in background. Alert UI bypassato.");
  }
}

// ============================================================
// UTILITY — ORARI
// ============================================================

function formatAndValidateTimeArray(val) {
  if (val === undefined || val === null || val === "") return "";
  if (val instanceof Date) {
    return Utilities.formatDate(val,
      SpreadsheetApp.getActiveSpreadsheet().getSpreadsheetTimeZone(), "HH:mm");
  }
  let str = val.toString().trim();
  if (str.includes("1899") || str.includes("GMT")) {
    const match = str.match(/(\d{2}):(\d{2})/);
    return match ? match[0] : "";
  }
  return str.replace(/\b(\d{1,2})(\d{2})\b/g, (match, h, m) => {
    const hh = parseInt(h, 10), mm = parseInt(m, 10);
    if (hh >= 0 && hh < 24 && mm >= 0 && mm < 60)
      return `${String(hh).padStart(2, '0')}:${m}`;
    return "";
  }).trim();
}

function computeTimeDiffArray(baseStr, targetStr) {
  const parseMinsLocal = t => {
    const [h, m] = t.split(':');
    return parseInt(h, 10) * 60 + parseInt(m, 10);
  };
  const cleanArray = s => s.toString().split(' ').map(x => {
    if (x.includes("1899") || x.includes("GMT")) {
      const m = x.match(/(\d{2}):(\d{2})/);
      return m ? m[0] : "";
    }
    return x;
  }).filter(x => x.includes(':'));

  const baseArr   = cleanArray(baseStr);
  const targetArr = cleanArray(targetStr);
  if (baseArr.length === 0 || targetArr.length === 0) return "";

  return baseArr.map((bTime, idx) => {
    const tTime = targetArr[idx] !== undefined
      ? targetArr[idx]
      : targetArr[targetArr.length - 1];
    const diff = parseMinsLocal(tTime) - parseMinsLocal(bTime);
    return diff >= 0 ? diff : diff + 1440;
  }).join(' ');
}

function computeMancataCoincidenzaArray(nProsStr, lArrStr) {
  const parseMinsLocal = t => {
    const m = t.match(/(\d{1,2}):(\d{2})/);
    return m ? parseInt(m[1], 10) * 60 + parseInt(m[2], 10) : null;
  };
  const cleanArray = s => s.toString().split(' ').map(x => {
    if (x.includes("1899") || x.includes("GMT")) {
      const m = x.match(/(\d{2}):(\d{2})/);
      return m ? m[0] : "";
    }
    return x;
  }).filter(x => x.includes(':'));

  const nArr  = cleanArray(nProsStr);
  const lMins = parseMinsLocal(lArrStr.toString().trim().split(' ').pop());
  if (nArr.length === 0 || lMins === null) return { persa: false, tempi: "" };

  const losses = nArr
    .map(n => { const nm = parseMinsLocal(n); return nm !== null ? lMins - nm : null; })
    .filter(d => d !== null && d > 0);

  return {
    persa: losses.length > 0,
    tempi: losses.length > 0 ? losses.join(' ') : ""
  };
}

function computeSingleTimeDiff(startStr, endStr) {
  const s = startStr.toString().trim().split(' ').pop();
  const e = endStr.toString().trim().split(' ').pop();
  if (!s || !e || !s.includes(':') || !e.includes(':')) return "";
  const start = parseMins(s), end = parseMins(e);
  if (start === null || end === null) return "";
  const diff = end - start;
  return diff >= 0 ? diff : diff + 1440;
}

function parseMins(t) {
  if (!t) return null;
  const match = t.toString().match(/(\d{1,2}):(\d{2})/);
  return match ? parseInt(match[1], 10) * 60 + parseInt(match[2], 10) : null;
}

function _sameDate(a, b) {
  const sa = a instanceof Date ? a.toDateString() : a.toString();
  const sb = b instanceof Date ? b.toDateString() : b.toString();
  return sa === sb;
}

/**
 * ============================================================
 * ODYSSEY Engine v4 — TRIGGER & ROUTER (onEdit)
 * ============================================================
 * Trigger reattivo che intercetta le modifiche manuali al foglio.
 * Mantiene piena compatibilità con l'inserimento diretto da
 * Google Fogli, in parallelo alla Web App.
 *
 * CHANGELOG v4:
 *  - CAMBI ora punta a colonna 7 (G) invece di 5 (E)
 *  - TRIP_TYPE ora punta a colonna 4 (D) = tipo_viaggio (corretto)
 *  - Aggiunto placeholder meteo su inserimento data
 *  - Riferimenti via CONFIG.COLS (nessun hardcode)
 * ============================================================
 */

// ── Alias per ricalcolo da menu ──────────────────────────────
function processaDatiPendolare() { ricalcolaTutto(); }

function onOpen() {
  try {
    SpreadsheetApp.getUi()
      .createMenu('⚙️ ODYSSEY v4')
      .addItem('🔄 Ricalcola Tutto', 'ricalcolaTutto')
      .addToUi();
  } catch (e) {
    Logger.log("onOpen: contesto sandbox, menu non disponibile.");
  }
}

// ============================================================
// TRIGGER REATTIVO onEdit
// ============================================================

function onEdit(e) {
  if (!e) return;

  const sheet     = e.source.getActiveSheet();
  const sheetName = sheet.getName();
  const range     = e.range;
  const col       = range.getColumn();
  const row       = range.getRow();
  const val       = e.value; // undefined quando la cella viene cancellata

  // ── PALETTE ───────────────────────────────────────────────
  if (sheetName === CONFIG.SHEET_PALETTE) {
    if (col <= 2 && val && (val.startsWith('#') || val.length === 6 || val.length === 3)) {
      let cleanHex = val.startsWith('#') ? val : '#' + val;
      if (cleanHex.length === 4 || cleanHex.length === 7) {
        applyHexPalette(range, cleanHex);
      }
    }
    return;
  }

  // ── Solo foglio dataset, riga >= 2 ────────────────────────
  if (sheetName !== CONFIG.SHEET_DATA || row < 2) return;

  // ── Logica A: Data → giorno automatico ────────────────────
  if (col === CONFIG.COLS.DATE) {
    if (!val) {
      sheet.getRange(row, CONFIG.COLS.DAY).setValue("");
      return;
    }
    const parsedDay = parseInt(val, 10);
    if (!isNaN(parsedDay) && parsedDay >= 1 && parsedDay <= 31 && val.toString().trim().length <= 2) {
      const d = new Date();
      const newDate = new Date(d.getFullYear(), d.getMonth(), parsedDay);
      range.setValue(newDate);
      range.setNumberFormat("dd.MM.yyyy");
      sheet.getRange(row, CONFIG.COLS.DAY).setValue(CONFIG.GIORNI[newDate.getDay()]);
    }

    // Placeholder meteo
    const weatherCell = sheet.getRange(row, CONFIG.COLS.WEATHER);
    if (weatherCell.getValue().toString().trim() === "") {
      weatherCell.setValue("⏳ In attesa di orario...");
    }
    return;
  }

  // Guard generico: le altre colonne non fanno nulla se vuote
  if (!val) return;

  // ── Logica B: Normalizzazione Orari (H, I, L, N) ─────────
  const timeCols = [CONFIG.COLS.H_PREV, CONFIG.COLS.I_EFF, CONFIG.COLS.L_ARR, CONFIG.COLS.N_PROS];
  if (timeCols.includes(col)) {
    range.setNumberFormat("@");
    const checkedTime = formatAndValidateTimeArray(val);
    range.setValue(checkedTime);

    // Lettura valori correnti per calcoli derivati
    const hPrev = sheet.getRange(row, CONFIG.COLS.H_PREV).getValue().toString();
    const iEff  = sheet.getRange(row, CONFIG.COLS.I_EFF ).getValue().toString();
    const lArr  = sheet.getRange(row, CONFIG.COLS.L_ARR ).getValue().toString();
    const nPros = sheet.getRange(row, CONFIG.COLS.N_PROS).getValue().toString();

    // J — Ritardo vettoriale (I - H)
    if (hPrev && iEff) {
      sheet.getRange(row, CONFIG.COLS.J_RIT).setNumberFormat("@")
        .setValue(computeTimeDiffArray(hPrev, iEff));
    }

    // M — Durata viaggio (L - I)
    if (iEff && lArr) {
      sheet.getRange(row, CONFIG.COLS.M_DUR).setNumberFormat("0")
        .setValue(computeSingleTimeDiff(iEff, lArr));
    }

    // P/Q — Coincidenza persa (vettoriale)
    if (lArr && nPros) {
      const { persa, tempi } = computeMancataCoincidenzaArray(nPros, lArr);
      sheet.getRange(row, CONFIG.COLS.P_COINC).setValue(persa);
      sheet.getRange(row, CONFIG.COLS.Q_MANC).setNumberFormat("@").setValue(tempi);
    }

    // O — Durata attesa inter-riga (I(riga+1) - L(riga))
    const cambi   = parseInt(sheet.getRange(row, CONFIG.COLS.CAMBI).getValue(), 10);
    const lastRow = sheet.getLastRow();
    const currentDate = sheet.getRange(row, CONFIG.COLS.DATE     ).getValue().toString();
    const currentTrip = sheet.getRange(row, CONFIG.COLS.TRIP_TYPE).getValue().toString();

    if (col === CONFIG.COLS.L_ARR && row < lastRow && !isNaN(cambi) && cambi > 0) {
      const nextDate = sheet.getRange(row + 1, CONFIG.COLS.DATE     ).getValue().toString();
      const nextTrip = sheet.getRange(row + 1, CONFIG.COLS.TRIP_TYPE).getValue().toString();
      if (currentDate === nextDate && currentTrip === nextTrip) {
        const nextIEff = formatAndValidateTimeArray(
          sheet.getRange(row + 1, CONFIG.COLS.I_EFF).getValue()
        );
        sheet.getRange(row, CONFIG.COLS.O_ATT).setNumberFormat("0")
          .setValue(computeSingleTimeDiff(checkedTime, nextIEff));
      }
    }

    if (col === CONFIG.COLS.I_EFF && row > 2) {
      const prevCambi = parseInt(sheet.getRange(row - 1, CONFIG.COLS.CAMBI).getValue(), 10);
      const prevDate  = sheet.getRange(row - 1, CONFIG.COLS.DATE     ).getValue().toString();
      const prevTrip  = sheet.getRange(row - 1, CONFIG.COLS.TRIP_TYPE).getValue().toString();
      if (currentDate === prevDate && currentTrip === prevTrip &&
          !isNaN(prevCambi) && prevCambi > 0) {
        const prevLArr = formatAndValidateTimeArray(
          sheet.getRange(row - 1, CONFIG.COLS.L_ARR).getValue()
        );
        sheet.getRange(row - 1, CONFIG.COLS.O_ATT).setNumberFormat("0")
          .setValue(computeSingleTimeDiff(prevLArr, checkedTime));
      }
    }

    // Trigger meteo
    fetchWeatherHistorical(sheet, row);
  }

  // ── Logica C: Vincolo T → U (seduta) ─────────────────────
  if (col === CONFIG.COLS.SEAT_AVAIL && val.toUpperCase() === "FALSE") {
    sheet.getRange(row, CONFIG.COLS.SITTING).setValue("FALSE");
  }

  // ── Logica D: Validazione Audio V ─────────────────────────
  if (col === CONFIG.COLS.AUDIO) {
    range.setValue(strictAudioValidation(val));
  }

  // ── Autoresize selettivo ──────────────────────────────────
  const colsToResize = new Set([col]);
  if (timeCols.includes(col)) {
    [CONFIG.COLS.J_RIT, CONFIG.COLS.M_DUR, CONFIG.COLS.O_ATT,
     CONFIG.COLS.P_COINC, CONFIG.COLS.Q_MANC]
      .forEach(c => colsToResize.add(c));
  }
  colsToResize.forEach(c => sheet.autoResizeColumn(c));
}

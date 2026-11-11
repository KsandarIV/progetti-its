/**
 * ============================================================
 * ODYSSEY Engine v4 — DB SERVICE (CRUD & LOGICA ACCESSO)
 * ============================================================
 * Gestisce la persistenza e le scritture sul foglio 'dataset'.
 * Include la logica di inserimento singolo segmento con 
 * ricalcolo istantaneo per la Web App.
 * ============================================================
 */

/**
 * Salva un segmento (tratta) inviato dalla Web App sul foglio.
 * Esegue le normalizzazioni e le formule prima di scrivere per
 * assicurare consistenza ed efficienza.
 * 
 * @param {Object} dataObj - I dati provenienti dal form client
 * @returns {Object} Risultato dell'operazione
 */
function appendSegment(dataObj) {
  // ── Guard globale: qualsiasi eccezione viene catturata e restituita al client ──
  // in modo strutturato (success: false). Questo evita il messaggio generico
  // "Odyssey offline" e permette al client di accodare l'item offline.
  try {
    return appendSegmentImpl(dataObj);
  } catch (err) {
    Logger.log("appendSegment errore: " + err);
    return { success: false, error: String(err && err.message ? err.message : err) };
  }
}

function appendSegmentImpl(dataObj) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.SHEET_DATA);
  
  if (!sheet) {
    throw new Error(`Foglio '${CONFIG.SHEET_DATA}' non trovato!`);
  }

  // 1. Parsing Data & Giorno
  let dateVal = new Date();
  if (dataObj.date) {
    const parts = dataObj.date.split('.');
    if (parts.length === 3) {
      dateVal = new Date(parseInt(parts[2], 10), parseInt(parts[1], 10) - 1, parseInt(parts[0], 10));
    }
  }
  const dayVal = CONFIG.GIORNI[dateVal.getDay()];

  // Determine Day Type (Prefestivo se Sabato, Festivo se Domenica, Feriale altrimenti)
  let dayTypeVal = dataObj.day_type || "feriale";
  if (dateVal.getDay() === 0) dayTypeVal = "festivo";
  else if (dateVal.getDay() === 6) dayTypeVal = "prefestivo";

  // 2. Normalizzazione Orari
  const hPrev = formatAndValidateTimeArray(dataObj.h_prev || "");
  const iEff  = formatAndValidateTimeArray(dataObj.i_eff || "");
  const lArr  = formatAndValidateTimeArray(dataObj.l_arr || "");
  const nPros = formatAndValidateTimeArray(dataObj.n_pros || "");

  // 3. Calcolo Ritardo J = I - H
  let delayVal = "";
  if (hPrev && iEff && hPrev.includes(':') && iEff.includes(':')) {
    delayVal = computeTimeDiffArray(hPrev, iEff);
  }

  // 4. Calcolo Durata Viaggio M = L - I
  let durationVal = "";
  if (iEff && lArr && iEff.includes(':') && lArr.includes(':')) {
    durationVal = computeSingleTimeDiff(iEff, lArr);
  }

  // 5. Coincidenza Persa P/Q
  let coincVal = false;
  let mancVal = "";
  if (lArr && nPros && lArr.includes(':') && nPros.includes(':')) {
    const { persa, tempi } = computeMancataCoincidenzaArray(nPros, lArr);
    coincVal = persa;
    mancVal = tempi;
  }

  // 6. Vincolo Seduta T -> U
  const seatAvailVal = dataObj.seat_avail === "on" || dataObj.seat_avail === true;
  let sittingVal = dataObj.sitting === "on" || dataObj.sitting === true;
  if (!seatAvailVal) {
    sittingVal = false;
  }

  // 7. Preparazione riga (24 colonne).
  // Metadati percorso (id, indice, totale) salvati nella colonna NOTES
  // con un prefisso strutturato [PERC:id#idx#tot] per evitare di modificare
  // lo schema del foglio.
  const rowData = new Array(24).fill("");
  
  rowData[CONFIG.COLS.DATE - 1]          = dateVal;
  rowData[CONFIG.COLS.DAY - 1]           = dayVal;
  rowData[CONFIG.COLS.DAY_TYPE - 1]      = dayTypeVal;
  rowData[CONFIG.COLS.TRIP_TYPE - 1]     = dataObj.tripType || "andata";
  rowData[CONFIG.COLS.ROUTE - 1]         = dataObj.route || "";
  rowData[CONFIG.COLS.TRANSPORT - 1]     = dataObj.transport || "";
  rowData[CONFIG.COLS.CAMBI - 1]         = dataObj.cambi ? parseInt(dataObj.cambi, 10) : 0;
  rowData[CONFIG.COLS.H_PREV - 1]        = hPrev;
  rowData[CONFIG.COLS.I_EFF - 1]         = iEff;
  rowData[CONFIG.COLS.J_RIT - 1]         = delayVal;
  rowData[CONFIG.COLS.DELAY_REASON - 1]  = dataObj.delay_reason || "";
  rowData[CONFIG.COLS.L_ARR - 1]         = lArr;
  rowData[CONFIG.COLS.M_DUR - 1]         = durationVal;
  rowData[CONFIG.COLS.N_PROS - 1]        = nPros;
  rowData[CONFIG.COLS.O_ATT - 1]         = "";
  rowData[CONFIG.COLS.P_COINC - 1]       = coincVal;
  rowData[CONFIG.COLS.Q_MANC - 1]        = mancVal;
  rowData[CONFIG.COLS.WEATHER - 1]       = "⏳ Calcolo in corso...";
  rowData[CONFIG.COLS.CROWDING - 1]      = dataObj.crowding || "";
  rowData[CONFIG.COLS.SEAT_AVAIL - 1]    = seatAvailVal ? "TRUE" : "FALSE";
  rowData[CONFIG.COLS.SITTING - 1]       = sittingVal ? "TRUE" : "FALSE";
  rowData[CONFIG.COLS.AUDIO - 1]         = strictAudioValidation(dataObj.audio);
  rowData[CONFIG.COLS.MOOD - 1]          = dataObj.mood || "";
  // Costruisci il valore di NOTES con prefisso percorso (se presente)
  let notesVal = dataObj.notes || "";
  if (dataObj.percorso_id) {
    const prefix = "[PERC:" + (dataObj.percorso_id || "") + "#"
                 + (dataObj.tratta_index || "0") + "#"
                 + (dataObj.tratte_totali || "1") + "]";
    notesVal = notesVal ? (prefix + " " + notesVal) : prefix;
  }
  rowData[CONFIG.COLS.NOTES - 1]         = notesVal;

  // 8. Scrittura sul foglio
  sheet.appendRow(rowData);
  const newRowIndex = sheet.getLastRow();

  // 9. Applicazione Formati alla nuova riga
  sheet.getRange(newRowIndex, CONFIG.COLS.DATE).setNumberFormat("dd.MM.yyyy");
  [CONFIG.COLS.H_PREV, CONFIG.COLS.I_EFF, CONFIG.COLS.L_ARR,
   CONFIG.COLS.N_PROS, CONFIG.COLS.J_RIT, CONFIG.COLS.Q_MANC]
    .forEach(c => sheet.getRange(newRowIndex, c).setNumberFormat("@"));
  
  [CONFIG.COLS.M_DUR, CONFIG.COLS.O_ATT]
    .forEach(c => sheet.getRange(newRowIndex, c).setNumberFormat("0"));

  // 10. Calcolo Durata Attesa Inter-riga (se applicabile)
  const cambiNum = parseInt(rowData[CONFIG.COLS.CAMBI - 1], 10);
  if (newRowIndex > 2 && cambiNum > 0) {
    const prevDate = sheet.getRange(newRowIndex - 1, CONFIG.COLS.DATE).getValue();
    const prevTrip = sheet.getRange(newRowIndex - 1, CONFIG.COLS.TRIP_TYPE).getValue().toString();
    const prevCambi = parseInt(sheet.getRange(newRowIndex - 1, CONFIG.COLS.CAMBI).getValue(), 10);

    if (_sameDate(dateVal, prevDate) && rowData[CONFIG.COLS.TRIP_TYPE - 1] === prevTrip && prevCambi > 0) {
      const prevLArr = formatAndValidateTimeArray(sheet.getRange(newRowIndex - 1, CONFIG.COLS.L_ARR).getValue());
      if (prevLArr && iEff) {
        sheet.getRange(newRowIndex - 1, CONFIG.COLS.O_ATT).setValue(computeSingleTimeDiff(prevLArr, iEff));
      }
    }
  }

  // 11. Chiamata asincrona/immediata meteo storico
  fetchWeatherHistorical(sheet, newRowIndex);

  // Auto-resize
  try {
    sheet.autoResizeColumns(1, 24);
  } catch(e) {}

  return {
    success: true,
    rowIndex: newRowIndex,
    date: dataObj.date,
    route: dataObj.route
  };
}

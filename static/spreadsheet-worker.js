/* Parsing stays off the UI thread. No macros, formulas or links are executed. */
importScripts("/vendor/sheetjs/xlsx.full.min.js");

let workbook;
const MAX_ROWS = 10000, MAX_COLUMNS = 256;

function page(sheetIndex, offset) {
  const sheet = workbook.Sheets[workbook.SheetNames[sheetIndex]];
  if (!sheet) throw new Error("Лист не найден");
  const range = XLSX.utils.decode_range(sheet["!ref"] || "A1");
  const full = XLSX.utils.decode_range(sheet["!fullref"] || sheet["!ref"] || "A1");
  const endColumn = Math.min(range.e.c, MAX_COLUMNS - 1);
  const firstColumn = Math.min(range.s.c, endColumn);
  const endRow = Math.min(range.e.r, MAX_ROWS - 1);
  const firstRow = Math.min(range.s.r, endRow);
  const pageSize = Math.min(200, Math.floor(20000 / (endColumn - firstColumn + 1)));
  const start = Math.min(endRow, firstRow + Math.max(0, offset));
  const end = Math.min(endRow, start + pageSize - 1);
  const cells = [], heights = [], widths = [], merges = [];
  let formulasWithoutResult = false;
  function value(row, column) {
    const cell = sheet[XLSX.utils.encode_cell({ r: row, c: column })];
    if (!cell) return { text: "", numeric: false };
    if (cell.v == null && cell.f) formulasWithoutResult = true;
    let formatted = cell.w;
    if (formatted == null && cell.t === "n" && cell.z && XLSX.SSF.is_date(cell.z)) {
      try {
        formatted = XLSX.SSF.format(cell.z.replace(/([dmy])\.(?=[dmy])/gi, "$1\\."), cell.v,
          { date1904: Boolean(workbook.Workbook?.WBProps?.date1904) });
      } catch (_) { /* Keep the stored value when a custom format is unsupported. */ }
    }
    return { text: formatted ?? (cell.v == null && cell.f ? "=" + cell.f : String(cell.v ?? "")), numeric: cell.t === "n" };
  }
  for (let row = start; row <= end; row++) {
    const line = [];
    for (let column = firstColumn; column <= endColumn; column++) line.push(value(row, column));
    cells.push(line);
    heights.push(Math.min(300, Math.max(22, (sheet["!rows"]?.[row]?.hpt || 16.5) * 4 / 3)));
  }
  for (let column = firstColumn; column <= endColumn; column++) {
    widths.push(Math.min(500, Math.max(18, sheet["!cols"]?.[column]?.wpx || 90)));
  }
  for (const merge of sheet["!merges"] || []) {
    if (merge.e.r < start || merge.s.r > end || merge.e.c < firstColumn || merge.s.c > endColumn) continue;
    merges.push({ r: Math.max(start, merge.s.r) - start, c: Math.max(firstColumn, merge.s.c) - firstColumn,
      rows: Math.min(end, merge.e.r) - Math.max(start, merge.s.r) + 1,
      columns: Math.min(endColumn, merge.e.c) - Math.max(firstColumn, merge.s.c) + 1,
      ...value(merge.s.r, merge.s.c) });
  }
  return { sheetIndex, cells, widths, heights, merges, start, end, firstColumn, firstRow,
    totalRows: endRow - firstRow + 1, pageSize,
    limited: full.e.r >= MAX_ROWS || full.e.c >= MAX_COLUMNS, formulasWithoutResult };
}

self.onmessage = async ({ data }) => {
  try {
    if (data.type === "load") {
      const response = await fetch(data.url, { signal: AbortSignal.timeout(30000), cache: "no-store" });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        throw new Error(result.error || "Не удалось загрузить таблицу. Попробуй ещё раз.");
      }
      const raw = await response.arrayBuffer();
      if (raw.byteLength > 20 * 1024 * 1024) throw new Error("Таблица больше 20 МБ. Скачай файл целиком.");
      workbook = XLSX.read(raw, { type: "array", codepage: 1251, cellStyles: true, cellHTML: false,
        bookVBA: false, sheetRows: MAX_ROWS });
      if (!workbook.SheetNames.length) throw new Error("В таблице нет листов");
      self.postMessage({ id: data.id, sheets: workbook.SheetNames, ...page(0, 0) });
    } else {
      self.postMessage({ id: data.id, ...page(data.sheetIndex, data.offset) });
    }
  } catch (error) {
    const message = data.type === "load" && /password|encrypt/i.test(error.message)
      ? "Таблица защищена паролем. Встроенный просмотр такого файла недоступен."
      : error.message;
    self.postMessage({ id: data.id, error: message || "Не удалось прочитать таблицу" });
  }
};

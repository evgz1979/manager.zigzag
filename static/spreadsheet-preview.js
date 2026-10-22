/* Read-only spreadsheet viewer; all document text is inserted as text nodes. */
window.SpreadsheetPreview = (() => {
  let active;
  function close() {
    if (!active) return;
    active.worker.terminate();
    clearTimeout(active.timeout);
    active = null;
  }
  function open(container, url, onError) {
    close();
    const worker = new Worker("/spreadsheet-worker.js");
    const current = active = { worker, id: 0, timeout: null };
    const viewer = document.createElement("div");
    viewer.className = "spreadsheet-viewer";
    const toolbar = document.createElement("div");
    toolbar.className = "spreadsheet-toolbar";
    const label = document.createElement("label");
    label.textContent = "Лист ";
    const sheets = document.createElement("select");
    sheets.setAttribute("aria-label", "Лист таблицы");
    sheets.disabled = true;
    label.append(sheets);
    const zoomLabel = document.createElement("label");
    zoomLabel.textContent = "Масштаб ";
    const zoom = document.createElement("select");
    zoom.setAttribute("aria-label", "Масштаб таблицы");
    for (const percent of [50, 75, 100, 125, 150, 200]) zoom.add(new Option(percent + "%", percent));
    zoom.value = "100";
    zoomLabel.append(zoom);
    const readonly = document.createElement("span");
    readonly.textContent = "Только чтение";
    toolbar.append(label, zoomLabel, readonly);
    const scroll = document.createElement("div");
    scroll.className = "spreadsheet-scroll";
    scroll.tabIndex = 0;
    scroll.setAttribute("aria-label", "Содержимое таблицы, только чтение");
    scroll.textContent = "Загрузка таблицы…";
    const footer = document.createElement("div");
    footer.className = "spreadsheet-footer";
    const previous = document.createElement("button"), next = document.createElement("button");
    previous.textContent = "←";
    next.textContent = "→";
    previous.setAttribute("aria-label", "Предыдущие строки");
    next.setAttribute("aria-label", "Следующие строки");
    const status = document.createElement("span"), notice = document.createElement("span");
    notice.className = "spreadsheet-notice";
    footer.append(previous, status, next, notice);
    footer.hidden = true;
    viewer.append(toolbar, scroll, footer);
    container.replaceChildren(viewer);
    let result, table;
    function fail(message) {
      if (active !== current) return;
      close();
      onError(message);
    }
    function send(message) {
      clearTimeout(current.timeout);
      current.timeout = setTimeout(() => fail("Таблица слишком долго открывается. Попробуй ещё раз или скачай файл."), 45000);
      worker.postMessage({ ...message, id: ++current.id });
    }
    function changePage(sheetIndex, offset) {
      previous.disabled = next.disabled = true;
      send({ type: "page", sheetIndex, offset });
    }
    sheets.addEventListener("change", () => changePage(Number(sheets.value), 0));
    previous.addEventListener("click", () => changePage(result.sheetIndex, Math.max(0, result.start - result.firstRow - result.pageSize)));
    next.addEventListener("click", () => changePage(result.sheetIndex, result.start - result.firstRow + result.pageSize));
    function resize() {
      if (table) table.style.zoom = Number(zoom.value) / 100;
    }
    zoom.addEventListener("change", resize);
    worker.onerror = () => fail("Не удалось открыть таблицу. Попробуй ещё раз или скачай файл.");
    worker.onmessage = ({ data }) => {
      if (active !== current || data.id !== current.id) return;
      clearTimeout(current.timeout);
      if (data.error) return fail(data.error);
      result = data;
      if (data.sheets) data.sheets.forEach((name, index) => sheets.add(new Option(name, index)));
      sheets.disabled = false;
      sheets.value = String(data.sheetIndex);
      table = document.createElement("table");
      table.className = "spreadsheet-table";
      table.setAttribute("aria-label", sheets.selectedOptions[0].textContent);
      const columns = document.createElement("colgroup");
      const cornerColumn = document.createElement("col");
      cornerColumn.style.width = "42px";
      columns.append(cornerColumn);
      data.widths.forEach((width) => {
        const col = document.createElement("col");
        col.style.width = width + "px";
        columns.append(col);
      });
      table.style.width = (42 + data.widths.reduce((sum, width) => sum + width, 0)) + "px";
      const head = table.createTHead(), heading = head.insertRow();
      heading.append(document.createElement("th"));
      function columnName(index) {
        let name = "";
        for (++index; index; index = Math.floor((index - 1) / 26)) name = String.fromCharCode(65 + (index - 1) % 26) + name;
        return name;
      }
      data.widths.forEach((_, index) => {
        const th = document.createElement("th");
        th.scope = "col";
        th.textContent = columnName(data.firstColumn + index);
        heading.append(th);
      });
      table.prepend(columns);
      const covered = new Set(), merged = new Map();
      data.merges.forEach((merge) => {
        merged.set(merge.r + ":" + merge.c, merge);
        for (let r = merge.r; r < merge.r + merge.rows; r++) {
          for (let c = merge.c; c < merge.c + merge.columns; c++) {
            if (r !== merge.r || c !== merge.c) covered.add(r + ":" + c);
          }
        }
      });
      const body = table.createTBody();
      data.cells.forEach((line, r) => {
        const row = body.insertRow();
        row.style.height = data.heights[r] + "px";
        const th = document.createElement("th");
        th.scope = "row";
        th.textContent = data.start + r + 1;
        row.append(th);
        line.forEach((cell, c) => {
          const key = r + ":" + c;
          if (covered.has(key)) return;
          const td = row.insertCell(), merge = merged.get(key);
          if (merge) { td.rowSpan = merge.rows; td.colSpan = merge.columns; cell = merge; }
          td.textContent = cell.text;
          if (cell.numeric) td.className = "spreadsheet-number";
        });
      });
      resize();
      scroll.replaceChildren(table);
      scroll.scrollTop = scroll.scrollLeft = 0;
      previous.disabled = data.start <= data.firstRow;
      next.disabled = data.end >= data.firstRow + data.totalRows - 1;
      status.textContent = "Строки " + (data.start + 1) + "–" + (data.end + 1) + " из " + (data.firstRow + data.totalRows);
      notice.textContent = [data.limited ? "Показаны первые 10 000 строк и 256 столбцов. Остальное — в скачанном файле." : "",
        data.formulasWithoutResult ? "Формулы без сохранённого результата показаны текстом." : ""].filter(Boolean).join(" ");
      footer.hidden = false;
    };
    send({ type: "load", url });
  }
  return { open, close };
})();

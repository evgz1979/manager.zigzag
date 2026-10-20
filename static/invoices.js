/* Invoice fields live in SQLite; a browser draft is never the saved copy. */
(() => {
  let editor = null, listedPath = null, loading = 0, pendingCreate = null;
  const fields = { kind: "invoiceKind", number: "invoiceNumber", date: "invoiceDate", due_date: "invoiceDue",
    buyer_name: "invoiceBuyer", buyer_inn: "invoiceBuyerInn", buyer_kpp: "invoiceBuyerKpp", buyer_address: "invoiceBuyerAddress",
    note: "invoiceNote", work_start: "invoiceWorkStart", work_end: "invoiceWorkEnd", terms: "invoiceTerms" };
  const sellerFields = { name: "Исполнитель", inn: "ИНН", kpp: "КПП", address: "Адрес", bank: "Банк",
    bik: "БИК", account: "Расчётный счёт", correspondent: "Корреспондентский счёт", signer: "Подписант" };
  const cash = (cents) => new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB" }).format(cents / 100);
  const pdfUrl = (record, preview = false) => apiUrl(preview ? "/api/invoice-preview" : "/api/invoice-pdf", record.path, { id: record.id });
  const message = (text, error = false) => {
    $("invoiceEditorState").textContent = text;
    $("invoiceEditorState").classList.toggle("error", error);
  };

  async function refreshList(force = false) {
    const folder = state.folder;
    const visible = Boolean(folder?.order);
    $("invoiceSection").hidden = !visible;
    if (!visible) { listedPath = null; return; }
    if (listedPath === folder.path && !force) return;
    const version = ++loading;
    if (listedPath !== folder.path) { $("invoiceList").replaceChildren(); $("invoiceCount").textContent = ""; }
    listedPath = folder.path;
    $("invoiceListState").textContent = "Загрузка счетов…";
    try {
      const result = await request(apiUrl("/api/invoices", folder.path));
      if (version !== loading || state.folder?.path !== folder.path) return;
      $("invoiceCount").textContent = result.items.length || "";
      $("invoiceListState").textContent = result.items.length ? "" : "Выпиши первый счёт по этому заказу.";
      $("invoiceList").innerHTML = result.items.map((record) => {
        const label = (record.data.kind === "contract" ? "Счёт-договор" : "Счёт") + " № " + record.number;
        const sync = record.state === "draft" ? "Черновик" : record.sync_error ? "PDF в базе · " + record.sync_error + " · автоповтор" : record.sync_pending ? "PDF в базе · копия в # bills ожидает выгрузки" : "PDF в # bills";
        return '<div class="invoice-row"><button type="button" class="invoice-row-name" data-invoice-edit="' + record.id + '">' + escapeHtml(label) + '<small>' + escapeHtml(record.data.date.split("-").reverse().join(".")) + '</small></button><strong>' + cash(record.data.total) + '</strong><span class="invoice-row-state' + (record.sync_error ? ' error' : '') + '">' + escapeHtml(sync) + '</span>' +
          (record.state === "issued" ? '<a class="secondary-button" href="' + escapeHtml(pdfUrl(record)) + '" target="_blank" rel="noopener">PDF ↗</a>' : '') + '<button class="secondary-button" type="button" data-invoice-copy="' + record.id + '">На основе</button></div>';
      }).join("");
      // Store records on this exact list, independent of grid positions.
      $("invoiceList").invoiceRecords = result.items;
    } catch (error) {
      if (version === loading) { listedPath = null; $("invoiceListState").textContent = error.message; }
    }
  }

  function itemMarkup(item) {
    return '<tr>' + [["name", "Наименование", 500], ["quantity", "Количество", 30], ["unit", "Единица", 16], ["price", "Цена", 30]].map(([key, label, limit]) =>
      '<td><input data-field="' + key + '" aria-label="' + label + '" maxlength="' + limit + '" value="' + escapeHtml(item[key]) + '"' + (["quantity", "price"].includes(key) ? ' inputmode="decimal"' : '') + '></td>').join("") + '<td class="invoice-item-total"></td><td><button class="icon-button" type="button" data-invoice-remove aria-label="Удалить позицию">✕</button></td></tr>';
  }

  function collect() {
    const data = Object.fromEntries(Object.entries(fields).map(([field, id]) => [field, $(id).value]));
    data.seller = Object.fromEntries(Object.keys(sellerFields).map((key) => [key, $("invoiceSeller-" + key).value]));
    data.items = [...$("invoiceItems").rows].map((row) => Object.fromEntries([...row.querySelectorAll("input")].map((input) => [input.dataset.field, input.value])));
    return data;
  }

  function totals() {
    let total = 0n;
    const scaled = (value, places) => {
      value = value.replace(/[\s\u00a0]/g, "").replace(",", ".");
      if (!new RegExp("^\\d+(?:\\.\\d{0," + places + "})?$").test(value) || value.length > 20) throw new Error();
      const [whole, fraction = ""] = value.split(".");
      return BigInt(whole) * 10n ** BigInt(places) + BigInt(fraction.padEnd(places, "0"));
    };
    for (const row of $("invoiceItems").rows) {
      try {
        const quantity = scaled(row.querySelector('[data-field="quantity"]').value, 3);
        const price = scaled(row.querySelector('[data-field="price"]').value, 2);
        const amount = (quantity * price + 500n) / 1000n;
        row.querySelector(".invoice-item-total").textContent = cash(Number(amount)); total += amount;
      } catch { row.querySelector(".invoice-item-total").textContent = "—"; }
    }
    $("invoiceTotal").textContent = cash(Number(total));
    $("invoiceContract").hidden = $("invoiceKind").value !== "contract";
    $("invoiceTitle").textContent = ($("invoiceKind").value === "contract" ? "Счёт-договор" : "Счёт") + " № " + $("invoiceNumber").value;
  }

  function controls() {
    if (!editor) return;
    const issued = editor.record.state === "issued";
    for (const input of $("invoiceForm").querySelectorAll("input, textarea, select, [data-invoice-remove]")) input.disabled = issued || Boolean(editor.issuing);
    for (const id of ["saveInvoice", "issueInvoice", "previewInvoice", "closeInvoice"]) $(id).disabled = Boolean(editor.saving || editor.issuing);
    $("saveInvoice").hidden = issued;
    $("issueInvoice").hidden = issued;
    $("addInvoiceItem").hidden = issued;
    $("previewInvoice").textContent = issued ? "Открыть PDF ↗" : "Предпросмотр ↗";
    $("invoiceDraftHint").textContent = issued ? "Выпущен · для изменений создай новый на основе этого" : "Черновик сохраняется автоматически · одна страница";
  }

  function show(record) {
    editor = { record, dirty: false, saving: null, issuing: false, timer: null };
    $("invoiceTitle").textContent = (record.data.kind === "contract" ? "Счёт-договор" : "Счёт") + " № " + record.number;
    $("invoiceOrderPath").textContent = record.path;
    for (const [field, id] of Object.entries(fields)) $(id).value = record.data[field] || "";
    $("invoiceSellerFields").innerHTML = Object.entries(sellerFields).map(([key, label]) => '<label>' + label + '<input id="invoiceSeller-' + key + '" maxlength="' + (key === "address" ? 500 : 300) + '" value="' + escapeHtml(record.data.seller[key] || "") + '"></label>').join("");
    $("invoiceItems").innerHTML = record.data.items.map(itemMarkup).join("");
    $("invoiceRememberSeller").checked = false;
    editor.saved = JSON.stringify(collect());
    message(record.state === "issued" ? "Выпущенный PDF сохранён в базе." : "Черновик сохранён в базе.");
    controls(); totals();
    if (!$("invoiceDialog").open) $("invoiceDialog").showModal();
    $("invoiceBuyer").focus();
  }

  async function save() {
    const current = editor;
    if (!current || current.record.state === "issued") return;
    clearTimeout(current.timer);
    if (current.saving) { await current.saving; if (current.dirty) return save(); return; }
    if (!current.dirty) return;
    const data = collect(), snapshot = JSON.stringify(data);
    const remember = $("invoiceRememberSeller").checked;
    message("Сохранение в базе…");
    current.saving = request("/api/invoice-save", { path: current.record.path, id: current.record.id,
      revision: current.record.revision, data, remember_seller: remember });
    controls();
    try {
      const record = await current.saving;
      current.record = record; current.saved = snapshot;
      current.dirty = JSON.stringify(collect()) !== snapshot;
      message(current.dirty ? "Сохраняю оставшиеся правки…" : "Черновик сохранён в базе.");
      refreshList(true);
    } catch (error) { message(error.message + " Ввод остался в форме.", true); throw error; }
    finally { current.saving = null; controls(); }
    if (current.dirty) return save();
  }

  async function close() {
    if (editor?.issuing) return;
    await save();
    clearTimeout(editor?.timer);
    editor = null; $("invoiceDialog").close(); refreshList(true);
  }

  async function create(source) {
    const path = state.folder?.path;
    if (!path || !state.folder.order) return;
    if (!pendingCreate || pendingCreate.path !== path || pendingCreate.source !== source) {
      // crypto.randomUUID is unavailable on HTTP LAN origins.
      const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
      const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
      pendingCreate = { path, source, id: hex.slice(0, 8) + "-" + hex.slice(8, 12) + "-" + hex.slice(12, 16) + "-" + hex.slice(16, 20) + "-" + hex.slice(20) };
    }
    $("newInvoice").disabled = true;
    try {
      const record = await request("/api/invoice-create", pendingCreate);
      pendingCreate = null;
      if (state.folder?.path === path) show(record);
      await refreshList(true);
    } finally { $("newInvoice").disabled = false; }
  }

  function action(work) {
    return Promise.resolve().then(work).catch((error) => {
      if (editor) message(error.message + " Ввод остался в форме.", true);
      else notify(error.message, true);
    });
  }
  function changed() {
    if (!editor || editor.record.state !== "draft") return;
    editor.dirty = JSON.stringify(collect()) !== editor.saved || $("invoiceRememberSeller").checked;
    totals();
    clearTimeout(editor.timer);
    if (editor.dirty) { message("Есть несохранённые изменения…"); editor.timer = setTimeout(() => action(save), 900); }
  }
  $("invoiceForm").addEventListener("input", changed);
  $("invoiceForm").addEventListener("change", changed);
  $("invoiceForm").addEventListener("submit", (event) => { event.preventDefault(); action(save); });
  $("closeInvoice").addEventListener("click", () => action(close));
  $("invoiceDialog").addEventListener("cancel", (event) => { event.preventDefault(); action(close); });
  $("newInvoice").addEventListener("click", () => action(() => create()));
  $("addInvoiceItem").addEventListener("click", () => {
    if (!editor || editor.record.state !== "draft") return;
    if ($("invoiceItems").rows.length >= 40) { message("До 40 позиций; PDF должен поместиться на одну страницу.", true); return; }
    $("invoiceItems").insertAdjacentHTML("beforeend", itemMarkup({ name: "", quantity: "1", unit: "шт", price: "0" }));
    $("invoiceItems").lastElementChild.querySelector("input").focus(); changed();
  });
  $("invoiceItems").addEventListener("click", (event) => {
    if (!event.target.closest("[data-invoice-remove]") || editor?.record.state !== "draft") return;
    if ($("invoiceItems").rows.length === 1) { message("Оставь хотя бы одну позицию.", true); return; }
    event.target.closest("tr").remove(); changed();
  });
  $("invoiceList").addEventListener("click", (event) => {
    const copy = event.target.closest("[data-invoice-copy]");
    const edit = event.target.closest("[data-invoice-edit]");
    if (copy) action(() => create(copy.dataset.invoiceCopy));
    else if (edit) {
      const record = $("invoiceList").invoiceRecords?.find((item) => item.id === edit.dataset.invoiceEdit && item.path === state.folder?.path);
      if (record) show(record);
    }
  });
  $("previewInvoice").addEventListener("click", () => {
    const tab = window.open("about:blank", "_blank");
    action(async () => {
      try {
        await save();
        const record = editor.record;
        if (record.state === "issued") { if (tab) tab.location = pdfUrl(record); return; }
        const response = await fetch(pdfUrl(record, true));
        if (!response.ok) { const data = await response.json(); throw new Error(data.error); }
        const url = URL.createObjectURL(await response.blob());
        if (tab) tab.location = url;
        setTimeout(() => URL.revokeObjectURL(url), 600000);
      } catch (error) { tab?.close(); throw error; }
    });
  });
  $("issueInvoice").addEventListener("click", () => action(async () => {
    if (!editor || editor.issuing) return;
    await save();
    const current = editor;
    current.issuing = true; controls(); message("Подготовка одностраничного PDF…");
    try {
      current.record = await request("/api/invoice-issue", { path: current.record.path, id: current.record.id, revision: current.record.revision });
      message("PDF выпущен и сохранён в базе. Копия в # bills поставлена в очередь.");
      await refreshList(true);
    } finally { current.issuing = false; controls(); }
  }));
  document.addEventListener("manager-folder-rendered", () => refreshList());
  window.addEventListener("beforeunload", (event) => {
    if (editor?.dirty || editor?.saving || editor?.issuing) { event.preventDefault(); event.returnValue = ""; }
  });
  setInterval(() => { if (!document.hidden && state.view !== "orders" && !$("invoiceSection").hidden) refreshList(true); }, 5000);
  refreshList();
})();

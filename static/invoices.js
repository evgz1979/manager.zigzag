/* Invoice fields live in SQLite; a browser draft is never the saved copy. */
(() => {
  let editor = null, attachment = null, listedPath = null, listMarkup = null, trashMarkup = null, loading = 0, pendingCreate = null;
  let pendingRemoval = null, removing = false, planning = null;
  const statusSaving = new Set();
  const listStatusLabels = { active: "Актуально", inactive: "Неактуально", later: "Позже", sent: "Отправлен" };
  const planLabels = { invoice: 'Запланирована выписка счёта', incoming: 'Запланировано получение оплаты', outgoing: 'Запланирован платёж' };
  const invoiceLabel = (record) => record.state === 'planned' ? planLabels[record.data.operation || 'invoice'] || 'Запланировано' : record.state === 'external' ? record.data.original_name : (record.data.kind === 'contract' ? 'Счёт-договор' : 'Счёт') + ' № ' + record.number;
  const displayDate = (value) => typeof value === 'string' ? value.split('-').reverse().join('.') : 'Дата не распознана';
  const planAmount = (record) => ['incoming', 'outgoing'].includes(record.data.operation) && Number.isSafeInteger(record.data.amount) ? (record.data.operation === 'incoming' ? '+' : '−') + cash(record.data.amount) : '';
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

  function renderInvoiceList(records) {
    const focusedPlan = document.activeElement?.dataset.invoicePlan;
    const focused = document.activeElement?.closest('[data-invoice-status]');
    const focusKey = focused ? { id: focused.dataset.invoiceStatus, value: focused.dataset.value } : null;
    const markup = records.map((record) => {
      const external = record.state === "external";
      const label = invoiceLabel(record);
      const date = displayDate(record.data.date);
      if (record.state === 'planned') {
        return '<div class="invoice-row"><button type="button" class="invoice-row-name" data-invoice-plan="' + record.id + '"' + (record.plan_editable ? '' : ' disabled') + '><span class="invoice-row-label">' + escapeHtml(label) + '</span><small class="invoice-row-meta">' + escapeHtml(date + (planAmount(record) ? ' · ' + planAmount(record) : '')) + (record.plan_editable ? '' : ' · Неизвестный формат плана') + '</small></button><div class="invoice-row-actions"><button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + record.id + '" aria-label="В корзину · ' + escapeHtml(label + ' · ' + date) + '">×</button></div></div>';
      }
      const details = (external ? 'Внешний · ' : '') + date;
      const comment = external ? record.data.comment?.trim() : '';
      const heading = comment || label;
      const secondary = (comment ? label + ' · ' : '') + details;
      const sync = record.state === "draft" ? "Черновик" : record.sync_error ? "PDF в базе · " + record.sync_error + " · автоповтор" : record.sync_pending ? "PDF в базе · копия в # bills ожидает выгрузки" : "PDF в # bills";
      const busy = statusSaving.has(record.id);
      const status = record.list_status === undefined ? 'none' : record.list_status;
      const buttons = '<div class="invoice-list-status" role="group" aria-label="Отметка счёта · ' + escapeHtml(label) + '" aria-busy="' + busy + '">' +
        Object.entries(listStatusLabels).map(([value, name]) => '<button type="button" class="secondary-button" data-invoice-status="' + record.id + '" data-value="' + value + '" aria-pressed="' + (status === value) + '" title="' + (status === null ? 'Неизвестная отметка сохранена без замены' : status === value ? 'Снять отметку «' + name + '»' : name) + '"' + (busy || status === null ? ' disabled' : '') + '>' + name + '</button>').join('') + '</div>';
      return '<div class="invoice-row"><button type="button" class="invoice-row-name" data-invoice-' + (external ? 'view' : 'edit') + '="' + record.id + '"><span class="invoice-row-label' + (comment ? ' invoice-row-comment' : '') + '" title="' + escapeHtml(heading) + '">' + escapeHtml(heading) + '</span><small class="invoice-row-meta" title="' + escapeHtml(secondary + ' · ' + sync) + '">' + escapeHtml(secondary) + '<span class="invoice-row-state' + (record.sync_error ? ' error' : '') + '"> · ' + escapeHtml(sync) + '</span></small></button><div class="invoice-row-actions">' + (external ? '' : '<strong>' + cash(record.data.total) + '</strong>') + buttons +
        (external ? '<button class="secondary-button" type="button" data-invoice-view="' + record.id + '">PDF</button>' : record.state !== "draft" ? '<a class="secondary-button" href="' + escapeHtml(pdfUrl(record)) + '" target="_blank" rel="noopener">PDF ↗</a>' : '') + (external ? '' : '<button class="secondary-button" type="button" data-invoice-copy="' + record.id + '">На основе</button>') + '<button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + record.id + '" title="В корзину" aria-label="' + escapeHtml('В корзину · ' + label) + '">×</button></div></div>';
    }).join("");
    if (markup !== listMarkup) {
      $("invoiceList").innerHTML = markup;
      listMarkup = markup;
      if (focusKey && document.activeElement === document.body) focusStatusButton(focusKey);
      if (focusedPlan && document.activeElement === document.body) [...$("invoiceList").querySelectorAll('[data-invoice-plan]')].find((button) => button.dataset.invoicePlan === focusedPlan)?.focus({ preventScroll: true });
    }
    // Store records on this exact list, independent of grid positions.
    $("invoiceList").invoiceRecords = records;
  }

  function focusStatusButton(key) {
    [...$("invoiceList").querySelectorAll('[data-invoice-status]')].find((button) =>
      button.dataset.invoiceStatus === key.id && button.dataset.value === key.value)?.focus({ preventScroll: true });
  }

  async function toggleListStatus(record, value) {
    if (statusSaving.has(record.id)) return;
    const focusKey = { id: record.id, value };
    statusSaving.add(record.id);
    renderInvoiceList($("invoiceList").invoiceRecords || []);
    try {
      const saved = await request('/api/invoice-list-status', { path: record.path, id: record.id, revision: record.revision,
        value: record.list_status === value ? 'none' : value });
      if (state.folder?.path === record.path) {
        renderInvoiceList(($("invoiceList").invoiceRecords || []).map((item) => item.id === saved.id ? saved : item));
        await refreshList(true);
      }
    } catch (error) {
      if (state.folder?.path === record.path) await refreshList(true);
      throw error;
    } finally {
      statusSaving.delete(record.id);
      if (state.folder?.path === record.path) {
        renderInvoiceList($("invoiceList").invoiceRecords || []);
        if (document.activeElement === document.body) focusStatusButton(focusKey);
      }
    }
  }

  async function refreshList(force = false) {
    const folder = state.folder;
    const visible = Boolean(folder?.order) && !isWorkOrderPath(folder.path);
    $("invoiceSection").hidden = !visible;
    if (!visible) { listedPath = null; ++loading; return; }
    if (listedPath === folder.path && !force) return;
    const version = ++loading;
    if (listedPath !== folder.path) {
      $("invoiceList").replaceChildren(); $("invoiceCount").textContent = "";
      listMarkup = null;
      trashMarkup = null; $("invoiceTrash").hidden = true; $("invoiceTrash").open = false;
      $("invoiceListState").textContent = "Загрузка счетов…";
    }
    listedPath = folder.path;
    try {
      const result = await request(apiUrl("/api/invoices", folder.path));
      if (version !== loading || state.folder?.path !== folder.path) return;
      $("invoiceCount").textContent = result.items.length || "";
      $("invoiceListState").textContent = result.items.length ? "" : "Запланируй выписку, прикрепи PDF или выпиши счёт по этому заказу.";
      renderInvoiceList(result.items);
      const trashed = result.trash || [];
      $("invoiceTrash").hidden = !trashed.length;
      $("invoiceTrashCount").textContent = trashed.length;
      const removedMarkup = trashed.map((record) => {
        const label = invoiceLabel(record), marker = record.trash;
        const sync = marker.error ? marker.error + ' · автоповтор' : marker.state === 'pending' ? 'Перенос PDF в .trash…' : record.filename ? 'В корзине · # bills/.trash' : record.state === 'planned' ? 'План в корзине · ' + displayDate(record.data.date) + ' ' + planAmount(record) : 'Черновик в корзине';
        const comment = record.state === 'external' && record.data.comment ? record.data.comment + ' · ' : '';
        return '<div class="invoice-row"><div class="invoice-row-name"><span class="invoice-row-label" title="' + escapeHtml(label) + '">' + escapeHtml(label) + '</span><small class="invoice-row-meta' + (marker.error ? ' error' : '') + '" title="' + escapeHtml(comment + sync) + '">' + escapeHtml(comment + sync) + '</small></div><button class="secondary-button" type="button" data-invoice-restore="' + record.id + '">Восстановить</button></div>';
      }).join('');
      if (removedMarkup !== trashMarkup) { $("invoiceTrashList").innerHTML = removedMarkup; trashMarkup = removedMarkup; }
      $("invoiceTrashList").invoiceRecords = trashed;
    } catch (error) {
      if (version === loading && state.folder?.path === folder.path) $("invoiceListState").textContent = error.message;
    }
  }

  function newIdentity() {
    // crypto.randomUUID is unavailable on HTTP LAN origins.
    const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
    const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
    return hex.slice(0, 8) + "-" + hex.slice(8, 12) + "-" + hex.slice(12, 16) + "-" + hex.slice(16, 20) + "-" + hex.slice(20);
  }

  function showPlan(record = null) {
    if (!state.folder?.order || (record && !record.plan_editable)) return;
    const date = record?.data.date || new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Moscow', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    planning = { path: record?.path || state.folder.path, id: record?.id || newIdentity(), record, saved: date, busy: false, conflict: false };
    $("planInvoiceOrder").textContent = state.folder.order.title || planning.path;
    $("planInvoiceDate").value = date;
    $("planInvoiceOperation").value = record?.data.operation || 'invoice';
    $("planInvoiceAmount").value = record?.data.amount ? (record.data.amount / 100).toFixed(2).replace('.', ',') : '';
    updatePlanFields();
    planning.savedForm = JSON.stringify(planValues());
    $("planInvoiceState").textContent = '';
    $("planInvoiceState").classList.remove('error');
    $("refreshInvoicePlan").hidden = true;
    $("saveInvoicePlan").disabled = false;
    $("saveInvoicePlan").textContent = record ? 'Сохранить' : 'Запланировать';
    $("planInvoiceDialog").showModal(); $("planInvoiceDate").focus();
  }

  function closePlan() {
    if (planning?.busy) return;
    planning = null; $("planInvoiceDialog").close();
  }

  function planValues() {
    return { date: $("planInvoiceDate").value, operation: $("planInvoiceOperation").value, amount: $("planInvoiceAmount").value };
  }

  function updatePlanFields() {
    const payment = $("planInvoiceOperation").value !== 'invoice';
    $("planInvoiceAmountLabel").hidden = !payment;
    $("planInvoiceAmount").required = payment;
  }

  async function savePlan() {
    const current = planning;
    if (!current || current.busy || current.conflict) return;
    current.busy = true;
    for (const id of ['planInvoiceDate', 'planInvoiceOperation', 'planInvoiceAmount', 'saveInvoicePlan', 'cancelInvoicePlan']) $(id).disabled = true;
    const status = $("planInvoiceState");
    status.textContent = 'Сохраняю…'; status.classList.remove('error');
    try {
      const record = await request('/api/invoice-plan', { path: current.path, id: current.id, ...planValues(),
        ...(current.record ? { revision: current.record.revision } : {}) });
      current.busy = false; closePlan();
      await refreshList(true);
      notify(invoiceLabel(record) + ' · ' + displayDate(record.data.date));
    } catch (error) {
      status.textContent = error.message + ' Ввод остался в форме.'; status.classList.add('error');
      current.conflict = error.status === 409;
      $("refreshInvoicePlan").hidden = !current.conflict;
    } finally {
      current.busy = false;
      for (const id of ['planInvoiceDate', 'planInvoiceOperation', 'planInvoiceAmount', 'cancelInvoicePlan']) $(id).disabled = false;
      $("saveInvoicePlan").disabled = current.conflict;
    }
  }

  async function checkPlan() {
    const current = planning;
    if (!current || current.busy) return;
    const button = $("refreshInvoicePlan"); button.disabled = true;
    try {
      const record = await request(apiUrl('/api/invoice', current.path, { id: current.id }));
      if (planning !== current) return;
      if (!record.plan_editable) throw new Error('План недоступен для правки');
      current.record = record; current.conflict = false;
      $("planInvoiceState").textContent = 'Сохранено: ' + invoiceLabel(record) + ' · ' + displayDate(record.data.date) + ' ' + planAmount(record) + '. Проверь изменения перед сохранением своего ввода.';
      $("planInvoiceState").classList.remove('error');
      button.hidden = true; $("saveInvoicePlan").disabled = false;
    } catch (error) { $("planInvoiceState").textContent = error.message + ' Выбранная дата осталась в форме.'; }
    finally { button.disabled = false; }
  }

  function showExternal(record = null) {
    const path = record?.path || state.folder?.path;
    if (!path || !state.folder?.order) return;
    attachment = { path, record, file: null, id: record?.id || newIdentity(), busy: false, saved: record?.data.comment || "" };
    $("externalInvoiceTitle").textContent = record ? "Внешний счёт" : "Прикрепить внешний счёт";
    $("externalInvoicePath").textContent = path;
    $("externalInvoiceFile").value = "";
    $("externalInvoiceFileHint").textContent = "Один PDF до 20 МБ";
    $("externalInvoiceDialog").classList.remove("invoice-dragging");
    $("externalInvoiceFileLabel").hidden = Boolean(record);
    $("externalInvoiceName").hidden = !record;
    $("externalInvoiceName").textContent = record?.data.original_name || "";
    $("externalInvoiceComment").value = attachment.saved;
    $("externalInvoiceState").textContent = "";
    $("externalInvoiceState").classList.remove("error");
    $("externalInvoicePdf").hidden = !record;
    $("saveExternalInvoice").textContent = record ? "Сохранить комментарий" : "Прикрепить";
    $("externalInvoiceDialog").showModal();
    (record ? $("externalInvoiceComment") : $("externalInvoiceFile")).focus();
  }

  function closeExternal() {
    if (attachment?.busy) return;
    attachment = null;
    $("externalInvoiceDialog").close();
  }

  function selectExternalFile(file) {
    if (!attachment || attachment.busy || attachment.record) return;
    const status = $("externalInvoiceState");
    if (!file || !/\.pdf$/i.test(file.name) || !file.size || file.size > 20 * 1024 * 1024) {
      status.textContent = "Выбери один PDF до 20 МБ."; status.classList.add("error"); return;
    }
    attachment.file = file;
    attachment.id = newIdentity();
    $("externalInvoiceFileHint").textContent = file.name + " · " + formatSize(file.size);
    status.textContent = ""; status.classList.remove("error");
  }

  async function saveExternal() {
    const current = attachment;
    if (!current || current.busy) return;
    const file = current.file, comment = $("externalInvoiceComment").value;
    const status = $("externalInvoiceState");
    if (!current.record && (!file || !/\.pdf$/i.test(file.name) || file.size > 20 * 1024 * 1024)) {
      status.textContent = "Выбери PDF до 20 МБ."; status.classList.add("error"); return;
    }
    current.busy = true;
    for (const id of ["externalInvoiceFile", "externalInvoiceComment", "saveExternalInvoice", "closeExternalInvoice"]) $(id).disabled = true;
    status.classList.remove("error");
    status.textContent = current.record ? "Сохранение комментария…" : "Загрузка PDF на M4…";
    try {
      if (!current.record) {
        const pdf = await new Promise((resolve, reject) => {
          const reader = new FileReader(); reader.onerror = () => reject(new Error("Не удалось прочитать PDF на этом компьютере"));
          reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.readAsDataURL(file);
        });
        current.record = await request("/api/invoice-upload", { path: current.path, id: current.id, name: file.name, comment, pdf });
      }
      if (current.record.data.comment !== comment) current.record = await request("/api/invoice-comment", {
        path: current.path, id: current.record.id, revision: current.record.revision, comment,
      });
      current.saved = comment;
      current.busy = false;
      closeExternal();
      await refreshList(true);
    } catch (error) { status.textContent = error.message + " Ввод остался в форме."; status.classList.add("error"); }
    finally {
      current.busy = false;
      for (const id of ["externalInvoiceFile", "externalInvoiceComment", "saveExternalInvoice", "closeExternalInvoice"]) $(id).disabled = false;
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
      pendingCreate = { path, source, id: newIdentity() };
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
  $("attachInvoice").addEventListener("click", () => showExternal());
  $("planInvoice").addEventListener('click', () => showPlan());
  $("planInvoiceOperation").addEventListener('change', updatePlanFields);
  $("planInvoiceForm").addEventListener('submit', (event) => { event.preventDefault(); savePlan(); });
  $("cancelInvoicePlan").addEventListener('click', closePlan);
  $("planInvoiceDialog").addEventListener('cancel', (event) => { event.preventDefault(); closePlan(); });
  $("refreshInvoicePlan").addEventListener('click', checkPlan);
  $("closeExternalInvoice").addEventListener("click", closeExternal);
  $("externalInvoiceDialog").addEventListener("cancel", (event) => { event.preventDefault(); closeExternal(); });
  $("externalInvoiceForm").addEventListener("submit", (event) => { event.preventDefault(); saveExternal(); });
  $("externalInvoiceFile").addEventListener("change", (event) => selectExternalFile(event.target.files[0]));
  $("externalInvoicePdf").addEventListener("click", () => { if (attachment?.record) action(() => showInvoicePreview(attachment.record)); });
  $("externalInvoiceDialog").addEventListener("dragover", (event) => {
    if (!Array.from(event.dataTransfer?.types || []).includes("Files")) return;
    event.preventDefault(); event.stopPropagation();
    const allowed = attachment && !attachment.busy && !attachment.record;
    event.dataTransfer.dropEffect = allowed ? "copy" : "none";
    $("externalInvoiceDialog").classList.toggle("invoice-dragging", Boolean(allowed));
  });
  $("externalInvoiceDialog").addEventListener("dragleave", (event) => {
    if (!event.currentTarget.contains(event.relatedTarget)) event.currentTarget.classList.remove("invoice-dragging");
  });
  $("externalInvoiceDialog").addEventListener("dragend", () => $("externalInvoiceDialog").classList.remove("invoice-dragging"));
  $("externalInvoiceDialog").addEventListener("drop", (event) => {
    if (!Array.from(event.dataTransfer?.types || []).includes("Files")) return;
    event.preventDefault(); event.stopPropagation();
    $("externalInvoiceDialog").classList.remove("invoice-dragging");
    if (!attachment || attachment.busy || attachment.record) return;
    const files = Array.from(event.dataTransfer.files || []);
    const directory = Array.from(event.dataTransfer.items || []).some((item) => item.webkitGetAsEntry?.()?.isDirectory);
    if (directory || files.length !== 1) {
      $("externalInvoiceState").textContent = "Перетащи один PDF до 20 МБ, без папок.";
      $("externalInvoiceState").classList.add("error"); return;
    }
    selectExternalFile(files[0]);
  });
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
    const plan = event.target.closest('[data-invoice-plan]');
    if (plan) {
      const record = $("invoiceList").invoiceRecords?.find((item) => item.id === plan.dataset.invoicePlan && item.path === state.folder?.path);
      if (record) showPlan(record);
      return;
    }
    const status = event.target.closest('[data-invoice-status]');
    if (status) {
      const record = $("invoiceList").invoiceRecords?.find((item) => item.id === status.dataset.invoiceStatus && item.path === state.folder?.path);
      if (record) action(() => toggleListStatus(record, status.dataset.value));
      return;
    }
    const remove = event.target.closest('[data-invoice-remove]');
    if (remove) {
      const record = $("invoiceList").invoiceRecords?.find((item) => item.id === remove.dataset.invoiceRemove && item.path === state.folder?.path);
      if (record) {
        pendingRemoval = record;
        $("removeInvoiceName").textContent = invoiceLabel(record);
        $("removeInvoicePath").textContent = record.filename ? record.pdf_path + ' → # bills/.trash' : record.state === 'planned' ? 'План на ' + displayDate(record.data.date) + ' ' + planAmount(record) : 'Черновик без PDF';
        $("removeInvoiceState").textContent = '';
        $("removeInvoiceState").classList.remove('error');
        $("removeInvoiceDialog").showModal(); $("cancelRemoveInvoice").focus();
      }
      return;
    }
    const copy = event.target.closest("[data-invoice-copy]");
    const edit = event.target.closest("[data-invoice-edit]");
    const view = event.target.closest("[data-invoice-view]");
    if (view) {
      const record = $("invoiceList").invoiceRecords?.find((item) => item.id === view.dataset.invoiceView && item.path === state.folder?.path);
      if (record) action(() => showInvoicePreview(record));
      return;
    }
    if (copy) action(() => create(copy.dataset.invoiceCopy));
    else if (edit) {
      const record = $("invoiceList").invoiceRecords?.find((item) => item.id === edit.dataset.invoiceEdit && item.path === state.folder?.path);
      if (record) { if (record.state === "external") showExternal(record); else show(record); }
    }
  });
  $("cancelRemoveInvoice").addEventListener('click', () => { if (!removing) { pendingRemoval = null; $("removeInvoiceDialog").close(); } });
  $("removeInvoiceDialog").addEventListener('cancel', (event) => { if (removing) event.preventDefault(); else pendingRemoval = null; });
  $("removeInvoiceForm").addEventListener('submit', async (event) => {
    event.preventDefault();
    const record = pendingRemoval;
    if (!record || removing) return;
    removing = true;
    $("cancelRemoveInvoice").disabled = $("confirmRemoveInvoice").disabled = true;
    $("removeInvoiceState").textContent = 'Перенос в корзину…'; $("removeInvoiceState").classList.remove('error');
    try {
      await request('/api/invoice-remove', {path:record.path,id:record.id,revision:record.revision,confirmed:true});
      pendingRemoval = null; $("removeInvoiceDialog").close(); await refreshList(true);
    } catch (error) { $("removeInvoiceState").textContent = error.message; $("removeInvoiceState").classList.add('error'); }
    finally { removing = false; $("cancelRemoveInvoice").disabled = $("confirmRemoveInvoice").disabled = false; }
  });
  $("invoiceTrashList").addEventListener('click', (event) => {
    const button = event.target.closest('[data-invoice-restore]');
    const record = button && $("invoiceTrashList").invoiceRecords?.find((item) => item.id === button.dataset.invoiceRestore && item.path === state.folder?.path);
    if (record) action(async () => {
      button.disabled = true;
      try { await request('/api/invoice-restore', {path:record.path,id:record.id,revision:record.revision}); await refreshList(true); }
      finally { button.disabled = false; }
    });
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
  document.addEventListener("manager-invoice-updated", () => refreshList(true));
  window.addEventListener("beforeunload", (event) => {
    if (removing || planning?.busy || (planning && JSON.stringify(planValues()) !== planning.savedForm) || editor?.dirty || editor?.saving || editor?.issuing || attachment?.busy || (attachment && $("externalInvoiceComment").value !== attachment.saved)) { event.preventDefault(); event.returnValue = ""; }
  });
  setInterval(() => { if (!document.hidden && state.view !== "orders" && !$("invoiceSection").hidden) refreshList(true); }, 5000);
  refreshList();
})();

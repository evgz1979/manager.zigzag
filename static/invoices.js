/* Invoice fields live in SQLite; a browser draft is never the saved copy. */
(() => {
  let editor = null, attachment = null, listedPath = null, listMarkup = null, trashMarkup = null, loading = 0, pendingCreate = null;
  let folderCandidates = [], candidatePath = null, candidateLoading = 0, candidateMarkup = null;
  let pendingRemoval = null, removing = false, planning = null;
  const statusSaving = new Set();
  const listStatusLabels = { active: "Актуально", inactive: "Неактуально", later: "Позже", sent: "Отправлен", paid: "Оплачен" };
  const planLabels = { invoice: 'Запланирована выписка счёта', incoming: 'Запланировано получение оплаты', outgoing: 'Запланирован платёж' };
  // Формирует отображаемое название счёта или плана.
  // Результат вычисляется из переданных аргументов и текущего состояния компонента.
  const invoiceLabel = (record) => record.state === 'planned' ? planLabels[record.data.operation || 'invoice'] || 'Запланировано' : record.state === 'external' ? record.data.original_name : (record.data.kind === 'contract' ? 'Счёт-договор' : 'Счёт') + ' № ' + record.number;
  // Форматирует сохранённую дату для показа пользователю.
  // Использует `value.split('-').reverse().join`, `value.split('-').reverse`, `value.split`.
  const displayDate = (value) => typeof value === 'string' ? value.split('-').reverse().join('.') : 'Дата не распознана';
  // Форматирует сохранённую дату для показа пользователю.
  // Использует `Date`, `Number.isNaN`, `end.getTime`.
  const displayPlanDate = (record) => {
    const start = record.data.date, end = new Date(start + 'T00:00:00Z');
    if (record.data.period !== 'week' || Number.isNaN(end.getTime())) return displayDate(start);
    end.setUTCDate(end.getUTCDate() + 6);
    return 'Неделя ' + displayDate(start) + ' — ' + displayDate(end.toISOString().slice(0, 10));
  };
  // Выбирает сохранённую сумму плана для формы и списка.
  // Использует `['incoming', 'outgoing'].includes`, `Number.isSafeInteger`, `cash`.
  const planAmount = (record) => ['incoming', 'outgoing'].includes(record.data.operation) && Number.isSafeInteger(record.data.amount) ? (record.data.operation === 'incoming' ? '+' : '−') + cash(record.data.amount) : '';
  const fields = { kind: "invoiceKind", number: "invoiceNumber", date: "invoiceDate", due_date: "invoiceDue",
    buyer_name: "invoiceBuyer", buyer_inn: "invoiceBuyerInn", buyer_kpp: "invoiceBuyerKpp", buyer_address: "invoiceBuyerAddress",
    note: "invoiceNote", work_start: "invoiceWorkStart", work_end: "invoiceWorkEnd", terms: "invoiceTerms" };
  // Форматирует денежное значение для соответствующего компонента.
  // Использует `Intl.NumberFormat`.
  const cash = (cents) => new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB" }).format(cents / 100);
  // Собирает URL запроса с безопасным кодированием параметров.
  // Использует `/api/invoice-preview`, `/api/invoice-pdf`.
  const pdfUrl = (record, preview = false) => apiUrl(preview ? "/api/invoice-preview" : "/api/invoice-pdf", record.path, { id: record.id });
  // Показывает сообщение пользователю и предусмотренное действие отмены.
  // Использует `$`, `$("invoiceEditorState").classList.toggle`.
  const message = (text, error = false) => {
    $("invoiceEditorState").textContent = text;
    $("invoiceEditorState").classList.toggle("error", error);
  };

  // Показывает счета, планы и состояние документов текущего заказа.
  // Обращается к DOM текущего документа или переданного контейнера.
  function renderInvoiceList(records) {
    // Keep the input alive while the native file picker is open or cancelled.
    const picker = document.activeElement;
    if (picker?.matches('input[type="file"][data-doc-action="files"]') && !picker.files.length) return;
    const documentFocus = InvoiceDocuments.focusKey();
    const focusedPlan = document.activeElement?.dataset.invoicePlan;
    const focusedSchedule = document.activeElement?.dataset.invoiceSchedule;
    const focusedReconciliation = document.activeElement?.dataset.invoiceReconciliation;
    const focused = document.activeElement?.closest('[data-invoice-status]');
    const focusKey = focused ? { id: focused.dataset.invoiceStatus, value: focused.dataset.value } : null;
    const sources = new Map(records.filter((record) => ['issued', 'external'].includes(record.state)).map((record) => [record.id, record]));
    const linkedPlans = new Map();
    const rows = records.filter((record) => {
      const source = record.state === 'planned' ? sources.get(record.data.invoice_id) : null;
      if (!source || source.path !== record.path) return true;
      if (!linkedPlans.has(source.id)) linkedPlans.set(source.id, []);
      linkedPlans.get(source.id).push(record);
      return false;
    });
    $("invoiceCount").textContent = rows.length || "";
    const markup = rows.map((record) => {
      const external = record.state === "external";
      const label = invoiceLabel(record);
      const date = record.state === 'planned' ? displayPlanDate(record) : displayDate(record.data.date);
      if (record.state === 'planned') {
        const completed = record.data._calendar_completed === true;
        const details = [date, planAmount(record), record.data.invoice_label, record.data.text].filter(Boolean).join(' · ');
        const planLabelClass = completed ? ' invoice-completed-plan-label' : (record.data.operation || 'invoice') === 'invoice' ? ' invoice-issuance-plan-label' : '';
        const planLabel = (completed ? '✓ Выполнено · ' : '') + label;
        return '<div class="invoice-row"><button type="button" class="invoice-row-name' + (completed ? ' invoice-plan-completed' : '') + '" data-invoice-plan="' + record.id + '" title="' + escapeHtml(planLabel + ' · ' + details) + '"' + (record.plan_editable ? '' : ' disabled') + '><span class="invoice-row-label' + planLabelClass + '">' + escapeHtml(planLabel) + '</span><small class="invoice-row-meta" title="' + escapeHtml(details) + '">' + escapeHtml(details) + (record.plan_editable ? '' : ' · Неизвестный формат плана') + '</small></button><div class="invoice-row-actions"><button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + record.id + '" aria-label="В корзину · ' + escapeHtml(planLabel + ' · ' + date) + '">×</button></div></div>';
      }
      const details = (external ? 'Внешний · ' : '') + date;
      const comment = external ? record.data.comment?.trim() : '';
      const heading = comment || label;
      const secondary = (comment ? label + ' · ' : '') + details;
      const sync = record.state === "draft" ? "Черновик" : record.sync_error ? "PDF в базе · " + record.sync_error + " · автоповтор" : record.sync_pending ? "PDF в базе · копия в # bills ожидает выгрузки" : "PDF в # bills";
      const busy = statusSaving.has(record.id) || InvoiceDocuments.isBusy(record.id);
      const status = record.list_status === undefined ? 'none' : record.list_status;
      const buttons = '<div class="invoice-list-status" role="group" aria-label="Отметка счёта · ' + escapeHtml(label) + '" aria-busy="' + busy + '">' +
        Object.entries(listStatusLabels).map(([value, name]) => '<button type="button" class="secondary-button" data-invoice-status="' + record.id + '" data-value="' + value + '" aria-pressed="' + (status === value) + '" title="' + (status === null ? 'Неизвестная отметка сохранена без замены' : status === value ? 'Снять отметку «' + name + '»' : name) + '"' + (busy || status === null ? ' disabled' : '') + '>' + name + '</button>').join('') + '</div>';
      const schedule = record.state === 'draft' ? '' : '<button class="secondary-button" type="button" data-invoice-schedule="' + record.id + '" aria-label="Запланировать оплату · ' + escapeHtml(label) + '">Запланировать</button>';
      const plans = (linkedPlans.get(record.id) || []).map((plan) => {
        const inactive = record.list_status === 'inactive' || plan.data._calendar_inactive === true;
        const completed = plan.data._calendar_completed === true;
        const status = [completed ? '✓ Выполнено' : '', inactive ? 'Неактуально' : ''].filter(Boolean).join(' · ') || 'Запланировано';
        const summary = [status + ': ' + planAmount(plan), displayPlanDate(plan), plan.data.text].filter(Boolean).join(' · ');
        const description = [completed ? 'Выполнено' : '', inactive ? 'Неактуально' : '', invoiceLabel(plan), label, displayPlanDate(plan), planAmount(plan), plan.data.text].filter(Boolean).join(' · ');
        return '<div class="invoice-linked-entry"><button type="button" class="invoice-linked-plan' + (inactive ? ' invoice-linked-inactive' : '') + (completed ? ' invoice-plan-completed' : '') + '" data-invoice-plan="' + plan.id + '" data-operation="' + escapeHtml(plan.data.operation || 'invoice') + '" aria-label="' + escapeHtml(description) + '" title="' + escapeHtml(description) + '"' + (plan.plan_editable ? '' : ' disabled') + '>' + escapeHtml(summary) + (plan.plan_editable ? '' : ' · Неизвестный формат плана') + '</button><button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + plan.id + '" aria-label="' + escapeHtml('В корзину · ' + description) + '">×</button></div>';
      }).join('');
      return '<div class="invoice-row" data-invoice-row="' + record.id + '"><div class="invoice-row-content"><button type="button" class="invoice-row-name" data-invoice-' + (external ? 'view' : 'edit') + '="' + record.id + '"><span class="invoice-row-label' + (comment ? ' invoice-row-comment' : '') + '" title="' + escapeHtml(heading) + '">' + escapeHtml(heading) + '</span><small class="invoice-row-meta" title="' + escapeHtml(secondary + ' · ' + sync) + '">' + escapeHtml(secondary) + '<span class="invoice-row-state' + (record.sync_error ? ' error' : '') + '"> · ' + escapeHtml(sync) + '</span></small></button>' + (plans ? '<div class="invoice-linked-plans">' + plans + '</div>' : '') + InvoiceDocuments.markup(record) + '</div><div class="invoice-row-actions">' + (external ? '' : '<strong>' + cash(record.data.total) + '</strong>') + buttons + schedule + InvoiceDocuments.button(record) +
        (typeof ReconciliationUI === 'undefined' ? '' : ReconciliationUI.button(record)) + (external ? '<button class="secondary-button" type="button" data-invoice-view="' + record.id + '">PDF</button>' : record.state !== "draft" ? '<a class="secondary-button" href="' + escapeHtml(pdfUrl(record)) + '" target="_blank" rel="noopener">PDF ↗</a>' : '') + (external ? '' : '<button class="secondary-button" type="button" data-invoice-copy="' + record.id + '">На основе</button>') + '<button class="secondary-button invoice-remove" type="button" data-invoice-remove="' + record.id + '" title="В корзину" aria-label="' + escapeHtml('В корзину · ' + label) + '">×</button></div></div>';
    }).join("");
    if (markup !== listMarkup) {
      $("invoiceList").innerHTML = markup;
      listMarkup = markup;
      if (focusKey && document.activeElement === document.body) focusStatusButton(focusKey);
      if (focusedPlan && document.activeElement === document.body) [...$("invoiceList").querySelectorAll('[data-invoice-plan]')].find((button) => button.dataset.invoicePlan === focusedPlan)?.focus({ preventScroll: true });
      if (focusedSchedule && document.activeElement === document.body) [...$("invoiceList").querySelectorAll('[data-invoice-schedule]')].find((button) => button.dataset.invoiceSchedule === focusedSchedule)?.focus({ preventScroll: true });
      if (focusedReconciliation && document.activeElement === document.body) [...$("invoiceList").querySelectorAll('[data-invoice-reconciliation]')].find(button => button.dataset.invoiceReconciliation === focusedReconciliation)?.focus({ preventScroll: true });
      InvoiceDocuments.restoreFocus(documentFocus);
    }
    // Store records on this exact list, independent of grid positions.
    $("invoiceList").invoiceRecords = records;
  }

  // Возвращает фокус на статус выбранной строки счёта.
  // Обращается к DOM текущего документа или переданного контейнера.
  function focusStatusButton(key) {
    [...$("invoiceList").querySelectorAll('[data-invoice-status]')].find((button) =>
      button.dataset.invoiceStatus === key.id && button.dataset.value === key.value)?.focus({ preventScroll: true });
  }

  // Сохраняет изменение статуса строки счёта.
  // Использует `/api/invoice-list-status`.
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

  // Перечитывает счета из SQLite с учётом открытых редакторов.
  // Использует `/api/invoices`.
  async function refreshList(force = false) {
    const folder = state.folder;
    const visible = Boolean(folder?.order) && !isWorkOrderPath(folder.path);
    $("invoiceSection").hidden = !visible;
    if (!visible) { listedPath = null; candidatePath = null; ++candidateLoading; ++loading; return; }
    if (listedPath === folder.path && !force) return;
    const version = ++loading;
    if (listedPath !== folder.path) {
      $("invoiceList").replaceChildren(); $("invoiceCount").textContent = "";
      listMarkup = null;
      trashMarkup = null; $("invoiceTrash").hidden = true; $("invoiceTrash").open = false;
      $("invoiceListState").textContent = "Загрузка счетов…";
      folderCandidates = []; candidatePath = folder.path; candidateMarkup = null;
      renderCandidates();
      checkInvoiceFolder();
    }
    listedPath = folder.path;
    try {
      const result = await request(apiUrl("/api/invoices", folder.path));
      if (version !== loading || state.folder?.path !== folder.path) return;
      $("invoiceListState").textContent = result.items.length ? "" : "Запланируй выписку, прикрепи PDF или выпиши счёт по этому заказу.";
      renderInvoiceList(result.items);
      const trashed = result.trash || [];
      const known = new Set([...result.items, ...trashed].flatMap((record) => [record.filename,
        ...(record.closing_documents || []).map((item) => item.filename), ...(record.closing_documents_trash || []).map((item) => item.filename)])
        .filter(Boolean).map((name) => name.normalize('NFC').toLowerCase()));
      folderCandidates = folderCandidates.filter((item) => !known.has(item.name.normalize('NFC').toLowerCase()));
      renderCandidates();
      $("invoiceTrash").hidden = !trashed.length;
      $("invoiceTrashCount").textContent = trashed.length;
      const removedMarkup = trashed.map((record) => {
        const label = invoiceLabel(record), marker = record.trash;
        const sync = marker.error ? marker.error + ' · автоповтор' : marker.state === 'pending' ? 'Перенос PDF в .trash…' : record.filename ? 'В корзине · # bills/.trash' : record.state === 'planned' ? 'План в корзине · ' + displayPlanDate(record) + ' ' + planAmount(record) : 'Черновик в корзине';
        const comment = record.state === 'external' && record.data.comment ? record.data.comment + ' · ' : '';
        return '<div class="invoice-row"><div class="invoice-row-name"><span class="invoice-row-label" title="' + escapeHtml(label) + '">' + escapeHtml(label) + '</span><small class="invoice-row-meta' + (marker.error ? ' error' : '') + '" title="' + escapeHtml(comment + sync) + '">' + escapeHtml(comment + sync) + '</small></div><button class="secondary-button" type="button" data-invoice-restore="' + record.id + '">Восстановить</button></div>';
      }).join('');
      if (removedMarkup !== trashMarkup) { $("invoiceTrashList").innerHTML = removedMarkup; trashMarkup = removedMarkup; }
      $("invoiceTrashList").invoiceRecords = trashed;
    } catch (error) {
      if (version === loading && state.folder?.path === folder.path) $("invoiceListState").textContent = error.message;
    }
  }

  // Показывает найденные ещё не прикреплённые PDF из # bills.
  // Использует `/api/file`.
  function renderCandidates() {
    const list = $("invoiceCandidates"), focused = document.activeElement?.dataset.invoiceCandidate;
    const markup = folderCandidates.map((item) => '<div class="invoice-row invoice-candidate"><div class="invoice-row-content"><a class="invoice-row-name" href="' +
      escapeHtml(apiUrl('/api/file', candidatePath + '/# bills/' + item.name)) + '" target="_blank" rel="noopener"><span class="invoice-row-label">' + escapeHtml(item.name) +
      '</span></a><small class="invoice-row-meta">В папке найден новый счёт · ' + escapeHtml(formatSize(item.size)) + '</small></div><button type="button" class="secondary-button" data-invoice-candidate="' +
      escapeHtml(item.name) + '" aria-label="Прикрепить найденный счёт · ' + escapeHtml(item.name) + '">Прикрепить?</button></div>').join('');
    if (markup === candidateMarkup) return;
    list.innerHTML = markup; candidateMarkup = markup;
    if (focused && document.activeElement === document.body) [...list.querySelectorAll('[data-invoice-candidate]')]
      .find((button) => button.dataset.invoiceCandidate === focused)?.focus({ preventScroll: true });
  }

  // Явно запрашивает проверку непосредственных файлов # bills.
  // Использует `/api/invoice-folder-candidates`.
  async function checkInvoiceFolder() {
    const path = state.folder?.path;
    if (!state.folder?.order || isWorkOrderPath(path)) return;
    const version = ++candidateLoading, status = $("invoiceFolderState");
    $("checkInvoiceFolder").disabled = true;
    status.textContent = 'Проверка # bills…'; status.classList.remove('error');
    try {
      const result = await request(apiUrl('/api/invoice-folder-candidates', path));
      if (version !== candidateLoading || state.folder?.path !== path) return;
      candidatePath = path; folderCandidates = result.items; renderCandidates();
      status.textContent = [result.items.length ? 'Найдено новых PDF: ' + result.items.length : 'Новых PDF нет', result.warning].filter(Boolean).join(' · ');
    } catch (error) {
      if (version === candidateLoading && state.folder?.path === path) {
        status.textContent = 'Не удалось проверить # bills: ' + error.message; status.classList.add('error');
      }
    } finally { if (version === candidateLoading) $("checkInvoiceFolder").disabled = false; }
  }

  // Создаёт новый UUID клиентского намерения для защиты от повтора.
  // Использует `crypto.getRandomValues`, `Uint8Array`, `[...bytes].map((b) => b.toString(16).padStart(2, "0")).join`.
  function newIdentity() {
    // crypto.randomUUID is unavailable on HTTP LAN origins.
    const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
    const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
    return hex.slice(0, 8) + "-" + hex.slice(8, 12) + "-" + hex.slice(12, 16) + "-" + hex.slice(16, 20) + "-" + hex.slice(20);
  }

  // Открывает редактор самостоятельного или связанного плана платежа.
  // Использует `Intl.DateTimeFormat`, `Date`.
  function showPlan(record = null, options = {}) {
    if ((record && !record.plan_editable) || (!record && !options.calendar && !state.folder?.order)) return;
    const path = record ? record.path : options.source?.path || (options.calendar ? '' : state.folder.path);
    const date = record?.data.date || options.date || new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Moscow', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    planning = { path, id: record?.id || newIdentity(), record, source: options.source || null, calendar: Boolean(options.calendar),
      busy: false, sourceLoading: false, conflict: false };
    for (const id of ['planInvoicePeriod', 'planInvoiceDate', 'planInvoiceOperation', 'planInvoiceAmount', 'planInvoiceText', 'deleteInvoicePlan', 'cancelInvoicePlan']) $(id).disabled = false;
    $("planInvoiceOrder").textContent = path ? (state.orders.find((order) => order.path === path)?.title || (state.folder?.path === path ? state.folder.order?.title : '') || path) : 'Оплата без заказа';
    $("planInvoiceSource").hidden = !(options.source || record?.data.invoice_label);
    $("planInvoiceSource").textContent = options.source ? invoiceLabel(options.source) : record?.data.invoice_label || '';
    $("planInvoiceDate").value = date;
    $("planInvoicePeriod").value = record?.data.period || options.period || 'day';
    normalizePlanDate();
    $("planInvoiceOperation").value = record?.data.operation || options.operation || (options.source || options.calendar ? 'incoming' : 'invoice');
    const amount = record?.data.amount ?? options.source?.data.total;
    $("planInvoiceAmount").value = amount ? (amount / 100).toFixed(2).replace('.', ',') : '';
    $("planInvoiceText").value = record?.data.text || '';
    $("deleteInvoicePlan").hidden = !record || Boolean(record.path);
    updatePlanFields();
    planning.savedForm = JSON.stringify(planValues());
    $("planInvoiceState").textContent = '';
    $("planInvoiceState").classList.remove('error');
    $("refreshInvoicePlan").hidden = true;
    $("saveInvoicePlan").disabled = false;
    $("saveInvoicePlan").textContent = record ? 'Сохранить' : 'Запланировать';
    $("planInvoiceDialog").showModal(); $("planInvoiceDate").focus();
    if (options.source) readPlanSource(planning);
  }

  // Закрывает форму плана и очищает её локальное состояние.
  // Использует `$("planInvoiceDialog").close`, `$`.
  function closePlan() {
    if (planning?.busy) return;
    planning = null; $("planInvoiceDialog").close();
  }

  // Собирает текущие значения формы плана платежа.
  // Использует `$`.
  function planValues() {
    return { path: planning?.path,
      date: $("planInvoiceDate").value, period: $("planInvoicePeriod").value, operation: $("planInvoiceOperation").value, amount: $("planInvoiceAmount").value, text: $("planInvoiceText").value };
  }

  // Нормализует дату плана относительно дневного или недельного периода.
  // Использует `$`, `Date`, `Number.isNaN`.
  function normalizePlanDate() {
    const weekly = $("planInvoicePeriod").value === 'week';
    $("planInvoiceDateCaption").textContent = weekly ? 'Неделя с' : 'День';
    $("planInvoiceWeekHint").hidden = !weekly;
    $("planInvoiceWeekHint").textContent = '';
    const date = new Date($("planInvoiceDate").value + 'T00:00:00Z');
    if (!weekly || Number.isNaN(date.getTime())) return;
    date.setUTCDate(date.getUTCDate() - (date.getUTCDay() + 6) % 7);
    $("planInvoiceDate").value = date.toISOString().slice(0, 10);
    $("planInvoiceWeekHint").textContent = displayPlanDate({ data: { date: $("planInvoiceDate").value, period: 'week' } });
  }

  // Обновляет доступность и подписи зависимых полей плана.
  // Обращается к DOM текущего документа или переданного контейнера.
  function updatePlanFields() {
    const payment = $("planInvoiceOperation").value !== 'invoice';
    $("planInvoiceAmountLabel").hidden = !payment;
    $("planInvoiceAmount").required = payment;
    $("planInvoiceTextLabel").hidden = !payment;
    const invoiceOption = $("planInvoiceOperation").querySelector('[value="invoice"]');
    invoiceOption.hidden = invoiceOption.disabled = Boolean(planning?.calendar || planning?.source || planning?.record?.data.invoice_id);
  }

  // Читает выбранный источник плана из текущей формы.
  // Использует `/api/invoice-plan-source`.
  async function readPlanSource(current, preserveInput = false) {
    if (!current || current.sourceLoading) return;
    const previous = $("planInvoiceAmount").value;
    current.sourceLoading = true; $("saveInvoicePlan").disabled = true;
    $("refreshInvoicePlan").disabled = true;
    $("planInvoiceState").textContent = 'Читаю сумму счёта…';
    try {
      const source = await request(apiUrl('/api/invoice-plan-source', current.path, { id: current.source.id }));
      if (planning !== current) return;
      current.source = { ...current.source, ...source };
      if (!preserveInput && $("planInvoiceAmount").value === previous && Number.isSafeInteger(source.total)) $("planInvoiceAmount").value = (source.total / 100).toFixed(2).replace('.', ',');
      $("planInvoiceSource").textContent = source.label;
      $("planInvoiceState").textContent = source.hint || 'Сумма из счёта: ' + cash(source.total) + '. Можно указать часть оплаты.';
      $("planInvoiceState").classList.remove('error');
      current.conflict = false; $("refreshInvoicePlan").hidden = true;
    } catch (error) {
      if (planning !== current) return;
      current.conflict = true;
      $("planInvoiceState").textContent = error.message + ' Ввод остался в форме.';
      $("planInvoiceState").classList.add('error'); $("refreshInvoicePlan").hidden = false;
    } finally {
      current.sourceLoading = false;
      if (planning === current) {
        $("saveInvoicePlan").disabled = current.conflict;
        $("deleteInvoicePlan").disabled = current.conflict;
        $("refreshInvoicePlan").disabled = false;
      }
    }
  }

  // Сохраняет план платежа с UUID и ожидаемой версией.
  // Использует `/api/invoice-plan`.
  async function savePlan() {
    const current = planning;
    if (!current || current.busy || current.conflict || current.sourceLoading) return;
    normalizePlanDate();
    current.busy = true;
    for (const id of ['planInvoicePeriod', 'planInvoiceDate', 'planInvoiceOperation', 'planInvoiceAmount', 'planInvoiceText', 'deleteInvoicePlan', 'saveInvoicePlan', 'cancelInvoicePlan']) $(id).disabled = true;
    const status = $("planInvoiceState");
    status.textContent = 'Сохраняю…'; status.classList.remove('error');
    try {
      const record = await request('/api/invoice-plan', { id: current.id, ...planValues(),
        ...(current.record ? { revision: current.record.revision } : current.source ? { source_invoice: current.source.id, source_revision: current.source.revision } : {}) });
      current.busy = false; closePlan();
      await refreshList(true);
      notify(invoiceLabel(record) + ' · ' + displayPlanDate(record));
      try { await loadOrders(); } catch (error) { notify('План сохранён. Не удалось обновить календарь: ' + error.message, true); }
    } catch (error) {
      status.textContent = error.message + ' Ввод остался в форме.'; status.classList.add('error');
      current.conflict = error.status === 409;
      $("refreshInvoicePlan").hidden = !current.conflict;
    } finally {
      current.busy = false;
      if (!planning || planning === current) {
        for (const id of ['planInvoicePeriod', 'planInvoiceDate', 'planInvoiceOperation', 'planInvoiceAmount', 'planInvoiceText', 'deleteInvoicePlan', 'cancelInvoicePlan']) $(id).disabled = false;
        $("saveInvoicePlan").disabled = current.conflict;
        $("deleteInvoicePlan").disabled = current.conflict;
      }
    }
  }

  // Помещает выбранный план платежа в корзину.
  // Использует `$`, `removeCalendarRecord`, `closePlan`.
  async function deletePlan() {
    const current = planning;
    if (!current?.record || current.record.path || current.busy || current.conflict) return;
    current.busy = true;
    for (const id of ['planInvoicePeriod', 'planInvoiceDate', 'planInvoiceOperation', 'planInvoiceAmount', 'planInvoiceText', 'deleteInvoicePlan', 'saveInvoicePlan', 'cancelInvoicePlan']) $(id).disabled = true;
    $("planInvoiceState").textContent = 'Удаляю…';
    try {
      await removeCalendarRecord({ plan: true, path: '', id: current.id, revision: current.record.revision });
      current.busy = false;
      closePlan();
    } catch (error) {
      current.conflict = error.status === 409;
      $("planInvoiceState").textContent = error.message + ' Твой ввод остался в форме.';
      $("planInvoiceState").classList.add('error');
      $("refreshInvoicePlan").hidden = !current.conflict;
    } finally {
      current.busy = false;
      if (planning === current) {
        for (const id of ['planInvoicePeriod', 'planInvoiceDate', 'planInvoiceOperation', 'planInvoiceAmount', 'planInvoiceText', 'cancelInvoicePlan']) $(id).disabled = false;
        $("deleteInvoicePlan").disabled = $("saveInvoicePlan").disabled = current.conflict;
      }
    }
  }

  // Перечитывает источник плана после конфликта без автоматического повтора.
  // Использует `/api/invoice`.
  async function checkPlan() {
    const current = planning;
    if (!current || current.busy) return;
    if (!current.record && current.source) { await readPlanSource(current, true); return; }
    const button = $("refreshInvoicePlan"); button.disabled = true;
    try {
      const record = await request(apiUrl('/api/invoice', current.path, { id: current.id }));
      if (planning !== current) return;
      if (!record.plan_editable) throw new Error('План недоступен для правки');
      current.record = record; current.conflict = false;
      $("planInvoiceState").textContent = 'Сохранено: ' + invoiceLabel(record) + ' · ' + displayPlanDate(record) + ' ' + planAmount(record) + '. Проверь изменения перед сохранением своего ввода.';
      $("planInvoiceState").classList.remove('error');
      button.hidden = true; $("saveInvoicePlan").disabled = false;
      $("deleteInvoicePlan").disabled = false;
    } catch (error) { $("planInvoiceState").textContent = error.message + ' Выбранная дата осталась в форме.'; }
    finally { button.disabled = false; }
  }

  // Открывает форму прикрепления внешнего PDF к заказу.
  // Использует `newIdentity`, `$`, `$("externalInvoiceDialog").classList.remove`.
  function showExternal(record = null, candidate = null) {
    const path = record?.path || state.folder?.path;
    if (!path || !state.folder?.order) return;
    attachment = { path, record, candidate, file: null, id: record?.id || newIdentity(), busy: false, saved: record?.data.comment || "" };
    $("externalInvoiceTitle").textContent = record ? "Внешний счёт" : "Прикрепить внешний счёт";
    $("externalInvoicePath").textContent = path;
    $("externalInvoiceFile").value = "";
    $("externalInvoiceFileHint").textContent = "Один PDF до 20 МБ";
    $("externalInvoiceDialog").classList.remove("invoice-dragging");
    $("externalInvoiceFileLabel").hidden = Boolean(record || candidate);
    $("externalInvoiceName").hidden = !record && !candidate;
    $("externalInvoiceName").textContent = record?.data.original_name || candidate?.name || "";
    $("externalInvoiceComment").value = attachment.saved;
    $("externalInvoiceState").textContent = "";
    $("externalInvoiceState").classList.remove("error");
    $("externalInvoicePdf").hidden = !record;
    $("saveExternalInvoice").textContent = record ? "Сохранить комментарий" : "Прикрепить";
    $("externalInvoiceDialog").showModal();
    (record || candidate ? $("externalInvoiceComment") : $("externalInvoiceFile")).focus();
  }

  // Закрывает форму внешнего PDF и освобождает выбранный файл.
  // Использует `$("externalInvoiceDialog").close`, `$`.
  function closeExternal() {
    if (attachment?.busy) return;
    attachment = null;
    $("externalInvoiceDialog").close();
  }

  // Проверяет выбранный файл внешнего PDF в браузере.
  // Использует `$`, `/\.pdf$/i.test`, `status.classList.add`.
  function selectExternalFile(file) {
    if (!attachment || attachment.busy || attachment.record || attachment.candidate) return;
    const status = $("externalInvoiceState");
    if (!file || !/\.pdf$/i.test(file.name) || !file.size || file.size > 20 * 1024 * 1024) {
      status.textContent = "Выбери один PDF до 20 МБ."; status.classList.add("error"); return;
    }
    attachment.file = file;
    attachment.id = newIdentity();
    $("externalInvoiceFileHint").textContent = file.name + " · " + formatSize(file.size);
    status.textContent = ""; status.classList.remove("error");
  }

  // Передаёт проверенный внешний PDF и комментарий серверу.
  // Использует `/api/invoice-folder-attach`, `/api/invoice-upload`, `/api/invoice-comment`.
  async function saveExternal() {
    const current = attachment;
    if (!current || current.busy) return;
    const file = current.file, comment = $("externalInvoiceComment").value;
    const status = $("externalInvoiceState");
    if (!current.record && !current.candidate && (!file || !/\.pdf$/i.test(file.name) || file.size > 20 * 1024 * 1024)) {
      status.textContent = "Выбери PDF до 20 МБ."; status.classList.add("error"); return;
    }
    current.busy = true;
    for (const id of ["externalInvoiceFile", "externalInvoiceComment", "saveExternalInvoice", "closeExternalInvoice"]) $(id).disabled = true;
    status.classList.remove("error");
    status.textContent = current.record ? "Сохранение комментария…" : current.candidate ? "Чтение PDF из # bills…" : "Загрузка PDF на M4…";
    try {
      if (!current.record && current.candidate) {
        current.record = await request('/api/invoice-folder-attach', { path: current.path, name: current.candidate.name, key: current.candidate.key, comment });
      } else if (!current.record) {
        const pdf = await new Promise((resolve, reject) => {
          const reader = new FileReader(); reader.onerror = () => reject(new Error("Не удалось прочитать PDF на этом компьютере"));
          reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.readAsDataURL(file);
        });
        current.record = await request("/api/invoice-upload", { path: current.path, id: current.id, name: file.name, comment, pdf });
      }
      if (!current.candidate && current.record.data.comment !== comment) current.record = await request("/api/invoice-comment", {
        path: current.path, id: current.record.id, revision: current.record.revision, comment,
      });
      current.saved = comment;
      current.busy = false;
      if (current.candidate && candidatePath === current.path) {
        folderCandidates = folderCandidates.filter((item) => item.name !== current.candidate.name); renderCandidates();
        $("invoiceFolderState").textContent = 'Счёт прикреплён';
      }
      closeExternal();
      await refreshList(true);
    } catch (error) { status.textContent = error.message + " Ввод остался в форме."; status.classList.add("error"); }
    finally {
      current.busy = false;
      for (const id of ["externalInvoiceFile", "externalInvoiceComment", "saveExternalInvoice", "closeExternalInvoice"]) $(id).disabled = false;
    }
  }

  // Строит строку позиции редактируемого счёта.
  // Экранирует значения полей и задаёт допустимую длину ввода каждой позиции.
  function itemMarkup(item) {
    return '<tr>' + [["name", "Наименование", 500], ["quantity", "Количество", 30], ["unit", "Единица", 16], ["price", "Цена", 30]].map(([key, label, limit]) =>
      '<td><input data-field="' + key + '" aria-label="' + label + '" maxlength="' + limit + '" value="' + escapeHtml(item[key]) + '"' + (["quantity", "price"].includes(key) ? ' inputmode="decimal"' : '') + '></td>').join("") + '<td class="invoice-item-total"></td><td><button class="icon-button" type="button" data-invoice-remember title="Сохранить позицию в товары" aria-label="Сохранить позицию в товары">＋</button><button class="icon-button" type="button" data-invoice-remove aria-label="Удалить позицию">✕</button></td></tr>';
  }

  // Собирает значения полей редактора счёта для сохранения.
  // Использует `Object.fromEntries`, `Object.entries(fields).map`, `Object.entries`.
  function collect() {
    const data = Object.fromEntries(Object.entries(fields).map(([field, id]) => [field, $(id).value]));
    data.seller = { ...editor.record.data.seller };
    data.items = [...$("invoiceItems").rows].map((row) => Object.fromEntries([...row.querySelectorAll("input")].map((input) => [input.dataset.field, input.value])));
    return data;
  }

  // Вычисляет отображаемые итоги позиций счёта.
  // Обращается к DOM текущего документа или переданного контейнера.
  function totals() {
    let total = 0n;
    // Преобразует десятичное значение в масштабированное целое для расчёта.
    // Использует `value.replace(/[\s\u00a0]/g, "").replace`, `value.replace`, `new RegExp("^\\d+(?:\\.\\d{0," + places + "})?$").test`.
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

  // Обновляет доступность действий открытого редактора в модуле счетов и планов платежей.
  // Обращается к DOM текущего документа или переданного контейнера.
  function controls() {
    if (!editor) return;
    const issued = editor.record.state === "issued";
    for (const input of $("invoiceForm").querySelectorAll(".invoice-editor-body input, .invoice-editor-body textarea, .invoice-editor-body select, [data-invoice-remove], [data-invoice-remember]")) input.disabled = issued || Boolean(editor.issuing);
    InvoiceProducts.setEditable(!issued && !editor.issuing);
    $("addInvoiceItem").disabled = issued || Boolean(editor.issuing);
    for (const id of ["saveInvoice", "issueInvoice", "previewInvoice", "closeInvoice"]) $(id).disabled = Boolean(editor.saving || editor.issuing);
    $("saveInvoice").hidden = issued;
    $("issueInvoice").hidden = issued;
    $("addInvoiceItem").hidden = issued;
    $("previewInvoice").textContent = issued ? "Открыть PDF ↗" : "Предпросмотр ↗";
    $("invoiceDraftHint").textContent = issued ? "Выпущен · для изменений создай новый на основе этого" : "Черновик сохраняется автоматически · одна страница";
  }

  // Открывает прежний редактор счёта из карточки заказа или общего списка.
  // Для общего списка сохраняет ключ возврата фокуса; поля и автосохранение используют путь самого счёта.
  function show(record, returnFocus = null) {
    editor = { record, dirty: false, saving: null, issuing: false, timer: null, returnFocus };
    $("invoiceTitle").textContent = (record.data.kind === "contract" ? "Счёт-договор" : "Счёт") + " № " + record.number;
    $("invoiceOrderPath").textContent = record.path;
    for (const [field, id] of Object.entries(fields)) $(id).value = record.data[field] || "";
    $("invoiceItems").innerHTML = record.data.items.map(itemMarkup).join("");
    editor.saved = JSON.stringify(collect());
    message(record.state === "issued" ? "Выпущенный PDF сохранён в базе." : "Черновик сохранён в базе.");
    controls(); totals();
    if (!$("invoiceDialog").open) $("invoiceDialog").showModal();
    $("invoiceBuyer").focus();
    InvoiceProducts.load().catch(() => {});
  }

  // Сохраняет данные открытой формы с ожидаемой версией.
  // Использует `/api/invoice-save`.
  async function save() {
    const current = editor;
    if (!current || current.record.state === "issued") return;
    clearTimeout(current.timer);
    if (current.saving) { await current.saving; if (current.dirty) return save(); return; }
    if (!current.dirty) return;
    const data = collect(), snapshot = JSON.stringify(data);
    message("Сохранение в базе…");
    current.saving = request("/api/invoice-save", { path: current.record.path, id: current.record.id,
      revision: current.record.revision, data });
    controls();
    try {
      const record = await current.saving;
      current.record = record; current.saved = snapshot;
      current.dirty = JSON.stringify(collect()) !== snapshot;
      message(current.dirty ? "Сохраняю оставшиеся правки…" : "Черновик сохранён в базе.");
      refreshList(true);
      document.dispatchEvent(new Event('manager-invoice-saved'));
    } catch (error) { message(error.message + " Ввод остался в форме.", true); throw error; }
    finally { current.saving = null; controls(); }
    if (current.dirty) return save();
  }

  // Закрывает компонент и освобождает его временное состояние в модуле счетов и планов платежей.
  // Управляет отложенным обновлением через таймер или кадр браузера.
  async function close() {
    if (editor?.issuing) return;
    await save();
    const returnFocus = editor?.returnFocus;
    clearTimeout(editor?.timer);
    editor = null; $("invoiceDialog").close(); refreshList(true);
    if (returnFocus) [...$('billsCatalogRows').querySelectorAll('[data-bills-key]')].find(item => item.dataset.billsKey === returnFocus)?.focus({ preventScroll: true });
  }

  // Создаёт черновик из заказа или явную новую правку из общего списка.
  // Повтор использует прежний UUID; выпущенный источник не меняется, редактор открывается только в исходном контексте.
  async function create(source, ownerPath = null, returnFocus = null) {
    const path = ownerPath || state.folder?.path, context = state.folder;
    if (!path || (!source && (!context?.order || context.path !== path))) return;
    if (!pendingCreate || pendingCreate.path !== path || pendingCreate.source !== source) {
      pendingCreate = { path, source, id: newIdentity() };
    }
    $("newInvoice").disabled = true;
    try {
      const record = await request("/api/invoice-create", pendingCreate);
      pendingCreate = null;
      if (state.folder === context) show(record, returnFocus);
      await refreshList(true);
      document.dispatchEvent(new Event('manager-invoice-saved'));
    } finally { $("newInvoice").disabled = false; }
  }

  // Загружает выбранный счёт и открывает его правку поверх общего списка.
  // Черновик меняется на месте, выпущенный создаёт новый «На основе» только по явному действию copy.
  async function openFromCatalog(path, identity, mode, returnFocus) {
    const context = state.folder;
    if (context?.folderKind !== 'bills_root' || editor?.issuing) return;
    await save();
    const record = await request(apiUrl('/api/invoice', path, { id: identity }));
    if (state.folder !== context || state.view !== 'folder') return;
    if (mode === 'edit' && record.state === 'draft') show(record, returnFocus);
    else if (mode === 'copy' && record.state === 'issued') await create(record.id, record.path, returnFocus);
    else throw new Error('Состояние счёта изменилось. Обнови список перед правкой.');
  }

  // Маршрутизирует выбранное действие пользователя внутри компонента.
  // Использует `Promise.resolve().then(work).catch`, `Promise.resolve().then`, `Promise.resolve`.
  function action(work) {
    return Promise.resolve().then(work).catch((error) => {
      if (editor) message(error.message + " Ввод остался в форме.", true);
      else notify(error.message, true);
    });
  }
  // Помечает редактор изменённым и обновляет зависимые поля.
  // Управляет отложенным обновлением через таймер или кадр браузера.
  function changed() {
    if (!editor || editor.record.state !== "draft") return;
    editor.dirty = JSON.stringify(collect()) !== editor.saved;
    totals();
    clearTimeout(editor.timer);
    if (editor.dirty) { message("Есть несохранённые изменения…"); editor.timer = setTimeout(() => action(save), 900); }
  }
  InvoiceDocuments.init({ render: renderInvoiceList, /* Перечитывает данные открытого компонента по установленным правилам в модуле счетов и планов платежей.
   * Использует `refreshList`. */ refresh: () => refreshList(true), /* Принимает подтверждённые данные счёта в локальный редактор.
   * Использует `renderInvoiceList`, `($("invoiceList").invoiceRecords || []).map`, `$`. */ accept: (saved) => {
    if (state.folder?.path !== saved.path) return;
    ++loading;
    renderInvoiceList(($("invoiceList").invoiceRecords || []).map((record) => record.id === saved.id && record.revision <= saved.revision ? saved : record));
  } });
  $("invoiceForm").addEventListener("input", changed);
  $("invoiceForm").addEventListener("change", changed);
  $("invoiceForm").addEventListener("submit", (event) => { event.preventDefault(); action(save); });
  $("closeInvoice").addEventListener("click", () => action(close));
  $("invoiceDialog").addEventListener("cancel", (event) => { event.preventDefault(); action(close); });
  $("newInvoice").addEventListener("click", () => action(() => create()));
  $("attachInvoice").addEventListener("click", () => showExternal());
  $("checkInvoiceFolder").addEventListener("click", checkInvoiceFolder);
  $("invoiceCandidates").addEventListener('click', (event) => {
    const button = event.target.closest('[data-invoice-candidate]');
    if (!button || candidatePath !== state.folder?.path) return;
    const candidate = folderCandidates.find((item) => item.name === button.dataset.invoiceCandidate);
    if (candidate) showExternal(null, candidate);
  });
  $("planInvoice").addEventListener('click', () => showPlan());
  $("planInvoiceOperation").addEventListener('change', updatePlanFields);
  $("planInvoicePeriod").addEventListener('change', normalizePlanDate);
  $("planInvoiceDate").addEventListener('change', normalizePlanDate);
  $("planInvoiceForm").addEventListener('submit', (event) => { event.preventDefault(); savePlan(); });
  $("cancelInvoicePlan").addEventListener('click', closePlan);
  $("deleteInvoicePlan").addEventListener('click', deletePlan);
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
    const allowed = attachment && !attachment.busy && !attachment.record && !attachment.candidate;
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
    if (!attachment || attachment.busy || attachment.record || attachment.candidate) return;
    const files = Array.from(event.dataTransfer.files || []);
    const directory = Array.from(event.dataTransfer.items || []).some((item) => item.webkitGetAsEntry?.()?.isDirectory);
    if (directory || files.length !== 1) {
      $("externalInvoiceState").textContent = "Перетащи один PDF до 20 МБ, без папок.";
      $("externalInvoiceState").classList.add("error"); return;
    }
    selectExternalFile(files[0]);
  });
  // Добавляет ручную позицию или снимок товара в прежний редактор счёта.
  // Пустая начальная строка заменяется товаром; прежние позиции и цены сохраняются, предел — 40 строк.
  function addItem(item = { name: "", quantity: "1", unit: "шт", price: "0" }) {
    if (!editor || editor.record.state !== "draft" || editor.issuing) return;
    const rows = $("invoiceItems").rows, first = rows[0];
    if (item.name && rows.length === 1 && !first.querySelector('[data-field="name"]').value.trim() &&
        first.querySelector('[data-field="quantity"]').value === '1' && Number(first.querySelector('[data-field="price"]').value.replace(',', '.')) === 0) first.remove();
    if ($("invoiceItems").rows.length >= 40) { message("До 40 позиций; PDF должен поместиться на одну страницу.", true); return; }
    $("invoiceItems").insertAdjacentHTML("beforeend", itemMarkup(item));
    $("invoiceItems").lastElementChild.querySelector("input").focus(); changed();
  }
  InvoiceProducts.init(addItem, newIdentity);
  $("addInvoiceItem").addEventListener("click", () => addItem());
  $("invoiceItems").addEventListener("click", (event) => {
    if (event.target.closest('[data-invoice-remember]') && editor?.record.state === 'draft' && !editor.issuing) {
      const item = Object.fromEntries([...event.target.closest('tr').querySelectorAll('input')].map(input => [input.dataset.field, input.value]));
      InvoiceProducts.open('product', item); return;
    }
    if (!event.target.closest("[data-invoice-remove]") || editor?.record.state !== "draft") return;
    if ($("invoiceItems").rows.length === 1) { message("Оставь хотя бы одну позицию.", true); return; }
    event.target.closest("tr").remove(); changed();
  });
  $("invoiceList").addEventListener("click", (event) => {
    const reconciliation = event.target.closest('[data-invoice-reconciliation]');
    if (reconciliation) {
      const record = $("invoiceList").invoiceRecords?.find(item => item.id === reconciliation.dataset.invoiceReconciliation && item.path === state.folder?.path);
      if (record) action(() => ReconciliationUI.open(record));
      return;
    }
    const schedule = event.target.closest('[data-invoice-schedule]');
    if (schedule) {
      const record = $("invoiceList").invoiceRecords?.find((item) => item.id === schedule.dataset.invoiceSchedule && item.path === state.folder?.path);
      if (record) showPlan(null, { source: record });
      return;
    }
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
      document.dispatchEvent(new Event('manager-invoice-saved'));
    } finally { current.issuing = false; controls(); }
  }));
  document.addEventListener("manager-folder-rendered", () => refreshList());
  document.addEventListener('manager-reconciliation-changed', () => refreshList(true));
  document.addEventListener('manager-plan-payment', (event) => action(async () => {
    const { id, path = '', date, period, operation } = event.detail;
    if (id) showPlan(await request(apiUrl('/api/invoice', path, { id })), { calendar: true });
    else showPlan(null, { calendar: true, date, period, operation });
  }));
  document.addEventListener("manager-invoice-updated", () => refreshList(true));
  window.addEventListener("beforeunload", (event) => {
    if (removing || planning?.busy || (planning && JSON.stringify(planValues()) !== planning.savedForm) || editor?.dirty || editor?.saving || editor?.issuing || attachment?.busy || (attachment && $("externalInvoiceComment").value !== attachment.saved)) { event.preventDefault(); event.returnValue = ""; }
  });
  setInterval(() => { if (!document.hidden && state.view !== "orders" && !$("invoiceSection").hidden) refreshList(true); }, 5000);
  refreshList();
  window.ManagerInvoices = { openFromCatalog };
})();

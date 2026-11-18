/* Сверки используют свои карточки; счета остаются у исходных заказов. */
const ReconciliationUI = (() => {
  let assignment = null, refreshVersion = 0, tableMarkup = null, tablePath = null, listMarkup = null, listPath = null;
  const links = new Map();
  const listStatuses = { active: 'Активна', paid: 'Оплачена' };
  const statusSaves = new Set();
  let listRecords = [];
  // Форматирует денежное значение для соответствующего компонента.
  // Использует `Number.isSafeInteger`, `rubles`.
  const money = value => Number.isSafeInteger(value) ? rubles(value) : '—';
  // Форматирует сохранённую дату для показа пользователю.
  // Использует `/^\d{4}-\d{2}-\d{2}$/.test`, `value.split('-').reverse().join`, `value.split('-').reverse`.
  const date = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '') ? value.split('-').reverse().join('.') : '—';

  // Строит список сверок с активными строками перед оплаченными.
  // Сохраняет фокус и прокрутку; связывает цвет клиента только при однозначном совпадении.
  function renderList(folder, records) {
    const byPath = new Map(records.map(item => [item.path.normalize('NFC'), item]));
    const clients = [...state.tree, ...state.groups.flatMap(group => group.children)].filter(node => node.isClient);
    const rows = folder.directories.filter(item => !item.name.startsWith('#'))
      .map(item => ({ item, record: byPath.get(item.path.normalize('NFC')) }))
      .sort((a, b) => Number(a.record?.status === 'paid') - Number(b.record?.status === 'paid'));
    const markup = rows.map(({ item, record }) => {
      const title = record?.title || item.name;
      const client = (record?.client || '').normalize('NFC');
      const matches = clients.filter(node => node.name.normalize('NFC') === client || node.path.normalize('NFC') === client);
      const options = Object.entries(listStatuses).map(([value, label]) => '<option value="' + value + '"' +
        (value === record?.status ? ' selected' : '') + '>' + label + '</option>').join('');
      const status = record ? '<select class="status-badge order-status-select reconciliation-status-select" data-status="' + escapeHtml(record.status) +
        '" data-reconciliation-status="' + escapeHtml(record.id) + '" aria-label="' + escapeHtml('Статус сверки «' + title + '»') +
        '"' + (statusSaves.has(record.id) ? ' disabled' : '') + '>' + options + '</select>' : '—';
      return '<tr role="row"><td role="cell" class="reconciliation-list-title"><a href="?path=' + encodeURIComponent(item.path) +
        '" data-reconciliation-path="' + escapeHtml(item.path) + '">' + escapeHtml(title) + '</a></td>' +
        '<td role="cell" class="reconciliation-list-client" data-empty="' + !client + '">' + ClientBadge.markup(record?.client || '—', matches.length === 1 ? matches[0].path : '') + '</td>' +
        '<td role="cell" class="reconciliation-list-note-cell" data-empty="' + !record?.note + '"><span class="reconciliation-list-note">' + escapeHtml(record?.note || '—') + '</span></td>' +
        '<td role="cell" class="reconciliation-list-status">' + status + '</td></tr>';
    }).join('');
    listRecords = records;
    if (markup !== listMarkup || listPath !== folder.path) {
      const focused = document.activeElement?.dataset;
      const focusKey = focused?.reconciliationStatus ? 'reconciliationStatus' : 'reconciliationPath';
      const pane = document.querySelector('.content-pane'), scroll = pane.scrollTop;
      const body = $('reconciliationListRows');
      body.innerHTML = markup;
      listMarkup = markup; listPath = folder.path;
      if (focused?.[focusKey] && document.activeElement === document.body) {
        [...body.querySelectorAll('[data-reconciliation-path], [data-reconciliation-status]')]
          .find(el => el.dataset[focusKey] === focused[focusKey])?.focus({ preventScroll: true });
      }
      pane.scrollTop = scroll;
    }
    $('reconciliationListTable').hidden = !rows.length;
    $('reconciliationListCount').textContent = rows.length;
    $('reconciliationListState').textContent = rows.length ? '' : 'Создай первую сверку кнопкой «Создать сверку».';
  }

  // Проверяет, можно ли заменить DOM списка при фоновом обновлении.
  // Сохраняет открытый выбор статуса и ожидает завершения записи.
  function listStatusEditing() {
    return statusSaves.size > 0 || Boolean(document.activeElement?.matches('#reconciliationListRows [data-reconciliation-status]'));
  }

  // Сохраняет выбранный статус по версии строки и переставляет её после ответа.
  // При ошибке возвращает сохранённое значение и перечитывает список без повтора записи.
  async function saveListStatus(control) {
    const folder = state.folder, current = listRecords.find(item => item.id === control.dataset.reconciliationStatus);
    if (!current || statusSaves.has(current.id) || !Object.hasOwn(listStatuses, control.value) || control.value === current.status) return;
    const status = control.value, wasFocused = document.activeElement === control;
    control.value = current.status;
    control.disabled = true;
    statusSaves.add(current.id);
    ++refreshVersion;
    let saved;
    try {
      saved = await request('/api/reconciliation-save', { action: 'status', path: current.path, id: current.id, revision: current.revision, status });
    } catch (error) {
      notify(error.status === 409 ? 'Сверка изменилась. Проверь текущий статус и выбери заново.' : error.message, true);
    } finally {
      control.disabled = false;
      statusSaves.delete(current.id);
    }
    if (state.folder !== folder || state.view !== 'folder') return;
    if (saved) {
      ++refreshVersion;
      renderList(folder, listRecords.map(item => item.id === current.id ? saved : item));
    } else {
      await refresh(true);
    }
    if (wasFocused && state.folder === folder && (document.activeElement === document.body || document.activeElement === control)) {
      [...$('reconciliationListRows').querySelectorAll('[data-reconciliation-status]')]
        .find(el => el.dataset.reconciliationStatus === current.id)?.focus({ preventScroll: true });
    }
  }

  // Строит кнопку сверки в строке счёта.
  // Подсвечивает привязанный счёт и передаёт название сверки в подсказку и доступное имя.
  function button(invoice) {
    if (invoice.reconciliation) links.set(invoice.id, invoice.reconciliation);
    const link = links.get(invoice.id);
    const label = link?.id ? 'Сверка: ' + (link.title || 'недоступна') : 'В сверку';
    return '<button type="button" class="icon-button invoice-action" data-invoice-reconciliation="' + escapeHtml(invoice.id) +
      '" data-assigned="' + Boolean(link?.id) + '" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(label) + '">' + icon('checklist') + '</button>';
  }

  // Показывает назначенные счета, комментарии, состояние и исходные заказы.
  // Сохраняет переносы строк в комментариях; готовые счета открывает через `/api/invoice-pdf`.
  function renderTable(record) {
    const rows = record.invoices || [];
    $('reconciliationInvoiceCount').textContent = rows.length || '';
    const markup = rows.map(item => {
      const pdf = !item.trash && ['issued', 'external'].includes(item.state);
      const label = escapeHtml(item.label);
      const href = pdf ? apiUrl('/api/invoice-pdf', item.path, { id: item.id }) : '?path=' + encodeURIComponent(item.path);
      const stateLabel = item.trash ? 'В корзине' : { draft: 'Черновик', issued: 'Выпущен', external: 'Внешний' }[item.state] || item.state;
      return '<tr data-reconciliation-invoice="' + escapeHtml(item.id) + '">' +
        '<td><a href="' + escapeHtml(href) + '"' + (pdf ? ' target="_blank" rel="noopener"' : ' data-reconciliation-order="' + escapeHtml(item.path) + '"') + '>' + label + '</a></td>' +
        '<td class="reconciliation-invoice-comment">' + escapeHtml(item.comment || '—') + '</td>' +
        '<td>' + date(item.date) + '</td>' +
        '<td><a href="?path=' + encodeURIComponent(item.path) + '" data-reconciliation-order="' + escapeHtml(item.path) + '" title="' + escapeHtml(item.path) + '">' + escapeHtml(item.order_title) + '</a></td>' +
        '<td class="reconciliation-amount">' + money(item.total) + '</td><td>' + escapeHtml(stateLabel) + '</td>' +
        '<td><button type="button" class="secondary-button" data-reconciliation-unlink="' + escapeHtml(item.id) + '" aria-label="' + escapeHtml('Убрать из сверки · ' + item.label) + '">×</button></td></tr>';
    }).join('');
    if (markup !== tableMarkup || tablePath !== record.path) {
      const focused = document.activeElement?.dataset.reconciliationUnlink;
      const pane = document.querySelector('.content-pane'), scroll = pane.scrollTop;
      $('reconciliationInvoiceRows').innerHTML = markup;
      tableMarkup = markup; tablePath = record.path;
      if (focused && document.activeElement === document.body) [...$('reconciliationInvoiceRows').querySelectorAll('[data-reconciliation-unlink]')].find(el => el.dataset.reconciliationUnlink === focused)?.focus({ preventScroll: true });
      pane.scrollTop = scroll;
    }
    $('reconciliationInvoiceState').textContent = rows.length ? '' : 'Добавь счета через значок «В сверку» в исходном заказе.';
    $('reconciliationInvoiceRows').invoiceRecords = rows;
  }

  // Перечитывает данные открытого компонента по установленным правилам в модуле самостоятельных сверок.
  // Принудительно перечитывает список после ошибки записи статуса через `/api/reconciliations`.
  async function refresh(forceList = false) {
    const folder = state.view === 'folder' ? state.folder : null;
    const list = folder?.folderKind === 'reconciliations_root';
    $('reconciliationList').hidden = !list;
    $('reconciliationInvoices').hidden = !folder?.reconciliation;
    if (list) {
      tablePath = null;
      if (listPath !== folder.path) renderList(folder, []);
      if (forceList !== true && listStatusEditing()) return;
      const version = ++refreshVersion;
      try {
        const catalog = await request('/api/reconciliations');
        if (version !== refreshVersion || state.folder !== folder || state.view !== 'folder' || (forceList !== true && listStatusEditing())) return;
        renderList(folder, catalog.items);
      } catch (error) {
        if (version === refreshVersion && state.folder === folder) $('reconciliationListState').textContent = error.message;
      }
      return;
    }
    listPath = null;
    if (!folder?.reconciliation) { tablePath = null; ++refreshVersion; return; }
    if (tablePath !== folder.path) renderTable(folder.reconciliation);
    const version = ++refreshVersion;
    try {
      const record = await request(apiUrl('/api/reconciliation', folder.path));
      if (version !== refreshVersion || state.folder !== folder) return;
      renderTable(record);
      // Не повышаем версию редактора поверх несохранённого или сфокусированного ввода.
      if (record.revision !== folder.reconciliation.revision && !state.dirty && !state.saving &&
          !document.activeElement?.closest('#statusForm, #todoPanel')) {
        const changedTodos = JSON.stringify(folder.todo_items) !== JSON.stringify(record.todo_items);
        folder.reconciliation = record; folder.note = record.note; folder.todo_items = record.todo_items;
        $('orderTitleInput').value = record.title; $('reconciliationClient').value = record.client; $('orderNote').value = record.note;
        if (changedTodos) renderTodos();
        resizeOrderNote(); renderOrderHeading(); renderStatus();
      }
    } catch (error) {
      if (version === refreshVersion && state.folder === folder) $('reconciliationInvoiceState').textContent = error.message;
    }
  }

  // Обновляет доступность действий открытого редактора в модуле самостоятельных сверок.
  // Использует `$`.
  function controls(busy) {
    for (const id of ['invoiceReconciliationSelect', 'saveInvoiceReconciliation', 'refreshInvoiceReconciliations', 'cancelInvoiceReconciliation']) $(id).disabled = busy;
  }

  // Загружает допустимые сверки и текущее назначение счёта.
  // Использует `/api/reconciliations`, `/api/invoice`.
  async function loadAssignment(current, preserve = false) {
    const selected = preserve ? $('invoiceReconciliationSelect').value : null;
    current.loading = true; controls(true);
    try {
      const [catalog, invoice] = await Promise.all([request('/api/reconciliations'), request(apiUrl('/api/invoice', current.invoice.path, { id: current.invoice.id }))]);
      if (assignment !== current) return;
      current.invoice = invoice; current.items = catalog.items;
      current.link = invoice.reconciliation || links.get(invoice.id) || { id: '', revision: 0 };
      $('invoiceReconciliationSelect').innerHTML = '<option value="">Без сверки</option>' + catalog.items.map(item => '<option value="' + escapeHtml(item.id) + '">' + escapeHtml(item.title + (item.client ? ' · ' + item.client : '')) + '</option>').join('');
      if (current.link.id && !catalog.items.some(item => item.id === current.link.id)) $('invoiceReconciliationSelect').insertAdjacentHTML('beforeend', '<option value="' + escapeHtml(current.link.id) + '" disabled>Недоступная сверка</option>');
      $('invoiceReconciliationSelect').value = selected !== null && (!selected || catalog.items.some(item => item.id === selected)) ? selected : current.link.id;
      current.ready = true;
      $('invoiceReconciliationState').textContent = catalog.items.length ? (preserve ? 'Данные обновлены. Проверь выбор и сохрани.' : '') : 'Сначала открой раздел reconciliations и создай сверку.';
    } catch (error) {
      if (assignment === current) { current.ready = false; $('invoiceReconciliationState').textContent = error.message; }
    } finally {
      if (assignment === current) { current.loading = false; controls(false); $('saveInvoiceReconciliation').disabled = !current.ready; }
    }
  }

  // Открывает компонент и загружает его исходные данные в модуле самостоятельных сверок.
  // Использует `$`, `$('invoiceReconciliationDialog').showModal`, `loadAssignment`.
  async function open(invoice) {
    const current = assignment = { invoice, items: [], ready: false, loading: false, busy: false };
    $('invoiceReconciliationName').textContent = invoice.state === 'external' ? invoice.data.original_name : 'Счёт № ' + invoice.number;
    $('invoiceReconciliationState').textContent = 'Загрузка сверок…';
    $('invoiceReconciliationDialog').showModal();
    await loadAssignment(current);
    if (assignment === current) $('invoiceReconciliationSelect').focus();
  }

  // Закрывает компонент и освобождает его временное состояние в модуле самостоятельных сверок.
  // Использует `$('invoiceReconciliationDialog').close`, `$`.
  function close() {
    if (assignment?.busy || assignment?.loading) return;
    assignment = null; $('invoiceReconciliationDialog').close();
  }

  $('invoiceReconciliationForm').addEventListener('submit', async event => {
    event.preventDefault();
    const current = assignment;
    if (!current?.ready || current.busy || current.loading) return;
    current.busy = true; controls(true);
    try {
      const id = $('invoiceReconciliationSelect').value;
      const target = current.items.find(item => item.id === id);
      const link = await request('/api/invoice-reconciliation', { path: current.invoice.path, id: current.invoice.id,
        invoice_revision: current.invoice.revision, revision: current.link.revision, reconciliation_id: id,
        ...(target ? { target_revision: target.revision } : {}) });
      links.set(current.invoice.id, link);
      assignment = null; $('invoiceReconciliationDialog').close();
      document.dispatchEvent(new CustomEvent('manager-reconciliation-changed'));
      notify(id ? 'Счёт добавлен в сверку' : 'Назначение сверки снято');
    } catch (error) {
      current.ready = false;
      $('invoiceReconciliationState').textContent = error.message + ' Нажми «Обновить список» перед повтором.';
    } finally {
      current.busy = false; controls(false);
      if (assignment === current) $('saveInvoiceReconciliation').disabled = !current.ready;
    }
  });
  $('refreshInvoiceReconciliations').addEventListener('click', () => { if (assignment && !assignment.busy && !assignment.loading) loadAssignment(assignment, true); });
  $('cancelInvoiceReconciliation').addEventListener('click', close);
  $('invoiceReconciliationDialog').addEventListener('cancel', event => { event.preventDefault(); close(); });
  $('refreshReconciliation').addEventListener('click', refresh);
  $('reconciliationListRows').addEventListener('change', event => {
    if (event.target.matches('[data-reconciliation-status]')) run(() => saveListStatus(event.target));
  });
  $('reconciliationListRows').addEventListener('click', event => {
    const link = event.target.closest('[data-reconciliation-path]');
    if (link && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      event.preventDefault(); run(() => navigate(link.dataset.reconciliationPath));
    }
  });
  $('reconciliationInvoiceRows').addEventListener('click', event => {
    const source = event.target.closest('[data-reconciliation-order]');
    if (source && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      event.preventDefault(); run(() => navigate(source.dataset.reconciliationOrder)); return;
    }
    const button = event.target.closest('[data-reconciliation-unlink]');
    const invoice = button && $('reconciliationInvoiceRows').invoiceRecords?.find(item => item.id === button.dataset.reconciliationUnlink);
    if (!invoice || button.disabled) return;
    button.disabled = true;
    run(async () => {
      try {
        await request('/api/invoice-reconciliation', { path: invoice.path, id: invoice.id, invoice_revision: invoice.revision,
          revision: invoice.link_revision, reconciliation_id: '' });
        await refresh(); notify('Счёт убран из сверки');
      } finally { button.disabled = false; }
    });
  });
  document.addEventListener('manager-folder-rendered', refresh);
  document.addEventListener('manager-reconciliation-changed', refresh);
  setInterval(() => { if (!document.hidden) refresh(); }, 5000);
  refresh();
  return { button, open };
})();

/* Сверки используют свои карточки; счета остаются у исходных заказов. */
const ReconciliationUI = (() => {
  let assignment = null, refreshVersion = 0, tableMarkup = null, tablePath = null;
  const links = new Map();
  const money = value => Number.isSafeInteger(value) ? rubles(value) : '—';
  const date = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '') ? value.split('-').reverse().join('.') : '—';

  function button(invoice) {
    if (invoice.reconciliation) links.set(invoice.id, invoice.reconciliation);
    const link = links.get(invoice.id);
    const label = link?.id ? 'Сверка: ' + (link.title || 'недоступна') : 'В сверку';
    return '<button type="button" class="secondary-button invoice-reconciliation-button" data-invoice-reconciliation="' + escapeHtml(invoice.id) + '" title="' + escapeHtml(label) + '">' + escapeHtml(label) + '</button>';
  }

  function renderTable(record) {
    const rows = record.invoices || [];
    $('reconciliationInvoiceCount').textContent = rows.length || '';
    const markup = rows.map(item => {
      const pdf = !item.trash && ['issued', 'external'].includes(item.state);
      const label = escapeHtml(item.label);
      const href = pdf ? apiUrl('/api/invoice-pdf', item.path, { id: item.id }) : '?path=' + encodeURIComponent(item.path);
      const stateLabel = item.trash ? 'В корзине' : { draft: 'Черновик', issued: 'Выпущен', external: 'Внешний' }[item.state] || item.state;
      return '<tr data-reconciliation-invoice="' + escapeHtml(item.id) + '"><td><a href="' + escapeHtml(href) + '"' + (pdf ? ' target="_blank" rel="noopener"' : ' data-reconciliation-order="' + escapeHtml(item.path) + '"') + '>' + label + '</a>' + (item.comment ? '<small title="' + escapeHtml(item.comment) + '">' + escapeHtml(item.comment) + '</small>' : '') + '</td><td>' + date(item.date) + '</td><td><a href="?path=' + encodeURIComponent(item.path) + '" data-reconciliation-order="' + escapeHtml(item.path) + '" title="' + escapeHtml(item.path) + '">' + escapeHtml(item.order_title) + '</a></td><td class="reconciliation-amount">' + money(item.total) + '</td><td>' + escapeHtml(stateLabel) + '</td><td><button type="button" class="secondary-button" data-reconciliation-unlink="' + escapeHtml(item.id) + '" aria-label="' + escapeHtml('Убрать из сверки · ' + item.label) + '">×</button></td></tr>';
    }).join('');
    if (markup !== tableMarkup || tablePath !== record.path) {
      const focused = document.activeElement?.dataset.reconciliationUnlink;
      const pane = document.querySelector('.content-pane'), scroll = pane.scrollTop;
      $('reconciliationInvoiceRows').innerHTML = markup;
      tableMarkup = markup; tablePath = record.path;
      if (focused && document.activeElement === document.body) [...$('reconciliationInvoiceRows').querySelectorAll('[data-reconciliation-unlink]')].find(el => el.dataset.reconciliationUnlink === focused)?.focus({ preventScroll: true });
      pane.scrollTop = scroll;
    }
    $('reconciliationInvoiceState').textContent = rows.length ? '' : 'Добавь счета через кнопку «В сверку» в исходном заказе.';
    $('reconciliationInvoiceRows').invoiceRecords = rows;
  }

  async function refresh() {
    const folder = state.view === 'folder' ? state.folder : null;
    $('reconciliationInvoices').hidden = !folder?.reconciliation;
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

  function controls(busy) {
    for (const id of ['invoiceReconciliationSelect', 'saveInvoiceReconciliation', 'refreshInvoiceReconciliations', 'cancelInvoiceReconciliation']) $(id).disabled = busy;
  }

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

  async function open(invoice) {
    const current = assignment = { invoice, items: [], ready: false, loading: false, busy: false };
    $('invoiceReconciliationName').textContent = invoice.state === 'external' ? invoice.data.original_name : 'Счёт № ' + invoice.number;
    $('invoiceReconciliationState').textContent = 'Загрузка сверок…';
    $('invoiceReconciliationDialog').showModal();
    await loadAssignment(current);
    if (assignment === current) $('invoiceReconciliationSelect').focus();
  }

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

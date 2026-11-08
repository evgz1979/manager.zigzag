/* Общий список читает SQLite; входящие остаются обычными файлами своей папки. */
(() => {
  let path = null, records = [], markup = null, version = 0;
  let sortKey = 'date', sortDirection = -1;
  let opening = null;
  let clientFilter = '', clientFilterLabel = '', clientOptionsMarkup = null;
  const statuses = { none: '—', active: 'Актуально', inactive: 'Неактуально', later: 'Позже', sent: 'Отправлен', paid: 'Оплачен' };
  // Форматирует дату счёта без преобразования часового пояса.
  // Нераспознанная или отсутствующая дата показана прочерком.
  const date = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '') ? value.split('-').reverse().join('.') : '—';

  // Возвращает точный ключ клиента для фильтра общего списка.
  // Путь различает одноимённые папки, JSON отделяет отсутствие клиента от режима «Все клиенты».
  function clientKey(item) {
    return JSON.stringify(item.client_path || item.client || '');
  }

  // Обновляет полный список клиентов независимо от поиска и выбранного фильтра.
  // Не меняет открытый select; исчезнувший выбранный клиент остаётся выбранным с пустым результатом.
  function renderClientFilter() {
    const clients = new Map(records.map(item => [clientKey(item), { name: item.client || 'Без клиента', path: item.client_path || '' }]));
    const names = new Map();
    for (const item of clients.values()) names.set(normalize(item.name), (names.get(normalize(item.name)) || 0) + 1);
    const entries = [...clients.entries()].sort(([, a], [, b]) => OrderSorting.text(a.name, b.name) || OrderSorting.text(a.path, b.path));
    const options = entries.map(([key, item]) => {
      const label = names.get(normalize(item.name)) > 1 && item.path ? item.name + ' · ' + item.path : item.name;
      if (key === clientFilter) clientFilterLabel = label;
      return '<option value="' + escapeHtml(key) + '" data-client-label="' + escapeHtml(label) + '">' + escapeHtml(label) + '</option>';
    }).join('');
    const missing = clientFilter && !clients.has(clientFilter) ? '<option value="' + escapeHtml(clientFilter) + '" data-client-label="' + escapeHtml(clientFilterLabel) + '">' + escapeHtml(clientFilterLabel + ' · нет счетов') + '</option>' : '';
    const html = '<option value="">Все клиенты</option>' + options + missing;
    const select = $('billsClientFilter');
    if (document.activeElement !== select) {
      if (html !== clientOptionsMarkup) { select.innerHTML = html; clientOptionsMarkup = html; }
      select.value = clientFilter;
    }
  }

  // Применяет выбор клиента из списка или по имени в колонке.
  // Поиск и сортировка сохраняются; фильтрация не отправляет запросы записи.
  function selectClient(key) {
    clientFilter = key;
    clientFilterLabel = [...$('billsClientFilter').options].find(option => option.value === key)?.dataset.clientLabel || '';
    renderCatalog();
  }

  // Выбирает значение выбранной колонки для сортировки счетов.
  // Даты сравниваются в ISO, суммы — в копейках; отсутствующие значения возвращают null.
  function sortValue(item) {
    if (sortKey === 'total') return Number.isSafeInteger(item.total) ? item.total : null;
    if (sortKey === 'date') return /^\d{4}-\d{2}-\d{2}$/.test(item.date || '') ? item.date : null;
    if (sortKey === 'list_status') return item.list_status === null ? 'Неизвестная отметка' : item.list_status === 'none' ? null : statuses[item.list_status] || null;
    return item[sortKey]?.trim() || null;
  }

  // Сравнивает счета по текущей колонке и направлению без изменения исходного массива.
  // Пустые значения всегда в конце, равные сохраняют устойчивый порядок ответа сервера.
  function compareRecords(first, second) {
    const a = sortValue(first), b = sortValue(second);
    if (a === null || b === null) return a === b ? 0 : a === null ? 1 : -1;
    return sortDirection * (typeof a === 'number' ? a - b : OrderSorting.text(a, b));
  }

  // Обновляет направление сортировки в заголовках для мыши и клавиатуры.
  // aria-sort отражает текущую колонку, подсказка описывает следующее переключение.
  function renderSorting() {
    $('billsCatalog').querySelectorAll('[data-bills-sort]').forEach(button => {
      const active = button.dataset.billsSort === sortKey;
      button.closest('th').setAttribute('aria-sort', active ? sortDirection === 1 ? 'ascending' : 'descending' : 'none');
      const next = active ? -sortDirection : button.dataset.billsSort === 'date' ? -1 : 1;
      button.title = 'Сортировать по ' + (next === 1 ? 'возрастанию' : 'убыванию');
    });
  }

  // Заменяет строки списка, сохраняя фокус ссылки и положение прокрутки.
  // Неизменившаяся разметка не пересоздаётся; ключи ссылок устойчивы к опросу.
  function replaceRows(id, html) {
    if ($(id).innerHTML === html) return;
    const focused = document.activeElement?.closest('#' + id + ' [data-bills-key]')?.dataset.billsKey;
    const pane = document.querySelector('.content-pane'), scroll = pane.scrollTop;
    const table = $(id).closest('.bills-table-scroll'), horizontal = table.scrollLeft;
    $(id).innerHTML = html;
    if (focused && document.activeElement === document.body) [...$(id).querySelectorAll('[data-bills-key]')].find(item => item.dataset.billsKey === focused)?.focus({ preventScroll: true });
    pane.scrollTop = scroll; table.scrollLeft = horizontal;
  }

  // Показывает счета с фильтром одного клиента, поиском, сортировкой и действиями правки.
  // Клиент выбирается по точному пути; обновление сохраняет фильтр, ссылки и доступные действия.
  function renderCatalog() {
    renderClientFilter();
    const query = normalize($('billsCatalogSearch').value.trim());
    const visible = records.filter(item => (!clientFilter || clientKey(item) === clientFilter) && (!query || normalize([item.label, item.client, item.order_title, item.path, item.comment, item.date, statuses[item.list_status]].join(' ')).includes(query))).sort(compareRecords);
    renderSorting();
    const html = visible.map(item => {
      const pdf = ['issued', 'external'].includes(item.state);
      const href = pdf ? apiUrl('/api/invoice-pdf', item.path, { id: item.id }) : '?path=' + encodeURIComponent(item.path);
      const type = { draft: 'Черновик', issued: 'Выпущен', external: 'Прикреплён' }[item.state];
      const editable = item.edit_action === 'edit' && item.state === 'draft' || item.edit_action === 'copy' && item.state === 'issued';
      const action = item.edit_action === 'edit' ? 'Редактировать' : 'Новая правка';
      const name = editable ? '<button type="button" class="bills-edit" data-bills-key="' + escapeHtml(item.id) + '" data-bills-edit="' + escapeHtml(item.id) + '" title="' + escapeHtml(item.edit_action === 'edit' ? 'Редактировать черновик · ' + item.label : 'Создать отдельный черновик на основе · ' + item.label) + '"' + (opening ? ' disabled' : '') + '><span>' + escapeHtml(item.label) + '</span><span class="bills-edit-badge">' + action + '</span></button>' : '<a data-bills-key="' + escapeHtml(item.id) + '" href="' + escapeHtml(href) + '"' + (pdf ? ' target="_blank" rel="noopener"' : ' data-bills-order="' + escapeHtml(item.path) + '"') + '>' + escapeHtml(item.label) + '</a>';
      return '<tr' + (editable ? ' class="bills-editable"' : '') + '><td class="bills-date">' + date(item.date) + '</td><td>' + name + '<small>' + escapeHtml(type) + (editable && pdf ? ' · <a data-bills-key="' + escapeHtml(item.id + ':pdf') + '" href="' + escapeHtml(href) + '" target="_blank" rel="noopener">PDF</a>' : '') + '</small>' + (item.comment ? '<small class="bills-comment" title="' + escapeHtml(item.comment) + '">' + escapeHtml(item.comment) + '</small>' : '') + '</td><td><button type="button" class="bills-client" data-bills-key="' + escapeHtml(item.id + ':client') + '" data-bills-client="' + escapeHtml(clientKey(item)) + '" title="' + escapeHtml('Показать только счета клиента · ' + (item.client || 'Без клиента')) + '">' + escapeHtml(item.client || '—') + '</button></td><td><a data-bills-key="' + escapeHtml(item.id + ':order') + '" data-bills-order="' + escapeHtml(item.path) + '" href="?path=' + encodeURIComponent(item.path) + '" title="' + escapeHtml(item.path) + '">' + escapeHtml(item.order_title) + '</a></td><td class="reconciliation-amount">' + (Number.isSafeInteger(item.total) ? rubles(item.total) : '—') + '</td><td>' + escapeHtml(item.list_status === null ? 'Неизвестная отметка' : statuses[item.list_status] || '—') + '</td></tr>';
    }).join('');
    if (html !== markup) { replaceRows('billsCatalogRows', html); markup = html; }
    $('billsCatalogCount').textContent = query || clientFilter ? visible.length + ' из ' + records.length : records.length;
    $('billsCatalogState').textContent = visible.length ? '' : query ? 'Счета не найдены.' : clientFilter ? 'У выбранного клиента пока нет счетов.' : records.length ? 'Счета не найдены.' : 'Здесь появятся счета, созданные и прикреплённые в заказах всех клиентов.';
  }

  // Показывает непосредственные входящие файлы без прикрепления их к заказам.
  // Использует проверенный список открытой папки и прежний просмотрщик файлов.
  function renderInbox(folder) {
    const files = folder.files || [];
    replaceRows('billsInboxRows', files.map(file => '<tr><td><button type="button" class="bills-file" data-bills-key="' + escapeHtml(file.path) + '" data-bills-file="' + escapeHtml(file.path) + '">' + escapeHtml(file.name) + '</button></td><td class="bills-date">' + formatSize(file.size) + '</td><td class="bills-date">' + new Date(file.modified * 1000).toLocaleDateString('ru-RU') + '</td></tr>').join(''));
    $('billsInboxCount').textContent = files.length;
    $('billsInboxState').textContent = folder.filesUnavailable ? 'Папка сейчас недоступна.' : files.length ? '' : 'Входящих файлов пока нет.';
  }

  // Обновляет общий список только при открытом финансовом разделе счетов.
  // Опрос читает SQLite; устаревший ответ после навигации не применяется.
  async function refresh() {
    const folder = state.view === 'folder' ? state.folder : null;
    const catalog = folder?.folderKind === 'bills_root';
    $('billsCatalog').hidden = !catalog;
    $('billsInbox').hidden = folder?.folderKind !== 'bills_inbox';
    if (folder?.folderKind === 'bills_inbox') renderInbox(folder);
    const current = ++version;
    if (!catalog) { path = null; return; }
    if (path !== folder.path) {
      path = folder.path; records = []; markup = null;
      $('billsCatalogSearch').value = ''; renderCatalog();
      $('billsCatalogState').textContent = 'Загрузка счетов…';
    }
    try {
      const result = await request('/api/invoice-catalog');
      if (current !== version || state.folder !== folder || state.view !== 'folder') return;
      records = result.items; renderCatalog();
    } catch (error) {
      if (current === version && state.folder === folder) $('billsCatalogState').textContent = error.message;
    }
  }

  $('billsCatalogSearch').addEventListener('input', renderCatalog);
  $('billsClientFilter').addEventListener('change', event => selectClient(event.target.value));
  $('billsClientFilter').addEventListener('blur', renderCatalog);
  $('billsCatalog').querySelector('thead').addEventListener('click', event => {
    const button = event.target.closest('[data-bills-sort]');
    if (!button) return;
    const key = button.dataset.billsSort;
    sortDirection = sortKey === key ? -sortDirection : key === 'date' ? -1 : 1;
    sortKey = key; renderCatalog();
  });
  $('billsCatalogRows').addEventListener('click', event => {
    const client = event.target.closest('[data-bills-client]');
    if (client) { selectClient(client.dataset.billsClient); return; }
    const edit = event.target.closest('[data-bills-edit]');
    if (edit && !opening) {
      const item = records.find(record => record.id === edit.dataset.billsEdit), context = state.folder;
      if (!item || edit.disabled) return;
      run(async () => {
        opening = item.id; renderCatalog();
        try { await window.ManagerInvoices.openFromCatalog(item.path, item.id, item.edit_action, item.id); }
        finally {
          opening = null; renderCatalog();
          if (state.folder === context && document.activeElement === document.body) [...$('billsCatalogRows').querySelectorAll('[data-bills-key]')].find(button => button.dataset.billsKey === item.id)?.focus({ preventScroll: true });
        }
      });
      return;
    }
    const link = event.target.closest('[data-bills-order]');
    if (link && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      event.preventDefault(); run(() => navigate(link.dataset.billsOrder));
    }
  });
  $('billsInboxRows').addEventListener('click', event => {
    const file = event.target.closest('[data-bills-file]');
    if (file) run(() => showPreview(file.dataset.billsFile));
  });
  document.addEventListener('manager-folder-rendered', refresh);
  document.addEventListener('manager-invoice-saved', refresh);
  document.addEventListener('manager-invoice-updated', refresh);
  setInterval(() => { if (!document.hidden) refresh(); }, 5000);
  refresh();
})();

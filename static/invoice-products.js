/* Shared products are copied into invoice rows; later price changes affect future additions. */
const InvoiceProducts = (() => {
  let catalog = null, editing = null, saving = false, loading = 0, editable = false, addItem = null, createIdentity = null;
  // Находит постоянный узел панели товаров или её отдельной формы.
  // Узлы не заменяются при загрузке каталога, поэтому ввод и фокус формы сохраняются.
  const el = id => document.getElementById(id);
  // Экранирует текст каталога перед включением в разметку.
  // Пользовательские названия, группы и цены никогда не интерпретируются как HTML.
  const html = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  // Читает или явно сохраняет общий каталог с прежней защитой внешней сессии.
  // При конфликте и сетевой ошибке не повторяет запрос; версия передаётся вызывающим кодом.
  async function api(payload) {
    const response = await fetch('/api/invoice-products', payload ? {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Manager-Invoice-Preferences': '1' }, body: JSON.stringify(payload),
    } : { cache: 'no-store' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Не удалось сохранить каталог');
    return data;
  }
  // Строит варианты плоских групп, сохраняя выбранное значение, включая пустую группу.
  // Используется только при явной загрузке и сохранении; опрос счетов select не перестраивает.
  function groups(select, all = false) {
    const selected = select.value;
    select.innerHTML = (all ? '<option value="*">Все группы</option>' : '') + '<option value="">Без группы</option>' +
      catalog.groups.map(group => '<option value="' + group.id + '">' + html(group.name) + '</option>').join('');
    if ([...select.options].some(option => option.value === selected)) select.value = selected;
  }
  // Показывает товары выбранной группы и поиска без изменения строк счёта.
  // Каждый товар имеет отдельные действия добавления и правки; сохранённая цена показана в рублях.
  function render() {
    const group = el('invoiceProductGroup').value, query = el('invoiceProductsSearch').value.trim().toLocaleLowerCase('ru');
    el('editInvoiceProductGroup').disabled = !catalog?.groups.some(item => item.id === group);
    const products = (catalog?.products || []).filter(item => (group === '*' || item.group_id === group) &&
      (item.name + ' ' + (catalog.groups.find(g => g.id === item.group_id)?.name || '')).toLocaleLowerCase('ru').includes(query));
    el('invoiceProductsList').innerHTML = products.map(item => '<div class="invoice-product-row"><button type="button" class="invoice-product-add" data-product-add="' + item.id + '"' +
      (editable ? '' : ' disabled') + ' title="Добавить в счёт"><span>' + html(item.name) + '</span><small>' +
      html(new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(item.price))) + ' ₽' +
      (item.unit ? ' / ' + html(item.unit) : '') + '</small></button><button class="icon-button" type="button" data-product-edit="' + item.id + '" aria-label="Изменить товар ' + html(item.name) + '" title="Изменить товар">✎</button></div>').join('');
    if (catalog) el('invoiceProductsState').textContent = products.length ? '' : catalog.products.length ? 'Товары не найдены.' : 'Добавь товары и цены — они сохранятся для следующих счетов.';
  }
  // Загружает последнюю версию общего каталога при открытии окна или явном обновлении.
  // Ответ прежней загрузки игнорируется; поля счёта и открытого товара не заменяются.
  async function load() {
    const version = ++loading;
    el('invoiceProductsState').textContent = 'Загрузка товаров…';
    try {
      const data = await api();
      if (version !== loading) return;
      catalog = data; groups(el('invoiceProductGroup'), true); render();
      el('newInvoiceProduct').disabled = false; el('newInvoiceProductGroup').disabled = false;
    } catch (error) {
      if (version === loading) { el('invoiceProductsState').textContent = error.message; throw error; }
    }
  }
  // Открывает отдельную форму группы или товара, в том числе из ручной строки счёта.
  // Версия фиксируется до ввода; UUID создаёт прежний генератор редактора, доступный и по HTTP LAN.
  function open(kind, item = null) {
    if (!catalog || saving) return;
    editing = { kind, id: item?.id || createIdentity(), revision: catalog.revision, returnFocus: document.activeElement };
    el('invoiceProductTitle').textContent = kind === 'group' ? (item?.id ? 'Изменить группу' : 'Новая группа') : (item?.id ? 'Изменить товар' : 'Новый товар');
    el('invoiceProductName').maxLength = kind === 'group' ? 100 : 500;
    el('invoiceProductName').value = item?.name || '';
    groups(el('invoiceProductParent'));
    el('invoiceProductParent').value = item?.group_id ?? (el('invoiceProductGroup').value === '*' ? '' : el('invoiceProductGroup').value);
    el('invoiceProductUnit').value = item?.unit ?? 'шт'; el('invoiceProductPrice').value = item?.price ?? '0';
    for (const node of el('invoiceProductDialog').querySelectorAll('[data-product-only]')) node.hidden = kind !== 'product';
    el('invoiceProductState').textContent = ''; el('reloadInvoiceProduct').hidden = true;
    el('invoiceProductDialog').showModal(); el('invoiceProductName').focus();
  }
  // Отправляет одну явную правку товара или группы и обновляет доступные позиции.
  // Ошибка сохраняет весь ввод и UUID; повтор возможен только действием пользователя.
  async function save(event) {
    event.preventDefault();
    if (!editing || saving) return;
    const current = editing, payload = { kind: current.kind, id: current.id, revision: current.revision, name: el('invoiceProductName').value };
    if (current.kind === 'product') Object.assign(payload, { group_id: el('invoiceProductParent').value, unit: el('invoiceProductUnit').value, price: el('invoiceProductPrice').value });
    saving = true; el('invoiceProductFields').disabled = true; el('saveInvoiceProduct').disabled = true; el('cancelInvoiceProduct').disabled = true;
    el('invoiceProductState').textContent = 'Сохранение…';
    try {
      catalog = await api(payload); groups(el('invoiceProductGroup'), true);
      if (current.kind === 'group') el('invoiceProductGroup').value = current.id;
      render(); el('invoiceProductDialog').close();
    } catch (error) { el('invoiceProductState').textContent = error.message + ' Ввод остался в форме.'; el('reloadInvoiceProduct').hidden = false; }
    finally { saving = false; el('invoiceProductFields').disabled = false; el('saveInvoiceProduct').disabled = false; el('cancelInvoiceProduct').disabled = false; }
  }
  // Перечитывает конфликтующий каталог с сохранением введённого названия и цены.
  // Показывает актуальную запись и только затем разрешает явное сохранение с новой версией.
  async function review() {
    if (!editing || saving) return;
    const currentEditing = editing;
    el('saveInvoiceProduct').disabled = true; el('reloadInvoiceProduct').disabled = true;
    try {
      await load();
      if (editing !== currentEditing) return;
      const current = catalog[editing.kind === 'group' ? 'groups' : 'products'].find(item => item.id === editing.id);
      editing.revision = catalog.revision;
      el('invoiceProductState').textContent = current ? 'Сейчас сохранено: ' + current.name + (editing.kind === 'product' ? ' · ' + current.price + ' ₽ / ' + current.unit : '') + '. Твой ввод оставлен. Проверь его и нажми «Сохранить».' : 'Каталог обновлён. Твой ввод оставлен; проверь группу и нажми «Сохранить».';
      groups(el('invoiceProductParent')); el('reloadInvoiceProduct').hidden = true;
    } catch (error) { el('invoiceProductState').textContent = error.message; }
    finally { el('saveInvoiceProduct').disabled = false; el('reloadInvoiceProduct').disabled = false; }
  }
  // Подключает панель к редактору и устанавливает обработчики один раз.
  // Принимает добавление позиции и генератор UUID редактора, не зависящий от HTTPS-контекста.
  function init(callback, identity) {
    addItem = callback; createIdentity = identity;
    el('newInvoiceProduct').disabled = true; el('newInvoiceProductGroup').disabled = true;
    el('newInvoiceProduct').addEventListener('click', () => open('product'));
    el('newInvoiceProductGroup').addEventListener('click', () => open('group'));
    el('editInvoiceProductGroup').addEventListener('click', () => open('group', catalog.groups.find(item => item.id === el('invoiceProductGroup').value)));
    el('refreshInvoiceProducts').addEventListener('click', () => load().catch(() => {}));
    el('invoiceProductGroup').addEventListener('change', render); el('invoiceProductsSearch').addEventListener('input', render);
    el('invoiceProductsList').addEventListener('click', event => {
      const add = event.target.closest('[data-product-add]'), edit = event.target.closest('[data-product-edit]');
      const product = catalog?.products.find(item => item.id === (add?.dataset.productAdd || edit?.dataset.productEdit));
      if (product && add && editable) addItem({ name: product.name, quantity: '1', unit: product.unit, price: product.price });
      if (product && edit) open('product', product);
    });
    el('invoiceProductForm').addEventListener('submit', save);
    el('reloadInvoiceProduct').addEventListener('click', review);
    el('cancelInvoiceProduct').addEventListener('click', () => el('invoiceProductDialog').close());
    el('invoiceProductDialog').addEventListener('cancel', event => { if (saving) event.preventDefault(); });
    el('invoiceProductDialog').addEventListener('close', () => {
      const target = editing?.returnFocus?.isConnected ? editing.returnFocus : el('invoiceProductsList').querySelector('[data-product-edit="' + editing?.id + '"]');
      target?.focus({ preventScroll: true }); editing = null;
    });
  }
  // Меняет доступность добавления без перестроения панели и потери фокуса.
  // Выпущенный счёт и процесс выпуска не допускают новых строк.
  function setEditable(value) {
    editable = value;
    for (const button of el('invoiceProductsList').querySelectorAll('[data-product-add]')) button.disabled = !value;
  }
  return { init, load, setEditable, open };
})();

/* Supplier edits update the purchase in its original order. */
(() => {
  let folder = null, model = null, markup = null, generation = 0, saving = false, pendingKey = null, error = "", readError = "";
  const panel = $("supplierPurchasesSection"), list = $("supplierPurchasesList");
  // Показывает сводку в разделе поставщика и его непосредственном заказе.
  // Использует вычисленный сервером путь раздела закупок.
  const visible = () => state.view === "folder" && Boolean(state.folder?.purchaseSupplierPath);
  // Вычисляет устойчивый ключ строки исходной закупки.
  // Результат вычисляется из переданных аргументов и текущего состояния компонента.
  const itemKey = (order, item) => order.id + ":" + item.index;
  const dialog = $("supplierPurchaseDialog");
  let editor = null;

  // Показывает текущие закупки и сохраняет фокус и прокрутку при обновлении.
  // Чекбокс отделён от текста закупки, чтобы текст можно было выделить и скопировать.
  function render() {
    panel.hidden = !visible() || (!error && !readError && model?.orders.length === 0);
    $("orderOverview").classList.toggle("with-supplier-purchases", !panel.hidden);
    if (panel.hidden) return;
    const pane = document.querySelector(".content-pane"), scroll = pane.scrollTop;
    const focused = document.activeElement?.dataset.supplierPurchaseDone;
    const focusedSource = document.activeElement?.dataset.supplierPurchaseSource;
    const focusedCopy = document.activeElement?.dataset.supplierPurchaseCopy;
    const focusedEdit = document.activeElement?.dataset.supplierPurchaseEdit;
    const groups = model?.orders || [], all = groups.flatMap(order => order.items);
    const showDone = $("supplierPurchasesShowDone").checked;
    $("supplierPurchasesCount").textContent = all.filter(item => !item.done).length;
    $("refreshSupplierPurchases").disabled = saving;
    const next = groups.map(order => {
      const items = order.items.filter(item => showDone || !item.done || itemKey(order, item) === pendingKey);
      if (!items.length) return "";
      const name = [order.client, order.object, order.title].filter(Boolean).join(" · ");
      return '<section class="supplier-purchase-group" data-supplier-purchase-order="' + escapeHtml(order.id) + '">' +
        items.map(item => '<div class="supplier-purchase-row' + (item.done ? ' done' : '') + '"><div class="supplier-purchase-task"><input type="checkbox" class="todo-check" data-supplier-purchase-done="' + escapeHtml(itemKey(order, item)) +
          '" data-purchase-index="' + item.index + '" aria-label="Закупка выполнена: ' + escapeHtml(item.text + ' · ' + name) + '"' + (item.done ? ' checked' : '') + (saving ? ' disabled' : '') +
          '><span title="' + escapeHtml(item.text) + '">' + escapeHtml(item.text) + '</span></div>' +
          '<a class="order-row-link supplier-purchase-source" data-supplier-purchase-path="' + escapeHtml(order.path) + '" data-supplier-purchase-source="' + escapeHtml(itemKey(order, item)) +
          '" href="?path=' + encodeURIComponent(order.path) + '" title="' + escapeHtml(name + ' · ' + order.path) + '" aria-label="' + escapeHtml('Открыть заказ · ' + name + ' · ' + order.path) + '">' + escapeHtml(name) + '</a>' +
          '<button class="secondary-button supplier-purchase-copy" type="button" data-supplier-purchase-copy="' + escapeHtml(itemKey(order, item)) +
          '" title="Копировать весь текст закупки" aria-label="' + escapeHtml('Копировать: ' + item.text + ' · ' + name) + '">Копировать</button>' +
          '<button class="supplier-purchase-edit" type="button" data-supplier-purchase-edit="' + escapeHtml(itemKey(order, item)) + '" data-purchase-index="' + item.index + '" title="Изменить закупку" aria-label="' + escapeHtml('Изменить закупку: ' + item.text + ' · ' + name) + '"' + (saving ? ' disabled' : '') + '>' + icon("edit") + '</button></div>').join("") + '</section>';
    }).join("") || (model ? '<p class="todo-empty">Все закупки выполнены. Их можно раскрыть выше.</p>' : '');
    if (markup !== next) { list.innerHTML = next; markup = next; }
    $("supplierPurchasesState").textContent = error || readError || (saving ? "Сохраняю…" : model ? "Текст и выполнение общие с исходным заказом и другими выбранными поставщиками." : "Загрузка закупок…");
    if (focused) ([...list.querySelectorAll("[data-supplier-purchase-done]")].find(el => el.dataset.supplierPurchaseDone === focused) || $("supplierPurchasesShowDone")).focus({ preventScroll: true });
    if (focusedSource) ([...list.querySelectorAll("[data-supplier-purchase-source]")].find(el => el.dataset.supplierPurchaseSource === focusedSource) || $("supplierPurchasesShowDone")).focus({ preventScroll: true });
    if (focusedCopy) ([...list.querySelectorAll("[data-supplier-purchase-copy]")].find(el => el.dataset.supplierPurchaseCopy === focusedCopy) || $("supplierPurchasesShowDone")).focus({ preventScroll: true });
    if (focusedEdit) focusEdit(focusedEdit);
    pane.scrollTop = scroll;
  }

  // Перечитывает сводку закупок раздела, к которому относится открытая папка.
  // Передаёт путь раздела в `/api/supplier-purchases` и отбрасывает устаревший ответ.
  async function refresh() {
    if (!visible()) { ++generation; folder = null; model = null; markup = null; panel.hidden = true; $("orderOverview").classList.remove("with-supplier-purchases"); return; }
    const current = state.folder;
    if (folder !== current) {
      folder = current; model = null; markup = null; error = ""; readError = "";
      $("supplierPurchasesShowDone").checked = false;
      list.innerHTML = "";
    }
    if (saving) return;
    const version = ++generation;
    render();
    try {
      const result = await request(apiUrl("/api/supplier-purchases", current.purchaseSupplierPath));
      if (version !== generation || state.folder !== current) return;
      model = result; readError = "";
    } catch (problem) {
      if (version !== generation || state.folder !== current) return;
      readError = problem.message;
    }
    render();
  }

  // Возвращает фокус на кнопку правки исходной закупки.
  // Обращается к DOM текущего документа или переданного контейнера.
  function focusEdit(key) {
    ([...list.querySelectorAll("[data-supplier-purchase-edit]")].find(el => el.dataset.supplierPurchaseEdit === key) || $(panel.hidden ? "openFolderButton" : "supplierPurchasesShowDone")).focus({ preventScroll: true });
  }

  // Обновляет доступность сохранения редактора закупки.
  // Использует `Boolean`, `$`.
  function editorControls() {
    const busy = Boolean(editor?.busy);
    $("supplierPurchaseText").readOnly = busy;
    $("saveSupplierPurchase").disabled = busy || Boolean(editor?.conflict);
    $("cancelSupplierPurchase").disabled = busy;
    $("checkSupplierPurchase").disabled = busy;
    $("checkSupplierPurchase").hidden = !editor?.conflict;
  }

  // Открывает правку точной исходной строки закупки у поставщика.
  // Использует `model.orders.find`, `itemKey`, `$`.
  function openEditor(button) {
    if (saving || !model || state.folder !== folder) return;
    const order = model.orders.find(row => row.id === button.closest("[data-supplier-purchase-order]").dataset.supplierPurchaseOrder);
    const item = order?.items.find(row => row.index === Number(button.dataset.purchaseIndex));
    if (!item) return;
    editor = { folder, order: { ...order }, item: { ...item }, key: itemKey(order, item), busy: false, conflict: false };
    $("supplierPurchaseSource").textContent = [order.client, order.object, order.title].filter(Boolean).join(" · ");
    $("supplierPurchaseText").value = item.text;
    $("supplierPurchaseEditState").textContent = "";
    $("supplierPurchaseCurrent").hidden = true;
    editorControls();
    dialog.showModal();
    $("supplierPurchaseText").focus({ preventScroll: true });
  }

  // Сохраняет текст исходной закупки с её версией и проверочной строкой.
  // Использует `/api/supplier-purchase-text`.
  async function saveText() {
    const edit = editor;
    if (!edit || edit.busy || edit.conflict) return;
    if (state.folder !== edit.folder) { $("supplierPurchaseEditState").textContent = "Страница поставщика изменилась. Текст остался в поле; открой нужную закупку заново."; return; }
    const value = $("supplierPurchaseText").value.trim();
    if (!value) { $("supplierPurchaseEditState").textContent = "Введи текст закупки"; return; }
    if (value === edit.item.text) { dialog.close(); return; }
    edit.busy = true; saving = true; ++generation;
    editorControls(); render();
    $("supplierPurchaseEditState").textContent = "Сохраняю…";
    try {
      const saved = await request("/api/supplier-purchase-text", { supplier_path: edit.folder.purchaseSupplierPath, path: edit.order.path, id: edit.order.id, revision: edit.order.revision, index: edit.item.index, text: edit.item.text, new_text: value });
      applyOrderRecord(null, saved);
      edit.busy = false;
      dialog.close();
      notify("Закупка сохранена");
    } catch (problem) {
      edit.conflict = true;
      $("supplierPurchaseEditState").textContent = problem.message + " Твой текст остался в поле. Нажми «Проверить изменения» перед повторным сохранением.";
    } finally {
      edit.busy = false; saving = false;
      editorControls();
      await refresh();
      if (dialog.open && editor === edit) $("supplierPurchaseText").focus({ preventScroll: true });
    }
  }

  // Перечитывает источник закупки при конфликте, сохраняя введённый черновик.
  // Использует `/api/supplier-purchases`.
  async function checkText() {
    const edit = editor;
    if (!edit || edit.busy) return;
    edit.busy = true; ++generation; editorControls();
    try {
      if (state.folder !== edit.folder) throw new Error("Страница поставщика изменилась. Твой текст остался в поле; открой нужную закупку заново.");
      const current = await request(apiUrl("/api/supplier-purchases", edit.folder.purchaseSupplierPath));
      if (state.folder !== edit.folder) throw new Error("Страница поставщика изменилась. Твой текст остался в поле.");
      const order = current.orders.find(row => row.id === edit.order.id && row.path === edit.order.path);
      const item = order?.items.find(row => row.index === edit.item.index);
      model = current; render();
      if (!item) throw new Error("Исходная закупка больше недоступна у поставщика. Твой текст остался в поле.");
      $("supplierPurchaseCurrent").textContent = "Сейчас в заказе: " + item.text + (item.done ? " · выполнено" : " · не выполнено") + " · поставщики: " + (item.suppliers.join(", ") || "без поставщика");
      $("supplierPurchaseCurrent").hidden = false;
      if (item.text !== edit.item.text) throw new Error("Текст строки изменился или закупки переставлены. Твой ввод сохранён; отмени редактирование и выбери нужную строку в обновлённом списке.");
      edit.order = { ...order }; edit.item = { ...item }; edit.conflict = false;
      $("supplierPurchaseEditState").textContent = "Актуальная строка показана выше. Проверь текст и нажми «Сохранить», чтобы применить правку.";
    } catch (problem) {
      $("supplierPurchaseEditState").textContent = problem.message;
    } finally {
      edit.busy = false; editorControls();
      if (dialog.open && editor === edit) $("supplierPurchaseText").focus({ preventScroll: true });
    }
  }

  list.addEventListener("click", event => {
    const copy = event.target.closest("[data-supplier-purchase-copy]");
    if (copy) {
      const text = copy.closest(".supplier-purchase-row").querySelector(".supplier-purchase-task > span").textContent;
      copyText(text).then(() => notify("Текст закупки скопирован"), problem => notify(problem.message, true));
      return;
    }
    const edit = event.target.closest("[data-supplier-purchase-edit]");
    if (edit) { openEditor(edit); return; }
    const link = event.target.closest("[data-supplier-purchase-path]");
    if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) {
      event.preventDefault(); run(() => navigate(link.dataset.supplierPurchasePath));
    }
  });
  list.addEventListener("change", event => {
    const input = event.target.closest("[data-supplier-purchase-done]");
    if (!input || saving || !model || state.folder !== folder) return;
    const order = model.orders.find(row => row.id === input.closest("[data-supplier-purchase-order]").dataset.supplierPurchaseOrder);
    const item = order?.items.find(row => row.index === Number(input.dataset.purchaseIndex));
    if (!item) return;
    const current = folder, done = input.checked, previous = item.done, focusKey = input.dataset.supplierPurchaseDone;
    run(async () => {
      saving = true; pendingKey = focusKey; item.done = done; error = ""; ++generation;
      render();
      try {
        const saved = await request("/api/supplier-purchase-done", { supplier_path: current.purchaseSupplierPath, path: order.path, id: order.id, revision: order.revision, index: item.index, text: item.text, done });
        applyOrderRecord(null, saved);
        // Update the view immediately, then read all suppliers/rows from the shared source.
        order.revision = saved.revision;
        item.done = done;
      } catch (problem) {
        item.done = previous;
        notify(problem.message, true);
        if (state.folder === current) error = problem.message + (problem.status === 409 ? " Проверь обновлённый список перед повторным нажатием." : " Отметка не повторяется автоматически; обнови список перед повтором.");
      } finally {
        saving = false; pendingKey = null;
        if (state.folder === current) render();
        await refresh();
        if (state.folder === current && document.activeElement === document.body) ([...list.querySelectorAll("[data-supplier-purchase-done]")].find(el => el.dataset.supplierPurchaseDone === focusKey) || $("supplierPurchasesShowDone")).focus({ preventScroll: true });
      }
    });
  });
  $("supplierPurchasesShowDone").addEventListener("change", render);
  $("refreshSupplierPurchases").addEventListener("click", () => { error = ""; readError = ""; run(refresh); });
  $("supplierPurchaseForm").addEventListener("submit", event => { event.preventDefault(); run(saveText); });
  $("cancelSupplierPurchase").addEventListener("click", () => { if (!editor?.busy) dialog.close(); });
  $("checkSupplierPurchase").addEventListener("click", () => run(checkText));
  dialog.addEventListener("cancel", event => { if (editor?.busy) event.preventDefault(); });
  dialog.addEventListener("close", () => { const key = editor?.key; editor = null; if (state.folder === folder && visible() && key) focusEdit(key); });
  dialog.addEventListener("keydown", event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") { event.preventDefault(); event.stopPropagation(); $("supplierPurchaseForm").requestSubmit(); }
  });
  document.addEventListener("manager-folder-rendered", () => run(refresh));
  setInterval(() => { if (!document.hidden && visible() && !saving) run(refresh); }, 5000);
  run(refresh);
})();

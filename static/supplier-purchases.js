/* A supplier's checkbox edits the purchase in its original order. */
(() => {
  let folder = null, model = null, markup = null, generation = 0, saving = false, pendingKey = null, error = "", readError = "";
  const panel = $("supplierPurchasesSection"), list = $("supplierPurchasesList");
  const visible = () => state.view === "folder" && Boolean(state.folder?.purchaseSupplier);
  const itemKey = (order, item) => order.id + ":" + item.index;

  function render() {
    panel.hidden = !visible() || (!error && !readError && model?.orders.length === 0);
    if (panel.hidden) return;
    const pane = document.querySelector(".content-pane"), scroll = pane.scrollTop;
    const focused = document.activeElement?.dataset.supplierPurchaseDone;
    const focusedSource = document.activeElement?.dataset.supplierPurchaseSource;
    const groups = model?.orders || [], all = groups.flatMap(order => order.items);
    const showDone = $("supplierPurchasesShowDone").checked;
    $("supplierPurchasesCount").textContent = all.filter(item => !item.done).length;
    $("refreshSupplierPurchases").disabled = saving;
    const next = groups.map(order => {
      const items = order.items.filter(item => showDone || !item.done || itemKey(order, item) === pendingKey);
      if (!items.length) return "";
      const name = [order.client, order.object, order.title].filter(Boolean).join(" · ");
      return '<section class="supplier-purchase-group" data-supplier-purchase-order="' + escapeHtml(order.id) + '">' +
        items.map(item => '<div class="supplier-purchase-row' + (item.done ? ' done' : '') + '"><label class="supplier-purchase-task"><input type="checkbox" class="todo-check" data-supplier-purchase-done="' + escapeHtml(itemKey(order, item)) +
          '" data-purchase-index="' + item.index + '" aria-label="Закупка выполнена: ' + escapeHtml(item.text + ' · ' + name) + '"' + (item.done ? ' checked' : '') + (saving ? ' disabled' : '') +
          '><span title="' + escapeHtml(item.text) + '">' + escapeHtml(item.text) + '</span></label>' +
          '<a class="order-row-link supplier-purchase-source" data-supplier-purchase-path="' + escapeHtml(order.path) + '" data-supplier-purchase-source="' + escapeHtml(itemKey(order, item)) +
          '" href="?path=' + encodeURIComponent(order.path) + '" title="' + escapeHtml(name + ' · ' + order.path) + '" aria-label="' + escapeHtml('Открыть заказ · ' + name + ' · ' + order.path) + '">' + escapeHtml(name) + '</a></div>').join("") + '</section>';
    }).join("") || (model ? '<p class="todo-empty">Все закупки выполнены. Их можно раскрыть выше.</p>' : '');
    if (markup !== next) { list.innerHTML = next; markup = next; }
    $("supplierPurchasesState").textContent = error || readError || (saving ? "Сохраняю…" : model ? "Выполнение общее с исходным заказом и другими выбранными поставщиками." : "Загрузка закупок…");
    if (focused) ([...list.querySelectorAll("[data-supplier-purchase-done]")].find(el => el.dataset.supplierPurchaseDone === focused) || $("supplierPurchasesShowDone")).focus({ preventScroll: true });
    if (focusedSource) ([...list.querySelectorAll("[data-supplier-purchase-source]")].find(el => el.dataset.supplierPurchaseSource === focusedSource) || $("supplierPurchasesShowDone")).focus({ preventScroll: true });
    pane.scrollTop = scroll;
  }

  async function refresh() {
    if (!visible()) { ++generation; folder = null; model = null; markup = null; panel.hidden = true; return; }
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
      const result = await request(apiUrl("/api/supplier-purchases", current.path));
      if (version !== generation || state.folder !== current) return;
      model = result; readError = "";
    } catch (problem) {
      if (version !== generation || state.folder !== current) return;
      readError = problem.message;
    }
    render();
  }

  list.addEventListener("click", event => {
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
        const saved = await request("/api/supplier-purchase-done", { supplier_path: current.path, path: order.path, id: order.id, revision: order.revision, index: item.index, text: item.text, done });
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
  document.addEventListener("manager-folder-rendered", () => run(refresh));
  setInterval(() => { if (!document.hidden && visible() && !saving) run(refresh); }, 5000);
  run(refresh);
})();

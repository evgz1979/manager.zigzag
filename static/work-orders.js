/* A direct #work order may link supplier orders without moving their folders. */
(() => {
  let model = null, key = null, loading = 0, markup = null, selection = null, saving = false, editingFolder = null;
  const visible = (folder) => folder?.order?.can_group_supplier_orders || (folder?.folderKind === "order" && folder.path.split("/").length === 2 && /^#\s*work$/i.test(folder.path.split("/")[0]));

  function render() {
    const items = model?.items || [];
    $("workLinksCount").textContent = items.length || "";
    $("editWorkLinks").disabled = saving || !model || model.linked_ids === null;
    $("editWorkLinks").textContent = items.length ? "Изменить подборку" : "Выбрать заказы";
    const next = items.map((item) => '<div class="work-link-row"><div>' + (item.path
      ? '<button type="button" class="order-row-link" data-work-order-path="' + escapeHtml(item.path) + '">' + escapeHtml(item.title) + '</button>'
      : '<span>' + escapeHtml(item.title) + '</span>') + '<small>' + escapeHtml(item.supplier || "") + (item.registered ? "" : " · Убран из списка") + '</small>' +
      (item.path ? '<small>' + escapeHtml(item.path) + '</small>' : '') + '</div>' + (item.status ? '<span class="status-badge" data-status="' + escapeHtml(item.status) + '">' + escapeHtml(statusLabels[item.status] || item.status) + '</span>' : '') + '</div>').join("");
    if (next !== markup) { $("workLinksList").innerHTML = next; markup = next; }
    $("workLinksState").textContent = model?.linked_ids === null ? "Неизвестный раздел связанных заказов сохранён без изменений." : items.length ? "Папки заказов остаются у поставщиков." : "Можно оставить обычным заказом с событиями или собрать здесь заказы поставщиков.";
  }

  async function refresh(force = false) {
    const folder = state.folder;
    $("workLinksSection").hidden = state.view === "orders" || !visible(folder);
    if ($("workLinksSection").hidden) { key = null; model = null; ++loading; return; }
    if (!folder.order) {
      key = null; model = null; ++loading; render();
      $("workLinksState").textContent = "Для подборки поставщиков сначала добавь этот заказ в общий список. События можно создавать сразу.";
      return;
    }
    const nextKey = folder.path + ":" + folder.order.id;
    if (!force && key === nextKey) return;
    const version = ++loading;
    if (key !== nextKey) { model = null; render(); $("workLinksState").textContent = "Загрузка подборки…"; }
    key = nextKey;
    try {
      const result = await request(apiUrl("/api/work-order-links", folder.path));
      if (version !== loading || state.folder !== folder) return;
      model = result; render();
    } catch (error) {
      if (version === loading && state.folder === folder) $("workLinksState").textContent = error.message;
    }
  }

  function renderOptions() {
    const options = [...model.candidates, ...model.items.filter((item) => !model.candidates.some((candidate) => candidate.id === item.id))];
    const query = normalize($("workLinksSearch").value.trim());
    const matches = options.filter((item) => !query || normalize([item.title, item.supplier, item.path || ""].join(" ")).includes(query));
    $("workLinksOptions").innerHTML = matches.map((item) => '<label class="work-link-option"><input type="checkbox" data-work-order-id="' + escapeHtml(item.id) + '"' + (selection.has(item.id) ? ' checked' : '') + '><span><strong>' + escapeHtml(item.title) + '</strong><small>' + escapeHtml(item.supplier || "") + (item.registered ? "" : " · Убран из списка") + '</small><small>' + escapeHtml(item.path || "Запись недоступна") + '</small></span></label>').join("") || '<p class="todo-empty">' + (query ? 'Ничего не найдено.' : 'Сначала добавь заказы из разделов поставщиков в общий список.') + '</p>';
  }

  $("editWorkLinks").addEventListener("click", () => run(async () => {
    await refresh(true);
    if (!model || model.linked_ids === null) return;
    editingFolder = state.folder;
    selection = new Set(model.linked_ids);
    $("workLinksSearch").value = ""; $("workLinksError").textContent = "";
    renderOptions(); $("workLinksDialog").showModal(); $("workLinksSearch").focus();
  }));
  $("workLinksSearch").addEventListener("input", renderOptions);
  $("workLinksOptions").addEventListener("change", (event) => {
    const id = event.target.dataset.workOrderId;
    if (id) { if (event.target.checked) selection.add(id); else selection.delete(id); }
  });
  $("cancelWorkLinks").addEventListener("click", () => { if (!saving) $("workLinksDialog").close(); });
  $("workLinksDialog").addEventListener("cancel", (event) => { if (saving) event.preventDefault(); });
  $("workLinksList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-work-order-path]");
    if (button) run(() => navigate(button.dataset.workOrderPath));
  });
  $("workLinksForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (saving || !selection || state.folder !== editingFolder) return;
    run(async () => {
      saving = true; let pending;
      $("saveWorkLinks").disabled = true; $("cancelWorkLinks").disabled = true;
      $("workLinksError").textContent = "Сохраняю…";
      const folder = editingFolder, ids = [...selection];
      try {
        if (state.saving) await state.saving;
        if (state.folder !== folder || !folder.order) throw new Error("Открой заказ заново перед изменением подборки");
        pending = request("/api/work-order-links", { path: folder.path, revision: folder.order.revision, order_ids: ids }).then((saved) => {
          folder.order = saved;
          const listed = state.orders.find((item) => item.path === saved.path);
          if (listed) Object.assign(listed, saved);
        });
        state.saving = pending;
        await pending;
        if (state.saving === pending) state.saving = null;
        $("workLinksDialog").close();
        await refresh(true);
      } catch (error) { $("workLinksError").textContent = error.message; }
      finally {
        if (pending && state.saving === pending) state.saving = null;
        saving = false; $("saveWorkLinks").disabled = false; $("cancelWorkLinks").disabled = false;
        if (state.view !== "orders" && state.folder) { renderOrderHeading(); renderExportState(); renderStatus(); }
        render();
      }
    });
  });
  document.addEventListener("manager-folder-rendered", () => refresh());
  setInterval(() => { if (!document.hidden && state.view !== "orders" && !$("workLinksSection").hidden && !$("workLinksDialog").open && !saving) refresh(true); }, 5000);
  refresh();
})();

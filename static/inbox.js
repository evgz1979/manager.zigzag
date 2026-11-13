/* Inbox has its own keyed rows; order polling never replaces its controls. */
(() => {
  let entries = [], loading = false, saving = false, generation = 0;
  const rows = new Map();
  let folder = { path: "", count: 0, error: "" }, folderLoading = false, folderOpening = false;

  // Показывает доступность и количество файлов папки Inbox.
  // Использует `$`, `Boolean`, `button.setAttribute`.
  function renderFolder() {
    const button = $("inboxFolderButton");
    $("inboxFolderCount").textContent = folder.count ?? "—";
    button.disabled = folderOpening || !folder.path || !(folder.count > 0) || Boolean(folder.error);
    button.title = folder.error || (!folder.path ? "Папка #inbox не найдена" : folder.count === 0 ? "В папке #inbox нет файлов" : "Открыть папку #inbox в Finder");
    button.setAttribute("aria-label", "#inbox: " + (folder.count === null ? "число файлов недоступно" : "файлов " + folder.count) + ". " + button.title);
  }

  // Перечитывает узкий файловый счётчик папки Inbox.
  // Использует `/api/inbox-folder`.
  async function loadFolder() {
    if (state.view !== "orders" || folderLoading || document.hidden) return;
    folderLoading = true;
    try {
      folder = await request("/api/inbox-folder");
    } catch (_) {
      folder = { path: "", count: null, error: "Не удалось проверить папку #inbox. Повторим автоматически" };
    } finally {
      folderLoading = false;
      renderFolder();
    }
  }

  $("inboxFolderButton").addEventListener("click", () => run(async () => {
    if ($("inboxFolderButton").disabled) return;
    folderOpening = true;
    renderFolder();
    try { await openNative(folder.path); }
    finally { folderOpening = false; renderFolder(); }
  }));

  // Строит строки текущего списка компонента.
  // Использует `Set`, `items.map`, `ids.has`.
  function renderList(container, items) {
    const ids = new Set(items.map(item => item.id));
    for (const row of [...container.children]) if (!ids.has(row.dataset.inboxId)) row.remove();
    items.forEach((item, index) => {
      let row = rows.get(item.id);
      if (!row) {
        row = document.createElement("div");
        row.className = "inbox-item";
        row.dataset.inboxId = item.id;
        const input = document.createElement("input");
        input.type = "checkbox";
        input.addEventListener("change", () => run(() => complete(item.id, input.checked)));
        const task = document.createElement("label"), text = document.createElement("span");
        task.className = "inbox-task";
        text.className = "inbox-text";
        task.append(input, text);
        const actions = document.createElement("div"), copyButton = document.createElement("button"), removeButton = document.createElement("button");
        actions.className = "inbox-actions";
        copyButton.type = removeButton.type = "button";
        copyButton.className = "inbox-action inbox-copy";
        copyButton.innerHTML = icon("copy");
        copyButton.title = "Скопировать текст";
        copyButton.addEventListener("click", () => copy(item.id).catch(error => notify(error.message, true)));
        removeButton.className = "inbox-action inbox-remove";
        removeButton.textContent = "×";
        removeButton.title = "Удалить";
        removeButton.addEventListener("click", () => run(() => remove(item.id)));
        actions.append(copyButton, removeButton);
        row.append(task, actions);
        rows.set(item.id, row);
      }
      const input = row.querySelector("input"), text = row.querySelector(".inbox-text");
      input.checked = item.completed;
      input.disabled = saving;
      input.setAttribute("aria-label", (item.completed ? "Вернуть в Inbox: " : "Выполнить: ") + item.text);
      row.querySelector(".inbox-copy").setAttribute("aria-label", "Скопировать: " + item.text);
      const removeButton = row.querySelector(".inbox-remove");
      removeButton.setAttribute("aria-label", "Удалить из Inbox: " + item.text);
      removeButton.disabled = saving;
      if (text.textContent !== item.text) text.textContent = item.text;
      row.title = new Date(item.created_at * 1000).toLocaleString("ru", { timeZone: "Europe/Moscow" });
      row.classList.toggle("completed", item.completed);
      if (container.children[index] !== row) container.insertBefore(row, container.children[index] || null);
    });
  }

  // Обновляет DOM компонента из текущих данных в модуле Telegram Inbox.
  // Использует `entries.filter`, `renderList`, `$`.
  function render() {
    const active = entries.filter(item => !item.completed), done = entries.filter(item => item.completed);
    renderList($("inboxList"), active);
    renderList($("inboxCompletedList"), done);
    $("inboxCount").textContent = active.length;
    $("inboxEmpty").hidden = Boolean(active.length);
    $("inboxCompleted").hidden = !done.length;
    $("inboxCompletedSummary").textContent = "Выполненные · " + done.length;
  }

  // Загружает сохранённые данные компонента с сервера в модуле Telegram Inbox.
  // Использует `/api/inbox`.
  async function load() {
    if (state.view !== "orders" || loading || saving || document.hidden) return;
    const version = ++generation;
    loading = true;
    try {
      const result = await request("/api/inbox");
      if (version !== generation) return;
      entries = result.items;
      render();
      $("inboxState").textContent = result.error || (!result.configured ? "Подключи бота через «В Telegram»." : "");
      $("inboxState").classList.toggle("error", Boolean(result.error));
    } catch (error) {
      if (version === generation) {
        $("inboxState").textContent = error.message || "Нет связи с сервером. Показаны последние задачи.";
        $("inboxState").classList.add("error");
      }
    } finally { loading = false; }
  }

  // Возвращает фокус на действие конкретной задачи Inbox.
  // Использует `rows.get`.
  function focusTask(id) {
    rows.get(id)?.querySelector("input").focus({ preventScroll: true });
  }

  // Переводит фокус на доступную задачу после удаления строки.
  // Обращается к DOM текущего документа или переданного контейнера.
  function focusRemaining() {
    ($("inboxList").querySelector("input") || (!$("inboxCompleted").hidden && $("inboxCompletedSummary")) || $("inboxTitle")).focus({ preventScroll: true });
  }

  // Применяет подтверждённое частичное изменение к компоненту в модуле Telegram Inbox.
  // Использует `/api/inbox-`.
  async function update(item, action, fields = {}) {
    if (saving) throw new Error("Дождись сохранения задачи Inbox");
    const focused = document.activeElement;
    ++generation;
    saving = true;
    $("inboxPanel").querySelectorAll("input, .inbox-remove").forEach(control => { control.disabled = true; });
    let saved, failure;
    try {
      const response = await fetch("/api/inbox-" + action, {
        method: "POST", headers: { "Content-Type": "application/json", "X-Manager-Inbox": "1" },
        body: JSON.stringify({ id: item.id, revision: item.revision, ...fields }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Не удалось сохранить задачу Inbox");
      entries = entries.filter(entry => entry.id !== item.id);
      if (!result.deleted) entries.push(result);
      entries.sort((a, b) => a.created_at - b.created_at || a.message_id - b.message_id || a.line - b.line || a.id.localeCompare(b.id));
      saved = result;
    } catch (error) { failure = error; }
    finally {
      saving = false;
      render();
      if (focused?.isConnected) focused.focus({ preventScroll: true });
    }
    if (failure) { await load(); throw failure; }
    return saved;
  }

  // Сохраняет выполнение выбранной задачи Inbox с ожидаемой версией.
  // Использует `entries.find`, `update`, `focusRemaining`.
  async function complete(id, completed) {
    const item = entries.find(entry => entry.id === id);
    if (!item) return;
    await update(item, "complete", { completed });
    if (completed) focusRemaining();
    else focusTask(id);
  }

  // Удаляет выбранную задачу или документ через API компонента.
  // Использует `entries.find`, `update`, `focusRemaining`.
  async function remove(id) {
    const item = entries.find(entry => entry.id === id);
    if (!item) return;
    const removed = await update(item, "remove");
    focusRemaining();
    notify("Задача удалена", false, { label: "Отменить", /* Выполняет сохранённое действие отмены или подтверждённую операцию компонента.
     * Использует `update`, `$`, `focusTask`. */ run: async () => {
      const restored = await update(removed, "restore");
      if (restored.completed) $("inboxCompleted").open = true;
      focusTask(id);
      notify("Задача возвращена в Inbox");
    } });
  }

  // Копирует точный текст задачи и сообщает результат пользователю.
  // Использует общий буфер обмена браузера и уведомление об успехе.
  async function copy(id) {
    const item = entries.find(entry => entry.id === id);
    if (!item) return;
    await copyText(item.text);
    notify("Текст скопирован");
  }

  // Загружает задачи Telegram и файловый счётчик Inbox.
  // Использует `Promise.all`, `load`, `loadFolder`.
  function loadAll() { return Promise.all([load(), loadFolder()]); }
  window.ManagerInbox = { load: loadAll };
  setInterval(loadAll, 5000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) loadAll(); });
  loadAll();
})();

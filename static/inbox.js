/* Inbox has its own keyed rows; order polling never replaces its controls. */
(() => {
  let entries = [], loading = false, saving = false, generation = 0;
  const rows = new Map();

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

  function render() {
    const active = entries.filter(item => !item.completed), done = entries.filter(item => item.completed);
    renderList($("inboxList"), active);
    renderList($("inboxCompletedList"), done);
    $("inboxCount").textContent = active.length;
    $("inboxEmpty").hidden = Boolean(active.length);
    $("inboxCompleted").hidden = !done.length;
    $("inboxCompletedSummary").textContent = "Выполненные · " + done.length;
  }

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

  function focusTask(id) {
    rows.get(id)?.querySelector("input").focus({ preventScroll: true });
  }

  function focusRemaining() {
    ($("inboxList").querySelector("input") || (!$("inboxCompleted").hidden && $("inboxCompletedSummary")) || $("inboxTitle")).focus({ preventScroll: true });
  }

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

  async function complete(id, completed) {
    const item = entries.find(entry => entry.id === id);
    if (!item) return;
    await update(item, "complete", { completed });
    if (completed) focusRemaining();
    else focusTask(id);
  }

  async function remove(id) {
    const item = entries.find(entry => entry.id === id);
    if (!item) return;
    const removed = await update(item, "remove");
    focusRemaining();
    notify("Задача удалена", false, { label: "Отменить", run: async () => {
      const restored = await update(removed, "restore");
      if (restored.completed) $("inboxCompleted").open = true;
      focusTask(id);
      notify("Задача возвращена в Inbox");
    } });
  }

  async function copy(id) {
    const item = entries.find(entry => entry.id === id);
    if (!item) return;
    try {
      if (window.isSecureContext && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(item.text);
      } else {
        const focused = document.activeElement, selection = window.getSelection();
        const ranges = selection ? Array.from({ length: selection.rangeCount }, (_, i) => selection.getRangeAt(i).cloneRange()) : [];
        const field = document.createElement("textarea");
        field.value = item.text;
        field.readOnly = true;
        field.style.cssText = "position:fixed;left:-9999px;top:0";
        document.body.append(field);
        let copied = false;
        const onCopy = event => {
          if (!event.clipboardData) return;
          event.clipboardData.setData("text/plain", item.text);
          event.preventDefault();
          copied = true;
        };
        document.addEventListener("copy", onCopy, true);
        try {
          field.focus({ preventScroll: true });
          field.select();
          field.setSelectionRange(0, field.value.length);
          if (!document.execCommand("copy") || !copied) throw new Error("copy failed");
        } finally {
          document.removeEventListener("copy", onCopy, true);
          field.remove();
          if (focused?.isConnected) focused.focus({ preventScroll: true });
          if (selection) { selection.removeAllRanges(); ranges.forEach(range => selection.addRange(range)); }
        }
      }
      notify("Текст скопирован");
    } catch (_) { throw new Error("Не удалось скопировать текст. Выдели его и скопируй вручную"); }
  }

  window.ManagerInbox = { load };
  setInterval(load, 5000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) load(); });
  load();
})();

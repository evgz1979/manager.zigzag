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
        row = document.createElement("label");
        row.className = "inbox-item";
        row.dataset.inboxId = item.id;
        const input = document.createElement("input");
        input.type = "checkbox";
        input.addEventListener("change", () => complete(item.id, input.checked));
        row.append(input, document.createElement("span"));
        rows.set(item.id, row);
      }
      const input = row.firstElementChild;
      input.checked = item.completed;
      input.disabled = saving;
      input.setAttribute("aria-label", (item.completed ? "Вернуть в Inbox: " : "Выполнить: ") + item.text);
      if (row.lastElementChild.textContent !== item.text) row.lastElementChild.textContent = item.text;
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

  async function complete(id, completed) {
    if (saving) { render(); return; }
    const item = entries.find(entry => entry.id === id);
    if (!item) return;
    ++generation;
    saving = true;
    $("inboxPanel").querySelectorAll("input").forEach(input => { input.disabled = true; });
    let saved = false;
    try {
      const response = await fetch("/api/inbox-complete", {
        method: "POST", headers: { "Content-Type": "application/json", "X-Manager-Inbox": "1" },
        body: JSON.stringify({ id, revision: item.revision, completed }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Не удалось сохранить задачу Inbox");
      entries = entries.map(entry => entry.id === id ? result : entry);
      saved = true;
    } catch (error) { notify(error.message, true); }
    finally {
      saving = false;
      render();
      if (saved && completed) ($("inboxList").querySelector("input") || $("inboxCompletedSummary")).focus({ preventScroll: true });
      else rows.get(id)?.firstElementChild.focus({ preventScroll: true });
    }
    if (!saved) await load();
  }

  window.ManagerInbox = { load };
  setInterval(load, 5000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) load(); });
  load();
})();

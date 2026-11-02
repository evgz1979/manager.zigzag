/* Capture a detached copy: sending never scrolls or focuses the live calendar. */
(() => {
  const get = (id) => document.getElementById(id);
  const dialog = get("calendarTelegramSettings");
  let settingsBusy = false;
  async function readSettings() {
    const response = await fetch("/api/calendar-telegram-settings");
    if (!response.ok) throw new Error("Не удалось проверить настройку Telegram на M4");
    return response.json();
  }
  function showSettings(current) {
    const connected = get("calendarTelegramConnected");
    connected.hidden = !current.configured;
    connected.textContent = current.configured ? "Подключён: @" + (current.bot_username || "бот календаря") + " · чат " + current.chat_id : "";
    if (!dialog.open) dialog.showModal();
  }
  async function openSettings() {
    try { showSettings(await readSettings()); }
    catch (error) { notify(error.message, true); }
  }
  function setSettingsBusy(value) {
    settingsBusy = value;
    for (const control of dialog.querySelectorAll("input, select, button")) control.disabled = value;
    dialog.setAttribute("aria-busy", String(value));
  }
  async function settingsRequest(action) {
    const response = await fetch("/api/calendar-telegram-settings", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Manager-Calendar": "1" },
      body: JSON.stringify({action, bot_token: get("calendarTelegramToken").value.trim(), chat_id: get("calendarTelegramChatId").value.trim()}),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Не удалось подключить бота");
    return result;
  }
  get("calendarTelegramSettingsClose").addEventListener("click", () => { if (!settingsBusy) dialog.close(); });
  dialog.addEventListener("cancel", (event) => { if (settingsBusy) event.preventDefault(); });
  dialog.addEventListener("close", () => {
    get("calendarTelegramToken").value = "";
    get("calendarTelegramChatId").value = "";
    get("calendarTelegramChat").replaceChildren(new Option("Сначала нажми «Найти мой чат»", ""));
    get("calendarTelegramSettingsError").hidden = true;
    get("calendarTelegramSettingsHint").textContent = "Токен сохранится только на M4. При повторном открытии поле будет пустым.";
  });
  get("calendarTelegramChat").addEventListener("change", (event) => { get("calendarTelegramChatId").value = event.target.value; });
  get("calendarTelegramToken").addEventListener("input", () => {
    get("calendarTelegramChat").replaceChildren(new Option("Сначала нажми «Найти мой чат»", ""));
    get("calendarTelegramChatId").value = "";
  });
  get("calendarTelegramFindChat").addEventListener("click", async () => {
    if (settingsBusy || !get("calendarTelegramToken").reportValidity()) return;
    setSettingsBusy(true);
    get("calendarTelegramSettingsError").hidden = true;
    try {
      const result = await settingsRequest("chats");
      const select = get("calendarTelegramChat");
      select.replaceChildren(new Option("Выбери свой чат", ""), ...result.chats.map((chat) => new Option(chat.label + " · " + chat.id, chat.id)));
      if (result.chats.length === 1) { select.value = result.chats[0].id; get("calendarTelegramChatId").value = result.chats[0].id; }
      get("calendarTelegramSettingsHint").textContent = result.chats.length ? "Бот @" + result.bot_username + ". Проверь свой чат и нажми «Подключить бота»." : "Открой @" + result.bot_username + " в Telegram, нажми «Старт» или отправь сообщение, затем снова «Найти мой чат».";
    } catch (error) {
      get("calendarTelegramSettingsError").textContent = error.message;
      get("calendarTelegramSettingsError").hidden = false;
    } finally { setSettingsBusy(false); }
  });
  get("calendarTelegramSettingsForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (settingsBusy) return;
    setSettingsBusy(true);
    get("calendarTelegramSettingsError").hidden = true;
    try {
      const result = await settingsRequest("save");
      dialog.close();
      notify("Подключён отдельный бот @" + result.bot_username + ". Нажми «В Telegram» для отправки календаря");
    } catch (error) {
      get("calendarTelegramSettingsError").textContent = error.message;
      get("calendarTelegramSettingsError").hidden = false;
    } finally { setSettingsBusy(false); }
  });
  get("calendarTelegram").addEventListener("contextmenu", (event) => { event.preventDefault(); openSettings(); });
  get("calendarTelegram").addEventListener("keydown", (event) => {
    if (event.key === "F10" && event.shiftKey) { event.preventDefault(); openSettings(); }
  });
  document.getElementById("calendarTelegram").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    if (button.disabled) return;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.textContent = "Отправляю…";
    try {
      const current = await readSettings();
      if (!current.configured) { showSettings(current); return; }
      const { image, start, through } = await CalendarSnapshot.capture();
      const response = await fetch("/api/calendar-telegram?start=" + encodeURIComponent(start) + "&through=" + encodeURIComponent(through), {
        method: "POST", headers: { "Content-Type": "image/png", "X-Manager-Calendar": "1" }, body: image,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Не удалось отправить календарь");
      notify(result.todo_messages ? "Календарь и списки To-do отправлены в Telegram" : "Общий календарь отправлен в Telegram");
    } catch (error) {
      notify(error instanceof TypeError ? "Нет подтверждения отправки. Проверь Telegram перед повтором" : error.message, true, {label: "Настроить бота", run: openSettings});
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = "В Telegram";
    }
  });
})();

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
  let renderer;
  function loadRenderer() {
    if (!renderer) renderer = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "/vendor/html2canvas/html2canvas.min.js";
      script.onload = () => resolve(window.html2canvas);
      script.onerror = () => { script.remove(); renderer = null; reject(new Error("Не удалось загрузить создание снимка. Обнови страницу и повтори")); };
      document.head.append(script);
    });
    return renderer;
  }

  async function capture() {
    const render = await loadRenderer();
    await document.fonts.ready;
    const { element, start } = HomeCalendar.createSnapshot();
    element.style.width = Math.max(1440, Math.ceil(document.getElementById("homeCalendar").getBoundingClientRect().width)) + "px";
    document.body.append(element);
    try {
      for (const amount of element.querySelectorAll(".calendar-plan-amount")) {
        amount.style.fontSize = "";
        const available = amount.parentElement.clientWidth;
        if (available && amount.scrollWidth > available) amount.style.fontSize = (parseFloat(getComputedStyle(amount).fontSize) * available / amount.scrollWidth * .97) + "px";
      }
      // Expand every internal list, including free events below the orders.
      for (const week of element.querySelectorAll(".calendar-week")) {
        const content = week.querySelector(".calendar-week-content");
        const header = parseFloat(week.style.getPropertyValue("--calendar-header-height")) || 46;
        week.style.height = Math.max(week.getBoundingClientRect().height, header + content.scrollHeight + 2) + "px";
        content.scrollTop = 0;
      }
      const width = Math.ceil(element.getBoundingClientRect().width), height = Math.ceil(element.getBoundingClientRect().height);
      const scale = Math.min(2, 8192 / width, 16384 / height, Math.sqrt(32000000 / (width * height)));
      if (scale < 1) throw new Error("Слишком много строк для одного снимка календаря");
      const canvas = await render(element, {
        backgroundColor: "#fff", scale, logging: false, width, height,
        windowWidth: Math.max(window.innerWidth, width + 32),
        ignoreElements: (node) => node.parentElement === document.body && node !== element,
        onclone: (_document, copy) => { copy.style.position = "static"; copy.style.left = "0"; },
      });
      const image = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
      if (!image) throw new Error("Браузер не смог создать снимок календаря");
      if (image.size > 10 * 1024 * 1024) throw new Error("Снимок календаря превышает 10 МБ");
      return { image, start };
    } finally { element.remove(); }
  }

  document.getElementById("calendarTelegram").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    if (button.disabled) return;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.textContent = "Отправляю…";
    try {
      const current = await readSettings();
      if (!current.configured) { showSettings(current); return; }
      const { image, start } = await capture();
      const response = await fetch("/api/calendar-telegram?start=" + encodeURIComponent(start), {
        method: "POST", headers: { "Content-Type": "image/png", "X-Manager-Calendar": "1" }, body: image,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Не удалось отправить календарь");
      notify("Текущая и две следующие недели отправлены в Telegram");
    } catch (error) {
      notify(error instanceof TypeError ? "Нет подтверждения отправки. Проверь Telegram перед повтором" : error.message, true, {label: "Настроить бота", run: openSettings});
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = "В Telegram";
    }
  });
})();

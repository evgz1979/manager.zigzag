/* Capture a detached copy: sending never scrolls or focuses the live calendar. */
(() => {
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
      const { image, start } = await capture();
      const response = await fetch("/api/calendar-telegram?start=" + encodeURIComponent(start), {
        method: "POST", headers: { "Content-Type": "image/png", "X-Manager-Calendar": "1" }, body: image,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Не удалось отправить календарь");
      notify("Текущая и две следующие недели отправлены в Telegram");
    } catch (error) {
      notify(error instanceof TypeError ? "Нет подтверждения отправки. Проверь Telegram перед повтором" : error.message, true);
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = "В Telegram";
    }
  });
})();

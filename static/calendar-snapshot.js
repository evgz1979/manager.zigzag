/* Shared browser and server calendar image rendering. */
const CalendarSnapshot = (() => {
  let renderer;
  // Лениво загружает локальную библиотеку HTML-снимка.
  // Использует `Promise.resolve`, `Promise`.
  function loadRenderer() {
    if (window.html2canvas) return Promise.resolve(window.html2canvas);
    if (!renderer) renderer = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "/vendor/html2canvas/html2canvas.min.js";
      script.onload = () => resolve(window.html2canvas);
      script.onerror = () => { script.remove(); renderer = null; reject(new Error("Не удалось загрузить создание снимка. Обнови страницу и повтори")); };
      document.head.append(script);
    });
    return renderer;
  }

  // Создаёт общий PNG из отдельного DOM-снимка календаря.
  // Обращается к DOM текущего документа или переданного контейнера.
  async function capture(now = new Date()) {
    const render = await loadRenderer();
    await document.fonts.ready;
    const { element, start, through } = HomeCalendar.createSnapshot(now);
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
        // Исключает управляющие элементы из изображения календаря.
        // Результат вычисляется из переданных аргументов и текущего состояния компонента.
        ignoreElements: (node) => node.parentElement === document.body && node !== element,
        // Применяет нужные размеры и оформление к копии DOM для снимка.
        // Результат вычисляется из переданных аргументов и текущего состояния компонента.
        onclone: (_document, copy) => { copy.style.position = "static"; copy.style.left = "0"; },
      });
      const image = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
      if (!image) throw new Error("Браузер не смог создать снимок календаря");
      if (image.size > 10 * 1024 * 1024) throw new Error("Снимок календаря превышает 10 МБ");
      return { image, start, through };
    } finally { element.remove(); }
  }

  return { capture };
})();

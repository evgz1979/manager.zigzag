/* A bounded calendar with weekly order deadlines. Civil dates use Moscow. */
const HomeCalendar = (() => {
  const DAY = 86400000;
  const dateKey = (date) => date.toISOString().slice(0, 10);
  const shiftDays = (date, days) => new Date(date.getTime() + days * DAY);
  const monday = (date) => shiftDays(date, -((date.getUTCDay() + 6) % 7));
  const weekNumber = (date) => {
    const thursday = shiftDays(monday(date), 3);
    return Math.ceil(((thursday - new Date(Date.UTC(thursday.getUTCFullYear(), 0, 1))) / DAY + 1) / 7);
  };
  const moscowDate = (now) => {
    const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now);
    const value = (name) => Number(parts.find((part) => part.type === name).value);
    return new Date(Date.UTC(value("year"), value("month") - 1, value("day")));
  };
  const shiftMonths = (date, months) => {
    const first = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + months, 1));
    const lastDay = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
    first.setUTCDate(Math.min(date.getUTCDate(), lastDay));
    return first;
  };
  function calendarRange(now = new Date()) {
    const today = moscowDate(now), from = shiftMonths(today, -1), through = shiftMonths(today, 2);
    return { today, from, through, start: monday(from), end: shiftDays(monday(through), 6) };
  }

  let range, builtFor = "", initialized = false, frame = 0, rowPixels = 0, visibleWeek = 0, orders = [];
  const get = (id) => document.getElementById(id);
  const monthName = new Intl.DateTimeFormat("ru-RU", { month: "long", timeZone: "UTC" });
  const shortDate = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", timeZone: "UTC" });
  const fullDate = new Intl.DateTimeFormat("ru-RU", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const weekHeight = () => get("calendarWeeks").firstElementChild?.getBoundingClientRect().height || 1;
  const maxScroll = () => Math.max(0, get("calendarViewport").scrollHeight - get("calendarViewport").clientHeight);

  function updateHeading() {
    frame = 0;
    const viewport = get("calendarViewport");
    const height = weekHeight();
    // A resize can trigger a scroll event before ResizeObserver corrects the position.
    if (rowPixels && Math.abs(height - rowPixels) > .1) return;
    rowPixels = height;
    const index = visibleWeek = Math.round(viewport.scrollTop / height);
    const first = shiftDays(range.start, index * 7), last = shiftDays(first, 20);
    const sameMonth = first.getUTCMonth() === last.getUTCMonth() && first.getUTCFullYear() === last.getUTCFullYear();
    get("calendarTitle").textContent = sameMonth ? monthName.format(first) + " " + first.getUTCFullYear() :
      monthName.format(first) + (first.getUTCFullYear() !== last.getUTCFullYear() ? " " + first.getUTCFullYear() : "") + " — " + monthName.format(last) + " " + last.getUTCFullYear();
    get("calendarEarlier").disabled = viewport.scrollTop < 1;
    get("calendarLater").disabled = viewport.scrollTop >= maxScroll() - 1;
  }

  function scrollToWeek(date) {
    rowPixels = weekHeight();
    visibleWeek = Math.round((monday(date) - range.start) / (7 * DAY));
    get("calendarViewport").scrollTop = Math.min(maxScroll(), Math.max(0, visibleWeek * rowPixels));
    updateHeading();
  }

  function renderWeekOrders() {
    const byWeek = new Map();
    for (const order of orders) {
      if (!order.path || order.registered === false) continue;
      const eventWeeks = Object.keys(order.calendar_events || {}).map((day) => dateKey(monday(new Date(day + "T00:00:00Z"))));
      for (const week of new Set([...(order.deadline_weeks || []), ...eventWeeks, ...Object.keys(order.calendar_week_events || {})])) {
        if (!byWeek.has(week)) byWeek.set(week, []);
        byWeek.get(week).push(order);
      }
    }
    for (const row of get("calendarWeeks").children) {
      const list = row.querySelector(".calendar-orders-list"), weekly = byWeek.get(row.dataset.week) || [];
      const signature = JSON.stringify(weekly.map((order) => [order.id, order.path, order.title, order.client, order.object, order.work_supplier, order.work_supplier_color, order.calendar_events, order.calendar_week_events]));
      if (list.dataset.signature === signature) continue;
      list.dataset.signature = signature;
      const top = list.parentElement.scrollTop;
      const focused = list.contains(document.activeElement) ? document.activeElement : null;
      const existing = new Map([...list.children].map((item) => [item.dataset.orderKey, item]));
      const retained = new Set();
      let before = list.firstElementChild;
      for (const order of weekly) {
        const key = JSON.stringify([order.id, order.path]);
        let item = existing.get(key);
        if (!item) {
          item = document.createElement("li");
          item.dataset.orderKey = key;
          item.className = "calendar-order-row";
          const link = document.createElement("a"), title = document.createElement("span"), client = document.createElement("small");
          link.className = "calendar-order-link";
          title.className = "calendar-order-title";
          client.className = "calendar-order-client";
          link.append(title, client);
          item.append(link);
          for (let day = -1; day < 7; day++) {
            const slot = document.createElement("button");
            slot.type = "button";
            slot.className = "calendar-event-slot";
            item.append(slot);
          }
        }
        const supplier = Boolean(order.work_supplier), color = order.work_supplier_color;
        item.classList.toggle("calendar-supplier-order", supplier);
        item.classList.toggle("supplier-neutral", supplier && Boolean(color?.neutral));
        if (supplier) item.style.setProperty("--supplier-hue", String(color?.hue ?? 0));
        else item.style.removeProperty("--supplier-hue");
        const link = item.firstElementChild, title = order.title || order.path;
        link.href = "?path=" + encodeURIComponent(order.path);
        link.dataset.calendarOrder = order.path;
        link.setAttribute("aria-label", [title, order.client, order.object].filter(Boolean).join(" · "));
        link.firstElementChild.textContent = title;
        link.lastElementChild.textContent = order.client || "";
        link.lastElementChild.hidden = !order.client;
        for (let day = -1; day < 7; day++) {
          const week = new Date(row.dataset.week + "T00:00:00Z"), isWeek = day === -1;
          const date = shiftDays(week, isWeek ? 0 : day), key = dateKey(date);
          const entries = isWeek ? order.calendar_week_events : order.calendar_events;
          const slot = item.children[day + 2], text = entries?.[key] || "";
          slot.dataset.calendarEvent = order.path;
          slot.dataset.calendarDate = key;
          slot.dataset.calendarPeriod = isWeek ? "week" : "day";
          slot.classList.toggle("calendar-week-event-slot", isWeek);
          slot.textContent = text;
          slot.classList.toggle("has-event", Boolean(text));
          if (text) slot.setAttribute("aria-haspopup", "menu");
          else slot.removeAttribute("aria-haspopup");
          slot.disabled = entries === null || (isWeek ? shiftDays(week, 6) < range.from || week > range.through : date < range.from || date > range.through);
          const periodLabel = isWeek ? "Неделя " + weekNumber(week) + ": " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)) : fullDate.format(date);
          slot.setAttribute("aria-label", (text ? "Изменить событие: " + text : "Добавить событие") + " · " + title + " · " + periodLabel);
        }
        if (item !== before) list.insertBefore(item, before);
        before = item.nextElementSibling;
        retained.add(item);
      }
      for (const item of [...list.children]) if (!retained.has(item)) item.remove();
      if (!weekly.length) {
        const empty = document.createElement("li");
        empty.className = "calendar-orders-empty";
        empty.textContent = "Нет заказов";
        list.append(empty);
      }
      list.parentElement.scrollTop = top;
      if (focused && document.activeElement !== focused) {
        (focused.isConnected ? focused : list.querySelector("a") || get("calendarViewport")).focus({ preventScroll: true });
      }
    }
  }

  function show(nextOrders) {
    if (Array.isArray(nextOrders)) orders = nextOrders;
    const nextRange = calendarRange();
    if (builtFor !== dateKey(nextRange.today)) {
      range = nextRange;
      builtFor = dateKey(range.today);
      const weeks = document.createDocumentFragment();
      for (let week = range.start; week <= range.end; week = shiftDays(week, 7)) {
        const row = document.createElement("div");
        row.className = "calendar-week";
        row.dataset.week = dateKey(week);
        const orderCell = document.createElement("div"), content = document.createElement("div"), list = document.createElement("ul");
        orderCell.className = "calendar-day calendar-orders-cell";
        content.className = "calendar-week-content";
        list.className = "calendar-orders-list";
        list.setAttribute("aria-label", "Заказы на неделю: " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)));
        content.append(list);
        row.append(orderCell);
        const weekCell = document.createElement("div"), weekLabel = document.createElement("span");
        weekCell.className = "calendar-day calendar-week-events-cell";
        weekLabel.className = "calendar-week-number";
        weekLabel.textContent = weekNumber(week);
        weekLabel.setAttribute("aria-label", "Неделя " + weekNumber(week) + ": " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)));
        weekCell.append(weekLabel);
        row.append(weekCell);
        for (let day = 0; day < 7; day++) {
          const date = shiftDays(week, day), cell = document.createElement("div"), label = document.createElement("time");
          cell.className = "calendar-day" + (day > 4 ? " weekend" : "") + (date < range.from || date > range.through ? " calendar-outside" : "");
          label.dateTime = dateKey(date);
          label.setAttribute("aria-label", fullDate.format(date));
          label.textContent = date.getUTCDate() === 1 ? shortDate.format(date) : String(date.getUTCDate());
          if (dateKey(date) === builtFor) { label.className = "calendar-today"; label.setAttribute("aria-current", "date"); }
          cell.append(label);
          row.append(cell);
        }
        row.append(content);
        weeks.append(row);
      }
      get("calendarWeeks").replaceChildren(weeks);
      scrollToWeek(range.today);
    } else updateHeading();
    renderWeekOrders();
    if (initialized) return;
    initialized = true;
    const viewport = get("calendarViewport");
    get("calendarToday").addEventListener("click", () => { show(); scrollToWeek(range.today); });
    get("calendarEarlier").addEventListener("click", () => { viewport.scrollBy({ top: -weekHeight(), behavior: "smooth" }); });
    get("calendarLater").addEventListener("click", () => { viewport.scrollBy({ top: weekHeight(), behavior: "smooth" }); });
    viewport.addEventListener("scroll", () => { if (!frame) frame = requestAnimationFrame(updateHeading); }, { passive: true });
    viewport.addEventListener("keydown", (event) => {
      if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        viewport.scrollTop = event.key === "Home" ? 0 : maxScroll();
      }
    });
    // Keep the same week visible when the window changes height.
    new ResizeObserver(() => {
      const height = weekHeight();
      if (viewport.clientHeight && Math.abs(height - rowPixels) > .1) {
        rowPixels = height;
        viewport.scrollTop = Math.min(maxScroll(), visibleWeek * height);
        updateHeading();
      }
    }).observe(viewport);
  }
  return { show, calendarRange };
})();

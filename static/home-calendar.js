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

  let range, builtFor = "", initialized = false, frame = 0, rowPixels = 0, visibleWeek = 0, orders = [], events = [], invoicePlans = [];
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
      const signature = JSON.stringify(weekly.map((order) => [order.id, order.path, order.title, order.client, order.object, order.work_supplier, order.work_supplier_color, order.calendar_events, order.calendar_week_events, order.calendar_inactive]));
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
          slot.classList.toggle("calendar-inactive", Boolean(text) && Boolean(order.calendar_inactive?.[isWeek ? "week" : "day"]?.includes(key)));
          slot.classList.toggle("has-event", Boolean(text));
          if (text) slot.setAttribute("aria-haspopup", "menu");
          else slot.removeAttribute("aria-haspopup");
          slot.disabled = entries === null || (isWeek ? shiftDays(week, 6) < range.from || week > range.through : date < range.from || date > range.through);
          const periodLabel = isWeek ? "Неделя " + weekNumber(week) + ": " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)) : fullDate.format(date);
          slot.setAttribute("aria-label", (slot.classList.contains("calendar-inactive") ? "Неактуально · " : "") + (text ? "Изменить событие: " + text : "Добавить событие") + " · " + title + " · " + periodLabel);
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

  function renderFreeEvents() {
    for (const row of get("calendarWeeks").children) {
      const area = row.querySelector(".calendar-free-events"), week = new Date(row.dataset.week + "T00:00:00Z");
      const weekly = events.filter((event) => /^(day|week)$/.test(event.period) && /^\d{4}-\d{2}-\d{2}$/.test(event.date) && Number.isFinite(new Date(event.date + "T00:00:00Z").getTime()) && dateKey(monday(new Date(event.date + "T00:00:00Z"))) === row.dataset.week);
      const signature = JSON.stringify(weekly);
      if (area.dataset.signature === signature) continue;
      area.dataset.signature = signature;
      const top = area.parentElement.scrollTop;
      const focused = area.contains(document.activeElement) ? document.activeElement : null;
      const existing = new Map([...area.querySelectorAll(".has-event")].map((item) => [item.dataset.calendarFree, item]));
      const retained = new Set();
      for (let day = -1; day < 7; day++) {
        const column = area.children[day + 2], isWeek = day === -1;
        const date = shiftDays(week, isWeek ? 0 : day), key = dateKey(date), period = isWeek ? "week" : "day";
        const label = isWeek ? "Неделя " + weekNumber(week) + ": " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)) : fullDate.format(date);
        const add = column.lastElementChild;
        add.dataset.calendarDate = key;
        add.dataset.calendarPeriod = period;
        add.disabled = isWeek ? shiftDays(week, 6) < range.from || week > range.through : date < range.from || date > range.through;
        add.setAttribute("aria-label", "Добавить событие без заказа · " + label);
        for (const event of weekly.filter((event) => event.period === period && event.date === key)) {
          let button = existing.get(event.id);
          if (!button) {
            button = document.createElement("button");
            button.type = "button";
            button.className = "calendar-event-slot calendar-free-event has-event";
            button.dataset.calendarEvent = "";
            button.dataset.calendarFree = event.id;
            button.setAttribute("aria-haspopup", "menu");
          }
          button.textContent = event.text;
          button.dataset.calendarColor = event.color || "gray";
          button.classList.toggle("calendar-inactive", event.is_inactive === 1);
          button.dataset.calendarDate = key;
          button.dataset.calendarPeriod = period;
          button.disabled = event.version !== 1 || ![0, 1].includes(event.is_inactive) || !["gray", "red", "orange", "yellow", "green", "blue", "purple"].includes(event.color) || add.disabled;
          button.setAttribute("aria-label", (button.classList.contains("calendar-inactive") ? "Неактуально · " : "") + "Изменить событие без заказа: " + event.text + " · " + label);
          column.insertBefore(button, add);
          retained.add(button);
        }
      }
      for (const button of existing.values()) if (!retained.has(button)) button.remove();
      area.parentElement.scrollTop = top;
      if (focused && document.activeElement !== focused) {
        (focused.isConnected ? focused : area.querySelector(".calendar-free-add:not(:disabled)") || get("calendarViewport")).focus({ preventScroll: true });
      }
    }
  }

  function renderInvoicePlans() {
    const byDate = new Map();
    for (const plan of invoicePlans) {
      if (!byDate.has(plan.date)) byDate.set(plan.date, []);
      byDate.get(plan.date).push(plan);
    }
    for (const area of get("calendarWeeks").querySelectorAll('.calendar-invoice-plans')) {
      const order = { incoming: 0, outgoing: 1, invoice: 2 };
      const plans = (byDate.get(area.dataset.date) || []).sort((a, b) => (order[a.operation || 'invoice'] ?? 3) - (order[b.operation || 'invoice'] ?? 3));
      const signature = JSON.stringify(plans);
      if (area.dataset.signature === signature) continue;
      area.dataset.signature = signature;
      const top = area.scrollTop, focused = area.contains(document.activeElement) ? document.activeElement : null;
      const existing = new Map([...area.children].map((link) => [link.dataset.invoicePlan, link]));
      let before = area.firstElementChild;
      const retained = new Set();
      for (const plan of plans) {
        let link = existing.get(plan.id);
        if (!link) {
          link = document.createElement('a'); link.className = 'calendar-invoice-plan';
          link.dataset.invoicePlan = plan.id;
        }
        const operation = plan.operation || 'invoice', payment = operation !== 'invoice';
        const amount = payment ? new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(plan.amount / 100) : '';
        const label = operation === 'incoming' ? 'Запланировано получение оплаты' : operation === 'outgoing' ? 'Запланирован платёж' : 'Запланирована выписка счёта';
        link.dataset.operation = operation;
        link.dataset.calendarDate = plan.date;
        link.dataset.calendarPeriod = "day";
        link.classList.toggle("calendar-inactive", plan.is_inactive === true);
        link.setAttribute("aria-haspopup", "menu");
        link.textContent = payment ? (operation === 'incoming' ? '+' : '−') + amount : '✓';
        link.href = '?path=' + encodeURIComponent(plan.path);
        link.dataset.calendarOrder = plan.path;
        const description = [plan.is_inactive === true ? 'Неактуально' : '', label, amount ? link.textContent + ' ₽' : '', plan.title, plan.client, plan.object, fullDate.format(new Date(plan.date + 'T00:00:00Z'))].filter(Boolean).join(' · ');
        link.setAttribute('aria-label', description);
        link.title = description;
        if (link !== before) area.insertBefore(link, before);
        before = link.nextElementSibling; retained.add(link);
      }
      for (const link of existing.values()) if (!retained.has(link)) link.remove();
      area.scrollTop = top;
      if (focused && document.activeElement !== focused) (focused.isConnected ? focused : get('calendarViewport')).focus({ preventScroll: true });
    }
    sizeInvoicePlanHeaders();
  }

  function sizeInvoicePlanHeaders() {
    for (const row of get('calendarWeeks').children) {
      const height = Math.max(32, ...[...row.querySelectorAll('.calendar-invoice-plans')].map((area) => Math.ceil(area.getBoundingClientRect().height) + 8));
      const value = height + 'px';
      if (row.style.getPropertyValue('--calendar-header-height') === value) continue;
      const content = row.querySelector('.calendar-week-content'), top = content.scrollTop;
      row.style.setProperty('--calendar-header-height', value);
      content.scrollTop = top;
    }
  }

  function show(nextOrders, nextEvents, nextInvoicePlans) {
    if (Array.isArray(nextOrders)) orders = nextOrders;
    if (Array.isArray(nextEvents)) events = nextEvents;
    if (Array.isArray(nextInvoicePlans)) invoicePlans = nextInvoicePlans;
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
        const free = document.createElement("div"), freeLabel = document.createElement("span");
        free.className = "calendar-free-events";
        freeLabel.className = "calendar-free-label";
        freeLabel.textContent = "События";
        free.append(freeLabel);
        for (let column = 0; column < 8; column++) {
          const cell = document.createElement("div"), add = document.createElement("button");
          cell.className = "calendar-free-column";
          add.type = "button";
          add.className = "calendar-event-slot calendar-free-add";
          add.dataset.calendarEvent = "";
          add.dataset.calendarFree = "new";
          add.textContent = "+";
          cell.append(add);
          free.append(cell);
        }
        content.append(list, free);
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
          const plans = document.createElement('div');
          plans.className = 'calendar-invoice-plans'; plans.dataset.date = dateKey(date);
          cell.append(plans);
          row.append(cell);
        }
        row.append(content);
        weeks.append(row);
      }
      get("calendarWeeks").replaceChildren(weeks);
      scrollToWeek(range.today);
    } else updateHeading();
    renderWeekOrders();
    renderFreeEvents();
    renderInvoicePlans();
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
      sizeInvoicePlanHeaders();
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

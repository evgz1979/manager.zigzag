/* A bounded calendar with weekly order deadlines. Civil dates use Moscow. */
const HomeCalendar = (() => {
  const DAY = 86400000;
  const VISIBLE_WEEKS = 2;
  // Inline paths survive PNG capture, which omits the page's SVG sprite.
  const orderMarkers = [
    { field: "is_blue_plus", name: "blue-plus", label: "Синий плюс", content: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>' },
    { field: "is_dollar", name: "dollar", label: "Зелёный доллар", content: '$' },
    { field: "is_flagged", name: "flag", label: "Флажок", content: '<svg viewBox="0 0 24 24"><path d="M5 4c5-4 9 4 14 0v10c-5 4-9-4-14 0Z"/><path d="M5 3v18" fill="none"/></svg>' },
    { field: "is_favorite", name: "favorite", label: "Избранное", content: '★' },
  ];
  // Добавляет или снимает значок выезда у события календаря.
  // Использует `element.classList.toggle`, `element.insertAdjacentHTML`.
  function showTripMark(element, marked) {
    element.classList.toggle("calendar-trip", marked);
    if (marked) element.insertAdjacentHTML("afterbegin", '<svg class="calendar-trip-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 10 2-6h10l2 6M5 10h14a2 2 0 0 1 2 2v6H3v-6a2 2 0 0 1 2-2ZM5 18v3M19 18v3M7 14h.01M17 14h.01"/></svg>');
  }
  // Добавляет или снимает значок просмотра задач у события заказа.
  // Использует `element.classList.toggle`, `element.setAttribute`, `element.insertAdjacentHTML`.
  function showTodoMark(element, marked, path) {
    element.classList.toggle("calendar-watch-todos", marked);
    if (marked) {
      element.dataset.calendarTodos = path;
      element.setAttribute("aria-keyshortcuts", "Alt+ArrowDown");
      element.insertAdjacentHTML("afterbegin", '<svg class="calendar-todo-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5h11M9 12h11M9 19h11M3 4l1 1 2-2M3 11l1 1 2-2M3 18l1 1 2-2"/></svg>');
    } else {
      delete element.dataset.calendarTodos;
      element.removeAttribute("aria-keyshortcuts");
    }
  }
  // Формирует ключ гражданской даты YYYY-MM-DD.
  // Использует `date.toISOString().slice`, `date.toISOString`.
  const dateKey = (date) => date.toISOString().slice(0, 10);
  // Сдвигает гражданскую UTC-дату на заданное число суток.
  // Использует `Date`, `date.getTime`.
  const shiftDays = (date, days) => new Date(date.getTime() + days * DAY);
  // Возвращает понедельник недели переданной гражданской даты.
  // Использует `shiftDays`, `date.getUTCDay`.
  const monday = (date) => shiftDays(date, -((date.getUTCDay() + 6) % 7));
  // Вычисляет ISO-номер недели через её четверг.
  // Использует `shiftDays`, `monday`, `Math.ceil`.
  const weekNumber = (date) => {
    const thursday = shiftDays(monday(date), 3);
    return Math.ceil(((thursday - new Date(Date.UTC(thursday.getUTCFullYear(), 0, 1))) / DAY + 1) / 7);
  };
  // Преобразует текущее время в гражданскую дату Москвы.
  // Использует `Intl.DateTimeFormat`, `Date`.
  const moscowDate = (now) => {
    const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now);
    // Извлекает форматированное значение ячейки или части даты.
    // Использует `Number`, `parts.find`.
    const value = (name) => Number(parts.find((part) => part.type === name).value);
    return new Date(Date.UTC(value("year"), value("month") - 1, value("day")));
  };
  // Отбирает дни событий без выполнения и неактуальности.
  // Использует `Object.keys(order.calendar_events || {}).filter`, `Object.keys`.
  const activeOrderDays = (order) => Object.keys(order.calendar_events || {}).filter((day) =>
    !order.calendar_inactive?.day?.includes(day) && !order.calendar_completed?.day?.includes(day));
  // Вычисляет недели строк заказа; просмотр истории возвращает закрытые прошлые записи.
  // Не меняет сроки и отметки; снятые недельные тексты доступны только в прошлой истории.
  function visibleOrderWeeks(order, today, history = false) {
    if (!order.path || order.registered === false) return [];
    const currentWeek = dateKey(monday(today));
    const eventDays = history ? [...new Set([...activeOrderDays(order), ...Object.keys(order.calendar_events || {}).filter(day => day < currentWeek)])] : activeOrderDays(order);
    const eventWeeks = order.calendar_compact === true ? [] : eventDays.map((day) => dateKey(monday(new Date(day + "T00:00:00Z"))));
    const oldWeekly = history && order.calendar_compact !== true ? Object.keys(order.calendar_week_events || {}).filter(week => week < currentWeek) : [];
    const weeks = [...new Set([...(order.deadline_weeks || []), ...eventWeeks, ...oldWeekly])];
    return weeks.filter((week) => {
      if (history || order.calendar_compact === true || week >= currentWeek) return true;
      const end = dateKey(shiftDays(new Date(week + "T00:00:00Z"), 7));
      return [["week", order.calendar_week_events], ["day", order.calendar_events]].some(([period, entries]) => {
        // Unknown event text must remain reachable rather than look like an empty week.
        if (entries === null) return true;
        return Object.entries(entries || {}).some(([key, text]) =>
          (period === "week" ? key === week : key >= week && key < end) && text.trim() &&
          !order.calendar_completed?.[period]?.includes(key) && !order.calendar_inactive?.[period]?.includes(key));
      });
    });
  }
  // Проверяет отсутствие явных отметок выполнения и неактуальности свободной записи/плана.
  // Поддерживает SQLite 0/1 и JSON boolean; неизвестные значения не скрывают запись.
  const pendingRecord = (event) => ![true, 1].includes(event.is_completed) && ![true, 1].includes(event.is_inactive);
  // Выбирает недели календаря; прошлые без открытых событий доступны только в истории.
  // Текущая и будущие недели непрерывны; пустые промежутки прошлого пропускаются.
  function calendarRange(now = new Date(), calendarOrders = [], freeEvents = [], plans = [], history = false) {
    const today = moscowDate(now);
    const current = monday(today), currentKey = dateKey(current), past = new Set();
    let start = current, end = shiftDays(start, VISIBLE_WEEKS * 7 - 1);
    // Добавляет корректную дату или неделю в вычисляемый диапазон.
    // Использует `/^\d{4}-\d{2}-\d{2}$/.test`, `Date`, `Number.isFinite`.
    const include = (key, period = "day") => {
      if (typeof key !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(key)) return;
      const date = new Date(key + "T00:00:00Z");
      if (!Number.isFinite(date.getTime()) || dateKey(date) !== key || (period === "week" && date.getUTCDay() !== 1)) return;
      const week = monday(date), last = shiftDays(week, 6);
      if (week < current) { past.add(dateKey(week)); if (week < start) start = week; }
      if (last > end) end = last;
    };
    for (const order of calendarOrders) {
      if (!order.path || order.registered === false) continue;
      for (const week of visibleOrderWeeks(order, today, history)) {
        if (history || week >= currentKey || order.calendar_compact !== true) include(week, "week");
      }
    }
    for (const event of [...freeEvents, ...plans]) {
      if (!event.deleted && ["day", "week"].includes(event.period || "day") &&
          (history || event.date >= currentKey || pendingRecord(event))) include(event.date, event.period);
    }
    const weeks = history ? [] : [...past].sort();
    for (let week = history ? start : current; week <= end; week = shiftDays(week, 7)) weeks.push(dateKey(week));
    return { today, from: start, through: end, start, end, weeks };
  }

  let range, builtFor = "", initialized = false, frame = 0, weekTops = [], weekHeights = [], orders = [], events = [], invoicePlans = [];
  let scrollAnchor = { index: 0, offset: 0 };
  let layoutHidden = false;
  let showHistory = false;
  // Находит элемент интерфейса по устойчивому DOM-идентификатору.
  // Обращается к DOM текущего документа или переданного контейнера.
  const get = (id) => document.getElementById(id);
  const monthName = new Intl.DateTimeFormat("ru-RU", { month: "long", timeZone: "UTC" });
  const fullDate = new Intl.DateTimeFormat("ru-RU", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  // Вычисляет максимальную прокрутку календарного контейнера.
  // Использует `Math.max`, `Math.min`, `get`.
  const maxScroll = () => Math.max(0, Math.min(get("calendarViewport").scrollHeight - get("calendarViewport").clientHeight,
    weekTops[Math.max(0, weekTops.length - VISIBLE_WEEKS)] || 0));

  // Измеряет текущие высоты недель и их положения.
  // Использует `[...get("calendarWeeks").children].map`, `get`, `weekHeights.map`.
  function measureWeeks() {
    weekHeights = [...get("calendarWeeks").children].map((row) => row.getBoundingClientRect().height);
    let top = 0;
    weekTops = weekHeights.map((height) => { const value = top; top += height; return value; });
  }

  // Находит неделю, соответствующую текущей позиции прокрутки.
  // Использует `Math.min`, `Math.max`.
  function weekIndex(top) {
    let index = 0;
    while (index + 1 < weekTops.length && weekTops[index + 1] <= top + 1) index++;
    return Math.min(index, Math.max(0, weekTops.length - VISIBLE_WEEKS));
  }

  // Подгоняет высоту окна календаря под две полные недели.
  // Использует `weekHeights.slice(index, index + VISIBLE_WEEKS).reduce`, `weekHeights.slice`, `get`.
  function fitViewport(index) {
    const height = weekHeights.slice(index, index + VISIBLE_WEEKS).reduce((sum, value) => sum + value, 0);
    const viewport = get("calendarViewport"), weeks = get("calendarWeeks");
    // Keep the last pair reachable when the current pair is taller than it.
    const lastHeight = weekHeights.slice(-VISIBLE_WEEKS).reduce((sum, value) => sum + value, 0);
    const padding = Math.max(0, height - lastHeight) + "px";
    if (height > viewport.clientHeight) weeks.style.paddingBottom = padding;
    const value = Math.round(height * 1000) / 1000 + "px";
    if (height && viewport.style.height !== value) viewport.style.height = value;
    weeks.style.paddingBottom = padding;
  }

  // Прокручивает календарь к началу выбранной недели.
  // Использует `Math.max`, `Math.min`, `fitViewport`.
  function scrollToIndex(index) {
    index = Math.max(0, Math.min(index, weekTops.length - VISIBLE_WEEKS));
    fitViewport(index);
    get("calendarViewport").scrollTo({ top: Math.min(maxScroll(), weekTops[index] || 0), behavior: "auto" });
    updateHeading();
  }

  // Обновляет заголовок и доступность навигации календаря.
  // Использует `get`, `[...get("calendarWeeks").children].some`, `maxScroll`.
  function updateHeading() {
    frame = 0;
    const viewport = get("calendarViewport");
    if (!viewport.clientWidth) { layoutHidden = true; return; }
    if (!weekHeights.length) return;
    // ResizeObserver restores the same week after content or window size changes.
    if ([...get("calendarWeeks").children].some((row, i) => Math.abs(row.getBoundingClientRect().height - weekHeights[i]) > .1)) return;
    if (viewport.scrollTop > maxScroll() + 1) viewport.scrollTop = maxScroll();
    const index = weekIndex(viewport.scrollTop);
    fitViewport(index);
    scrollAnchor = { index, offset: viewport.scrollTop - (weekTops[index] || 0) };
    const first = new Date(range.weeks[index] + "T00:00:00Z"), last = shiftDays(new Date(range.weeks[Math.min(index + VISIBLE_WEEKS - 1, range.weeks.length - 1)] + "T00:00:00Z"), 6);
    viewport.setAttribute("aria-label", "Две недели календаря: " + fullDate.format(first) + " — " + fullDate.format(last) + " Прокручивай вверх и вниз; Home — начало, End — конец.");
    const sameMonth = first.getUTCMonth() === last.getUTCMonth() && first.getUTCFullYear() === last.getUTCFullYear();
    get("calendarTitle").textContent = sameMonth ? monthName.format(first) + " " + first.getUTCFullYear() :
      monthName.format(first) + (first.getUTCFullYear() !== last.getUTCFullYear() ? " " + first.getUTCFullYear() : "") + " — " + monthName.format(last) + " " + last.getUTCFullYear();
    get("calendarEarlier").disabled = viewport.scrollTop < 1;
    get("calendarLater").disabled = viewport.scrollTop >= maxScroll() - 1;
  }

  // Показывает заданную неделю или ближайшую следующую сохранившуюся неделю.
  // Поиск по ключам поддерживает пропущенные закрытые недели прошлого.
  function scrollToWeek(date) {
    const key = dateKey(monday(date)), index = range.weeks.findIndex(week => week >= key);
    scrollToIndex(index < 0 ? range.weeks.length - VISIBLE_WEEKS : index);
  }

  // Собирает обычные заказы под заголовками клиентов, поставщиков оставляет отдельными строками.
  // Различает точные пути клиентов и сохраняет порядок заказов источника внутри группы.
  function orderGroups(source) {
    const groups = new Map();
    for (const order of source) {
      const supplier = Boolean(order.work_supplier);
      const label = supplier ? order.work_supplier : order.client || "Без клиента";
      const identity = order.client_path || order.client || "";
      const key = supplier ? JSON.stringify(["supplier", order.id, order.path]) : JSON.stringify(["client", identity.normalize("NFC")]);
      if (!groups.has(key)) groups.set(key, { key, label, supplier, orders: [] });
      groups.get(key).orders.push(order);
    }
    return [...groups.values()];
  }

  // Обновляет отдельную строку заголовка клиентской группы календаря.
  // Название выводится безопасным текстом; поставщикам заголовки не создаются.
  function updateGroupHeading(heading, group) {
    heading.className = "calendar-order-group";
    heading.dataset.groupKey = group.key;
    if (!heading.firstElementChild) {
      const label = document.createElement("span");
      label.setAttribute("role", "heading");
      label.setAttribute("aria-level", "3");
      heading.append(label);
    }
    heading.firstElementChild.textContent = group.label;
    heading.firstElementChild.title = group.label;
  }

  // Строит заголовки клиентов обычных заказов и отдельные строки поставщиков.
  // Переиспользует узлы строк и групп, сохраняя фокус, прокрутку и привязку событий.
  function renderWeekOrders() {
    const byWeek = new Map();
    for (const order of orders) {
      for (const week of visibleOrderWeeks(order, range.today, showHistory)) {
        if (!byWeek.has(week)) byWeek.set(week, []);
        byWeek.get(week).push(order);
      }
    }
    for (const row of get("calendarWeeks").children) {
      const list = row.querySelector(".calendar-orders-list"), eligible = byWeek.get(row.dataset.week) || [];
      const compact = eligible.filter(order => order.calendar_compact === true);
      renderCompactOrders(row.querySelector(".calendar-compact-orders"), compact);
      const weekly = eligible.filter(order => order.calendar_compact !== true);
      const signature = compact.length + ":" + JSON.stringify(weekly.map((order) => [order.id, order.path, order.title, order.client, order.client_path, order.object, order.is_blue_plus, order.is_dollar, order.is_flagged, order.is_favorite, order.work_supplier, order.work_supplier_color, order.deadline_weeks, order.calendar_events, order.calendar_week_events, order.calendar_inactive, order.calendar_completed, order.calendar_trip, order.calendar_watch_todos, order.calendar_colors]));
      if (list.dataset.signature === signature) continue;
      list.dataset.signature = signature;
      const top = list.parentElement.scrollTop;
      const focused = list.contains(document.activeElement) ? document.activeElement : null;
      const existing = new Map([...list.children].map((item) => [item.dataset.orderKey, item]));
      const headings = new Map([...list.querySelectorAll(".calendar-order-group")].map(item => [item.dataset.groupKey, item]));
      const retained = new Set();
      let before = list.firstElementChild;
      for (const group of orderGroups(weekly)) {
        if (!group.supplier) {
          const heading = headings.get(group.key) || document.createElement("li");
          updateGroupHeading(heading, group);
          if (heading !== before) list.insertBefore(heading, before);
          before = heading.nextElementSibling;
          retained.add(heading);
        }
        for (const order of group.orders) {
          const supplier = Boolean(order.work_supplier), color = order.work_supplier_color;
          const key = JSON.stringify([order.id, order.path]);
          let item = existing.get(key);
          if (!item) {
            item = document.createElement("li");
            item.dataset.orderKey = key;
            item.className = "calendar-order-row";
            const link = document.createElement("a"), markers = document.createElement("span"), client = document.createElement("small"), title = document.createElement("span"), object = document.createElement("small");
            link.className = "calendar-order-link";
            markers.className = "calendar-order-markers";
            markers.setAttribute("aria-hidden", "true");
            markers.innerHTML = orderMarkers.map((marker) => '<span class="calendar-order-marker calendar-order-' + marker.name + '">' + marker.content + '</span>').join("");
            title.className = "calendar-order-title";
            client.className = "calendar-order-client";
            object.className = "calendar-order-object";
            link.append(markers, client, title, object);
            item.append(link);
            for (let day = -1; day < 7; day++) {
              const slot = document.createElement("button");
              slot.type = "button";
              slot.className = "calendar-event-slot";
              item.append(slot);
            }
          }
          item.classList.toggle("calendar-supplier-order", supplier);
          item.dataset.groupKey = group.key;
          item.classList.toggle("supplier-neutral", supplier && Boolean(color?.neutral));
          if (supplier) item.style.setProperty("--supplier-hue", String(color?.hue ?? 0));
          else item.style.removeProperty("--supplier-hue");
          const link = item.firstElementChild, title = order.title || order.path;
          const activeMarkers = orderMarkers.filter((marker) => order[marker.field] === true);
          const markers = link.firstElementChild;
          orderMarkers.forEach((marker, index) => { markers.children[index].hidden = order[marker.field] !== true; });
          markers.hidden = !activeMarkers.length;
          link.href = "?path=" + encodeURIComponent(order.path);
          link.dataset.calendarOrder = order.path;
          link.setAttribute("aria-label", [group.label, title, order.object, ...activeMarkers.map((marker) => marker.label)].filter(Boolean).join(" · "));
          link.querySelector(".calendar-order-title").textContent = title;
          const client = link.querySelector(".calendar-order-client");
          client.textContent = order.work_supplier || "";
          client.hidden = !supplier;
          const object = link.querySelector(".calendar-order-object");
          object.textContent = supplier ? "" : order.object || "";
          object.hidden = supplier || !order.object;
          for (let day = -1; day < 7; day++) {
            const week = new Date(row.dataset.week + "T00:00:00Z"), isWeek = day === -1;
            const date = shiftDays(week, isWeek ? 0 : day), key = dateKey(date);
            const entries = isWeek ? order.calendar_week_events : order.calendar_events;
            const slot = item.children[day + 2], text = entries?.[key] || "";
            slot.dataset.calendarEvent = order.path;
            slot.dataset.calendarDate = key;
            slot.dataset.calendarPeriod = isWeek ? "week" : "day";
            const eventColor = !supplier && text && order.calendar_colors?.[isWeek ? "week" : "day"]?.[key];
            if (eventColor) slot.dataset.calendarColor = eventColor;
            else delete slot.dataset.calendarColor;
            slot.classList.toggle("calendar-week-event-slot", isWeek);
            slot.textContent = text;
            showTripMark(slot, Boolean(text) && Boolean(order.calendar_trip?.[isWeek ? "week" : "day"]?.includes(key)));
            showTodoMark(slot, Boolean(text) && Boolean(order.calendar_watch_todos?.[isWeek ? "week" : "day"]?.includes(key)), order.path);
            slot.classList.toggle("calendar-inactive", Boolean(text) && Boolean(order.calendar_inactive?.[isWeek ? "week" : "day"]?.includes(key)));
            slot.classList.toggle("calendar-completed", Boolean(text) && Boolean(order.calendar_completed?.[isWeek ? "week" : "day"]?.includes(key)));
            const unselectedWeek = isWeek && Boolean(text) && Array.isArray(order.deadline_weeks) && !order.deadline_weeks.includes(key);
            slot.classList.toggle("calendar-unselected-week", unselectedWeek);
            slot.classList.toggle("has-event", Boolean(text));
            if (text) slot.setAttribute("aria-haspopup", "menu");
            else slot.removeAttribute("aria-haspopup");
            slot.disabled = entries === null || (isWeek ? shiftDays(week, 6) < range.from || week > range.through : date < range.from || date > range.through);
            const periodLabel = isWeek ? "Неделя " + weekNumber(week) + ": " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)) : fullDate.format(date);
            slot.setAttribute("aria-label", (slot.classList.contains("calendar-watch-todos") ? "Смотри ту-ду · " : "") + (slot.classList.contains("calendar-completed") ? "Выполнено · " : "") + (slot.classList.contains("calendar-trip") ? "Выезд · " : "") + (slot.classList.contains("calendar-inactive") ? "Неактуально · " : "") + (unselectedWeek ? "Отметка недели снята · " : "") + (text ? "Изменить событие: " + text : "Добавить событие") + " · " + title + " · " + periodLabel);
          }
          if (item !== before) list.insertBefore(item, before);
          before = item.nextElementSibling;
          retained.add(item);
        }
      }
      for (const item of [...list.children]) if (!retained.has(item)) item.remove();
      if (!weekly.length && !compact.length) {
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

  // Строит прежний плоский список синих ссылок мелких заказов без заголовков клиентов.
  // Сохраняет подписи, нижнюю левую область, узлы ссылок и фокус без показа скрытых событий.
  function renderCompactOrders(container, compact) {
    const focused = container.contains(document.activeElement) ? document.activeElement : null;
    const existing = new Map([...container.children].map(link => [link.dataset.calendarOrder, link]));
    const retained = new Set();
    let before = container.firstElementChild;
    for (const order of compact) {
      let link = existing.get(order.path);
      if (!link) { link = document.createElement("a"); link.className = "calendar-order-link calendar-compact-order"; }
      link.href = "?path=" + encodeURIComponent(order.path);
      link.dataset.calendarOrder = order.path;
      const title = order.title || order.path;
      const label = order.work_supplier ? order.work_supplier + " · " + title : title + (order.client ? " · " + order.client : "");
      link.textContent = label;
      link.setAttribute("aria-label", "Мелкий заказ · " + label + (order.object ? " · " + order.object : ""));
      if (link !== before) container.insertBefore(link, before);
      before = link.nextElementSibling; retained.add(link);
    }
    for (const link of [...container.children]) if (!retained.has(link)) link.remove();
    if (focused && document.activeElement !== focused) {
      (focused.isConnected ? focused : get("calendarViewport")).focus({ preventScroll: true });
    }
  }

  // Строит свободные события с отдельным значком непустого комментария.
  // Значок и UUID открывают общее окно просмотра; название, узлы и фокус сохраняются.
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
          showTripMark(button, event.is_trip === 1);
          button.removeAttribute("title");
          button.removeAttribute("aria-description");
          const hasComment = typeof event.comment === "string" && Boolean(event.comment.trim());
          button.classList.toggle("calendar-has-comment", hasComment);
          if (hasComment) {
            button.dataset.calendarComment = event.id;
            button.setAttribute("aria-keyshortcuts", "Alt+ArrowDown");
            button.insertAdjacentHTML("afterbegin", '<svg class="calendar-comment-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15a3 3 0 0 1-3 3H8l-5 4V6a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3Z"/><path d="M7 8h10M7 12h7"/></svg>');
          } else {
            delete button.dataset.calendarComment;
            button.removeAttribute("aria-keyshortcuts");
          }
          button.dataset.calendarColor = event.color || "gray";
          button.classList.toggle("calendar-inactive", event.is_inactive === 1);
          button.classList.toggle("calendar-completed", event.is_completed === 1);
          button.dataset.calendarDate = key;
          button.dataset.calendarPeriod = period;
          button.disabled = event.version !== 1 || (event.comment !== undefined && typeof event.comment !== "string") || ![0, 1].includes(event.is_inactive) || ![0, 1].includes(event.is_completed ?? 0) || ![0, 1].includes(event.is_trip ?? 0) || !["gray", "red", "orange", "yellow", "green", "blue", "purple"].includes(event.color) || add.disabled;
          button.setAttribute("aria-label", (hasComment ? "Есть комментарий · " : "") + (button.classList.contains("calendar-completed") ? "Выполнено · " : "") + (button.classList.contains("calendar-trip") ? "Выезд · " : "") + (button.classList.contains("calendar-inactive") ? "Неактуально · " : "") + "Изменить событие без заказа: " + event.text + " · " + label);
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

  // Строит приходы и расходы календаря с сохранёнными отметками.
  // Обращается к DOM текущего документа или переданного контейнера.
  function renderInvoicePlans() {
    const byDate = new Map();
    for (const plan of invoicePlans) {
      const key = plan.is_carryover === true && ['incoming', 'outgoing'].includes(plan.operation) ?
        'carryover:' + dateKey(monday(new Date(plan.date + 'T00:00:00Z'))) : (plan.period || 'day') + ':' + plan.date;
      if (!byDate.has(key)) byDate.set(key, []);
      byDate.get(key).push(plan);
    }
    for (const area of get("calendarWeeks").querySelectorAll('.calendar-invoice-plans')) {
      const plans = byDate.get(area.dataset.period + ':' + area.dataset.date) || [];
      const signature = JSON.stringify(plans);
      if (area.dataset.signature === signature) continue;
      area.dataset.signature = signature;
      const focused = area.contains(document.activeElement) ? document.activeElement : null;
      const existing = new Map([...area.querySelectorAll('.calendar-invoice-plan')].map((link) => [link.dataset.invoicePlan, link]));
      const targets = { incoming: area.querySelector('[data-plan-column="incoming"]'), outgoing: area.querySelector('[data-plan-column="outgoing"]') };
      const before = new Map(Object.values(targets).map((target) => [target, target.firstElementChild]));
      const retained = new Set();
      for (const plan of plans) {
        let link = existing.get(plan.id);
        if (!link) {
          link = document.createElement(plan.path ? 'a' : 'button'); link.className = 'calendar-invoice-plan';
          if (!plan.path) link.type = 'button';
          link.dataset.invoicePlan = plan.id;
        }
        const operation = plan.operation || 'invoice', payment = operation !== 'invoice';
        const amount = payment ? new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(plan.amount / 100) : '';
        const label = operation === 'incoming' ? 'Запланировано получение оплаты' : operation === 'outgoing' ? 'Запланирован платёж' : 'Запланирована выписка счёта';
        link.dataset.operation = operation;
        link.dataset.calendarDate = plan.date;
        link.dataset.calendarPeriod = plan.period || 'day';
        link.classList.toggle("calendar-inactive", plan.is_inactive === true);
        link.classList.toggle("calendar-completed", plan.is_completed === true);
        link.classList.toggle("calendar-notified", payment && plan.is_notified === true);
        link.setAttribute("aria-haspopup", "menu");
        const signedAmount = payment ? (operation === 'incoming' ? '+' : '−') + amount : '';
        const value = document.createElement('span'), caption = document.createElement('span');
        value.className = 'calendar-plan-amount'; value.textContent = payment ? signedAmount : '+ ****';
        caption.className = 'calendar-plan-caption';
        caption.textContent = plan.path ? plan.title : plan.text || (operation === 'incoming' ? 'поступление' : 'затрата');
        link.replaceChildren(value, caption);
        showTripMark(link, plan.is_trip === true);
        showTodoMark(link, Boolean(plan.path) && plan.is_watch_todos === true, plan.path);
        if (plan.path) {
          link.href = '?path=' + encodeURIComponent(plan.path);
          link.dataset.calendarOrder = plan.path;
        } else link.dataset.calendarPlanEdit = plan.id;
        const start = new Date(plan.date + 'T00:00:00Z');
        const periodLabel = plan.period === 'week' ? 'Неделя: ' + fullDate.format(start) + ' — ' + fullDate.format(shiftDays(start, 6)) : fullDate.format(start);
        const description = [payment && plan.is_notified === true ? 'Сообщил' : '', plan.is_carryover === true ? 'Перенос слева' : '', plan.is_watch_todos === true ? 'Смотри ту-ду' : '', plan.is_completed === true ? 'Выполнено' : '', plan.is_trip === true ? 'Выезд' : '', plan.is_inactive === true ? 'Неактуально' : '', label, signedAmount ? signedAmount + ' ₽' : '', plan.text, plan.invoice_label, plan.title, plan.client, plan.object, periodLabel].filter(Boolean).join(' · ');
        link.setAttribute('aria-label', description);
        link.title = plan.path ? description : plan.text || '';
        const target = operation === 'outgoing' ? targets.outgoing : targets.incoming, next = before.get(target);
        if (link !== next) target.insertBefore(link, next);
        before.set(target, link.nextElementSibling); retained.add(link);
      }
      for (const link of existing.values()) if (!retained.has(link)) link.remove();
      if (focused && document.activeElement !== focused) (focused.isConnected ? focused : get('calendarViewport')).focus({ preventScroll: true });
    }
    sizeInvoicePlanHeaders();
  }

  // Выравнивает высоту шапки оплат по наполнению недель.
  // Обращается к DOM текущего документа или переданного контейнера.
  function sizeInvoicePlanHeaders() {
    const viewport = get('calendarViewport');
    if (!viewport.clientWidth) { layoutHidden = true; return; }
    if (!get('calendarWeeks').children.length) return;
    const wasHidden = layoutHidden;
    layoutHidden = false;
    const resized = wasHidden || (weekHeights.length && [...get('calendarWeeks').children].some((row, i) => Math.abs(row.getBoundingClientRect().height - weekHeights[i]) > .1));
    const index = resized ? scrollAnchor.index : weekIndex(viewport.scrollTop);
    const offset = resized ? scrollAnchor.offset : viewport.scrollTop - (weekTops[index] || 0);
    const previousHeights = weekHeights;
    for (const amount of get('calendarWeeks').querySelectorAll('.calendar-plan-amount')) {
      amount.style.fontSize = '';
      const available = amount.parentElement.clientWidth;
      if (available && amount.scrollWidth > available) amount.style.fontSize = (parseFloat(getComputedStyle(amount).fontSize) * available / amount.scrollWidth * .97) + 'px';
    }
    for (const row of get('calendarWeeks').children) {
      const height = Math.max(46, ...[...row.querySelectorAll('.calendar-invoice-plans')].map((area) => Math.ceil(area.getBoundingClientRect().height) + 8));
      const value = height + 'px';
      if (row.style.getPropertyValue('--calendar-header-height') === value) continue;
      const content = row.querySelector('.calendar-week-content'), top = content.scrollTop;
      row.style.setProperty('--calendar-header-height', value);
      row.style.setProperty('--calendar-header-extra', (height - 32) + 'px');
      content.scrollTop = top;
    }
    measureWeeks();
    if (wasHidden || previousHeights.length !== weekHeights.length || weekHeights.some((height, i) => Math.abs(height - previousHeights[i]) > .1)) {
      fitViewport(index);
      viewport.scrollTop = Math.min(maxScroll(), Math.max(0, (weekTops[index] || 0) + offset));
    }
    updateHeading();
  }

  // Строит область планов или ручных переносов платежей.
  // Использует `document.createElement`, `fullDate.format`, `shiftDays`.
  function planHeader(date, label, period = 'day') {
    const controls = document.createElement('div');
    controls.className = 'calendar-payment-add';
    const periodLabel = period === 'week' ? 'Неделя: ' + fullDate.format(date) + ' — ' + fullDate.format(shiftDays(date, 6)) : fullDate.format(date);
    for (const operation of ['incoming', 'outgoing']) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = operation === 'incoming' ? '+' : '−';
      button.dataset.calendarPaymentAdd = operation;
      button.dataset.calendarDate = dateKey(date);
      button.dataset.calendarPeriod = period;
      button.disabled = (period === 'week' ? shiftDays(date, 6) : date) < range.from || date > range.through;
      button.setAttribute('aria-label', (operation === 'incoming' ? 'Запланировать получение оплаты' : 'Запланировать платёж') + ' · ' + periodLabel);
      controls.append(button);
    }
    const plans = document.createElement('div');
    plans.className = 'calendar-invoice-plans'; plans.dataset.date = dateKey(date); plans.dataset.period = period;
    const payments = document.createElement('div'); payments.className = 'calendar-payment-columns';
    for (const operation of ['incoming', 'outgoing']) {
      const column = document.createElement('div'); column.className = 'calendar-plan-column';
      column.dataset.planColumn = operation; payments.append(column);
    }
    const rail = document.createElement('div');
    rail.className = 'calendar-date-rail';
    rail.append(controls, label); plans.append(payments, rail);
    return plans;
  }

  // Строит область планов или ручных переносов платежей.
  // Использует `document.createElement`, `dateKey`, `area.setAttribute`.
  function carryoverHeader(week) {
    const area = document.createElement("div"), payments = document.createElement("div");
    area.className = "calendar-invoice-plans calendar-carryover-plans";
    area.dataset.period = "carryover"; area.dataset.date = dateKey(week);
    area.setAttribute("role", "group");
    area.setAttribute("aria-label", "Переносы доходов и расходов · неделя с " + fullDate.format(week));
    payments.className = "calendar-payment-columns";
    for (const operation of ["incoming", "outgoing"]) {
      const column = document.createElement("div"); column.className = "calendar-plan-column";
      column.dataset.planColumn = operation; payments.append(column);
    }
    area.append(payments); return area;
  }

  // Показывает компонент по полученным данным и текущему состоянию в модуле календарной сетки.
  // Подключает обработчики событий к существующим элементам компонента.
  function show(nextOrders, nextEvents, nextInvoicePlans, now = new Date()) {
    if (Array.isArray(nextOrders)) orders = nextOrders;
    if (Array.isArray(nextEvents)) events = nextEvents;
    if (Array.isArray(nextInvoicePlans)) invoicePlans = nextInvoicePlans;
    const nextRange = calendarRange(now, orders, events, invoicePlans, showHistory);
    if (builtFor !== dateKey(nextRange.today) || !range || range.weeks.join() !== nextRange.weeks.join()) {
      const viewport = get("calendarViewport"), index = weekIndex(viewport.scrollTop);
      const visibleWeek = range ? new Date(range.weeks[index] + "T00:00:00Z") : nextRange.today;
      const offset = range ? viewport.scrollTop - (weekTops[index] || 0) : 0;
      range = nextRange;
      builtFor = dateKey(range.today);
      const weeks = get("calendarWeeks"), existing = new Map([...weeks.children].map((row) => [row.dataset.week, row]));
      const focused = weeks.contains(document.activeElement) ? document.activeElement : null;
      const retained = new Set(range.weeks);
      for (const [key, row] of existing) if (!retained.has(key)) row.remove();
      let before = weeks.firstElementChild;
      for (const key of range.weeks) {
        const week = new Date(key + "T00:00:00Z");
        let row = existing.get(key);
        if (!row) {
          row = document.createElement("div");
          row.className = "calendar-week";
          row.dataset.week = dateKey(week);
          const orderCell = document.createElement("div"), content = document.createElement("div"), list = document.createElement("ul");
          orderCell.className = "calendar-day calendar-orders-cell";
          orderCell.style.gridArea = "1 / 1";
          orderCell.append(carryoverHeader(week));
          content.className = "calendar-week-content";
          list.className = "calendar-orders-list";
          list.setAttribute("aria-label", "Заказы на неделю: " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)));
          const free = document.createElement("div"), spacer = document.createElement("div");
          free.className = "calendar-free-events";
          spacer.className = "calendar-compact-orders";
          spacer.setAttribute("role", "group");
          spacer.setAttribute("aria-label", "Мелкие заказы · неделя с " + fullDate.format(week));
          free.append(spacer);
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
          weekCell.style.gridArea = "1 / 2";
          weekLabel.className = "calendar-week-number";
          weekLabel.textContent = weekNumber(week);
          weekLabel.setAttribute("aria-label", "Неделя " + weekNumber(week) + ": " + fullDate.format(week) + " — " + fullDate.format(shiftDays(week, 6)));
          weekCell.append(planHeader(week, weekLabel, 'week'));
          row.append(weekCell);
          for (let day = 0; day < 7; day++) {
            const date = shiftDays(week, day), cell = document.createElement("div"), label = document.createElement("time");
            cell.className = "calendar-day" + (day > 4 ? " weekend" : "") + (date < range.from || date > range.through ? " calendar-outside" : "");
            cell.style.gridArea = "1 / " + (day + 3);
            label.dateTime = dateKey(date);
            label.setAttribute("aria-label", fullDate.format(date));
            label.textContent = String(date.getUTCDate());
            cell.append(planHeader(date, label));
            row.append(cell);
          }
          row.append(content);
        }
        for (const label of row.querySelectorAll("time")) {
          label.classList.toggle("calendar-today", label.dateTime === builtFor);
          if (label.dateTime === builtFor) label.setAttribute("aria-current", "date");
          else label.removeAttribute("aria-current");
        }
        if (row !== before) weeks.insertBefore(row, before);
        before = row.nextElementSibling;
      }
      if (focused && !focused.isConnected) viewport.focus({ preventScroll: true });
      measureWeeks();
      scrollToWeek(visibleWeek);
      viewport.scrollTop = Math.max(0, Math.min(maxScroll(), viewport.scrollTop + offset));
      updateHeading();
    } else updateHeading();
    renderWeekOrders();
    renderFreeEvents();
    renderInvoicePlans();
    if (initialized) return;
    initialized = true;
    const viewport = get("calendarViewport");
    get("calendarToday").addEventListener("click", () => { show(); scrollToWeek(range.today); });
    get("calendarEarlier").addEventListener("click", () => { scrollToIndex(weekIndex(viewport.scrollTop) - 1); });
    get("calendarLater").addEventListener("click", () => { scrollToIndex(weekIndex(viewport.scrollTop) + 1); });
    const history = get("calendarHistory");
    if (history) history.addEventListener("change", () => {
      showHistory = history.checked;
      history.parentElement.title = showHistory ? "Скрыть прошедшие недели без актуальных невыполненных событий" : "Показать старые недели, включая выполненные и неактуальные записи";
      show();
    });
    viewport.addEventListener("scroll", () => { if (!frame) frame = requestAnimationFrame(updateHeading); }, { passive: true });
    viewport.addEventListener("keydown", (event) => {
      if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        scrollToIndex(event.key === "Home" ? 0 : weekTops.length - VISIBLE_WEEKS);
      }
    });
    // Keep the same week visible when the window changes height.
    const observer = new ResizeObserver(sizeInvoicePlanHeaders);
    observer.observe(get("calendarWeeks"));
  }
  // Выбирает две или три недели снимка независимо от просмотра истории.
  // Предыдущую неделю удерживает только видимое актуальное невыполненное событие.
  function snapshotRange(now = new Date(), calendarOrders = orders, freeEvents = events, plans = invoicePlans) {
    const today = moscowDate(now), current = monday(today), previous = dateKey(shiftDays(current, -7));
    const hasPrevious = calendarOrders.some(order => order.calendar_compact !== true && visibleOrderWeeks(order, today).includes(previous)) ||
      [...freeEvents, ...plans].some(event => !event.deleted && pendingRecord(event) && event.date >= previous && event.date < dateKey(current));
    const start = hasPrevious ? shiftDays(current, -7) : current, end = shiftDays(current, 13);
    return { start, end, count: hasPrevious ? 3 : 2 };
  }
  // Создаёт отдельный DOM календаря для рендера общего PNG.
  // Исключает строки прошлой истории и их пустые заголовки, сохраняя группировку и подписи.
  function createSnapshot(now = new Date()) {
    const { start, end, count } = snapshotRange(now);
    const snapshot = document.createElement("section");
    snapshot.className = "home-calendar calendar-snapshot";
    snapshot.setAttribute("aria-hidden", "true");
    snapshot.inert = true;
    const title = document.createElement("h2");
    title.textContent = "Зигзаг · " + fullDate.format(start) + " — " + fullDate.format(end);
    snapshot.append(title, get("homeCalendar").querySelector(".calendar-weekdays").cloneNode(true));
    for (let index = 0; index < count; index++) {
      const key = dateKey(shiftDays(start, index * 7));
      const row = [...get("calendarWeeks").children].find((item) => item.dataset.week === key);
      if (!row) throw new Error("Обнови календарь перед отправкой нужных недель");
      const clone = row.cloneNode(true);
      const visible = new Set(orders.filter(order => visibleOrderWeeks(order, moscowDate(now)).includes(key)).map(order => JSON.stringify([order.id, order.path])));
      for (const item of clone.querySelectorAll(".calendar-order-row")) if (!visible.has(item.dataset.orderKey)) item.remove();
      for (const heading of clone.querySelectorAll(".calendar-orders-list > .calendar-order-group")) {
        if (heading.nextElementSibling?.dataset.groupKey !== heading.dataset.groupKey) heading.remove();
      }
      snapshot.append(clone);
    }
    for (const element of snapshot.querySelectorAll("[id]")) element.removeAttribute("id");
    return { element: snapshot, start: dateKey(start), through: dateKey(end) };
  }
  return { show, calendarRange, createSnapshot, snapshotRange };
})();

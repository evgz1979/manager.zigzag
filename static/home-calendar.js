/* A bounded, empty calendar scaffold. Civil dates are calculated in Moscow. */
const HomeCalendar = (() => {
  const DAY = 86400000;
  const dateKey = (date) => date.toISOString().slice(0, 10);
  const shiftDays = (date, days) => new Date(date.getTime() + days * DAY);
  const monday = (date) => shiftDays(date, -((date.getUTCDay() + 6) % 7));
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

  let range, builtFor = "", initialized = false, frame = 0, rowPixels = 0, visibleWeek = 0;
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

  function show() {
    const nextRange = calendarRange();
    if (builtFor !== dateKey(nextRange.today)) {
      range = nextRange;
      builtFor = dateKey(range.today);
      const weeks = document.createDocumentFragment();
      for (let week = range.start; week <= range.end; week = shiftDays(week, 7)) {
        const row = document.createElement("div");
        row.className = "calendar-week";
        for (let day = 0; day < 7; day++) {
          const date = shiftDays(week, day), cell = document.createElement("div"), label = document.createElement("time");
          cell.className = "calendar-day" + (day > 4 ? " weekend" : "") + (date < range.from || date > range.through ? " calendar-outside" : "");
          label.dateTime = dateKey(date);
          label.title = fullDate.format(date);
          label.setAttribute("aria-label", fullDate.format(date));
          label.textContent = date.getUTCDate() === 1 ? shortDate.format(date) : String(date.getUTCDate());
          if (dateKey(date) === builtFor) { label.className = "calendar-today"; label.setAttribute("aria-current", "date"); }
          cell.append(label);
          row.append(cell);
        }
        weeks.append(row);
      }
      get("calendarWeeks").replaceChildren(weeks);
      get("calendarViewport").title = "Доступно: " + fullDate.format(range.from) + " — " + fullDate.format(range.through);
      scrollToWeek(range.today);
    } else updateHeading();
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

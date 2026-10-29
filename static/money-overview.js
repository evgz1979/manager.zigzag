const MoneyOverview = (() => {
  const COUNT = 4;
  const money = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 });
  const monthName = new Intl.DateTimeFormat("ru-RU", { month: "long", year: "numeric", timeZone: "UTC" });
  const shortDate = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", timeZone: "UTC" });
  const compactDate = new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "2-digit", timeZone: "UTC" });
  const escape = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  const key = (date) => date.toISOString().slice(0, 7);
  const shift = (month, offset) => new Date(Date.UTC(Number(month.slice(0, 4)), Number(month.slice(5, 7)) - 1 + offset, 1));
  const currentMonth = () => new Intl.DateTimeFormat("sv-SE", { year: "numeric", month: "2-digit", timeZone: "Europe/Moscow" }).format(new Date());
  let offset = 0, plans = [], initialized = false, rendered = "";

  function months(records, firstMonth) {
    const result = Array.from({ length: COUNT }, (_, index) => ({
      key: key(shift(firstMonth, index)), incoming: [], outgoing: [], income: 0, expense: 0,
    }));
    const byMonth = new Map(result.map((month) => [month.key, month]));
    for (const plan of records) {
      if (!["incoming", "outgoing"].includes(plan.operation) || !Number.isSafeInteger(plan.amount) || plan.amount <= 0 ||
          (plan.is_inactive === undefined ? false : plan.is_inactive) !== false ||
          (plan.is_completed === undefined ? false : plan.is_completed) !== false) continue;
      // Weekly plans belong wholly to the month of their calendar Monday.
      const month = byMonth.get(plan.date?.slice(0, 7));
      if (!month) continue;
      month[plan.operation].push(plan);
      month[plan.operation === "incoming" ? "income" : "expense"] += plan.amount;
    }
    for (const month of result) {
      for (const direction of ["incoming", "outgoing"]) month[direction].sort((a, b) => a.date.localeCompare(b.date) || String(a.id).localeCompare(String(b.id)));
    }
    return result;
  }

  function item(plan) {
    const amount = (plan.operation === "incoming" ? "+" : "−") + money.format(plan.amount / 100);
    const date = shortDate.format(new Date(plan.date + "T00:00:00Z"));
    const period = plan.period === "week" ? "Неделя с " + date : date;
    const inlineDate = (plan.period === "week" ? "нед. " : "") + compactDate.format(new Date(plan.date + "T00:00:00Z"));
    const caption = plan.path ? plan.title : plan.text || "Без заказа";
    const context = plan.path ? [plan.client, plan.object, plan.text].filter(Boolean).join(" · ") : "";
    const description = [period, plan.operation === "incoming" ? "Приход" : "Расход", amount + " ₽", caption, context, plan.invoice_label].filter(Boolean).join(" · ");
    const attrs = ' class="money-item" data-money-item="' + escape(plan.id) + '" title="' + escape(description) + '" aria-label="' + escape(description) + '"';
    const contents = '<span class="money-item-date">' + escape(inlineDate) + '</span><span class="money-item-caption">' + escape(caption) +
      '</span><strong class="money-item-amount">' + escape(amount) + '</strong>';
    return '<li>' + (plan.path ? '<a href="?path=' + encodeURIComponent(plan.path) + '" data-money-path="' + escape(plan.path) + '"' + attrs + '>' + contents + '</a>' :
      '<button type="button"' + attrs + ' data-money-plan="' + escape(plan.id) + '">' + contents + '</button>') + '</li>';
  }

  function render() {
    const container = document.getElementById("moneyMonths");
    const data = months(plans, key(shift(currentMonth(), offset)));
    const markup = data.map((month) => {
      const difference = month.income - month.expense;
      return '<section class="money-month" aria-label="' + escape(monthName.format(shift(month.key, 0))) + '">' +
        '<h3>' + escape(monthName.format(shift(month.key, 0))) + '</h3><div class="money-month-columns">' +
        ["incoming", "outgoing"].map((direction) => '<div class="money-direction money-' + direction + '"><h4>' + (direction === "incoming" ? 'Приходы' : 'Расходы') + '</h4><ul>' +
          (month[direction].map(item).join("") || '<li class="money-empty">Нет планов</li>') + '</ul></div>').join("") + '</div>' +
        '<footer class="money-totals"><div class="money-total-columns">' +
        '<p class="money-total money-total-incoming"><span>Приходы</span><strong>' + money.format(month.income / 100) + '</strong></p>' +
        '<p class="money-total money-total-outgoing"><span>Расходы</span><strong>' + money.format(month.expense / 100) + '</strong></p></div>' +
        '<p class="money-difference">Разница <strong class="' + (difference < 0 ? 'negative' : difference > 0 ? 'positive' : '') + '">' +
        (difference > 0 ? '+' : difference < 0 ? '−' : '') + money.format(Math.abs(difference) / 100) + ' ₽</strong></p></footer></section>';
    }).join("");
    if (rendered === markup) return;
    const focused = document.activeElement?.closest("[data-money-item]")?.dataset.moneyItem;
    const viewport = document.getElementById("moneyScroll"), pane = document.querySelector(".content-pane");
    const left = viewport.scrollLeft, top = pane.scrollTop;
    container.innerHTML = markup;
    rendered = markup;
    if (focused) [...container.querySelectorAll("[data-money-item]")].find((node) => node.dataset.moneyItem === focused)?.focus({ preventScroll: true });
    viewport.scrollLeft = left;
    pane.scrollTop = top;
  }

  function show(records, visible, { loaded = false, error = "" } = {}) {
    const panel = document.getElementById("moneyOverview");
    panel.hidden = !visible;
    document.getElementById("moneyNavigation").hidden = !visible;
    if (!visible) return;
    plans = records;
    document.getElementById("moneyScroll").hidden = !loaded;
    document.getElementById("moneyState").textContent = error ? (loaded ? "Нет связи с сервером · показаны последние загруженные планы" : "Не удалось загрузить планы календаря") :
      loaded ? "" : "Загрузка планов календаря…";
    panel.setAttribute("aria-busy", String(!loaded && !error));
    if (!initialized) {
      initialized = true;
      for (const [id, step] of [["moneyEarlier", -1], ["moneyLater", 1], ["moneyToday", 0]]) {
        document.getElementById(id).addEventListener("click", () => { offset = step ? offset + step : 0; render(); });
      }
      panel.addEventListener("click", (event) => {
        const button = event.target.closest("[data-money-plan]");
        if (button) document.dispatchEvent(new CustomEvent("manager-plan-payment", { detail: { id: button.dataset.moneyPlan, path: "" } }));
      });
    }
    render();
  }

  return { show, months };
})();

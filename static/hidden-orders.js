"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const escape = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  const normalize = (value) => String(value ?? "").normalize("NFC").toLocaleLowerCase("ru");
  const compare = new Intl.Collator("ru", { numeric: true, sensitivity: "base" }).compare;
  const storageKey = "zigzag.hidden-orders.collapsed.v1";
  let orders = [], labels = {}, loaded = false, loading = false, collapsed = new Set(), rendered = "";
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || "[]");
    if (Array.isArray(saved)) collapsed = new Set(saved.filter((key) => typeof key === "string"));
  } catch (_) { /* The list remains usable without browser storage. */ }
  const groupKey = (kind, path) => JSON.stringify([kind, path]);
  const href = (path) => "/?path=" + encodeURIComponent(path);
  const link = (path, label, className = "") => '<a class="' + className + '" href="' + escape(href(path)) + '">' + escape(label) + '</a>';
  const remember = () => { try { localStorage.setItem(storageKey, JSON.stringify([...collapsed])); } catch (_) { /* View state is optional. */ } };

  function groupOrders(rows) {
    const clients = new Map();
    for (const order of rows) {
      const clientPath = order.client_path || order.client;
      if (!clients.has(clientPath)) clients.set(clientPath, { path: order.client_path, name: order.client, objects: new Map(), count: 0 });
      const client = clients.get(clientPath), objectPath = order.object_path || "";
      if (!client.objects.has(objectPath)) client.objects.set(objectPath, { path: objectPath, name: order.object || "Без объекта", orders: [] });
      client.objects.get(objectPath).orders.push(order);
      client.count++;
    }
    return [...clients.values()].sort((a, b) => compare(a.name, b.name) || compare(a.path, b.path));
  }

  function render() {
    const needle = normalize($("hiddenOrdersSearch").value.trim()), selectedReason = $("hiddenOrdersReason").value;
    const reason = selectedReason === "all" || Object.hasOwn(labels, selectedReason) ? selectedReason : "all";
    const matching = orders.filter((order) => (!needle || normalize([order.client, order.object, order.title, order.path, order.note].join(" ")).includes(needle)));
    const options = '<option value="all">Все причины · ' + matching.length + '</option>' + Object.entries(labels).map(([key, label]) => '<option value="' + escape(key) + '">' + escape(label) + ' · ' + matching.filter((order) => order.reasons.includes(key)).length + '</option>').join("");
    if (document.activeElement !== $("hiddenOrdersReason") && $("hiddenOrdersReason").innerHTML !== options) { $("hiddenOrdersReason").innerHTML = options; $("hiddenOrdersReason").value = reason; }
    if ($("hiddenOrdersReason").value !== reason) $("hiddenOrdersReason").value = reason;
    const rows = matching.filter((order) => reason === "all" || order.reasons.includes(reason)), clients = groupOrders(rows);
    const active = document.activeElement, focusKey = active?.dataset.focusKey;
    const scrollTop = document.scrollingElement.scrollTop;
    const markup = clients.map((client) => {
      const key = groupKey("client", client.path || client.name);
      return '<details class="hidden-orders-client" data-group="' + escape(key) + '"' + (collapsed.has(key) ? '' : ' open') + '><summary data-focus-key="' + escape(key) + '"><strong>' + escape(client.name) + '</strong><span class="count-badge">' + client.count + '</span><span class="hidden-orders-group-path">' + escape(client.path) + '</span></summary><div class="hidden-orders-objects">' +
        [...client.objects.values()].sort((a, b) => !a.path - !b.path || compare(a.name, b.name) || compare(a.path, b.path)).map((object) => {
          const objectKey = groupKey("object", [client.path || client.name, object.path]);
          const sorted = object.orders.slice().sort((a, b) => (b.updated || 0) - (a.updated || 0) || compare(a.title, b.title) || compare(a.path, b.path));
          return '<details class="hidden-orders-object" data-group="' + escape(objectKey) + '"' + (collapsed.has(objectKey) ? '' : ' open') + '><summary data-focus-key="' + escape(objectKey) + '"><span>' + escape(object.name) + '</span><span class="count-badge">' + sorted.length + '</span></summary>' +
            (object.path ? '<p class="hidden-orders-location">' + link(object.path, "Открыть объект ↗") + '</p>' : '') + '<ul class="hidden-orders-list">' + sorted.map((order) => '<li class="hidden-orders-row"><div class="hidden-orders-order">' +
              '<a class="hidden-orders-title" data-focus-key="' + escape(groupKey("order", order.path)) + '" href="' + escape(href(order.path)) + '">' + escape(order.title) + '</a><span class="hidden-orders-order-path" title="' + escape(order.path) + '">' + escape(order.path) + '</span>' +
              (order.note ? '<span class="hidden-orders-note" title="' + escape(order.note) + '">' + escape(order.note) + '</span>' : '') + '</div><span class="status-badge">' + escape(order.status_label) + '</span><div class="hidden-orders-reasons">' + order.reasons.map((key) => '<span>' + escape(labels[key] || key) + '</span>').join("") + '</div></li>').join("") + '</ul></details>';
        }).join("") + '</div></details>';
    }).join("");
    if (rendered !== markup) {
      rendered = markup;
      $("hiddenOrdersGroups").innerHTML = markup;
      if (focusKey) [...$("hiddenOrdersGroups").querySelectorAll("[data-focus-key]")].find((element) => element.dataset.focusKey === focusKey)?.focus({ preventScroll: true });
      document.scrollingElement.scrollTop = scrollTop;
    }
    $("hiddenOrdersCount").textContent = loaded ? rows.length + " из " + orders.length + " заказов · клиентов: " + clients.length : "Загрузка…";
    $("hiddenOrdersEmpty").hidden = !loaded || Boolean(rows.length);
  }

  async function load() {
    if (loading) return;
    loading = true;
    $("hiddenOrdersRefresh").setAttribute("aria-busy", "true");
    $("hiddenOrdersGroups").setAttribute("aria-busy", "true");
    try {
      const response = await fetch("/api/hidden-orders");
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Не удалось загрузить заказы");
      orders = data.orders; labels = data.reason_labels; loaded = true;
      $("hiddenOrdersState").textContent = data.warnings.length ? data.warnings.slice(0, 3).join(" · ") : "";
      render();
    } catch (error) {
      $("hiddenOrdersState").textContent = (loaded ? "Показаны последние загруженные данные. " : "") + error.message + ". Нажми «Обновить», чтобы повторить.";
      if (!loaded) $("hiddenOrdersCount").textContent = "Не удалось загрузить заказы";
    } finally {
      loading = false;
      $("hiddenOrdersRefresh").setAttribute("aria-busy", "false");
      $("hiddenOrdersGroups").setAttribute("aria-busy", "false");
    }
  }

  $("hiddenOrdersGroups").addEventListener("toggle", (event) => {
    const element = event.target;
    if (!element.matches("details[data-group]")) return;
    if (element.open) collapsed.delete(element.dataset.group); else collapsed.add(element.dataset.group);
    remember();
  }, true);
  $("hiddenOrdersSearch").addEventListener("input", render);
  $("hiddenOrdersReason").addEventListener("change", render);
  $("hiddenOrdersRefresh").addEventListener("click", load);
  for (const [id, open] of [["hiddenOrdersCollapse", false], ["hiddenOrdersExpand", true]]) $(id).addEventListener("click", () => {
    $("hiddenOrdersGroups").querySelectorAll("details[data-group]").forEach((element) => {
      element.open = open;
      if (open) collapsed.delete(element.dataset.group); else collapsed.add(element.dataset.group);
    });
    remember();
  });
  setInterval(() => { if (!document.hidden) load(); }, 5000);
  load();
})();

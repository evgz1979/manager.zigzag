/* Shared order sorting for the live lists and calendar rendering on M4. */
const OrderSorting = (() => {
  function compareOrderText(first, second) {
    first = String(first ?? "").normalize("NFC");
    second = String(second ?? "").normalize("NFC");
    return first.localeCompare(second, "ru", { numeric: true }) || (first < second ? -1 : first > second ? 1 : 0);
  }

  function compareOrders(a, b, key = "title", direction = 1, labelSets = {}) {
    if (key === "folder_date") {
      if ((a.folder_date == null) !== (b.folder_date == null)) return a.folder_date == null ? 1 : -1;
      const dateOrder = compareOrderText(a.folder_date, b.folder_date);
      return direction * dateOrder || compareOrderText(a.path, b.path) || compareOrderText(a.id, b.id);
    }
    for (const [label, identity, groupDirection] of [
      ["client", "client_path", key === "client" ? direction : 1],
      ["object", "object_path", key === "object" ? direction : 1],
    ]) {
      const first = a[label] || "", second = b[label] || "";
      if (!first || !second) { if (Boolean(first) !== Boolean(second)) return first ? -1 : 1; }
      const nameOrder = compareOrderText(first, second);
      if (nameOrder) return groupDirection * nameOrder;
      const pathOrder = compareOrderText(a[identity] || "", b[identity] || "");
      if (pathOrder) return groupDirection * pathOrder;
    }
    const favoriteOrder = Number(b.is_favorite === true) - Number(a.is_favorite === true);
    if (favoriteOrder) return favoriteOrder;
    if (a[key] == null || b[key] == null) {
      if ((a[key] == null) !== (b[key] == null)) return a[key] == null ? 1 : -1;
    } else {
      const labels = labelSets[key];
      const first = labels ? labels[a[key]] || a[key] : a[key];
      const second = labels ? labels[b[key]] || b[key] : b[key];
      const valueOrder = typeof first === "string" ? compareOrderText(first, second) : first - second;
      if (valueOrder) return direction * valueOrder;
    }
    return compareOrderText(a.title, b.title) || compareOrderText(a.path, b.path) || compareOrderText(a.id, b.id);
  }

  return { text: compareOrderText, compare: compareOrders };
})();

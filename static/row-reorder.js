// Подключает ручки перемещения строк мышью и клавиатурой.
// Меняет DOM только при вставке, возвращает фокус ручке и вызывает changed после перестановки.
function bindRowReorder(list, rowSelector, transferType, changed) {
  let drag = null;

  // Находит точку вставки по верхней или нижней половине строки.
  // Возвращает null вне списка и при сохранении текущего порядка.
  function dropPosition(event) {
    const target = event.target.closest(rowSelector);
    if (target?.parentElement !== list || target === drag.row) return null;
    const bounds = target.getBoundingClientRect();
    const edge = event.clientY < bounds.top + bounds.height / 2 ? "before" : "after";
    const before = edge === "before" ? target : target.nextElementSibling;
    return before === drag.row || before === drag.row.nextElementSibling ? null : { target, edge, before };
  }

  // Показывает линию вставки у подходящего края строки.
  // Положение линии не меняет порядок до завершения перетаскивания.
  function markDrop(position) {
    const marker = drag.marker;
    if (marker?.target === position?.target && marker?.edge === position?.edge) return;
    marker?.target.removeAttribute("data-row-drop");
    if (position) position.target.dataset.rowDrop = position.edge;
    drag.marker = position;
  }

  // Очищает подсветку при вставке, отмене и замене списка.
  // Можно вызывать без активного перетаскивания.
  function clearDrag() {
    if (!drag) return;
    markDrop(null);
    drag.row.classList.remove("row-dragging");
    drag = null;
  }

  // Вставляет существующий узел перед соседней строкой или в конец.
  // Сохраняет поля узла и передаёт новый порядок владельцу списка.
  function moveRow(row, before) {
    list.insertBefore(row, before);
    row.querySelector(".row-drag-handle").focus();
    changed();
  }

  list.addEventListener("dragstart", (event) => {
    const handle = event.target.closest(".row-drag-handle");
    if (!handle || handle.disabled || !event.dataTransfer) return;
    const row = handle.closest(rowSelector);
    const bounds = row.getBoundingClientRect();
    event.dataTransfer.setData(transferType, "move");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setDragImage(row, event.clientX - bounds.left, event.clientY - bounds.top);
    clearDrag();
    drag = { row, marker: null };
    row.classList.add("row-dragging");
  });
  list.addEventListener("dragover", (event) => {
    if (!drag) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    markDrop(dropPosition(event));
  });
  list.addEventListener("dragleave", (event) => {
    if (drag && !list.contains(event.relatedTarget)) markDrop(null);
  });
  list.addEventListener("drop", (event) => {
    if (!drag) return;
    event.preventDefault();
    const { row } = drag, position = dropPosition(event);
    clearDrag();
    if (position) moveRow(row, position.before);
  });
  list.addEventListener("dragend", clearDrag);
  list.addEventListener("keydown", (event) => {
    const handle = event.target.closest(".row-drag-handle");
    if (!handle || handle.disabled || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const up = event.key === "ArrowUp";
    if (!up && event.key !== "ArrowDown") return;
    event.preventDefault();
    const row = handle.closest(rowSelector);
    const adjacent = up ? row.previousElementSibling : row.nextElementSibling;
    if (adjacent) moveRow(row, up ? adjacent : adjacent.nextElementSibling);
  });
  return clearDrag;
}

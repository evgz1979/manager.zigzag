/* Editable paper notes over the interactive calendar. */
const CalendarStickers = (() => {
  const viewport = document.getElementById("calendarViewport");
  const calendar = document.getElementById("calendarWeeks");
  const addButton = document.getElementById("calendarAddSticker");
  const entries = new Map();
  const fields = ["week", "x", "y", "text", "deleted"];
  let drag = null, writes = 0;

  // Возвращает поколение записей перед запросом очередной сводки.
  // Начало и завершение записи меняют поколение, поэтому старый список пропускается.
  function writeVersion() {
    return writes;
  }

  // Проверяет, есть ли у листка ещё не сохранённые изменения.
  // Нулевая ревизия обозначает новый листок, даже если текст пока пуст.
  function dirty(entry) {
    return !entry.saved || fields.some(key => entry.draft[key] !== entry.saved[key]);
  }

  // Принимает серверную запись как сохранённую или как текущий редакторский черновик.
  // Переводит SQLite 0/1 в boolean для следующих запросов и сравнений.
  function accept(entry, record, replaceDraft) {
    entry.saved = { ...record, deleted: Boolean(record.deleted) };
    if (replaceDraft) entry.draft = { ...entry.saved };
  }

  // Убирает листок из редактора и возвращает фокус кнопке добавления при необходимости.
  // Все отложенные сохранения этого листка отменяются.
  function remove(entry) {
    clearTimeout(entry.timer);
    entries.delete(entry.draft.id);
    if (entry.element?.contains(document.activeElement)) addButton.focus({ preventScroll: true });
    entry.element?.remove();
  }

  // Переносит свежие изменения из общей сводки в редактор.
  // Черновики и листок под указателем остаются локальными до окончания операции.
  function update(records, generation) {
    if (!Array.isArray(records) || generation !== writes) return;
    addButton.disabled = false;
    const incoming = new Set();
    for (const record of records) {
      incoming.add(record.id);
      if (!entries.has(record.id)) entries.set(record.id, {});
      const entry = entries.get(record.id);
      if (!entry.draft || (!dirty(entry) && !entry.pending && drag?.entry !== entry && record.revision > entry.saved.revision)) {
        accept(entry, record, true);
      }
    }
    for (const [id, entry] of entries) {
      if (!incoming.has(id) && !dirty(entry) && !entry.pending && drag?.entry !== entry) remove(entry);
    }
  }

  // Возвращает даты недель, которые нужны для показа всех открытых стикеров.
  // Черновик передаёт новое положение сразу после отпускания указателя.
  function weeks() {
    return [...new Set([...entries.values()].map(entry => entry.draft.week))];
  }

  // Обновляет кнопки листка с учётом сохранения, удаления и ошибки.
  // Ошибка доступна через подсказку кнопки, повторное действие запускает редактор.
  function controls(entry) {
    const { element, editor, grip, dismiss, retry, draft, pending, failure } = entry;
    element.classList.toggle("is-saving", Boolean(pending));
    element.setAttribute("aria-busy", String(Boolean(pending)));
    editor.readOnly = draft.deleted;
    grip.disabled = draft.deleted;
    dismiss.disabled = draft.deleted;
    retry.hidden = !failure;
    retry.disabled = Boolean(pending);
    retry.textContent = failure?.status === 409 ? "Обновить" : "Повторить";
    retry.title = failure?.message || "";
  }

  // Сохраняет очередной снимок черновика одного листка.
  // Пока идёт запрос, следующий ввод остаётся в черновике и записывается после ответа.
  async function save(entry) {
    clearTimeout(entry.timer);
    if (entry.pending || entry.failure || !dirty(entry)) return;
    entry.pending = true;
    writes++;
    controls(entry);
    try {
      const saved = await request("/api/calendar-sticker", { ...entry.draft, revision: entry.saved?.revision || 0 });
      accept(entry, saved, false);
      if (saved.deleted) {
        remove(entry);
        HomeCalendar.show();
      }
    } catch (error) {
      entry.failure = error;
      notify(error.message, true);
    } finally {
      writes++;
      entry.pending = false;
      if (entries.has(entry.draft.id)) {
        controls(entry);
        if (!entry.failure && dirty(entry)) queueSave(entry);
      }
    }
  }

  // Планирует автосохранение после короткой паузы ввода.
  // При уходе из поля или перемещении листка сохранение вызывается сразу.
  function queueSave(entry) {
    clearTimeout(entry.timer);
    entry.timer = setTimeout(() => save(entry), 600);
  }

  // Повторяет временно неудачную запись или открывает актуальную версию после конфликта.
  // Замена конфликтующего черновика требует отдельного явного действия.
  async function recover(entry) {
    if (entry.failure?.status !== 409) {
      entry.failure = null;
      await save(entry);
      return;
    }
    if (!window.confirm("Загрузить последнюю версию стикера? Твои несохранённые правки будут заменены.")) return;
    entry.pending = true;
    controls(entry);
    try {
      const record = await request("/api/calendar-sticker?id=" + encodeURIComponent(entry.draft.id));
      writes++;
      if (record?.version === 1 && !record.deleted) {
        accept(entry, record, true);
        entry.failure = null;
      } else remove(entry);
      HomeCalendar.show();
    } catch (error) {
      notify(error.message, true);
    } finally {
      entry.pending = false;
      if (entries.has(entry.draft.id)) controls(entry);
    }
  }

  // Выбирает неделю по вертикальной координате центра листка.
  // За пределами сетки ближайшая крайняя неделя получает координату 0 или 10000.
  function position(x, y) {
    const rows = [...calendar.children];
    const row = rows.find(item => y < item.getBoundingClientRect().bottom) || rows.at(-1);
    const box = row.getBoundingClientRect();
    // Преобразует координату в целую долю для хранения в SQLite.
    // Ограничивает результат границами выбранной недели.
    const ratio = (value, size) => Math.round(Math.min(1, Math.max(0, value / size)) * 10000);
    return { row, week: row.dataset.week, x: ratio(x - box.left, box.width), y: ratio(y - box.top, box.height) };
  }

  // Сохраняет новое положение после перетаскивания или нажатия стрелки.
  // Доли вычисляются относительно соответствующей недели и сохраняются вместе с текстом.
  function move(entry, x, y) {
    const next = position(x, y);
    Object.assign(entry.draft, { week: next.week, x: next.x, y: next.y });
    HomeCalendar.show();
    void save(entry);
  }

  // Перемещает сам листок вслед за указателем и прокручивает сетку у краёв.
  // Предпросмотр не меняет сохранённое положение до завершения жеста.
  function followPointer() {
    const { entry, x, y, offsetX, offsetY } = drag;
    const viewportBox = viewport.getBoundingClientRect();
    const left = viewportBox.left, right = left + viewport.clientWidth;
    const top = viewportBox.top + viewport.firstElementChild.offsetHeight, bottom = viewportBox.top + viewport.clientHeight;
    // Выбирает направление автопрокрутки у границы видимой области.
    // Средняя часть viewport даёт нулевой сдвиг.
    const speed = (point, start, end) => point < start + 32 ? -12 : point > end - 32 ? 12 : 0;
    if (x >= left && x <= right && y >= top && y <= bottom) {
      const dx = speed(x, left, right), dy = speed(y, top, bottom);
      if (dx || dy) viewport.scrollBy(dx, dy);
    }
    const rowBox = entry.element.parentElement.getBoundingClientRect();
    entry.element.style.left = (x - rowBox.left - offsetX) + "px";
    entry.element.style.top = (y - rowBox.top - offsetY) + "px";
    drag.frame = requestAnimationFrame(followPointer);
  }

  // Начинает жест только с ручки листка и захватывает один указатель.
  // Текст по-прежнему выделяется и редактируется в отдельном поле.
  function startDrag(entry, event) {
    if (drag || event.button !== 0 || !event.isPrimary) return;
    event.preventDefault();
    entry.grip.focus({ preventScroll: true });
    const box = entry.element.getBoundingClientRect();
    drag = { entry, pointer: event.pointerId, x: event.clientX, y: event.clientY,
      startX: event.clientX, startY: event.clientY, offsetX: event.clientX - box.left, offsetY: event.clientY - box.top, frame: 0 };
    entry.grip.setPointerCapture(event.pointerId);
  }

  // Превращает движение захваченного указателя в перетаскивание после небольшого порога.
  // Поддерживает мышь, палец и перо через Pointer Events.
  function dragPointer(event) {
    if (drag?.pointer !== event.pointerId) return;
    drag.x = event.clientX;
    drag.y = event.clientY;
    if (drag.frame || Math.hypot(drag.x - drag.startX, drag.y - drag.startY) < 4) return;
    viewport.classList.add("is-dragging-sticker");
    drag.entry.element.classList.add("is-dragging");
    followPointer();
  }

  // Завершает перетаскивание и записывает новую позицию только при отпускании указателя.
  // Отменённый захват или Escape возвращает листок в исходную точку.
  function endDrag(commit) {
    const { entry, pointer, frame, x, y, offsetX, offsetY } = drag;
    drag = null;
    cancelAnimationFrame(frame);
    if (entry.grip.hasPointerCapture(pointer)) entry.grip.releasePointerCapture(pointer);
    entry.element.classList.remove("is-dragging");
    entry.element.style.removeProperty("left");
    entry.element.style.removeProperty("top");
    if (commit && frame) {
      move(entry, x - offsetX + entry.element.offsetWidth / 2, y - offsetY + entry.element.offsetHeight / 2);
    }
    viewport.classList.remove("is-dragging-sticker");
  }

  // Создаёт редактор листка и подключает ввод, ручку и удаление.
  // Элемент сохраняет идентичность при опросе и при переносе в другую неделю.
  function create(entry) {
    const element = document.createElement("div");
    element.className = "calendar-sticker";
    element.dataset.stickerId = entry.draft.id;
    element.setAttribute("role", "group");
    element.setAttribute("aria-label", "Стикер календаря");
    element.innerHTML = `<div class="calendar-sticker-header">
      <button class="calendar-sticker-grip" type="button" aria-label="Переместить стикер" title="Перетащи или нажимай клавиши со стрелками" aria-keyshortcuts="ArrowUp ArrowDown ArrowLeft ArrowRight">⠿</button>
      <button class="calendar-sticker-retry" type="button" hidden></button>
      <button class="calendar-sticker-remove" type="button" aria-label="Удалить стикер" title="Удалить стикер">×</button>
      </div><textarea class="calendar-sticker-editor" aria-label="Текст стикера" placeholder="Напиши заметку…" maxlength="2000" spellcheck="true"></textarea>`;
    const [grip, retry, dismiss] = element.querySelectorAll("button");
    const editor = element.querySelector("textarea");
    Object.assign(entry, { element, grip, retry, dismiss, editor });
    grip.addEventListener("pointerdown", event => startDrag(entry, event));
    grip.addEventListener("pointermove", dragPointer);
    for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) {
      grip.addEventListener(type, event => { if (drag?.pointer === event.pointerId) endDrag(type === "pointerup"); });
    }
    grip.addEventListener("keydown", event => {
      if (event.key === "Escape" && drag?.entry === entry) { event.preventDefault(); endDrag(false); return; }
      const direction = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
      if (!direction || drag) return;
      event.preventDefault();
      const box = element.getBoundingClientRect();
      move(entry, box.left + box.width / 2 + 20 * direction[0], box.top + box.height / 2 + 20 * direction[1]);
      element.scrollIntoView({ block: "nearest", inline: "nearest" });
    });
    editor.addEventListener("input", () => { entry.draft.text = editor.value; queueSave(entry); });
    editor.addEventListener("blur", () => { void save(entry); });
    retry.addEventListener("click", () => recover(entry));
    dismiss.addEventListener("click", () => {
      if (entry.draft.text.trim() && !window.confirm("Удалить этот стикер?")) return;
      entry.draft.deleted = true;
      if (!entry.saved && !entry.pending && !entry.failure) { remove(entry); HomeCalendar.show(); }
      else { controls(entry); void save(entry); }
    });
  }

  // Раскладывает листки поверх нужных недель и оставляет фокус при переносе.
  // Доли задают центр листка; соседние недели могут лежать под одним листком.
  function render() {
    const rows = new Map([...calendar.children].map(row => [row.dataset.week, row]));
    for (const entry of entries.values()) {
      const row = rows.get(entry.draft.week);
      if (!row || drag?.entry === entry) continue;
      if (!entry.element) create(entry);
      const { element, editor, draft } = entry;
      element.style.setProperty("--sticker-x", draft.x / 10000);
      element.style.setProperty("--sticker-y", draft.y / 10000);
      if (editor.value !== draft.text) editor.value = draft.text;
      controls(entry);
      if (element.parentElement !== row) {
        const focus = element.contains(document.activeElement) ? document.activeElement : null;
        row.append(element);
        focus?.focus({ preventScroll: true });
      }
    }
  }

  addButton.addEventListener("click", () => {
    if (!calendar.firstElementChild) return;
    const box = viewport.getBoundingClientRect();
    const { week, x, y } = position(box.left + viewport.clientWidth / 2,
      box.top + (viewport.firstElementChild.offsetHeight + viewport.clientHeight) / 2);
    const draft = { id: freeCalendarIdentity(), week, x, y, text: "", deleted: false };
    const entry = { draft };
    entries.set(draft.id, entry);
    render();
    entry.editor.focus({ preventScroll: true });
    void save(entry);
  });

  return { writeVersion, update, weeks, render };
})();

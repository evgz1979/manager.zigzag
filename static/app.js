const $ = (id) => document.getElementById(id);
const statusLabels = { new: "Новый", measure: "Замеры", process: "В работе", workshop: "В цех", install: "Монтаж", rework: "Переделка/доделка", finishing: "Завершение/добивка", done: "Готово", done_but: "Готово, но…", cancelled: "Отменён", unspecified: "Не указан" };
const financialStatusLabels = { unspecified: "Не указан", payment: "На оплате", partial: "Частично оплачен", paid: "Оплачен" };
const eventRelevanceLabels = { none: "Без статуса", active: "Актуально", check: "Проверить", inactive: "Неактуально" };
const typeLabels = { all: "Все", images: "Фото", pdf: "PDF", design: "Макеты", docs: "Документы", video: "Видео", audio: "Аудио", other: "Другое" };
const state = {
  tree: [], auxiliary: [], nodes: new Map(), children: new Map(), expanded: new Set(),
  treeQuery: "", searchTree: null, folder: null, selected: "",
  fileQuery: "", fileType: "all", fileSort: "folders", limit: 120,
  folderRequest: null, navigation: 0, preview: null, dirty: false, saving: null,
  printTask: null, printSaving: null, printQuery: "",
  view: "orders", orders: [], orderFilter: "all", financialFilter: "all", orderQuery: "", orderSort: "updated", orderDirection: -1, scan: null, ordersRequest: 0,
  unregistrations: [], removeOrder: null, removingOrder: false,
  fileComment: null, fileCommentSaving: null,
  selectedFiles: new Set(), imageReport: null,
  fileRemoval: null, fileRemoving: false, trashRestoring: false,
  newOrderParent: null, creatingOrderFolder: false,
  eventPlan: null, eventBusy: false,
};
let searchTimer, toastTimer, todoSaveTimer, previewVersion = 0, treeSearchVersion = 0, printReadVersion = 0;
const icon = (name) => '<svg aria-hidden="true"><use href="#icon-' + name + '"/></svg>';
const escapeHtml = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
const normalize = (value) => String(value).normalize("NFC").toLocaleLowerCase("ru");
const apiUrl = (route, path = "", extra = {}) => route + "?" + new URLSearchParams({ path, ...extra });
const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + " Б";
  if (bytes < 1024 ** 2) return Math.round(bytes / 1024) + " КБ";
  if (bytes < 1024 ** 3) return (bytes / 1024 ** 2).toFixed(1) + " МБ";
  return (bytes / 1024 ** 3).toFixed(1) + " ГБ";
};
const formatDate = (seconds) => new Date(seconds * 1000).toLocaleDateString("ru", { day: "numeric", month: "short", year: "numeric" });
const printCountLabel = (count) => count + " " + ({ one: "задание", few: "задания", many: "заданий", other: "задания" }[new Intl.PluralRules("ru").select(count)]);
const folderParent = (path) => path.split("/").slice(0, -1).join("/");
const isServiceFolder = (path) => path.split("/").some((part) => part.startsWith("#"));

async function request(url, payload) {
  const response = await fetch(url, payload === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) {
    const error = new Error(result.error || "Не удалось выполнить действие");
    error.status = response.status;
    throw error;
  }
  return result;
}

function notify(message, error = false) {
  clearTimeout(toastTimer);
  $("toast").textContent = message;
  $("toast").classList.toggle("error", error);
  $("toast").hidden = false;
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, error ? 7000 : 3000);
}

function registerNodes(nodes) {
  for (const node of nodes) {
    state.nodes.set(node.path, node);
    if (node.children) registerNodes(node.children);
  }
}

function treeMarkup(nodes, depth = 0, searching = false) {
  return nodes.map((node, index) => {
    const open = searching ? Boolean(node.children?.length) : state.expanded.has(node.path);
    const children = searching ? node.children || [] : state.children.get(node.path) || [];
    const selected = node.path === state.selected;
    const tabIndex = selected || (!state.selected && depth === 0 && index === 0) ? 0 : -1;
    return '<div class="tree-branch" role="none"><div class="tree-row' + (selected ? " selected" : "") +
      '" role="treeitem" tabindex="' + tabIndex + '" aria-selected="' + selected + '"' +
      (node.hasChildren ? ' aria-expanded="' + open + '"' : "") + ' aria-level="' + (depth + 1) +
      '" data-path="' + escapeHtml(node.path) + '" style="--depth:' + depth + '" title="' + escapeHtml(node.name) + '">' +
      '<button class="tree-toggle' + (open ? " expanded" : "") + '" tabindex="-1" aria-label="' +
      (open ? "Свернуть " : "Раскрыть ") + escapeHtml(node.name) + '"' + (!node.hasChildren ? ' disabled aria-hidden="true"' : "") + ">" +
      icon("chevron") + "</button>" + icon("folder") + '<span class="tree-name">' + escapeHtml(node.name) +
      '</span></div>' + (open && children.length ? '<div role="group">' + treeMarkup(children, depth + 1, searching) + "</div>" : "") + "</div>";
  }).join("");
}

function renderTree() {
  const focused = document.activeElement?.closest(".tree-row")?.dataset.path;
  const nodes = state.searchTree || state.tree;
  $("folderTree").innerHTML = nodes.length ? treeMarkup(nodes, 0, Boolean(state.searchTree)) : '<p class="tree-empty">Папки не найдены</p>';
  if (!$("folderTree").querySelector('[tabindex="0"]')) $("folderTree").querySelector(".tree-row")?.setAttribute("tabindex", "0");
  if (focused) focusTree(focused);
  $("auxiliaryButtons").innerHTML = state.auxiliary.map((node) =>
    '<button class="auxiliary-button' + (state.selected === node.path || state.selected.startsWith(node.path + "/") ? " active" : "") +
    '" data-path="' + escapeHtml(node.path) + '" title="' + escapeHtml(node.name) + '">' + icon("folder") +
    '<span>' + escapeHtml(node.name) + "</span></button>").join("");
  $("auxiliaryButtons").hidden = !state.auxiliary.length;
}

function focusTree(path) {
  const row = [...$("folderTree").querySelectorAll(".tree-row")].find((item) => item.dataset.path === path);
  if (row) {
    $("folderTree").querySelectorAll(".tree-row").forEach((item) => { item.tabIndex = -1; });
    row.tabIndex = 0;
    row.focus({ preventScroll: true });
  }
}

async function loadChildren(path) {
  if (!state.children.has(path)) {
    const data = await request(apiUrl("/api/tree", path));
    registerNodes(data.children);
    state.children.set(path, data.children);
  }
  return state.children.get(path);
}

async function toggleFolder(path, forceOpen = false) {
  if (state.treeQuery) return;
  if (state.expanded.has(path) && !forceOpen) {
    state.expanded.delete(path);
  } else {
    await loadChildren(path);
    state.expanded.add(path);
  }
  renderTree();
}

async function revealPath(path, navigation) {
  if (!path || state.treeQuery || state.auxiliary.some((item) => path === item.path || path.startsWith(item.path + "/"))) return;
  const parts = path.split("/");
  for (let index = 1; index < parts.length; index++) {
    if (navigation !== state.navigation) return;
    const ancestor = parts.slice(0, index).join("/");
    await loadChildren(ancestor);
    state.expanded.add(ancestor);
  }
  if (navigation === state.navigation) {
    renderTree();
    const selected = $("folderTree").querySelector(".tree-row.selected");
    selected?.scrollIntoView({ block: "nearest" });
  }
}

async function loadTree() {
  const data = await request(apiUrl("/api/tree"));
  state.tree = data.children;
  state.auxiliary = data.auxiliary;
  state.nodes.clear();
  state.children.clear();
  registerNodes([...state.tree, ...state.auxiliary]);
  $("clientCount").textContent = state.tree.length;
  $("rootLabel").textContent = data.rootName;
  $("rootLabel").title = data.root;
  for (const path of [...state.expanded].sort((a, b) => a.split("/").length - b.split("/").length)) {
    try { await loadChildren(path); } catch { state.expanded.delete(path); }
  }
  renderTree();
}

function renderSubfolders() {
  const folder = state.folder;
  const focused = document.activeElement?.closest("[data-relevance]");
  const focusPath = focused?.dataset.eventPath, focusValue = focused?.dataset.relevance;
  const directories = folder.directories.filter((item) => !item.name.startsWith("#"));
  $("subfolders").classList.toggle("with-event-relevance", directories.some((item) => item.eventRelevance));
  $("folderSection").hidden = !directories.length;
  $("foldersTitle").textContent = folder.canCreateEventFolder ? "События" : folder.path ? "Подпапки" : "Папки";
  $("directoryCount").textContent = directories.length;
  $("subfolders").innerHTML = directories.map((item) => {
    const open = '<button class="subfolder" data-path="' + escapeHtml(item.path) + '" title="' + escapeHtml(item.name) + '">' +
      icon("folder") + '<span>' + escapeHtml(item.name) + "</span>" + icon("chevron") + "</button>";
    const relevance = item.eventRelevance;
    if (!relevance) return open;
    const message = item.relevanceSaving ? "Сохраняю…" : relevance.error || (relevance.sync_pending
      ? relevance.sync_error ? "В базе сохранено · не выгружено: " + relevance.sync_error : "В базе сохранено · ожидает выгрузки" : "");
    return '<div class="event-folder" data-relevance-state="' + escapeHtml(relevance.value || "none") + '" aria-busy="' + Boolean(item.relevanceSaving) + '">' + open +
      '<div class="event-relevance" role="group" aria-label="Актуальность события ' + escapeHtml(item.name) + '">' +
      Object.entries(eventRelevanceLabels).map(([value, label]) => '<button type="button" data-event-path="' + escapeHtml(item.path) + '" data-relevance="' + value +
        '" aria-pressed="' + (value === relevance.value) + '"' + (item.relevanceSaving || relevance.error || !relevance.revision ? " disabled" : "") + '>' + label + '</button>').join("") +
      '</div>' + (message ? '<p class="event-export' + (relevance.error || relevance.sync_error ? " error" : "") + '" role="status">' + escapeHtml(message) + '</p>' : "") + '</div>';
  }).join("");
  if (focusPath) [...$("subfolders").querySelectorAll("[data-relevance]")].find((button) => button.dataset.eventPath === focusPath && button.dataset.relevance === focusValue)?.focus();
}

async function refreshEventRelevance(folder) {
  if (!folder.canCreateEventFolder || state.folder !== folder) return;
  const records = await request(apiUrl("/api/event-relevance", folder.path));
  if (state.folder !== folder) return;
  let changed = false;
  for (const item of folder.directories) {
    if (!item.relevanceSaving && item.eventRelevance && records[item.path] && JSON.stringify(item.eventRelevance) !== JSON.stringify(records[item.path])) {
      item.eventRelevance = records[item.path];
      changed = true;
    }
  }
  if (changed) renderSubfolders();
}

async function saveEventRelevance(path, value) {
  const folder = state.folder, item = folder?.directories.find((directory) => directory.path === path);
  if (!item?.eventRelevance || item.relevanceSaving || item.eventRelevance.value === value) return;
  item.relevanceSaving = true;
  renderSubfolders();
  try {
    item.eventRelevance = await request("/api/event-relevance", { path, value, revision: item.eventRelevance.revision });
  } catch (error) {
    if (error.status === 409) {
      try {
        const records = await request(apiUrl("/api/event-relevance", folder.path));
        if (records[path]) item.eventRelevance = records[path];
      } catch { /* Сохраняем последнее известное состояние. */ }
    }
    throw error;
  } finally {
    item.relevanceSaving = false;
    if (state.folder === folder) renderSubfolders();
  }
}

function renderFolder(preserveForm = false) {
  const folder = state.folder;
  const printView = folder.view === "print";
  const service = folder.service = isServiceFolder(folder.path);
  const noteOnly = service || Boolean(folder.noteOnly);
  const hasTodo = Boolean(folder.path) && (!noteOnly || Boolean(folder.eventFolder));
  $("orderOverview").hidden = !folder.path || (printView && !folder.eventFolder);
  $("orderOverview").classList.toggle("with-todos", hasTodo);
  $("todoPanel").hidden = !hasTodo;
  $("breadcrumbs").innerHTML = folder.breadcrumbs.map((part, index) =>
    (index ? '<span class="breadcrumb-divider">/</span>' : "") +
    '<button data-path="' + escapeHtml(part.path) + '"' + (index === folder.breadcrumbs.length - 1 ? ' aria-current="page"' : "") + ">" +
    escapeHtml(part.name) + "</button>").join("");
  $("folderTitle").textContent = printView ? "Задания на печать" : folder.path ? folder.order?.title || folder.name : "Клиенты и заказы";
  $("clientLabel").textContent = printView ? "ШИРОКОФОРМАТНАЯ ПРОДУКЦИЯ" : service ? "СЛУЖЕБНАЯ ПАПКА" : folder.folderKindLabel && folder.folderKind !== "order" ? folder.folderKindLabel : folder.client || folder.name;
  $("folderSummary").textContent = printView ? printCountLabel(folder.fileCount) + " · название, ссылка и описание" : folder.filesLoading ? "Карточка из локальной базы · подпапки загружаются…" : folder.filesUnavailable ? "Карточка из локальной базы · папка сейчас недоступна" : folder.filesScope === "events" ? folder.folderCount + " папок · файлы доступны в событиях" : folder.path
    ? folder.fileCount + " файлов · " + folder.folderCount + " папок · " + formatSize(folder.totalSize)
    : "Выберите клиента или заказ в дереве слева";
  renderSubfolders();
  $("orderDetails").hidden = !folder.path;
  $("folderDetailsTitle").textContent = noteOnly ? "Заметка" : "Карточка заказа";
  $("statusBadge").hidden = noteOnly;
  $("statusLabel").hidden = noteOnly;
  $("orderStatusFields").hidden = noteOnly;
  $("statusForm").classList.toggle("note-only", noteOnly);
  $("orderNote").placeholder = noteOnly ? "Заметка к этой папке" : "Что важно по этому заказу";
  $("removeOrderButton").hidden = !folder.order;
  $("createOrderFolderButton").hidden = folder.canCreateOrderFolder !== true;
  $("createEventFolderButton").hidden = folder.canCreateEventFolder !== true;
  if (!preserveForm) {
    folder.todo_items = folder.order ? folder.order.todo_items : folder.todo_items === undefined ? [] : folder.todo_items;
    if (hasTodo) { $("todoNewText").value = ""; renderTodos(); }
    $("orderDetails").open = noteOnly || Boolean(folder.note || folder.order);
    $("orderTitleLabel").hidden = noteOnly || !folder.order;
    $("financialFields").hidden = noteOnly || !folder.order;
    $("orderTitleInput").value = folder.order?.title || folder.name;
    for (const [field, key] of [["orderAmount", "amount"], ["orderCosts", "costs"], ["orderPaid", "paid"]]) {
      $(field).value = folder.order?.[key] == null ? "" : (folder.order[key] / 100).toFixed(2);
    }
    $("addOrderButton").hidden = !folder.path || service || folder.canRegisterOrder !== true || Boolean(folder.order);
    renderOrderCalculated();
    renderExportState();
    $("statusSelect").value = folder.status || "new";
    $("financialStatusSelect").value = folder.financial_status || "unspecified";
    $("orderNote").value = folder.note;
    resizeOrderNote();
    renderStatus();
  }
  $("loadOrderFilesButton").hidden = !folder.filesUnavailable;
  const warnings = [...folder.warnings];
  if (folder.order && folder.canRegisterOrder === false && !folder.filesLoading && !folder.filesUnavailable) warnings.push(folder.registrationHint + " Эта папка уже зарегистрирована; убрать её из списка можно с подтверждением.");
  if (folder.registrationPending) warnings.push(folder.registrationError ? "Убрано из списка. Не удалось сохранить карточку в папку: " + folder.registrationError : "Убрано из списка. Карточка сохраняется в папку.");
  $("notice").hidden = !warnings.length;
  $("notice").textContent = warnings.join(" · ");
  $("fileSearch").value = state.fileQuery;
  $("filesSection").hidden = printView || folder.filesScope === "events" || Boolean(folder.filesLoading || folder.filesUnavailable);
  $("printWorkspace").hidden = !printView;
  if (printView) {
    state.printQuery = "";
    $("printTaskSearch").value = "";
    renderPrintList();
    $("printEditorForm").hidden = true;
    $("printEditorEmpty").hidden = false;
    $("printEditorEmpty").textContent = "Выберите задание или создайте новое";
    const requested = new URLSearchParams(location.search).get("task");
    const first = printFiles().find((file) => file.path === requested) || printFiles()[0];
    if (first) run(() => openPrintTask(first.path));
  } else renderFiles();
}

function resizeOrderNote() {
  const note = $("orderNote");
  if (!$("orderDetails").open) return;
  note.style.height = "auto";
  note.style.height = Math.min(480, Math.max(note.value.trim() ? 160 : 54, note.scrollHeight + 2)) + "px";
}

function renderStatus() {
  $("statusBadge").textContent = statusLabels[state.folder.status] || state.folder.status;
  $("statusBadge").dataset.status = state.folder.status;
  const financial = state.folder.financial_status || "unspecified";
  $("financialStatusBadge").textContent = financialStatusLabels[financial];
  $("financialStatusBadge").dataset.financialStatus = financial;
  $("financialStatusBadge").hidden = state.folder.service || state.folder.noteOnly || financial === "unspecified";
  $("saveStatusButton").textContent = state.dirty ? "Сохранить изменения" : "Сохранить";
  const folderNote = state.folder.folderNote;
  $("todoSaveState").textContent = state.saving ? "Сохраняю…" : state.dirty ? "Есть несохранённые изменения" : folderNote?.sync_error ? "Сохранено в базе. Выгрузка: " + folderNote.sync_error : folderNote?.sync_pending ? "Сохранено в базе · ожидает выгрузки в папку" : folderNote ? folderNote.file_exists ? "Сохранено в базе и в !.txt этой папки" : "Автоматическое сохранение в эту папку" : "Сохранено";
}

function renderTodos() {
  const items = state.folder.todo_items;
  const editable = Array.isArray(items);
  $("todoLegacy").hidden = editable;
  $("todoLegacyText").textContent = editable ? "" : (state.folder.order?.extra_blocks || state.folder.extra_blocks || {})["Задачи"] || "";
  $("todoAddForm").hidden = !editable;
  $("todoEmpty").hidden = !editable || Boolean(items.length);
  $("todoEmpty").textContent = state.folder.folderNote ? "Добавьте, что нужно сделать в этой папке." : "Добавьте, что нужно сделать по заказу.";
  $("todoCount").textContent = editable ? items.filter((item) => item.done).length + " / " + items.length : "";
  $("todoList").innerHTML = editable ? items.map((item, index) => '<div class="todo-row' + (item.done ? ' done' : '') + '" data-todo-index="' + index + '">' +
    '<input class="todo-check" type="checkbox" aria-label="Выполнено: ' + escapeHtml(item.text) + '"' + (item.done ? ' checked' : '') + '>' +
    '<input class="todo-text" type="text" maxlength="1000" aria-label="Текст задачи" value="' + escapeHtml(item.text) + '">' +
    '<button class="todo-delete" type="button" aria-label="Удалить задачу: ' + escapeHtml(item.text) + '">×</button></div>').join("") : "";
}

function saveTodosSoon(delay = 0) {
  clearTimeout(todoSaveTimer);
  state.dirty = true;
  renderStatus();
  const folder = state.folder;
  todoSaveTimer = setTimeout(() => { if (state.folder === folder) run(saveCurrentStatus); }, delay);
}

function filteredFiles() {
  if (!state.folder) return [];
  const needle = normalize(state.fileQuery.trim());
  const files = state.folder.files.filter((file) =>
    (state.fileType === "all" || file.type === state.fileType) &&
    (!needle || normalize(file.name + " " + file.folder).includes(needle)));
  if (state.fileSort === "modified") files.sort((a, b) => b.modified - a.modified);
  if (state.fileSort === "name") files.sort((a, b) => a.name.localeCompare(b.name, "ru", { numeric: true }));
  return files;
}

function fileCard(file) {
  const url = apiUrl("/api/preview", file.path);
  const media = file.preview === "image"
    ? '<img src="' + escapeHtml(url) + '" alt="" loading="lazy" decoding="async"><span class="thumbnail-fallback">' + icon("file") + '<small>' + escapeHtml(file.extension) + "</small></span>"
    : '<span class="file-symbol">' + icon("file") + '<span>' + escapeHtml(file.extension) + "</span></span>";
  return '<article class="file-card type-' + file.type + (state.selectedFiles.has(file.path) ? ' selected' : '') + '"><label class="file-select-label"><input type="checkbox" class="file-select" data-select-file="' + escapeHtml(file.path) + '" aria-label="Выбрать файл: ' + escapeHtml(file.name) + '"' + (state.selectedFiles.has(file.path) ? ' checked' : '') + '></label><button class="file-main" data-file="' + escapeHtml(file.path) + '" title="' +
    escapeHtml(file.name + (file.folder ? "\n" + file.folder : "")) + '" aria-label="' + escapeHtml(file.name) + '"><div class="file-thumbnail">' + media +
    '</div><span class="file-name">' + escapeHtml(file.name) + '</span>' + (file.comment?.trim() ? '<span class="file-comment-caption">' + escapeHtml(file.comment) + '</span>' : '') + '</button></article>';
}

function updateFileCommentCaption(path, text) {
  const file = state.folder?.files.find((item) => item.path === path);
  if (file) file.comment = text;
  const button = [...$("files").querySelectorAll("[data-file]")].find((item) => item.dataset.file === path);
  if (!button) return;
  let caption = button.querySelector(".file-comment-caption");
  if (!text.trim()) { caption?.remove(); return; }
  if (!caption) {
    caption = document.createElement("span");
    caption.className = "file-comment-caption";
    button.appendChild(caption);
  }
  caption.textContent = text;
}

function renderFiles() {
  const files = filteredFiles();
  const available = new Set(state.folder.files.map((file) => file.path));
  for (const path of state.selectedFiles) if (!available.has(path)) state.selectedFiles.delete(path);
  renderFileActions();
  $("fileCount").textContent = files.length;
  $("fileFilters").innerHTML = Object.entries(typeLabels)
    .filter(([type]) => type === "all" || state.folder.counts[type] > 0)
    .map(([type, label]) => '<button class="file-filter' + (state.fileType === type ? " active" : "") +
      '" data-type="' + type + '" aria-pressed="' + (state.fileType === type) + '">' + label + '<span>' +
      (type === "all" ? state.folder.fileCount : state.folder.counts[type]) + "</span></button>").join("");
  if (!files.length) {
    $("files").innerHTML = '<div class="empty-state">' + icon(state.folder.path ? "file" : "folder") +
      "<h3>" + (state.folder.fileCount ? "Ничего не найдено" : state.folder.path ? "В этой папке пока нет файлов" : "Откройте папку клиента") +
      "</h3><p>" + (state.folder.fileCount ? "Попробуйте другой запрос или тип файла" : "Выберите папку в дереве слева или выше") + "</p></div>";
    return;
  }
  const groups = new Map();
  for (const file of files.slice(0, state.limit)) {
    const key = state.fileSort === "folders" ? file.folder : "";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(file);
  }
  $("files").innerHTML = [...groups.entries()].map(([folder, group]) => {
    const path = [state.folder.path, folder].filter(Boolean).join("/");
    return '<section class="file-group">' +
      (state.fileSort === "folders" ? '<button class="file-group-heading" data-path="' + escapeHtml(path) + '">' +
        icon("folder") + "<span>" + escapeHtml(folder || "В выбранной папке") + '</span><small>' + group.length + "</small></button>" : "") +
      '<div class="file-grid">' + group.map(fileCard).join("") + "</div></section>";
  }).join("") + (files.length > state.limit ? '<button id="loadMoreFiles" class="load-more">Показать ещё · осталось ' + (files.length - state.limit) + "</button>" : "");
  $("files").querySelectorAll("img").forEach((image) => image.addEventListener("error", () => {
    image.hidden = true;
    image.parentElement.classList.add("preview-unavailable");
  }, { once: true }));
}

function renderFileActions() {
  const selected = state.folder.files.filter((file) => state.selectedFiles.has(file.path));
  const images = selected.filter((file) => file.type === "images");
  const visible = filteredFiles();
  const visibleSelected = visible.filter((file) => state.selectedFiles.has(file.path)).length;
  $("selectAllFiles").checked = visible.length > 0 && visibleSelected === visible.length;
  $("selectAllFiles").indeterminate = visibleSelected > 0 && visibleSelected < visible.length;
  $("selectAllFiles").disabled = !visible.length;
  $("fileSelectionCount").textContent = "Выбрано: " + selected.length + (selected.length ? " · изображений: " + images.length : "");
  $("clearFileSelection").hidden = !selected.length;
  const report = state.imageReport?.folder === state.folder ? state.imageReport : null;
  $("createImageReport").disabled = !images.length || Boolean(report?.busy);
  $("deleteSelectedFiles").disabled = !selected.length || Boolean(report?.busy) || state.fileRemoving;
  $("createImageReport").textContent = report?.busy ? "Формирую PDF…" : "PDF-отчёт";
  $("fileReportState").classList.toggle("error", Boolean(report?.error));
  $("fileReportState").textContent = report?.error || (report?.result ? "Сохранён: " + report.result.name + (report.result.skippedCount ? " · пропущено файлов других типов: " + report.result.skippedCount : "") : "");
  $("openImageReport").hidden = !report?.result;
  if (report?.result && !state.folder.files.some((file) => file.path === report.result.path)) $("openImageReport").hidden = true;
}

async function confirmFileRemoval() {
  if (state.fileRemoving || state.imageReport?.busy) return;
  const folder = state.folder;
  const selected = folder.files.filter((file) => state.selectedFiles.has(file.path)).map((file) => file.path);
  if (!selected.length) return;
  const preview = await request("/api/files-trash-preview", { path: folder.path, files: selected });
  if (state.folder !== folder) return;
  state.fileRemoval = { ...preview, folder };
  $("deleteFilesCount").textContent = "Выбрано файлов: " + preview.files.length + ". Включая файлы, скрытые текущим фильтром.";
  $("deleteFilesList").innerHTML = preview.files.map((file) => '<li>' + escapeHtml(file.path) + '</li>').join("");
  $("confirmDeleteFiles").disabled = false;
  $("cancelDeleteFiles").disabled = false;
  $("deleteFilesDialog").showModal();
}

async function removeSelectedFiles() {
  const removal = state.fileRemoval;
  if (!removal || state.fileRemoving) return;
  state.fileRemoving = true;
  $("confirmDeleteFiles").disabled = true;
  $("cancelDeleteFiles").disabled = true;
  $("confirmDeleteFiles").textContent = "Перемещаю…";
  try {
    const result = await request("/api/files-trash", { path: removal.folder.path, files: removal.files, confirmed: true });
    $("deleteFilesDialog").close();
    if (state.folder === removal.folder) {
      for (const path of result.removed) state.selectedFiles.delete(path);
      await loadOrderFiles(removal.folder.path, state.navigation);
      $("fileTrashState").classList.toggle("error", Boolean(result.error));
      $("fileTrashState").textContent = "В корзине: " + result.removed.length + (result.error ? ". Операция остановлена: " + result.error : ". Доступно восстановление.");
    }
    notify(result.error ? "Перемещение остановлено: " + result.error : "Файлы перемещены в корзину менеджера", Boolean(result.error));
  } finally {
    state.fileRemoving = false;
    $("confirmDeleteFiles").disabled = false;
    $("cancelDeleteFiles").disabled = false;
    $("confirmDeleteFiles").textContent = "В корзину";
    if (state.folder) renderFileActions();
  }
}

async function loadFileTrash() {
  const data = await request("/api/files-trash-list", {});
  $("fileTrashList").innerHTML = data.sessions.map((session) => '<section class="file-trash-session"><strong>' +
    escapeHtml(new Date(session.created).toLocaleString("ru", { timeZone: "Europe/Moscow" })) + ' · файлов: ' + session.count + '</strong><p>' + escapeHtml(session.folder) +
    '</p><ul class="file-operation-list">' + session.files.map((path) => '<li>' + escapeHtml(path) + '</li>').join("") + '</ul><button class="secondary-button" data-restore-session="' + session.session + '">Восстановить</button></section>').join("") || '<p>Корзина пуста.</p>';
}

async function openFileTrash() {
  $("fileTrashDialogState").textContent = "";
  await loadFileTrash();
  if (!$("fileTrashDialog").open) $("fileTrashDialog").showModal();
}

async function restoreFileSession(session) {
  if (state.trashRestoring) return;
  state.trashRestoring = true;
  $("fileTrashList").querySelectorAll("button").forEach((button) => { button.disabled = true; });
  const folder = state.folder;
  try {
    const result = await request("/api/files-trash-restore", { session });
    await loadFileTrash();
    if (folder && state.folder === folder) await loadOrderFiles(folder.path, state.navigation);
    $("fileTrashDialogState").classList.toggle("error", Boolean(result.error));
    $("fileTrashDialogState").textContent = result.error || "Файлы и комментарии восстановлены.";
    if (folder && state.folder === folder) {
      $("fileTrashState").classList.toggle("error", Boolean(result.error));
      $("fileTrashState").textContent = result.error || "Файлы восстановлены.";
    }
  } finally {
    state.trashRestoring = false;
    $("fileTrashList").querySelectorAll("button").forEach((button) => { button.disabled = false; });
  }
}

async function createImageReport() {
  const folder = state.folder;
  if (!folder || state.imageReport?.busy) return;
  const files = filteredFiles();
  const ordered = [...files, ...folder.files.filter((file) => !files.includes(file))].filter((file) => state.selectedFiles.has(file.path)).map((file) => file.path);
  if (!ordered.length) return;
  const report = state.imageReport = { folder, busy: true, result: null, error: "" };
  renderFileActions();
  try {
    report.result = await request("/api/image-report", { path: folder.path, files: ordered });
    if (state.folder === folder) await loadOrderFiles(folder.path, state.navigation);
    notify("PDF-отчёт сохранён: " + report.result.name);
  } catch (error) {
    report.error = error.message;
    throw error;
  } finally {
    report.busy = false;
    if (state.folder === folder) renderFileActions();
  }
}

function printFiles() {
  const needle = normalize(state.printQuery.trim());
  return state.folder.files.filter((file) => !needle || normalize(file.name + " " + file.folder).includes(needle))
    .sort((a, b) => b.modified - a.modified || b.name.localeCompare(a.name, "ru", { numeric: true }));
}

function renderPrintList() {
  $("printTaskCount").textContent = state.folder.fileCount;
  const files = printFiles();
  $("printTaskList").innerHTML = files.map((file) => '<button class="print-task-button' +
    (state.printTask?.path === file.path ? " active" : "") + '" data-task="' + escapeHtml(file.path) +
    '" title="' + escapeHtml(file.name) + '"><span>' + icon("file") + '<strong>' +
    escapeHtml(file.name.replace(/\.(textClipping|txt|text|md|rtf)$/i, "")) + '</strong></span><small>' +
    formatDate(file.modified) + (file.folder ? " · " + escapeHtml(file.folder) : "") + '</small></button>').join("") ||
    '<p class="tree-empty">' + (state.folder.fileCount ? "Задания не найдены" : "Заданий пока нет") + "</p>";
}

function renderPrintSaveState() {
  const task = state.printTask;
  if (!task) return;
  $("printTaskName").textContent = task.name;
  $("printSaveState").textContent = state.printSaving ? "Сохраняю…" : task.isNew ? "Новое задание · файл появится после сохранения" : task.dirty ? "Есть несохранённые изменения" : "Все изменения сохранены";
  $("printSaveState").classList.toggle("unsaved", Boolean(task.dirty));
  $("savePrintTask").textContent = task.isNew ? "Создать задание" : "Сохранить";
  $("savePrintTask").disabled = Boolean(state.printSaving);
  const link = $("printLink").value.trim();
  try {
    const url = new URL(link);
    const valid = ["http:", "https:"].includes(url.protocol);
    $("openPrintLink").hidden = !valid;
    if (valid) $("openPrintLink").href = url.href;
  } catch { $("openPrintLink").hidden = true; }
}

function showPrintTask(task) {
  state.printTask = { ...task, dirty: false };
  $("printTitle").value = task.title;
  $("printLink").value = task.link;
  $("printDescription").value = task.description;
  $("printEditorForm").hidden = false;
  $("printEditorEmpty").hidden = true;
  renderPrintList();
  renderPrintSaveState();
}

function renderNewOrderName() {
  const date = $("newOrderDate").value || "ГГГГ-ММ-ДД";
  const title = $("newOrderTitle").value.trim() || "Название заказа";
  $("newOrderFolderName").textContent = date + " - " + title;
}

function openCreateOrderFolder() {
  if (state.folder?.canCreateOrderFolder !== true) return;
  state.newOrderParent = state.folder.path;
  const parts = Object.fromEntries(new Intl.DateTimeFormat("ru-RU", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date()).map((part) => [part.type, part.value]));
  $("newOrderDate").value = parts.year + "-" + parts.month + "-" + parts.day;
  $("newOrderTitle").value = "";
  $("newOrderParent").textContent = state.newOrderParent;
  $("newOrderError").hidden = true;
  renderNewOrderName();
  $("createOrderFolderDialog").showModal();
  $("newOrderTitle").focus();
}

async function createOrderFolder() {
  if (state.creatingOrderFolder || !$("createOrderFolderForm").reportValidity()) return;
  state.creatingOrderFolder = true;
  const controls = ["submitCreateOrderFolder", "cancelCreateOrderFolder", "newOrderDate", "newOrderTitle"];
  controls.forEach((id) => { $(id).disabled = true; });
  $("submitCreateOrderFolder").textContent = "Создаю…";
  $("newOrderError").hidden = true;
  let created;
  try {
    await saveCurrentStatus();
    created = await request("/api/order-folder-create", { path: state.newOrderParent, date: $("newOrderDate").value, title: $("newOrderTitle").value });
  } catch (error) {
    $("newOrderError").textContent = error.message;
    $("newOrderError").hidden = false;
    return;
  } finally {
    state.creatingOrderFolder = false;
    controls.forEach((id) => { $(id).disabled = false; });
    $("submitCreateOrderFolder").textContent = "Создать папку";
  }
  $("createOrderFolderDialog").close();
  await loadTree();
  await navigate(created.path);
  notify("Папка заказа создана");
}

function renderNewEventName() {
  $("newEventFolderName").textContent = (state.eventPlan?.next_number || "00") + " - " + ($("newEventTitle").value.trim() || "Название события");
}

function renderEventProposal(previous = new Map()) {
  const suggestions = state.eventPlan.suggestions;
  $("eventRenameSection").hidden = !suggestions.length;
  $("confirmEventRenames").checked = false;
  $("eventRenameList").innerHTML = suggestions.map((item) => {
    const title = previous.get(item.source) ?? item.title;
    return '<div class="event-rename-row" data-number="' + item.number + '"><p class="event-old-name">' + escapeHtml(item.source) + '</p>' +
      '<label>Название события<input data-event-source="' + escapeHtml(item.source) + '" aria-label="Название для ' + escapeHtml(item.source) + '" type="text" maxlength="240" required value="' + escapeHtml(title) + '" placeholder="Укажите название"></label>' +
      '<p class="new-order-preview">→ <strong>' + escapeHtml(item.number + ' - ' + (title || 'Название события')) + '</strong></p></div>';
  }).join("");
  renderNewEventName();
}

async function openCreateEventFolder() {
  if (state.folder?.canCreateEventFolder !== true) return;
  const path = state.folder.path;
  const plan = await request(apiUrl("/api/event-folders", path));
  if (state.folder?.path !== path) return;
  state.eventPlan = plan;
  $("newEventParent").textContent = path;
  $("newEventTitle").value = "";
  $("eventFolderError").hidden = true;
  renderEventProposal();
  $("createEventFolderDialog").showModal();
  $("newEventTitle").focus();
}

async function eventAction(action) {
  if (state.eventBusy) return;
  const form = action === "create" ? $("createEventFolderForm") : $("renameEventFoldersForm");
  if (!form.reportValidity()) return;
  state.eventBusy = true;
  const controls = $("createEventFolderDialog").querySelectorAll("input, button");
  controls.forEach((control) => { control.disabled = true; });
  $("eventFolderError").hidden = true;
  let created;
  try {
    await saveCurrentStatus();
    const plan = state.eventPlan;
    if (action === "create") {
      created = await request("/api/event-folder-create", { path: plan.path, revision: plan.revision, title: $("newEventTitle").value });
    } else {
      const names = [...$("eventRenameList").querySelectorAll("input")].map((input) => ({ source: input.dataset.eventSource, title: input.value }));
      await request("/api/event-folders-rename", { path: plan.path, revision: plan.revision, names, confirmed: $("confirmEventRenames").checked });
      state.eventPlan = await request(apiUrl("/api/event-folders", plan.path));
      renderEventProposal();
      await loadTree();
      await navigate(plan.path, { history: false });
      notify("Папки событий переименованы");
    }
  } catch (error) {
    $("eventFolderError").textContent = error.message;
    $("eventFolderError").hidden = false;
  } finally {
    state.eventBusy = false;
    controls.forEach((control) => { control.disabled = false; });
  }
  if (created) {
    $("createEventFolderDialog").close();
    await loadTree();
    await navigate(created.path);
    notify("Событие создано");
  }
}

async function refreshEventProposal() {
  if (state.eventBusy) return;
  const previous = new Map([...$("eventRenameList").querySelectorAll("input")].map((input) => [input.dataset.eventSource, input.value]));
  state.eventPlan = await request(apiUrl("/api/event-folders", state.eventPlan.path));
  $("eventFolderError").hidden = true;
  renderEventProposal(previous);
}

async function openPrintTask(path) {
  await saveCurrentPrintTask();
  const version = ++printReadVersion;
  $("printEditorForm").hidden = true;
  $("printEditorEmpty").hidden = false;
  $("printEditorEmpty").textContent = "Загрузка задания…";
  try {
    const task = await request(apiUrl("/api/print-task", path));
    if (version !== printReadVersion || state.folder.view !== "print") return;
    showPrintTask(task);
    const url = new URL(location.href);
    url.searchParams.set("task", task.path);
    window.history.replaceState(null, "", url.pathname + url.search);
  } catch (error) {
    if (version === printReadVersion) {
      $("printEditorEmpty").textContent = error.message;
      if (state.printTask) $("printEditorForm").hidden = false;
    }
    throw error;
  }
}

async function newPrintTask() {
  await saveCurrentPrintTask();
  ++printReadVersion;
  showPrintTask({ path: "", name: state.folder.newFileName, title: "", link: "", description: "", isNew: true });
  const url = new URL(location.href);
  url.searchParams.delete("task");
  window.history.replaceState(null, "", url.pathname + url.search);
  $("printTitle").focus();
}

async function saveCurrentPrintTask(force = false) {
  if (state.printSaving) {
    await state.printSaving;
    if (state.printTask?.dirty) return saveCurrentPrintTask(force);
    return;
  }
  const task = state.printTask;
  if (!task || (!task.dirty && !(force && task.isNew))) return;
  if (!$("printLink").checkValidity()) {
    $("printLink").reportValidity();
    throw new Error("Проверьте ссылку на файлы");
  }
  const title = $("printTitle").value.trim(), link = $("printLink").value.trim(), description = $("printDescription").value;
  const folder = state.folder.path;
  state.printSaving = (async () => {
    const saved = await request(task.isNew ? "/api/print-create" : "/api/print-save", {
      path: task.isNew ? folder : task.path, revision: task.revision, title, link, description,
    });
    if (state.printTask === task) {
      Object.assign(task, saved, { isNew: false });
      task.dirty = $("printTitle").value.trim() !== saved.title || $("printLink").value.trim() !== saved.link || $("printDescription").value !== saved.description;
      const url = new URL(location.href);
      url.searchParams.set("task", saved.path);
      window.history.replaceState(null, "", url.pathname + url.search);
    }
    const refreshed = await request(apiUrl("/api/folder", folder));
    Object.assign(state.folder, refreshed, { note: state.folder.note });
    $("folderSummary").textContent = printCountLabel(state.folder.fileCount) + " · название, ссылка и описание";
    renderPrintList();
  })();
  renderPrintSaveState();
  try {
    await state.printSaving;
  } finally {
    state.printSaving = null;
    renderPrintSaveState();
  }
}

async function saveCurrentStatus() {
  if (state.saving) {
    await state.saving;
    if (state.dirty) return saveCurrentStatus();
    return;
  }
  if (!state.dirty || !state.folder) return;
  const folder = state.folder;
  const values = currentOrderValues();
  const status = values.status, note = values.note;
  $("saveStatusButton").disabled = true;
  $("saveStatusButton").textContent = "Сохраняю…";
  const noteOnly = folder.service || folder.noteOnly;
  state.saving = request(folder.folderNote ? "/api/folder-note-save" : noteOnly ? "/api/note" : folder.order ? "/api/order-save" : "/api/status", folder.folderNote
    ? { path: folder.path, revision: folder.folderNote.revision, ...values }
    : noteOnly
    ? { path: folder.path, note }
    : folder.order ? { path: folder.path, revision: folder.order.revision, ...values }
      : { path: folder.path, status, financial_status: values.financial_status, note, ...(values.todo_items ? { todo_items: values.todo_items } : {}) });
  renderStatus();
  try {
    const saved = await state.saving;
    if (!noteOnly) { folder.status = status; folder.financial_status = values.financial_status; }
    folder.note = note;
    folder.statusSource = folder.order || folder.folderNote ? "database" : "manual";
    if (folder.order) folder.order = saved;
    if (folder.folderNote) folder.folderNote = saved;
    state.dirty = JSON.stringify(currentOrderValues()) !== JSON.stringify(values);
    renderExportState();
    renderStatus();
  } finally {
    state.saving = null;
    $("saveStatusButton").disabled = false;
    renderStatus();
  }
}

const rubles = (value) => value == null ? "—" : new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 2 }).format(value / 100);

function currentOrderValues() {
  if (state.folder?.service || state.folder?.noteOnly) return { note: $("orderNote").value,
    ...(state.folder.folderNote && Array.isArray(state.folder.todo_items) ? { todo_items: state.folder.todo_items.map((item) => ({ ...item })) } : {}) };
  return { status: $("statusSelect").value, financial_status: $("financialStatusSelect").value, note: $("orderNote").value, title: $("orderTitleInput").value,
    ...(Array.isArray(state.folder?.todo_items) ? { todo_items: state.folder.todo_items.map((item) => ({ ...item })) } : {}),
    amount: $("orderAmount").value, costs: $("orderCosts").value, paid: $("orderPaid").value };
}

function renderOrderCalculated() {
  const read = (id) => {
    const text = $(id).value.replace(/[\s\u00a0]/g, "").replace(",", ".");
    return text && /^\d+(\.\d{1,2})?$/.test(text) ? Math.round(Number(text) * 100) : null;
  };
  const amount = read("orderAmount"), costs = read("orderCosts"), paid = read("orderPaid");
  $("orderProfit").textContent = rubles(amount != null && costs != null ? amount - costs : null);
  $("orderDebt").textContent = rubles(amount != null && paid != null ? amount - paid : null);
}

function renderExportState() {
  const order = state.folder?.order;
  $("orderExportState").textContent = !order ? "" : order.sync_error ? "Сохранено в базе. Не удалось выгрузить в папку: " + order.sync_error : order.sync_pending ? "Сохранено в базе · ожидает выгрузки в папку" : "Выгружено в !.txt";
}

async function loadOrders() {
  const version = ++state.ordersRequest;
  const result = await request("/api/orders");
  if (version !== state.ordersRequest) return;
  state.orders = result.orders;
  state.unregistrations = result.unregistrations || [];
  state.scan = result.scan;
  $("ordersNavCount").textContent = result.orders.length;
  if (state.view === "orders") renderOrders();
}

function orderTodoText(order) {
  return (order.todo_groups || []).map((group) => [group.label, ...(group.items || []).map((item) => item.text)].join(" ")).join(" ");
}

function renderOrderTodos(order) {
  const groups = order.todo_groups || [];
  const items = groups.flatMap((group) => group.items || []);
  const catalog = order.todo_index;
  const warning = catalog?.error ? "Сохранённые задачи · обновление папок: " + catalog.error : !catalog?.checked ? "Задачи папок обновляются…" : "";
  if (!groups.length && !warning) return "";
  return '<div class="order-todos" aria-label="To-do заказа и вложенных папок">' +
    (groups.length ? '<div class="order-todos-heading">To-do' + (items.length ? ' <span>' + items.length + '</span>' : '') + '</div>' : "") +
    groups.map((group) => '<section class="order-todo-group"><button class="order-todo-folder" data-order="' + escapeHtml(group.path) + '" title="' + escapeHtml(group.path) + '">' + escapeHtml(group.label) + '</button>' +
      (group.items === null ? '<small class="order-todo-state">Прежние записи задач — просмотрите в папке</small>' :
        '<ul>' + group.items.map((item) => '<li' + (item.done ? ' class="done"' : '') + '><span aria-hidden="true">' + (item.done ? '✓' : '○') + '</span><span class="visually-hidden">' + (item.done ? 'Выполнено: ' : 'Нужно сделать: ') + '</span><span class="order-todo-text">' + escapeHtml(item.text) + '</span></li>').join("") + '</ul>') +
      (group.sync_pending ? '<small class="order-todo-state">' + escapeHtml(group.sync_error ? "Сохранено в базе · выгрузка: " + group.sync_error : "Сохранено в базе · ожидает выгрузки") + '</small>' : "") + '</section>').join("") +
    (warning ? '<small class="order-todo-state">' + escapeHtml(warning) + '</small>' : '') + '</div>';
}

function renderOrders() {
  const needle = normalize(state.orderQuery.trim());
  const matching = state.orders.filter((order) => !needle || normalize([order.title, order.path, order.note, orderTodoText(order)].join(" ")).includes(needle));
  const productionMatching = matching.filter((order) => state.financialFilter === "all" || order.financial_status === state.financialFilter);
  const financeMatching = matching.filter((order) => state.orderFilter === "all" || order.status === state.orderFilter);
  const filtered = productionMatching.filter((order) => state.orderFilter === "all" || order.status === state.orderFilter);
  const { orderSort: key, orderDirection: direction } = state;
  filtered.sort((a, b) => {
    if (a[key] == null) return b[key] == null ? 0 : 1;
    if (b[key] == null) return -1;
    const labels = key === "status" ? statusLabels : key === "financial_status" ? financialStatusLabels : null;
    const first = labels ? labels[a[key]] : a[key];
    const second = labels ? labels[b[key]] : b[key];
    return direction * (typeof first === "string" ? first.localeCompare(second, "ru", { numeric: true }) : first - second);
  });
  $("folderSummary").textContent = filtered.length + " из " + state.orders.length + " заказов · данные из локальной базы";
  $("orderStatusFilters").innerHTML = Object.entries({ all: "Все", ...statusLabels }).map(([status, label]) =>
    '<button data-status="' + status + '" aria-pressed="' + (state.orderFilter === status) + '" class="file-filter' + (state.orderFilter === status ? " active" : "") + '">' + label + '<span>' + productionMatching.filter((order) => status === "all" || order.status === status).length + '</span></button>').join("");
  $("financialStatusFilter").innerHTML = Object.entries({ all: "Все", ...financialStatusLabels }).map(([status, label]) =>
    '<option value="' + status + '">' + label + ' · ' + financeMatching.filter((order) => status === "all" || order.financial_status === status).length + '</option>').join("");
  $("financialStatusFilter").value = state.financialFilter;
  $("orderTotals").innerHTML = [["amount", "Сумма заказов"], ["costs", "Затраты"], ["profit", "Расчётная прибыль"], ["paid", "Оплачено"], ["debt", "Остаток оплаты"]].map(([field, label]) => {
    const known = filtered.filter((order) => order[field] != null);
    const total = known.reduce((sum, order) => sum + order[field], 0);
    return '<div class="order-total"><span>' + label + '</span><strong>' + rubles(known.length ? total : null) + '</strong><small>' + (known.length === filtered.length && filtered.length ? "По всем выбранным заказам" : "Указано: " + known.length + " из " + filtered.length) + '</small></div>';
  }).join("");
  $("ordersTableBody").innerHTML = filtered.map((order) => '<tr><td><button class="order-row-link" data-order="' + escapeHtml(order.path) + '">' + escapeHtml(order.title) + '</button><span class="order-row-path">' + escapeHtml(order.path) + '</span>' + renderOrderTodos(order) + '</td><td><span class="status-badge" data-status="' + escapeHtml(order.status) + '">' + escapeHtml(statusLabels[order.status] || order.status) + '</span></td><td><span class="status-badge" data-financial-status="' + escapeHtml(order.financial_status) + '">' + escapeHtml(financialStatusLabels[order.financial_status] || "Не указан") + '</span></td>' +
    ["amount", "costs", "profit", "paid", "debt"].map((field) => '<td class="order-money' + (order[field] < 0 ? " negative" : "") + '">' + rubles(order[field]) + '</td>').join("") +
    '<td class="order-updated">' + formatDate(order.updated) + (order.sync_pending ? '<span class="sync-pending" title="' + escapeHtml(order.sync_error || "Ожидает выгрузки в папку") + '">' + (order.sync_error ? "Ошибка выгрузки" : "Ожидает выгрузки") + '</span>' : '<span class="sync-complete">Выгружено</span>') + '</td></tr>').join("");
  $("ordersEmpty").hidden = Boolean(filtered.length);
  $("ordersEmptyTitle").textContent = state.orders.length ? "Нет заказов по этому фильтру" : "Заказов пока нет";
  $("ordersEmptyHint").textContent = state.orders.length ? "Выберите другой статус или измените поисковый запрос." : "Откройте папку в дереве слева и нажмите «Добавить в список заказов». Кнопка «Найти заказы в папках» восстановит карточки из !.txt и прежних файлов статуса.";
  const pending = state.orders.filter((order) => order.sync_pending), errors = pending.filter((order) => order.sync_error);
  const scan = state.scan;
  $("discoverOrdersButton").disabled = Boolean(scan?.running);
  $("ordersSyncState").textContent = scan?.running ? "Поиск карточек в фоне · просмотрено папок: " + scan.folders + " · добавлено: " + scan.added :
    [scan?.folders ? "Поиск завершён: добавлено " + scan.added + (scan.errors.length ? ", ошибок: " + scan.errors.length : "") : "", errors.length ? "Не выгружено из-за ошибки: " + errors.length : pending.length ? "Ожидает выгрузки: " + pending.length : "Изменения выгружены в папки"].filter(Boolean).join(" · ");
  if (scan?.errors.length) $("ordersSyncState").textContent += " · " + scan.errors.slice(0, 3).join(" · ");
  if (state.unregistrations.length) $("ordersSyncState").textContent += " · Сохранение снятой регистрации: " + state.unregistrations.length + (state.unregistrations.some((item) => item.sync_error) ? " · есть ошибки, повторим выгрузку" : "");
  $("ordersWorkspace").querySelectorAll("th").forEach((th) => {
    const button = th.querySelector("button"), selected = button.dataset.sort === key;
    th.setAttribute("aria-sort", selected ? direction === 1 ? "ascending" : "descending" : "none");
    button.textContent = button.textContent.replace(/ [↕↑↓]$/, "") + (selected ? direction === 1 ? " ↑" : " ↓" : " ↕");
  });
}

async function showOrders({ history = true } = {}) {
  if ($("previewDialog").open) await closePreview();
  await saveCurrentPrintTask();
  await saveCurrentStatus();
  ++printReadVersion;
  ++state.navigation;
  state.folderRequest?.abort();
  state.view = "orders";
  state.folder = null;
  state.selectedFiles.clear();
  state.imageReport = null;
  state.printTask = null;
  state.selected = "";
  $("folderView").hidden = true;
  $("ordersWorkspace").hidden = false;
  $("openFolderButton").hidden = true;
  $("addOrderButton").hidden = true;
  $("removeOrderButton").hidden = true;
  $("createOrderFolderButton").hidden = true;
  $("createEventFolderButton").hidden = true;
  $("notice").hidden = true;
  $("loadOrderFilesButton").hidden = true;
  $("breadcrumbs").innerHTML = '<button aria-current="page">Все заказы</button>';
  $("folderTitle").textContent = "Все заказы";
  $("clientLabel").textContent = "ЗИГЗАГ · ОБЩИЙ СПИСОК";
  $("scanState").textContent = "";
  $("ordersButton").setAttribute("aria-current", "page");
  document.querySelector(".content-pane").setAttribute("aria-busy", "false");
  if (history) window.history.pushState(null, "", "?view=orders");
  renderTree();
  renderOrders();
  await loadOrders();
}

function openLocation() {
  const params = new URLSearchParams(location.search);
  return params.has("path") ? navigate(params.get("path"), { history: false }) : showOrders({ history: false });
}

async function navigate(path, { history = true } = {}) {
  if ($("previewDialog").open) await closePreview();
  await saveCurrentPrintTask();
  await saveCurrentStatus();
  ++printReadVersion;
  const navigation = ++state.navigation;
  state.folderRequest?.abort();
  state.folderRequest = new AbortController();
  $("scanState").textContent = "Загрузка…";
  document.querySelector(".content-pane").setAttribute("aria-busy", "true");
  try {
    let order = null;
    if (path && !isServiceFolder(path)) {
      try { order = await request(apiUrl("/api/order", path)); }
      catch (error) { if (error.status !== 404) throw error; }
    }
    let data;
    if (order) {
      const parts = path.split("/");
      data = { path, name: parts.at(-1), client: parts[0], status: order.status, financial_status: order.financial_status, note: order.note, todo_items: order.todo_items, order,
        breadcrumbs: [{ name: $("rootLabel").textContent, path: "" }, ...parts.map((name, index) => ({ name, path: parts.slice(0, index + 1).join("/") }))],
        directories: [], files: [], counts: {}, warnings: [], fileCount: 0, folderCount: 0, totalSize: 0, view: "files", filesScope: "events", filesLoading: true };
    } else {
      const response = await fetch(apiUrl("/api/folder", path), { signal: state.folderRequest.signal });
      data = await response.json();
      if (!response.ok) throw new Error(data.error || "Не удалось открыть папку");
    }
    if (navigation !== state.navigation) return;
    data.service = isServiceFolder(data.path);
    if (data.service) {
      delete data.order;
      delete data.status;
    }
    state.view = "folder";
    $("folderView").hidden = false;
    $("ordersWorkspace").hidden = true;
    $("openFolderButton").hidden = false;
    $("ordersButton").removeAttribute("aria-current");
    state.folder = data;
    $("fileTrashState").textContent = "";
    state.selectedFiles.clear();
    state.imageReport = null;
    state.printTask = null;
    state.selected = data.path;
    state.fileType = "all";
    state.fileQuery = "";
    state.limit = 120;
    state.dirty = false;
    if (history) window.history.pushState(null, "", data.path ? "?path=" + encodeURIComponent(data.path) : window.location.pathname);
    renderTree();
    renderFolder();
    document.querySelector(".content-pane").scrollTop = 0;
    $("scanState").textContent = "";
    revealPath(data.path, navigation).catch((error) => notify(error.message, true));
    if (order) run(() => loadOrderFiles(data.path, navigation));
  } catch (error) {
    if (error.name !== "AbortError" && navigation === state.navigation) {
      $("scanState").textContent = "Ошибка загрузки";
      $("notice").textContent = error.message;
      $("notice").hidden = false;
      notify(error.message, true);
    }
  } finally {
    if (navigation === state.navigation) document.querySelector(".content-pane").setAttribute("aria-busy", "false");
  }
}

async function loadOrderFiles(path, navigation) {
  $("loadOrderFilesButton").hidden = true;
  $("scanState").textContent = "Загрузка файлов…";
  try {
    const response = await fetch(apiUrl("/api/folder", path), { signal: state.folderRequest.signal });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Не удалось открыть папку");
    if (navigation !== state.navigation) return;
    const { order, status, financial_status, note, todo_items, noteOnly, registrationPending, registrationError } = state.folder;
    Object.assign(state.folder, data, { order, status, financial_status, note, todo_items, noteOnly, registrationPending, registrationError, filesLoading: false, filesUnavailable: false });
    renderFolder(true);
  } catch (error) {
    if (error.name === "AbortError" || navigation !== state.navigation) return;
    state.folder.filesLoading = false;
    state.folder.filesUnavailable = true;
    state.folder.warnings = ["Карточка доступна из базы. Не удалось загрузить файлы: " + error.message];
    renderFolder(true);
  } finally {
    if (navigation === state.navigation) $("scanState").textContent = "";
  }
}

async function openNative(path, reveal = false) {
  await request("/api/open", { path, reveal });
}

async function showPreview(path) {
  await saveFileComment();
  const file = state.folder.files.find((item) => item.path === path);
  if (!file) return;
  const version = ++previewVersion;
  state.preview = file;
  $("previewTitle").textContent = file.name;
  $("previewPath").textContent = file.folder || state.folder.name;
  $("previewMeta").textContent = file.extension + " · " + formatSize(file.size) + " · " + formatDate(file.modified);
  $("previewDownload").href = apiUrl("/api/file", path, { download: "1" });
  $("previewFolderNotePath").textContent = state.folder.path || state.folder.name;
  $("previewFolderNote").value = $("orderNote").value;
  const files = filteredFiles();
  const index = files.findIndex((item) => item.path === path);
  $("previewPrevious").disabled = index <= 0;
  $("previewNext").disabled = index < 0 || index === files.length - 1;
  $("previewBody").replaceChildren();
  if (!$("previewDialog").open) $("previewDialog").showModal();
  run(() => loadFileComment(path, version));
  const source = apiUrl("/api/file", path);
  let media;
  if (file.preview === "image") {
    media = document.createElement("img");
    media.src = apiUrl("/api/preview", path);
    media.alt = file.name;
    media.addEventListener("error", () => {
      if (version === previewVersion) previewUnavailable("Не удалось показать изображение. Откройте оригинал на Mac.");
    }, { once: true });
  } else if (file.preview === "pdf") {
    $("previewBody").textContent = "Загрузка PDF…";
    try {
      const info = await request(apiUrl("/api/pdf", path));
      if (version !== previewVersion) return;
      if (!info.pages) throw new Error("В PDF нет страниц");
      showPdfPages(file, info.pages, version);
    } catch (error) {
      if (version === previewVersion) previewUnavailable(error.message);
    }
    return;
  } else if (file.preview === "video" || file.preview === "audio") {
    media = document.createElement(file.preview);
    media.controls = true;
    media.preload = "metadata";
    media.src = source;
    media.addEventListener("error", () => {
      if (version === previewVersion) previewUnavailable("Браузер не поддерживает этот формат. Откройте файл на Mac.");
    }, { once: true });
  } else if (file.preview === "text") {
    $("previewBody").textContent = "Загрузка…";
    try {
      const result = await request(apiUrl("/api/text", path));
      if (version !== previewVersion) return;
      media = document.createElement("pre");
      media.textContent = result.text + (result.truncated ? "\n\n… Показаны первые 128 КБ. Скачайте файл целиком." : "");
      $("previewBody").replaceChildren();
    } catch (error) {
      if (version === previewVersion) previewUnavailable(error.message);
      return;
    }
  } else {
    previewUnavailable("Откройте этот файл в установленной программе на Mac.");
    return;
  }
  if (version === previewVersion) $("previewBody").appendChild(media);
}

function renderFileComment() {
  const comment = state.fileComment;
  const saving = Boolean(state.fileCommentSaving);
  $("fileCommentText").disabled = !comment?.loaded || comment.loading;
  $("saveFileComment").disabled = !comment?.loaded || !comment.dirty || saving;
  $("saveFileComment").textContent = saving ? "Сохраняю…" : "Сохранить";
  $("cancelFileComment").hidden = !comment?.dirty;
  $("cancelFileComment").disabled = saving;
  $("reloadFileComment").hidden = !comment?.error || comment.dirty;
  $("fileCommentState").classList.toggle("error", Boolean(comment?.error));
  $("fileCommentState").textContent = comment?.error || (comment?.loading ? "Загрузка комментария…" : saving ? "Сохраняю…" : comment?.dirty ? "Есть несохранённые изменения" : comment?.comment ? "Комментарий сохранён" : "Комментария пока нет");
}

async function loadFileComment(path, version) {
  const comment = state.fileComment = { path, comment: "", draft: "", loaded: false, loading: true, dirty: false, error: "" };
  $("fileCommentText").value = "";
  renderFileComment();
  try {
    const result = await request(apiUrl("/api/file-comment", path));
    if (version !== previewVersion || state.fileComment !== comment) return;
    Object.assign(comment, result, { loaded: true, loading: false, draft: result.comment });
    updateFileCommentCaption(path, result.comment);
    $("fileCommentText").value = result.comment;
  } catch (error) {
    if (version !== previewVersion || state.fileComment !== comment) return;
    comment.loading = false;
    comment.error = "Не удалось прочитать комментарий: " + error.message;
  }
  if (state.fileComment === comment) renderFileComment();
}

async function saveFileComment() {
  if (state.fileCommentSaving) {
    await state.fileCommentSaving;
    if (state.fileComment?.dirty) return saveFileComment();
    return;
  }
  const comment = state.fileComment;
  if (!comment?.loaded || !comment.dirty) return;
  const draft = comment.draft;
  state.fileCommentSaving = request("/api/file-comment", { path: comment.path, comment: draft, revision: comment.revision });
  comment.error = "";
  renderFileComment();
  try {
    const saved = await state.fileCommentSaving;
    Object.assign(comment, { comment: saved.comment, revision: saved.revision, dirty: comment.draft !== saved.comment });
    updateFileCommentCaption(comment.path, saved.comment);
  } catch (error) {
    comment.error = error.message;
    throw error;
  } finally {
    state.fileCommentSaving = null;
    if (state.fileComment === comment) renderFileComment();
  }
  if (comment.dirty) return saveFileComment();
}

async function closePreview() {
  await saveFileComment();
  $("previewDialog").close();
}

function showPdfPages(file, pages, version) {
  const viewer = document.createElement("div");
  viewer.className = "pdf-viewer";
  const toolbar = document.createElement("div");
  toolbar.className = "pdf-toolbar";
  const previous = document.createElement("button"), next = document.createElement("button");
  previous.textContent = "←";
  next.textContent = "→";
  previous.setAttribute("aria-label", "Предыдущая страница");
  next.setAttribute("aria-label", "Следующая страница");
  const label = document.createElement("label");
  label.textContent = "Страница ";
  const input = document.createElement("input");
  input.type = "number";
  input.min = "1";
  input.max = String(pages);
  input.setAttribute("aria-label", "Номер страницы");
  label.append(input, document.createTextNode(" из " + pages));
  toolbar.append(previous, label, next);
  const canvas = document.createElement("div");
  canvas.className = "pdf-page";
  const image = document.createElement("img");
  canvas.append(image);
  viewer.append(toolbar, canvas);
  let current = 0;
  function changePage(page) {
    current = Math.min(pages - 1, Math.max(0, page));
    input.value = String(current + 1);
    previous.disabled = current === 0;
    next.disabled = current === pages - 1;
    image.alt = "Страница " + (current + 1) + " · " + file.name;
    image.src = apiUrl("/api/pdf-page", file.path, { page: current });
    canvas.scrollTop = 0;
  }
  image.addEventListener("error", () => {
    if (version === previewVersion) previewUnavailable("Не удалось показать страницу PDF. Откройте оригинал на Mac.");
  });
  previous.addEventListener("click", () => changePage(current - 1));
  next.addEventListener("click", () => changePage(current + 1));
  input.addEventListener("change", () => changePage((Number(input.value) || 1) - 1));
  $("previewBody").replaceChildren(viewer);
  changePage(0);
}

function previewUnavailable(message) {
  const wrapper = document.createElement("div");
  wrapper.className = "preview-empty";
  const label = document.createElement("strong");
  label.textContent = state.preview.extension;
  const text = document.createElement("p");
  text.textContent = message;
  const button = document.createElement("button");
  button.className = "primary-button";
  button.textContent = "Открыть на Mac";
  button.addEventListener("click", () => run(() => openNative(state.preview.path)));
  wrapper.append(label, text, button);
  $("previewBody").replaceChildren(wrapper);
}

function stepPreview(direction) {
  if (!state.preview) return;
  const files = filteredFiles();
  const index = files.findIndex((item) => item.path === state.preview.path);
  if (files[index + direction]) run(() => showPreview(files[index + direction].path));
}

function run(action) {
  Promise.resolve().then(action).catch((error) => notify(error.message || "Не удалось выполнить действие", true));
}

$("folderTree").addEventListener("click", (event) => {
  const row = event.target.closest(".tree-row");
  if (!row) return;
  const path = row.dataset.path;
  if (event.target.closest(".tree-toggle")) run(() => toggleFolder(path));
  else run(async () => {
    await navigate(path);
    if (!state.treeQuery && state.nodes.get(path)?.hasChildren && !state.expanded.has(path)) await toggleFolder(path, true);
  });
});
$("folderTree").addEventListener("keydown", (event) => {
  const row = event.target.closest(".tree-row");
  if (!row) return;
  const path = row.dataset.path;
  const rows = [...$("folderTree").querySelectorAll(".tree-row")], index = rows.indexOf(row);
  if (!["ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Home", "End", "Enter", " "].includes(event.key)) return;
  event.preventDefault();
  if (event.key === "ArrowDown") focusTree(rows[Math.min(index + 1, rows.length - 1)].dataset.path);
  if (event.key === "ArrowUp") focusTree(rows[Math.max(index - 1, 0)].dataset.path);
  if (event.key === "Home") focusTree(rows[0].dataset.path);
  if (event.key === "End") focusTree(rows[rows.length - 1].dataset.path);
  if (event.key === "Enter" || event.key === " ") run(() => navigate(path));
  if (event.key === "ArrowRight" && row.hasAttribute("aria-expanded")) {
    if (row.getAttribute("aria-expanded") === "true") {
      if (rows[index + 1]) focusTree(rows[index + 1].dataset.path);
    } else run(() => toggleFolder(path, true));
  }
  if (event.key === "ArrowLeft") {
    if (row.getAttribute("aria-expanded") === "true" && !state.treeQuery) run(() => toggleFolder(path));
    else focusTree(folderParent(path));
  }
});
for (const id of ["auxiliaryButtons", "breadcrumbs", "subfolders"]) {
  $(id).addEventListener("click", (event) => {
    const button = event.target.closest("[data-path]");
    if (button) run(() => navigate(button.dataset.path));
  });
}
$("subfolders").addEventListener("click", (event) => {
  const button = event.target.closest("[data-relevance]");
  if (button) run(() => saveEventRelevance(button.dataset.eventPath, button.dataset.relevance));
});
$("treeSearch").addEventListener("input", (event) => {
  state.treeQuery = event.target.value;
  const version = ++treeSearchVersion;
  clearTimeout(searchTimer);
  if (!state.treeQuery.trim()) {
    state.searchTree = null;
    renderTree();
    run(() => revealPath(state.selected, state.navigation));
    return;
  }
  searchTimer = setTimeout(() => run(async () => {
    const result = await request(apiUrl("/api/tree", "", { q: state.treeQuery }));
    if (version !== treeSearchVersion) return;
    state.searchTree = result.children;
    registerNodes(result.children);
    renderTree();
  }), 250);
});
$("files").addEventListener("click", (event) => {
  const native = event.target.closest("[data-native]");
  const file = event.target.closest("[data-file]");
  const folder = event.target.closest("[data-path]");
  if (native) run(() => openNative(native.dataset.native));
  else if (file) run(() => showPreview(file.dataset.file));
  else if (folder) run(() => navigate(folder.dataset.path));
  else if (event.target.closest("#loadMoreFiles")) { state.limit += 120; renderFiles(); }
});
$("files").addEventListener("change", (event) => {
  const input = event.target.closest("[data-select-file]");
  if (!input) return;
  if (input.checked) state.selectedFiles.add(input.dataset.selectFile);
  else state.selectedFiles.delete(input.dataset.selectFile);
  input.closest(".file-card").classList.toggle("selected", input.checked);
  renderFileActions();
});
$("selectAllFiles").addEventListener("change", (event) => {
  for (const file of filteredFiles()) {
    if (event.target.checked) state.selectedFiles.add(file.path);
    else state.selectedFiles.delete(file.path);
  }
  renderFiles();
});
$("clearFileSelection").addEventListener("click", () => { state.selectedFiles.clear(); renderFiles(); });
$("createImageReport").addEventListener("click", () => run(createImageReport));
$("deleteSelectedFiles").addEventListener("click", () => run(confirmFileRemoval));
$("deleteFilesForm").addEventListener("submit", (event) => { event.preventDefault(); run(removeSelectedFiles); });
$("cancelDeleteFiles").addEventListener("click", () => $("deleteFilesDialog").close());
$("deleteFilesDialog").addEventListener("cancel", (event) => { if (state.fileRemoving) event.preventDefault(); });
$("openFileTrash").addEventListener("click", () => run(openFileTrash));
$("closeFileTrash").addEventListener("click", () => $("fileTrashDialog").close());
$("fileTrashList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-restore-session]");
  if (button) run(() => restoreFileSession(button.dataset.restoreSession));
});
$("openImageReport").addEventListener("click", () => run(() => showPreview(state.imageReport.result.path)));
$("fileFilters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-type]");
  if (button) { state.fileType = button.dataset.type; state.limit = 120; renderFiles(); }
});
$("fileSearch").addEventListener("input", (event) => { state.fileQuery = event.target.value; state.limit = 120; renderFiles(); });
$("fileSort").addEventListener("change", (event) => { state.fileSort = event.target.value; state.limit = 120; renderFiles(); });
$("orderStatusFilters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-status]");
  if (button) { state.orderFilter = button.dataset.status; renderOrders(); }
});
$("orderSearch").addEventListener("input", (event) => { state.orderQuery = event.target.value; renderOrders(); });
$("financialStatusFilter").addEventListener("change", (event) => { state.financialFilter = event.target.value; renderOrders(); });
$("ordersTableBody").addEventListener("click", (event) => {
  const button = event.target.closest("[data-order]");
  if (button) run(() => navigate(button.dataset.order));
});
$("ordersWorkspace").querySelector("thead").addEventListener("click", (event) => {
  const button = event.target.closest("[data-sort]");
  if (!button) return;
  state.orderDirection = state.orderSort === button.dataset.sort ? -state.orderDirection : 1;
  state.orderSort = button.dataset.sort;
  renderOrders();
});
$("discoverOrdersButton").addEventListener("click", () => run(async () => {
  state.scan = await request("/api/orders-discover", {});
  await loadOrders();
}));
$("syncOrdersButton").addEventListener("click", () => run(async () => {
  await request("/api/orders-sync", {});
  notify("Выгрузка в папки запущена");
  await loadOrders();
}));
$("refreshTodosButton").addEventListener("click", () => run(async () => {
  await request("/api/todos-refresh", {});
  notify("Обновление задач папок запущено");
  await loadOrders();
}));
$("loadOrderFilesButton").addEventListener("click", () => run(() => loadOrderFiles(state.selected, state.navigation)));
$("addOrderButton").addEventListener("click", () => run(async () => {
  $("addOrderButton").disabled = true;
  try {
    await saveCurrentStatus();
    state.folder.order = await request("/api/order-add", { path: state.folder.path });
    state.folder.note = state.folder.order.note;
    state.folder.status = state.folder.order.status;
    state.folder.financial_status = state.folder.order.financial_status;
    state.folder.todo_items = state.folder.order.todo_items;
    state.folder.noteOnly = false;
    state.folder.registrationPending = false;
    renderFolder();
    notify("Заказ добавлен в общий список");
    await loadOrders();
  } finally { $("addOrderButton").disabled = false; }
}));
function askRemoveOrder(path) {
  const order = state.folder?.path === path ? state.folder.order : state.orders.find((item) => item.path === path);
  if (!order) { notify("Обновите список заказов перед снятием регистрации", true); return; }
  state.removeOrder = { ...order };
  $("removeOrderName").textContent = order.title;
  $("removeOrderPath").textContent = order.path;
  $("removeOrderDialog").showModal();
  $("cancelRemoveOrder").focus();
}
$("removeOrderButton").addEventListener("click", () => askRemoveOrder(state.folder.path));
$("cancelRemoveOrder").addEventListener("click", () => $("removeOrderDialog").close());
$("removeOrderDialog").addEventListener("cancel", (event) => { if (state.removingOrder) event.preventDefault(); });
$("removeOrderDialog").addEventListener("close", () => { state.removeOrder = null; });
$("removeOrderForm").addEventListener("submit", (event) => {
  event.preventDefault();
  if (state.removingOrder || !state.removeOrder) return;
  run(async () => {
    state.removingOrder = true;
    $("confirmRemoveOrder").disabled = true;
    $("cancelRemoveOrder").disabled = true;
    try {
      let order = state.removeOrder;
      if (state.folder?.path === order.path) { await saveCurrentStatus(); order = state.folder.order; }
      const removed = await request("/api/order-remove", { path: order.path, revision: order.revision, confirmed: true });
      if (state.folder?.path === order.path) {
        delete state.folder.order;
        Object.assign(state.folder, { note: removed.note, noteOnly: true, registrationPending: removed.sync_pending, registrationError: removed.sync_error });
        state.dirty = false;
        renderFolder();
      }
      state.orders = state.orders.filter((item) => item.path !== order.path);
      $("ordersNavCount").textContent = state.orders.length;
      if (state.view === "orders") renderOrders();
      $("removeOrderDialog").close();
      notify("Папка убрана из списка заказов");
      await loadOrders();
    } finally {
      state.removingOrder = false;
      $("confirmRemoveOrder").disabled = false;
      $("cancelRemoveOrder").disabled = false;
    }
  });
});
for (const id of ["orderTitleInput", "orderAmount", "orderCosts", "orderPaid"]) {
  $(id).addEventListener("input", () => { state.dirty = true; renderStatus(); renderOrderCalculated(); });
}
setInterval(() => {
  if (document.hidden) return;
  if (state.view !== "orders" && state.folder?.canCreateEventFolder) refreshEventRelevance(state.folder).catch(() => {});
  if (state.view === "orders") loadOrders().catch(() => { $("ordersSyncState").textContent = "Нет связи с сервером · показаны последние загруженные данные"; });
  else if (state.folder?.folderNote && !state.dirty && !state.saving) {
    const folder = state.folder;
    request(apiUrl("/api/folder-note", folder.path)).then((record) => {
      if (state.folder === folder && !state.dirty && !state.saving && record.revision === folder.folderNote.revision) {
        folder.folderNote = record;
        renderStatus();
      }
    }).catch(() => {});
  } else if (state.folder?.order && !state.dirty && !state.saving) {
    const folder = state.folder;
    request(apiUrl("/api/order", folder.path)).then((order) => {
      if (state.folder === folder && !state.dirty && !state.saving && order.revision === folder.order.revision) {
        folder.order = order;
        renderExportState();
      }
    }).catch(() => {});
  }
}, 5000);
$("homeButton").addEventListener("click", () => run(() => showOrders()));
$("ordersButton").addEventListener("click", () => run(() => showOrders()));
$("openFolderButton").addEventListener("click", () => run(() => openNative(state.selected)));
$("createOrderFolderButton").addEventListener("click", openCreateOrderFolder);
$("createEventFolderButton").addEventListener("click", () => run(openCreateEventFolder));
$("newEventTitle").addEventListener("input", renderNewEventName);
$("createEventFolderForm").addEventListener("submit", (event) => { event.preventDefault(); run(() => eventAction("create")); });
$("renameEventFoldersForm").addEventListener("submit", (event) => { event.preventDefault(); run(() => eventAction("rename")); });
$("refreshEventProposal").addEventListener("click", () => run(refreshEventProposal));
$("closeCreateEventFolder").addEventListener("click", () => $("createEventFolderDialog").close());
$("createEventFolderDialog").addEventListener("cancel", (event) => { if (state.eventBusy) event.preventDefault(); });
$("eventRenameList").addEventListener("input", (event) => {
  const row = event.target.closest(".event-rename-row");
  if (row) row.querySelector("strong").textContent = row.dataset.number + " - " + (event.target.value.trim() || "Название события");
  $("confirmEventRenames").checked = false;
});
$("createOrderFolderForm").addEventListener("submit", (event) => { event.preventDefault(); run(createOrderFolder); });
$("cancelCreateOrderFolder").addEventListener("click", () => $("createOrderFolderDialog").close());
$("createOrderFolderDialog").addEventListener("cancel", (event) => { if (state.creatingOrderFolder) event.preventDefault(); });
for (const id of ["newOrderDate", "newOrderTitle"]) $(id).addEventListener("input", renderNewOrderName);
$("refreshButton").addEventListener("click", () => run(async () => {
  $("refreshButton").disabled = true;
  try {
    await saveCurrentStatus();
    ++treeSearchVersion;
    clearTimeout(searchTimer);
    state.searchTree = null;
    state.treeQuery = "";
    $("treeSearch").value = "";
    if (state.view === "orders") await loadOrders();
    else { await loadTree(); await navigate(state.selected, { history: false }); }
  } finally { $("refreshButton").disabled = false; }
}));
$("statusSelect").addEventListener("change", () => { state.dirty = true; renderStatus(); });
$("financialStatusSelect").addEventListener("change", () => { state.dirty = true; renderStatus(); });
$("orderNote").addEventListener("input", () => { state.dirty = true; resizeOrderNote(); renderStatus(); });
$("orderDetails").addEventListener("toggle", resizeOrderNote);
window.addEventListener("resize", resizeOrderNote);
$("todoAddForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const text = $("todoNewText").value.trim();
  if (!text || !Array.isArray(state.folder?.todo_items)) return;
  state.folder.todo_items.push({ text, done: false });
  $("todoNewText").value = "";
  renderTodos(); saveTodosSoon(); $("todoNewText").focus();
});
$("todoList").addEventListener("input", (event) => {
  if (!event.target.matches(".todo-text")) return;
  const row = event.target.closest("[data-todo-index]");
  const item = state.folder.todo_items[Number(row.dataset.todoIndex)];
  item.text = event.target.value;
  row.querySelector(".todo-check").setAttribute("aria-label", "Выполнено: " + item.text);
  row.querySelector(".todo-delete").setAttribute("aria-label", "Удалить задачу: " + item.text);
  saveTodosSoon(700);
});
$("todoList").addEventListener("change", (event) => {
  const row = event.target.closest("[data-todo-index]");
  if (!row) return;
  if (event.target.matches(".todo-check")) {
    state.folder.todo_items[Number(row.dataset.todoIndex)].done = event.target.checked;
    renderTodos(); saveTodosSoon();
  }
});
$("todoList").addEventListener("click", (event) => {
  if (!event.target.closest(".todo-delete")) return;
  state.folder.todo_items.splice(Number(event.target.closest("[data-todo-index]").dataset.todoIndex), 1);
  renderTodos(); saveTodosSoon();
});
$("todoList").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && event.target.matches(".todo-text")) { event.preventDefault(); event.target.blur(); saveTodosSoon(); }
});
$("statusForm").addEventListener("submit", (event) => { event.preventDefault(); run(async () => { await saveCurrentStatus(); notify(state.folder?.folderNote ? "Заметка и задачи сохранены в базе" : state.folder?.service || state.folder?.noteOnly ? "Заметка сохранена" : state.folder?.order ? "Карточка сохранена в базе, выгрузка в папку поставлена в очередь" : "Статус и заметка сохранены"); }); });
$("newPrintTask").addEventListener("click", () => run(newPrintTask));
$("printTaskList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-task]");
  if (button) run(() => openPrintTask(button.dataset.task));
});
$("printTaskSearch").addEventListener("input", (event) => { state.printQuery = event.target.value; renderPrintList(); });
for (const id of ["printTitle", "printLink", "printDescription"]) {
  $(id).addEventListener("input", () => {
    if (!state.printTask) return;
    state.printTask.dirty = $("printTitle").value.trim() !== state.printTask.title || $("printLink").value.trim() !== state.printTask.link || $("printDescription").value !== state.printTask.description;
    renderPrintSaveState();
  });
}
$("printEditorForm").addEventListener("submit", (event) => {
  event.preventDefault();
  run(async () => { await saveCurrentPrintTask(true); notify("Задание сохранено"); });
});
window.addEventListener("keydown", (event) => {
  if ($("previewDialog").open && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
    event.preventDefault(); run(saveFileComment); return;
  }
  if (!$("printWorkspace").hidden && state.printTask && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    run(async () => { await saveCurrentPrintTask(true); notify("Задание сохранено"); });
  }
});
$("previewClose").addEventListener("click", () => run(closePreview));
$("previewDialog").addEventListener("cancel", (event) => { event.preventDefault(); run(closePreview); });
$("previewDialog").addEventListener("close", () => { ++previewVersion; $("previewBody").replaceChildren(); state.preview = null; state.fileComment = null; });
$("fileCommentText").addEventListener("input", () => {
  if (!state.fileComment?.loaded) return;
  state.fileComment.draft = $("fileCommentText").value;
  state.fileComment.dirty = state.fileComment.draft !== state.fileComment.comment;
  renderFileComment();
});
$("fileCommentForm").addEventListener("submit", (event) => { event.preventDefault(); run(saveFileComment); });
$("cancelFileComment").addEventListener("click", () => run(() => loadFileComment(state.preview.path, previewVersion)));
$("reloadFileComment").addEventListener("click", () => run(() => loadFileComment(state.preview.path, previewVersion)));
$("previewPrevious").addEventListener("click", () => stepPreview(-1));
$("previewNext").addEventListener("click", () => stepPreview(1));
$("previewNative").addEventListener("click", () => run(() => openNative(state.preview.path)));
$("previewDialog").addEventListener("keydown", (event) => {
  if (["INPUT", "TEXTAREA"].includes(event.target.tagName)) return;
  if (event.key === "ArrowLeft") { event.preventDefault(); stepPreview(-1); }
  if (event.key === "ArrowRight") { event.preventDefault(); stepPreview(1); }
});
window.addEventListener("popstate", () => run(() => openLocation()));
window.addEventListener("beforeunload", (event) => { if (state.dirty || state.printTask?.dirty || state.printSaving || state.fileComment?.dirty || state.fileCommentSaving) { event.preventDefault(); event.returnValue = ""; } });

run(async () => {
  try {
    run(loadTree);
    await openLocation();
  } catch (error) {
    $("notice").textContent = error.message;
    $("notice").hidden = false;
    $("folderSummary").textContent = "Проверьте путь в manager.ini";
    document.querySelector(".content-pane").setAttribute("aria-busy", "false");
    throw error;
  }
});

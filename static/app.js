const $ = (id) => document.getElementById(id);
const statusLabels = { new: "Новый", measure: "Замеры", process: "В работе", workshop: "В цех", install: "Монтаж", done: "Готово" };
const typeLabels = { all: "Все", images: "Фото", pdf: "PDF", design: "Макеты", docs: "Документы", video: "Видео", audio: "Аудио", other: "Другое" };
const state = {
  tree: [], auxiliary: [], nodes: new Map(), children: new Map(), expanded: new Set(),
  treeQuery: "", searchTree: null, folder: null, selected: "",
  fileQuery: "", fileType: "all", fileSort: "folders", limit: 120,
  folderRequest: null, navigation: 0, preview: null, dirty: false, saving: null,
  printTask: null, printSaving: null, printQuery: "",
};
let searchTimer, toastTimer, previewVersion = 0, treeSearchVersion = 0, printReadVersion = 0;
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

async function request(url, payload) {
  const response = await fetch(url, payload === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Не удалось выполнить действие");
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

function renderFolder() {
  const folder = state.folder;
  const printView = folder.view === "print";
  $("breadcrumbs").innerHTML = folder.breadcrumbs.map((part, index) =>
    (index ? '<span class="breadcrumb-divider">/</span>' : "") +
    '<button data-path="' + escapeHtml(part.path) + '"' + (index === folder.breadcrumbs.length - 1 ? ' aria-current="page"' : "") + ">" +
    escapeHtml(part.name) + "</button>").join("");
  $("folderTitle").textContent = printView ? "Задания на печать" : folder.path ? folder.name : "Клиенты и заказы";
  const auxiliary = folder.client.startsWith("#");
  $("clientLabel").textContent = printView ? "ШИРОКОФОРМАТНАЯ ПРОДУКЦИЯ" : auxiliary ? "ОБЩИЕ ПАПКИ" : folder.client || folder.name;
  $("folderSummary").textContent = printView ? printCountLabel(folder.fileCount) + " · название, ссылка и описание" : folder.path
    ? folder.fileCount + " файлов · " + folder.folderCount + " папок · " + formatSize(folder.totalSize)
    : "Выберите клиента или заказ в дереве слева";
  $("folderSection").hidden = !folder.directories.length;
  $("foldersTitle").textContent = folder.path ? "Подпапки" : "Папки";
  $("directoryCount").textContent = folder.directories.length;
  $("subfolders").innerHTML = folder.directories.map((item) =>
    '<button class="subfolder" data-path="' + escapeHtml(item.path) + '" title="' + escapeHtml(item.name) + '">' +
    icon("folder") + '<span>' + escapeHtml(item.name) + "</span>" + icon("chevron") + "</button>").join("");
  $("orderDetails").hidden = !folder.path || auxiliary;
  $("orderDetails").open = Boolean(folder.note);
  $("statusSelect").value = folder.status;
  $("orderNote").value = folder.note;
  renderStatus();
  $("notice").hidden = !folder.warnings.length;
  $("notice").textContent = folder.warnings.join(" · ");
  $("fileSearch").value = state.fileQuery;
  $("filesSection").hidden = printView;
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

function renderStatus() {
  $("statusBadge").textContent = statusLabels[state.folder.status] || state.folder.status;
  $("statusBadge").dataset.status = state.folder.status;
  $("saveStatusButton").textContent = state.dirty ? "Сохранить изменения" : "Сохранить";
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
  return '<article class="file-card type-' + file.type + '"><button class="file-main" data-file="' + escapeHtml(file.path) + '" title="' +
    escapeHtml(file.name + (file.folder ? "\n" + file.folder : "")) + '"><div class="file-thumbnail">' + media +
    '</div><span class="file-name">' + escapeHtml(file.name) + '</span><span class="file-meta">' + formatSize(file.size) +
    " · " + formatDate(file.modified) + '</span>' +
    (state.fileSort !== "folders" && file.folder ? '<span class="file-location">' + escapeHtml(file.folder) + "</span>" : "") +
    '</button><button class="file-open" data-native="' + escapeHtml(file.path) + '" title="Открыть в установленной программе">Открыть на Mac ↗</button></article>';
}

function renderFiles() {
  const files = filteredFiles();
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
    state.folder = await request(apiUrl("/api/folder", folder));
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
  const status = $("statusSelect").value, note = $("orderNote").value;
  $("saveStatusButton").disabled = true;
  $("saveStatusButton").textContent = "Сохраняю…";
  state.saving = request("/api/status", { path: folder.path, status, note });
  try {
    await state.saving;
    folder.status = status;
    folder.note = note;
    folder.statusSource = "manual";
    state.dirty = $("statusSelect").value !== status || $("orderNote").value !== note;
    renderStatus();
  } finally {
    state.saving = null;
    $("saveStatusButton").disabled = false;
    renderStatus();
  }
}

async function navigate(path, { history = true } = {}) {
  await saveCurrentPrintTask();
  await saveCurrentStatus();
  ++printReadVersion;
  const navigation = ++state.navigation;
  state.folderRequest?.abort();
  state.folderRequest = new AbortController();
  $("scanState").textContent = "Загрузка…";
  document.querySelector(".content-pane").setAttribute("aria-busy", "true");
  try {
    const response = await fetch(apiUrl("/api/folder", path), { signal: state.folderRequest.signal });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Не удалось открыть папку");
    if (navigation !== state.navigation) return;
    state.folder = data;
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

async function openNative(path, reveal = false) {
  await request("/api/open", { path, reveal });
}

async function showPreview(path) {
  const file = state.folder.files.find((item) => item.path === path);
  if (!file) return;
  const version = ++previewVersion;
  state.preview = file;
  $("previewTitle").textContent = file.name;
  $("previewPath").textContent = file.folder || state.folder.name;
  $("previewMeta").textContent = file.extension + " · " + formatSize(file.size) + " · " + formatDate(file.modified);
  $("previewDownload").href = apiUrl("/api/file", path, { download: "1" });
  const files = filteredFiles();
  const index = files.findIndex((item) => item.path === path);
  $("previewPrevious").disabled = index <= 0;
  $("previewNext").disabled = index < 0 || index === files.length - 1;
  $("previewBody").replaceChildren();
  if (!$("previewDialog").open) $("previewDialog").showModal();
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
$("fileFilters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-type]");
  if (button) { state.fileType = button.dataset.type; state.limit = 120; renderFiles(); }
});
$("fileSearch").addEventListener("input", (event) => { state.fileQuery = event.target.value; state.limit = 120; renderFiles(); });
$("fileSort").addEventListener("change", (event) => { state.fileSort = event.target.value; state.limit = 120; renderFiles(); });
$("homeButton").addEventListener("click", () => run(() => navigate("")));
$("openFolderButton").addEventListener("click", () => run(() => openNative(state.selected)));
$("refreshButton").addEventListener("click", () => run(async () => {
  $("refreshButton").disabled = true;
  try {
    await saveCurrentStatus();
    ++treeSearchVersion;
    clearTimeout(searchTimer);
    state.searchTree = null;
    state.treeQuery = "";
    $("treeSearch").value = "";
    await loadTree();
    await navigate(state.selected, { history: false });
  } finally { $("refreshButton").disabled = false; }
}));
$("statusSelect").addEventListener("change", () => { state.dirty = true; renderStatus(); });
$("orderNote").addEventListener("input", () => { state.dirty = true; renderStatus(); });
$("statusForm").addEventListener("submit", (event) => { event.preventDefault(); run(async () => { await saveCurrentStatus(); notify("Статус и заметка сохранены"); }); });
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
  if (!$("printWorkspace").hidden && state.printTask && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    run(async () => { await saveCurrentPrintTask(true); notify("Задание сохранено"); });
  }
});
$("previewClose").addEventListener("click", () => $("previewDialog").close());
$("previewDialog").addEventListener("close", () => { ++previewVersion; $("previewBody").replaceChildren(); state.preview = null; });
$("previewPrevious").addEventListener("click", () => stepPreview(-1));
$("previewNext").addEventListener("click", () => stepPreview(1));
$("previewNative").addEventListener("click", () => run(() => openNative(state.preview.path)));
$("previewDialog").addEventListener("keydown", (event) => {
  if (["INPUT", "TEXTAREA"].includes(event.target.tagName)) return;
  if (event.key === "ArrowLeft") { event.preventDefault(); stepPreview(-1); }
  if (event.key === "ArrowRight") { event.preventDefault(); stepPreview(1); }
});
window.addEventListener("popstate", () => run(() => navigate(new URLSearchParams(location.search).get("path") || "", { history: false })));
window.addEventListener("beforeunload", (event) => { if (state.dirty || state.printTask?.dirty || state.printSaving) { event.preventDefault(); event.returnValue = ""; } });

run(async () => {
  try {
    await loadTree();
    await navigate(new URLSearchParams(location.search).get("path") || "", { history: false });
  } catch (error) {
    $("notice").textContent = error.message;
    $("notice").hidden = false;
    $("folderSummary").textContent = "Проверьте путь в manager.ini";
    document.querySelector(".content-pane").setAttribute("aria-busy", "false");
    throw error;
  }
});

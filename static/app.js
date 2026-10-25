const $ = (id) => document.getElementById(id);
const statusLabels = { new: "Новый", measure: "Замеры", process: "Расчеты", waiting: "Жду", offer_later: "Предложить позже", workshop: "В цех", install: "Монтаж", rework: "Переделка/доделка", finishing: "Завершение/добивка", deferred: "Отложен/возможно", done: "Готово", done_but: "Готово, но…", cancelled: "Отменён", unspecified: "Не указан" };
const orderStatusGroups = [
  ["new", "measure", "process"],
  ["workshop", "install", "rework", "finishing"],
  [],
];
const financialStatusLabels = { unspecified: "Не указан", payment: "На оплате", partial: "Частично оплачен", paid: "Оплачен" };
const purchaseSuppliers = ["newtek", "glass", "antares", "tbm", "remex"];
const eventRelevanceLabels = { none: "Без статуса", active: "Актуально", check: "Проверить", inactive: "Неактуально" };
const typeLabels = { all: "Все", images: "Фото", pdf: "PDF", design: "Макеты", docs: "Документы", video: "Видео", audio: "Аудио", other: "Другое" };
const state = {
  tree: [], groups: [], auxiliary: [], nodes: new Map(), children: new Map(), expanded: new Set(),
  treeQuery: "", searchTree: null, folder: null, selected: "",
  showInactive: false, clientActivitySaving: false,
  fileQuery: "", fileType: "all", fileSort: "folders", limit: 120,
  folderRequest: null, navigation: 0, preview: null, dirty: false, saving: null,
  printTask: null, printSaving: null, printQuery: "",
  view: "orders", orders: [], orderFilter: "all", financialFilter: "all", orderQuery: "", orderSort: "updated", orderDirection: -1, scan: null, ordersRequest: 0,
  unregistrations: [], removeOrder: null, removingOrder: false,
  objectOrders: [], objectOrdersError: "", orderListScope: "",
  collapsedOrderGroups: new Map(),
  flagSaving: new Set(), favoriteSaving: new Set(), orderStatusSaving: new Set(), deadlineSaving: new Set(), deadlineWeekOptions: [], favoriteOrders: [], supplierFavoriteSaving: new Set(), supplierFavoriteFocus: null,
  fileComment: null, fileCommentSaving: null,
  selectedFiles: new Set(), imageReport: null,
  fileRemoval: null, fileRemoving: false, trashRestoring: false,
  upload: null,
  newOrderParent: null, creatingOrderFolder: false,
  newObjectParent:null, creatingObject:false, objectYears:null, groupingYears:false,
  eventPlan: null, eventBusy: false,
  folderRename: null, folderRenaming: false,
  eventRemoval: null, eventRemoving: false,
  trashEventsOnly: false,
  orderTodoPath: null, orderTodoMarkup: null, orderTodoKind: "todos",
  calendarEvent: null,
  calendarMenu: null, calendarMoving: new Set(),
};
let searchTimer, toastTimer, todoSaveTimer, previewVersion = 0, treeSearchVersion = 0, printReadVersion = 0;
const icon = (name) => '<svg aria-hidden="true"><use href="#icon-' + name + '"/></svg>';
const escapeHtml = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
const normalize = (value) => String(value).normalize("NFC").toLocaleLowerCase("ru");
const isWorkOrderPath = (path) => /^#\s*work$/i.test(String(path || "").split("/")[0]);
const apiUrl = (route, path = "", extra = {}) => route + "?" + new URLSearchParams({ path, ...extra });
const treeUrl = (path = "", extra = {}) => apiUrl("/api/tree", path, { show_inactive: state.showInactive ? "1" : "0", ...extra });
const folderUrl = (path) => apiUrl("/api/folder", path, { show_inactive: state.showInactive ? "1" : "0" });
const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + " Б";
  if (bytes < 1024 ** 2) return Math.round(bytes / 1024) + " КБ";
  if (bytes < 1024 ** 3) return (bytes / 1024 ** 2).toFixed(1) + " МБ";
  return (bytes / 1024 ** 3).toFixed(1) + " ГБ";
};
const formatDate = (seconds) => new Date(seconds * 1000).toLocaleDateString("ru", { day: "numeric", month: "short", year: "numeric" });
const printCountLabel = (count) => count + " " + ({ one: "задание", few: "задания", many: "заданий", other: "задания" }[new Intl.PluralRules("ru").select(count)]);
const folderParent = (path) => path.split("/").slice(0, -1).join("/");

function renderUpload() {
  const job = state.upload;
  $("uploadPanel").hidden = !job;
  $("chooseUploadFiles").disabled = Boolean(job?.busy);
  $("uploadDropHint").textContent = state.folder?.upload ? "Или перетащи файлы в " + (state.folder.frezaTask ? "задание" : "открытое событие") + " · до " + state.folder.upload.maxFiles + " файлов, каждый до " + formatSize(state.folder.upload.maxBytes) : "";
  if (!job) return;
  $("uploadTitle").textContent = job.busy ? "Загрузка · " + job.index + " из " + job.total : "Загрузка завершена";
  $("uploadDestination").textContent = "В папку: " + job.path;
  $("uploadDestination").title = job.path;
  $("uploadDestination").setAttribute("aria-label", "Открыть папку назначения: " + job.path);
  $("uploadCurrent").textContent = job.busy ? (job.sent < job.size ? "Передаю: " : "Сохраняю на M4: ") + job.filename : "";
  $("uploadProgress").hidden = !job.busy;
  $("uploadProgress").value = job.size ? Math.round(100 * job.sent / job.size) : 100;
  $("closeUploadPanel").hidden = job.busy;
  const errors = job.results.filter((item) => item.error).length;
  $("uploadSummary").textContent = job.busy ? "" : "Сохранено на M4: " + (job.results.length - errors) + " из " + job.total + (errors ? " · не удалось: " + errors : "") + (job.refreshError ? " · " + job.refreshError : "");
  $("uploadSummary").classList.toggle("error", Boolean(errors || job.refreshError));
  const markup = job.results.map((item) => '<li' + (item.error ? ' class="error"' : '') + '>' + escapeHtml(item.error ? item.original + " — " + item.error : item.name + " · сохранён") + '</li>').join("");
  if ($("uploadResults").innerHTML !== markup) $("uploadResults").innerHTML = markup;
}

function sendUpload(file, job) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", apiUrl("/api/file-upload", job.path, { token:job.token, name:file.name }));
    xhr.setRequestHeader("Content-Type", "application/octet-stream");
    xhr.setRequestHeader("X-Manager-Upload", "1");
    xhr.responseType = "json";
    let painted = 0;
    xhr.upload.addEventListener("progress", (event) => {
      if (!event.lengthComputable) return;
      job.sent = event.loaded;
      if (Date.now()-painted>200 || event.loaded===event.total) { painted=Date.now(); renderUpload(); }
    });
    xhr.addEventListener("load", () => {
      if (xhr.status===201 && xhr.response?.path) resolve(xhr.response);
      else { const error=new Error(xhr.response?.error || "Не удалось загрузить файл · HTTP " + xhr.status); error.status=xhr.status; reject(error); }
    });
    xhr.addEventListener("error", () => reject(new Error("Нет связи с M4. Проверь файл в папке назначения перед повтором")));
    xhr.send(file);
  });
}

async function refreshUploadedFiles(job) {
  const folder = state.folder;
  if (state.view!=="folder" || folder?.path!==job.path || folder.upload?.token!==job.token) return;
  const data = await request(folderUrl(job.path));
  if (state.folder!==folder || data.upload?.token!==job.token) return;
  for (const key of ["files","directories","counts","fileCount","folderCount","totalSize"]) folder[key]=data[key];
  state.limit = Math.max(state.limit, 120 + job.results.filter((item) => !item.error).length);
  renderFiles();
  $("folderSummary").textContent = folder.fileCount + " файлов · " + folder.folderCount + " папок · " + formatSize(folder.totalSize);
}

async function uploadFiles(files) {
  if (state.upload?.busy) { notify("Дождись завершения текущей загрузки",true); return; }
  const folder = state.folder;
  if (state.view!=="folder" || !folder?.upload) { notify("Открой событие или папку внутри заказа для добавления файлов",true); return; }
  if (!files.length) return;
  if (files.length>folder.upload.maxFiles) { notify("За один раз можно добавить до " + folder.upload.maxFiles + " файлов",true); return; }
  const job = state.upload = { path:folder.path,token:folder.upload.token,maxBytes:folder.upload.maxBytes,busy:true,total:files.length,index:0,filename:"",size:0,sent:0,results:[] };
  $("uploadDetails").open = false;
  try {
    for (const file of files) {
      job.index++; job.filename=file.name; job.size=file.size; job.sent=0; renderUpload();
      try {
        if (file.size>job.maxBytes) throw new Error("Размер больше " + formatSize(job.maxBytes));
        job.results.push({ original:file.name,...await sendUpload(file,job) });
      } catch(error) {
        job.results.push({ original:file.name,error:error.message });
        if (error.status===404 || error.status===409) {
          for (const pending of files.slice(job.index)) job.results.push({ original:pending.name,error:"Не передан: папка назначения изменилась" });
          break;
        }
      }
    }
    if (job.results.some((item) => !item.error)) await refreshUploadedFiles(job).catch(() => { job.refreshError="Файлы приняты; обнови список в папке"; });
  } finally {
    job.busy=false;
    renderUpload();
  }
}

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
    return '<div class="tree-branch" role="none"><div class="tree-row' + (selected ? " selected" : "") + (node.inactive ? " inactive" : "") +
      '" role="treeitem" tabindex="' + tabIndex + '" aria-selected="' + selected + '"' +
      (node.hasChildren ? ' aria-expanded="' + open + '"' : "") + ' aria-level="' + (depth + 1) +
      '" data-path="' + escapeHtml(node.path) + '" style="--depth:' + depth + '" title="' + escapeHtml(node.name + (node.inactive ? " · Неактивная папка" : "")) + '">' +
      '<button class="tree-toggle' + (open ? " expanded" : "") + '" tabindex="-1" aria-label="' +
      (open ? "Свернуть " : "Раскрыть ") + escapeHtml(node.name) + '"' + (!node.hasChildren ? ' disabled aria-hidden="true"' : "") + ">" +
      icon("chevron") + "</button>" + icon("folder") + '<span class="tree-name">' + escapeHtml(node.name) +
      '</span></div>' + (open && children.length ? '<div role="group">' + treeMarkup(children, depth + 1, searching) + "</div>" : "") + "</div>";
  }).join("");
}

function renderFavoriteOrders() {
  const container = $("favoriteOrders");
  const favorites = state.favoriteOrders.filter((order) => order.is_favorite === true).sort((a,b) =>
    (a.client || "").localeCompare(b.client || "", "ru", { numeric:true }) || a.title.localeCompare(b.title,"ru",{ numeric:true }) || a.path.localeCompare(b.path,"ru"));
  const markup = favorites.map((order) => {
    const active = state.view !== "orders" && (state.selected === order.path || state.selected.startsWith(order.path + "/"));
    return '<button type="button" class="favorite-order-button' + (active ? ' active' : '') + '" data-path="' + escapeHtml(order.path) + '" title="' + escapeHtml(order.title + " · " + (order.client || "") + "\n" + order.path) + '"' + (active ? ' aria-current="page"' : '') + '><span class="favorite-order-star" aria-hidden="true">★</span><span class="favorite-order-text"><span class="favorite-order-title">' + escapeHtml(order.title) + '</span>' + (order.client ? '<span class="favorite-order-client">' + escapeHtml(order.client) + '</span>' : '') + '</span></button>';
  }).join("");
  if (container.innerHTML !== markup) {
    const focusedPath = container.contains(document.activeElement) ? document.activeElement.dataset.path : null;
    const scroll = container.scrollTop;
    container.innerHTML = markup;
    container.scrollTop = scroll;
    if (focusedPath) [...container.querySelectorAll("[data-path]")].find((button) => button.dataset.path === focusedPath)?.focus({ preventScroll:true });
  }
  container.hidden = !favorites.length;
}

function renderTree() {
  const focused = document.activeElement?.closest(".tree-row")?.dataset.path;
  const focusedGroup = document.activeElement?.closest("[data-catalog-group]")?.dataset.catalogGroup;
  const data = state.searchTree || { children: state.tree, groups: state.groups };
  const searching = Boolean(state.searchTree);
  const markup = (nodes) => nodes.length ? treeMarkup(nodes, 0, searching) : '<p class="tree-empty">Папки не найдены</p>';
  $("folderTree").innerHTML = '<section class="catalog-tree-section"><div class="tree-heading catalog-tree-heading"><span>Клиенты</span><span id="clientCount">' + data.children.length + '</span></div><div role="tree" aria-label="Основное дерево клиентов">' + markup(data.children) + '</div></section>' +
    data.groups.map((group) => '<section class="catalog-tree-section"><div class="tree-heading catalog-tree-heading"><button type="button" data-catalog-group="' + escapeHtml(group.path) + '" title="Открыть группу ' + escapeHtml(group.name) + '"' + (state.selected === group.path ? ' aria-current="page"' : '') + '>' + escapeHtml(group.name) + '</button><span>' + (group.error ? "—" : group.children.length) + '</span></div><div role="tree" aria-label="Группа ' + escapeHtml(group.name) + '">' + (group.error ? '<p class="tree-empty" role="status">' + escapeHtml(group.error) + '</p>' : markup(group.children)) + '</div></section>').join("");
  for (const tree of $("folderTree").querySelectorAll('[role="tree"]')) {
    const rows = [...tree.querySelectorAll(".tree-row")];
    const active = rows.find((row) => row.dataset.path === state.selected) || rows[0];
    rows.forEach((row) => { row.tabIndex = row === active ? 0 : -1; });
  }
  if (focused) focusTree(focused);
  if (focusedGroup) [...$("folderTree").querySelectorAll("[data-catalog-group]")].find((button) => button.dataset.catalogGroup === focusedGroup)?.focus({ preventScroll: true });
  $("auxiliaryButtons").innerHTML = state.auxiliary.map((node) =>
    '<button class="auxiliary-button' + (state.selected === node.path || state.selected.startsWith(node.path + "/") ? " active" : "") +
    '" data-path="' + escapeHtml(node.path) + '" title="' + escapeHtml(node.name) + '">' + icon("folder") +
    '<span>' + escapeHtml(node.name) + "</span></button>").join("");
  $("auxiliaryButtons").hidden = !state.auxiliary.length;
  renderFavoriteOrders();
}

function focusTree(path) {
  const row = [...$("folderTree").querySelectorAll(".tree-row")].find((item) => item.dataset.path === path);
  if (row) {
    row.closest('[role="tree"]').querySelectorAll(".tree-row").forEach((item) => { item.tabIndex = -1; });
    row.tabIndex = 0;
    row.focus({ preventScroll: true });
  }
}

async function loadChildren(path) {
  if (!state.children.has(path)) {
    const data = await request(treeUrl(path));
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
  const data = await request(treeUrl());
  state.tree = data.children;
  state.groups = data.groups || [];
  state.auxiliary = data.auxiliary;
  state.nodes.clear();
  state.children.clear();
  registerNodes([...state.tree, ...state.groups, ...state.auxiliary]);
  for (const group of state.groups) state.children.set(group.path, group.children);
  $("rootLabel").textContent = data.rootName;
  $("rootLabel").title = data.root;
  for (const path of [...state.expanded].sort((a, b) => a.split("/").length - b.split("/").length)) {
    try { await loadChildren(path); } catch { state.expanded.delete(path); }
  }
  renderTree();
}

async function reloadClientTrees() {
  ++treeSearchVersion;
  clearTimeout(searchTimer);
  state.searchTree = null;
  await loadTree();
  if (state.treeQuery.trim()) {
    const version = ++treeSearchVersion;
    const result = await request(treeUrl("", { q: state.treeQuery }));
    if (version !== treeSearchVersion) return;
    state.searchTree = { children: result.children, groups: result.groups || [] };
    registerNodes([...state.searchTree.children, ...state.searchTree.groups]);
    renderTree();
  }
}

function folderActivity(folder) {
  return folder?.objectActivity || folder?.clientActivity;
}

function activityRoute(folder) {
  return folder?.objectActivity ? "/api/object-activity" : "/api/client-activity";
}

function updateFolderActivity(folder, activity) {
  folder[folder.objectActivity ? "objectActivity" : "clientActivity"] = activity;
}

function renderClientActivity() {
  const folder = state.folder, activity = folderActivity(folder);
  $("folderFooter").hidden = !activity;
  $("clientActivityCard").hidden = !activity;
  if (!activity) return;
  const object = Boolean(folder.objectActivity), entity = object ? "объекта" : "клиента";
  $("clientActivityCard").setAttribute("aria-label", object ? "Активность объекта" : "Активность клиента");
  $("activityLabel").textContent = object ? "Неактивный объект" : "Неактивный клиент";
  $("activityHint").textContent = "Заказы и To-do неактивного " + entity + " скрыты на главной. Сними отметку, чтобы вернуть их.";
  $("clientInactive").checked = activity.inactive;
  $("clientInactive").disabled = state.clientActivitySaving || !activity.editable;
  $("clientActivityState").textContent = state.clientActivitySaving ? "Сохраняю…" : activity.storage === "database" ? "Сохранено в базе" : activity.sync_error || (activity.sync_pending ? "Сохранено в базе · ожидает выгрузки в !.txt" : "Сохранено в !.txt " + entity);
  $("clientActivityState").classList.toggle("error", Boolean(activity.sync_error));
  $("clientActivityAcceptFile").hidden = !activity.sync_pending || !activity.sync_error;
  $("clientActivityAcceptFile").disabled = state.clientActivitySaving;
}

async function saveClientActivity(inactive, acceptFile = false) {
  const folder = state.folder;
  if (!folderActivity(folder) || state.clientActivitySaving) return;
  state.clientActivitySaving = true;
  renderClientActivity();
  try {
    await saveCurrentStatus();
    updateFolderActivity(folder, await request(activityRoute(folder) + (acceptFile ? "-file" : ""), {
      path: folder.path, revision: folderActivity(folder).revision, inactive,
    }));
    await reloadClientTrees();
    await loadOrders();
  } catch (error) {
    if (error.status === 409) {
      try { updateFolderActivity(folder, await request(apiUrl(activityRoute(folder), folder.path))); } catch { /* Сохраняем последнее состояние. */ }
    }
    throw error;
  } finally {
    state.clientActivitySaving = false;
    if (state.folder === folder) renderClientActivity();
  }
}

function renderSketches() {
  const folder = state.folder, files = folder.sketches || [];
  const focused = document.activeElement?.closest("[data-sketch-status]");
  const focusPath = focused?.dataset.sketchFile, focusValue = focused?.dataset.sketchStatus;
  $("sketchSection").hidden = !files.length;
  $("sketchCount").textContent = files.length;
  $("sketchTiles").innerHTML = files.map((item) => {
    const relevance = item.relevance, saving = folder.sketchSavingFolders?.has(item.folder);
    const message = saving ? "Сохраняю…" : relevance.error || (relevance.sync_pending
      ? relevance.sync_error ? "В базе сохранено · не выгружено: " + relevance.sync_error : "В базе сохранено · ожидает выгрузки" : "");
    return '<div class="event-folder sketch-tile" data-relevance-state="' + escapeHtml(relevance.value || "none") + '">' +
      '<button class="subfolder sketch-open" data-sketch-open="' + escapeHtml(item.path) + '" data-sketch-key="' + escapeHtml(item.key) + '" title="' + escapeHtml(item.name + " · Открыть в CorelDRAW на M4") + '" aria-label="' + escapeHtml("Открыть в CorelDRAW: " + item.name) + '"' + (item.opening ? ' disabled' : '') + '>' +
      '<span class="sketch-picture"><img src="' + escapeHtml(apiUrl("/api/sketch-preview", item.path, { v: item.preview_version })) + '" alt="" loading="lazy" decoding="async"><span class="sketch-fallback">CDR</span></span><span class="sketch-name">' + escapeHtml(item.name) + '</span></button>' +
      '<div class="event-relevance" role="group" aria-label="' + escapeHtml("Актуальность эскиза " + item.name) + '">' +
      Object.entries(eventRelevanceLabels).map(([value, label]) => '<button type="button" data-sketch-file="' + escapeHtml(item.path) + '" data-sketch-status="' + value +
        '" aria-pressed="' + (value === relevance.value) + '"' + (saving || relevance.error || !relevance.revision ? ' disabled' : '') + '>' + label + '</button>').join("") + '</div>' +
      (message ? '<p class="event-export' + (relevance.error || relevance.sync_error ? ' error' : '') + '" role="status">' + escapeHtml(message) + '</p>' : '') + '</div>';
  }).join("");
  if (focusPath) [...$("sketchTiles").querySelectorAll("[data-sketch-status]")].find((button) => button.dataset.sketchFile === focusPath && button.dataset.sketchStatus === focusValue)?.focus();
}

function applySketchGroup(folder, path, record) {
  let changed = false;
  for (const item of folder.sketches || []) {
    if (item.folder !== path) continue;
    const { states, ...metadata } = record;
    const relevance = { ...metadata, value: states ? states[item.name.normalize("NFC")] || "none" : null };
    if (JSON.stringify(relevance) !== JSON.stringify(item.relevance)) { item.relevance = relevance; changed = true; }
  }
  return changed;
}

async function refreshSketchRelevance(folder) {
  if (!(folder.sketches || []).length || state.folder !== folder) return;
  const records = await request(apiUrl("/api/sketch-relevance", folder.path));
  if (state.folder !== folder) return;
  let changed = false;
  for (const [path, record] of Object.entries(records)) {
    if (!folder.sketchSavingFolders?.has(path)) changed = applySketchGroup(folder, path, record) || changed;
  }
  if (changed) renderSketches();
}

async function saveSketchRelevance(path, value) {
  const folder = state.folder, item = folder?.sketches?.find((file) => file.path === path);
  if (!item || folder.sketchSavingFolders?.has(item.folder) || item.relevance.value === value) return;
  folder.sketchSavingFolders ||= new Set();
  folder.sketchSavingFolders.add(item.folder);
  renderSketches();
  try {
    const result = await request("/api/sketch-relevance", { path, key: item.key, value, revision: item.relevance.revision });
    if (result.path !== item.path || result.key !== item.key || result.folder !== item.folder) throw new Error("Ответ относится к другому эскизу. Обнови страницу");
    applySketchGroup(folder, result.folder, result.status);
  } catch (error) {
    if (error.status === 409) {
      try {
        const records = await request(apiUrl("/api/sketch-relevance", folder.path));
        if (records[item.folder]) applySketchGroup(folder, item.folder, records[item.folder]);
      } catch { /* Оставляем последнее известное состояние. */ }
    }
    throw error;
  } finally {
    folder.sketchSavingFolders.delete(item.folder);
    if (state.folder === folder) renderSketches();
  }
}

async function openSketch(path, key) {
  const folder = state.folder, item = folder?.sketches?.find((file) => file.path === path && file.key === key);
  if (!item || item.opening) return;
  item.opening = true;
  renderSketches();
  try {
    await request("/api/sketch-open", { path, key });
    notify("Эскиз открыт в CorelDRAW на M4");
  } finally {
    item.opening = false;
    if (state.folder === folder) renderSketches();
  }
}

function subfolderButton(item) {
  const color = item.supplierColor;
  const open = '<button type="button" class="subfolder' + (item.inactive ? ' inactive' : '') + (color ? ' work-supplier-button' + (color.neutral ? ' supplier-neutral' : '') : '') +
    '"' + (color ? ' style="--supplier-hue:' + Number(color.hue) + '"' : '') + ' data-path="' + escapeHtml(item.path) + '" title="' + escapeHtml(item.name) + '">' +
    icon("folder") + '<span>' + escapeHtml(item.name) + "</span>" + icon("chevron") + "</button>";
  const favorite = item.supplierFavorite;
  if (!favorite) return open;
  const label = (favorite.is_favorite ? "Убрать раздел из избранного: " : "Добавить раздел в избранное: ") + item.name;
  return '<div class="work-supplier-tile" data-supplier-tile="' + escapeHtml(item.path) + '">' + open +
    '<button type="button" class="order-favorite-button work-supplier-star" data-supplier-favorite="' + escapeHtml(item.path) +
    '" aria-pressed="' + Boolean(favorite.is_favorite) + '" aria-label="' + escapeHtml(label) + '" title="' +
    escapeHtml(favorite.editable ? label : "Неизвестная отметка избранного сохранена без изменений") + '"' +
    (state.supplierFavoriteSaving.has(item.path) || !favorite.editable ? ' disabled' : '') + '><span aria-hidden="true">' +
    (favorite.is_favorite ? "★" : "☆") + '</span></button></div>';
}

function renderSubfolders() {
  const folder = state.folder;
  const focused = document.activeElement?.closest("[data-relevance]");
  const focusPath = focused?.dataset.eventPath, focusValue = focused?.dataset.relevance;
  const focusedSupplier = document.activeElement?.closest("[data-supplier-favorite]")?.dataset.supplierFavorite;
  const scroll = document.querySelector(".content-pane").scrollTop;
  const visibleDirectories = folder.directories.filter((item) => (["work_root", "moneys_root"].includes(folder.folderKind) || !item.name.startsWith("#")) &&
    !(isObjectOrderList() && state.objectOrders.some((order) => order.path.normalize("NFC") === item.path.normalize("NFC"))));
  $("frezaTaskSearchLabel").hidden = !folder.frezaSection;
  $("subfolders").classList.toggle("freza-task-grid", Boolean(folder.frezaSection));
  $("frezaLegacyFolders").hidden = !folder.frezaTask || !folder.directories.length;
  if (folder.frezaTask) {
    $("folderSection").hidden = true;
    $("workOrdersSection").hidden = true;
    $("printLegacyFolders").hidden = true;
    $("frezaLegacyCount").textContent = folder.directories.length;
    $("frezaLegacyList").innerHTML = folder.directories.map(subfolderButton).join("");
    return;
  }
  if (folder.frezaSection) {
    const query = normalize($("frezaTaskSearch").value.trim());
    const tasks = visibleDirectories.filter((item) => !query || normalize(item.name).includes(query)).sort((a, b) => b.name.localeCompare(a.name, "ru", { numeric: true }));
    $("folderSection").hidden = false;
    $("workOrdersSection").hidden = true;
    $("printLegacyFolders").hidden = true;
    $("subfolders").classList.remove("with-event-relevance");
    $("foldersTitle").textContent = "Задания на фрезеровку";
    $("directoryCount").textContent = tasks.length;
    $("subfolders").innerHTML = tasks.map((item) => '<button type="button" class="subfolder freza-task" data-path="' + escapeHtml(item.path) + '"><span class="freza-task-picture"><img src="' + escapeHtml(apiUrl("/api/freza-preview", item.path)) + '" alt="" loading="lazy" decoding="async"><span class="thumbnail-fallback">' + icon("file") + '</span></span><span>' + escapeHtml(item.name) + '</span>' + icon("chevron") + '</button>').join("") || '<p class="todo-empty">' + (query ? 'Задания не найдены' : 'Создай первое задание и добавь файлы') + '</p>';
    return;
  }
  const workRoot = folder.folderKind === "work_root";
  let directories = workRoot ? visibleDirectories.filter((item) => item.name.startsWith("#")) : visibleDirectories;
  let supplierDividerAfter = 0;
  if (workRoot) {
    const primary = directories.filter((item) => item.supplierFavorite?.is_favorite === true).sort((a,b) =>
      (a.supplierFavorite.position ?? Number.MAX_SAFE_INTEGER) - (b.supplierFavorite.position ?? Number.MAX_SAFE_INTEGER) || a.name.localeCompare(b.name, "ru", { numeric: true }));
    const other = directories.filter((item) => item.supplierFavorite?.is_favorite !== true);
    directories = [...primary, ...other];
    if (primary.length && other.length) supplierDividerAfter = primary.length;
  }
  const workOrders = workRoot ? visibleDirectories.filter((item) => !item.name.startsWith("#")) : [];
  $("workOrdersSection").hidden = !workOrders.length;
  $("workOrdersSection").classList.toggle("with-sections", Boolean(directories.length));
  $("workOrderDirectoryCount").textContent = workOrders.length;
  $("workOrderFolders").innerHTML = workOrders.map(subfolderButton).join("");
  const printView = folder.view === "print";
  $("printLegacyFolders").hidden = !printView || !folder.directories.length;
  if (printView) {
    $("folderSection").hidden = true;
    $("printLegacyFolderCount").textContent = folder.directories.length;
    $("printLegacyFolderList").innerHTML = folder.directories.map((item) => '<button type="button" class="subfolder" data-path="' + escapeHtml(item.path) + '">' + icon("folder") + '<span>' + escapeHtml(item.name) + '</span>' + icon("chevron") + '</button>').join("");
    return;
  }
  $("subfolders").classList.toggle("with-event-relevance", directories.some((item) => item.eventRelevance));
  $("folderSection").hidden = !directories.length;
  $("foldersTitle").textContent = folder.canCreateEventFolder ? "События" : ["supplier_root", "work_section"].includes(folder.folderKind) ? "Заказы поставщикам" : folder.folderKind === "moneys_section" ? "Финансовые записи" : workRoot ? "Разделы производства" : folder.folderKind === "moneys_root" ? "Финансовые разделы" : folder.path ? "Подпапки" : "Папки";
  $("directoryCount").textContent = directories.length;
  $("subfolders").innerHTML = directories.map((item, index) => {
    const open = subfolderButton(item);
    const relevance = item.eventRelevance;
    if (!relevance) return (supplierDividerAfter && index === supplierDividerAfter ? '<hr class="work-supplier-divider">' : "") + open;
    const message = item.relevanceSaving ? "Сохраняю…" : relevance.error || (relevance.sync_pending
      ? relevance.sync_error ? "В базе сохранено · не выгружено: " + relevance.sync_error : "В базе сохранено · ожидает выгрузки" : "");
    return '<div class="event-folder" data-relevance-state="' + escapeHtml(relevance.value || "none") + '" aria-busy="' + Boolean(item.relevanceSaving) + '">' + open +
      '<div class="event-relevance" role="group" aria-label="Актуальность события ' + escapeHtml(item.name) + '">' +
      Object.entries(eventRelevanceLabels).map(([value, label]) => '<button type="button" data-event-path="' + escapeHtml(item.path) + '" data-relevance="' + value +
        '" aria-pressed="' + (value === relevance.value) + '"' + (item.relevanceSaving || relevance.error || !relevance.revision ? " disabled" : "") + '>' + label + '</button>').join("") +
      '</div>' + (message ? '<p class="event-export' + (relevance.error || relevance.sync_error ? " error" : "") + '" role="status">' + escapeHtml(message) + '</p>' : "") + '</div>';
  }).join("");
  if (focusPath) [...$("subfolders").querySelectorAll("[data-relevance]")].find((button) => button.dataset.eventPath === focusPath && button.dataset.relevance === focusValue)?.focus();
  if (focusedSupplier) focusSupplierStar(focusedSupplier);
  if (workRoot) document.querySelector(".content-pane").scrollTop = scroll;
}

function focusSupplierStar(path) {
  [...$("subfolders").querySelectorAll("[data-supplier-favorite]")].find((button) => button.dataset.supplierFavorite === path)?.focus({ preventScroll: true });
}

async function refreshSupplierFavorites(folder) {
  if (folder?.folderKind !== "work_root" || state.folder !== folder) return;
  const records = await request(apiUrl("/api/work-supplier-favorites", folder.path));
  if (state.folder !== folder) return;
  let changed = false;
  for (const item of folder.directories) {
    const saved = records[String(item.path).normalize("NFC")];
    const currentRevision = String(item.supplierFavorite?.revision || "").split(":"), savedRevision = String(saved?.revision || "").split(":");
    const older = savedRevision[0] === currentRevision[0] && Number(savedRevision[1]) < Number(currentRevision[1]);
    if (saved && !older && !state.supplierFavoriteSaving.has(item.path) && JSON.stringify(saved) !== JSON.stringify(item.supplierFavorite)) {
      item.supplierFavorite = saved;
      changed = true;
    }
  }
  if (changed) renderSubfolders();
}

async function toggleSupplierFavorite(path) {
  const folder = state.folder, item = folder?.directories.find((entry) => entry.path === path);
  if (folder?.folderKind !== "work_root" || !item?.supplierFavorite?.editable || state.supplierFavoriteSaving.has(path)) return;
  state.supplierFavoriteSaving.add(path);
  state.supplierFavoriteFocus = path;
  renderSubfolders();
  try {
    item.supplierFavorite = await request("/api/work-supplier-favorite", {
      path, revision: item.supplierFavorite.revision, is_favorite: !item.supplierFavorite.is_favorite,
    });
  } catch (error) {
    if (error.status === 409) {
      state.supplierFavoriteSaving.delete(path);
      await refreshSupplierFavorites(folder);
    }
    throw error;
  } finally {
    state.supplierFavoriteSaving.delete(path);
    if (state.folder === folder) {
      renderSubfolders();
      if (state.supplierFavoriteFocus === path && document.activeElement === document.body) focusSupplierStar(path);
    }
  }
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
  document.dispatchEvent(new CustomEvent("manager-folder-rendered"));
  renderClientActivity();
  const printView = folder.view === "print";
  const service = Boolean(folder.service);
  const noteOnly = service || Boolean(folder.noteOnly);
  const workCard = isWorkOrderPath(folder.path);
  const hasTodo = Boolean(folder.path) && (!noteOnly || Boolean(folder.eventFolder));
  const showFinance = hasDescendantTodos(folder) && !workCard;
  $("orderFinanceOverview").hidden = !showFinance || !folder.order;
  $("purchasePanel").hidden = !showFinance;
  $("orderOverview").hidden = !folder.path || (printView && !folder.eventFolder);
  $("orderOverview").classList.toggle("with-todos", hasTodo);
  $("todoPanel").hidden = !hasTodo;
  $("orderTasksColumn").hidden = !hasTodo && !showFinance;
  $("breadcrumbs").innerHTML = folder.breadcrumbs.map((part, index) =>
    (index ? '<span class="breadcrumb-divider">/</span>' : "") +
    '<button data-path="' + escapeHtml(part.path) + '"' + (index === folder.breadcrumbs.length - 1 ? ' aria-current="page"' : "") + ">" +
    escapeHtml(part.name) + "</button>").join("");
  renderOrderHeading();
  $("clientLabel").textContent = folder.frezaSection || folder.frezaTask ? "ФРЕЗЕРОВКА" : printView ? "ШИРОКОФОРМАТНАЯ ПРОДУКЦИЯ" : service ? "СЛУЖЕБНАЯ ПАПКА" : folder.folderKindLabel && folder.folderKind !== "order" ? folder.folderKindLabel : folder.client || folder.name;
  $("folderSummary").textContent = folder.frezaSection ? printCountLabel(folder.directories.filter((item) => !item.name.startsWith("#")).length) + " · превью и файлы" : printView ? printCountLabel(folder.fileCount) + " · название, ссылка и описание" : folder.filesLoading ? "Карточка из локальной базы · подпапки загружаются…" : folder.filesUnavailable ? "Карточка из локальной базы · папка сейчас недоступна" : folder.frezaTask ? "Файлов: " + folder.fileCount + " · " + formatSize(folder.totalSize) + " · добавляй файлы прямо в задание" : folder.filesScope === "events" ? folder.folderCount + " папок · файлы доступны в событиях" : folder.filesScope === "subfolders" ? folder.folderCount + " папок" : folder.path
    ? folder.fileCount + " файлов · " + folder.folderCount + " папок · " + formatSize(folder.totalSize)
    : "Выберите клиента или заказ в дереве слева";
  renderSubfolders();
  renderSketches();
  renderDescendantTodos();
  $("orderDetails").hidden = !folder.path;
  $("folderDetailsTitle").textContent = folder.frezaTask ? "Задание на фрезеровку" : noteOnly ? "Заметка" : "Карточка заказа";
  $("statusLabel").hidden = noteOnly || workCard;
  $("orderStatusFields").hidden = noteOnly || workCard;
  $("orderTitleLabel").hidden = noteOnly || !folder.order;
  $("orderTitleLabel").firstChild.textContent = folder.frezaTask ? "Название задания" : "Название заказа";
  $("financialFields").hidden = noteOnly || workCard || !folder.order;
  $("statusForm").classList.toggle("note-only", noteOnly);
  $("orderNote").placeholder = folder.frezaTask ? "Материал, толщина, размеры, количество и другие детали задания…" : noteOnly ? "Заметка к этой папке" : "Что важно по этому заказу";
  $("removeOrderButton").hidden = !folder.order;
  $("addOrderButton").textContent = isWorkOrderPath(folder.path) ? "+ Добавить в производство" : "+ Добавить в список заказов";
  $("removeOrderButton").textContent = isWorkOrderPath(folder.path) ? "Убрать из производства" : "Убрать из списка заказов";
  $("createObjectFolderButton").hidden = folder.canCreateObjectFolder !== true;
  $("groupObjectYearsButton").hidden = folder.canGroupOrdersByYear !== true;
  $("createOrderFolderButton").hidden = folder.canCreateOrderFolder !== true;
  $("createOrderFolderButton").textContent = folder.frezaSection ? "+ Новое задание" : folder.folderKind === "moneys_section" ? "+ Создать запись" : ["supplier_root", "work_section"].includes(folder.folderKind) ? "+ Создать заказ поставщику" : "+ Создать заказ";
  $("createEventFolderButton").hidden = folder.canCreateEventFolder !== true;
  $("renameFolderButton").hidden = folder.canRenameFolder !== true;
  $("deleteEventButton").hidden = folder.canDeleteEvent !== true;
  $("openEventTrash").hidden = folder.hasEventTrash !== true;
  if (!preserveForm) {
    folder.todo_items = folder.order ? folder.order.todo_items : folder.todo_items === undefined ? [] : folder.todo_items;
    folder.purchase_items = folder.order ? folder.order.purchase_items : folder.purchase_items === undefined ? [] : folder.purchase_items;
    if (hasTodo) { $("todoNewText").value = ""; renderTodos(); }
    $("purchaseNewText").value = "";
    renderPurchases();
    $("orderDetails").open = noteOnly || Boolean(folder.note || folder.order);
    $("orderTitleInput").value = folder.order?.title || folder.draftCard?.title || folder.name;
    for (const [field, key] of [["orderAmount", "amount"], ["orderCosts", "costs"], ["orderPaid", "paid"]]) {
      const card = folder.order || folder.draftCard;
      $(field).value = card?.[key] == null ? "" : (card[key] / 100).toFixed(2);
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
  $("filesSection").hidden = printView || ["events", "subfolders"].includes(folder.filesScope) || Boolean(folder.filesLoading || folder.filesUnavailable);
  $("uploadDropZone").hidden = !folder.upload;
  renderUpload();
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
  renderCardDeadlines();
  mountOrderList();
  if (isObjectOrderList()) renderOrders();
}

function resizeOrderNote() {
  const note = $("orderNote");
  if (!$("orderDetails").open) return;
  note.style.height = "auto";
  note.style.height = Math.min(480, Math.max(note.value.trim() ? 160 : 54, note.scrollHeight + 2)) + "px";
}

function renderOrderHeading() {
  const folder = state.folder;
  const order = folder?.order;
  const supplier = folder?.workSupplier ?? order?.work_supplier ?? "";
  const supplierLabel = $("workSupplierName");
  supplierLabel.hidden = !supplier;
  supplierLabel.textContent = supplier;
  supplierLabel.setAttribute("aria-label", "Поставщик: " + supplier);
  const color = folder?.workSupplierColor ?? order?.work_supplier_color;
  supplierLabel.style.setProperty("--supplier-hue", String(color?.hue ?? 0));
  supplierLabel.classList.toggle("supplier-neutral", Boolean(color?.neutral));
  $("folderTitleText").textContent = folder?.frezaSection ? "Задания на фрезеровку" : folder?.view === "print" ? "Задания на печать" : folder?.path ? order?.title || folder.draftCard?.title || folder.name : "Клиенты и заказы";
  const showFolderName = Boolean(order || folder?.folderKind === "order");
  $("orderFolderName").hidden = !showFolderName;
  $("orderFolderName").textContent = showFolderName ? "Папка: " + folder.name : "";
  const button = $("orderPageFavorite");
  button.hidden = !order;
  if (!order) return;
  const label = (order.is_favorite ? "Убрать из избранного" : "Добавить в избранное") + " · " + order.title;
  button.setAttribute("aria-pressed", String(Boolean(order.is_favorite)));
  button.setAttribute("aria-label", label);
  button.title = order.is_favorite === null ? "Неизвестный раздел «Избранное» сохранён без изменений" : label;
  button.disabled = order.is_favorite === null || orderRowSaving(order.path);
  button.firstElementChild.textContent = order.is_favorite ? "★" : "☆";
}

function renderStatus() {
  const hideStatuses = state.folder.service || state.folder.noteOnly || isWorkOrderPath(state.folder.path);
  $("statusBadge").hidden = hideStatuses;
  $("statusBadge").textContent = statusLabels[state.folder.status] || state.folder.status;
  $("statusBadge").dataset.status = state.folder.status;
  const financial = state.folder.financial_status || "unspecified";
  $("financialStatusBadge").textContent = financialStatusLabels[financial];
  $("financialStatusBadge").dataset.financialStatus = financial;
  $("financialStatusBadge").hidden = hideStatuses || financial === "unspecified";
  $("saveStatusButton").textContent = state.dirty ? "Сохранить изменения" : "Сохранить";
  const folderNote = state.folder.folderNote;
  $("todoSaveState").textContent = state.saving ? "Сохраняю…" : state.dirty ? "Есть несохранённые изменения" : folderNote?.storage === "database" ? "Сохранено в базе" : folderNote?.sync_error ? "Сохранено в базе. Выгрузка: " + folderNote.sync_error : folderNote?.sync_pending ? "Сохранено в базе · ожидает выгрузки в папку" : folderNote ? folderNote.file_exists ? "Сохранено в базе и в !.txt этой папки" : "Автоматическое сохранение в эту папку" : "Сохранено";
  renderPurchaseSaveState();
  renderCardDeadlines();
}

function renderPurchaseSaveState() {
  const order = state.folder?.order;
  $("purchaseSaveState").textContent = state.saving ? "Сохраняю…" : state.dirty ? "Есть несохранённые изменения" : order?.storage === "database" ? "Сохранено в базе" : order?.sync_error ? "Сохранено в базе · выгрузка: " + order.sync_error : order?.sync_pending ? "Сохранено в базе · ожидает выгрузки в папку" : order ? "Выгружено в !.txt" : "Автоматическое сохранение в !.txt заказа";
}

function renderPurchases() {
  const folder = state.folder, items = folder.purchase_items;
  const editable = Array.isArray(items);
  $("purchaseLegacy").hidden = editable;
  $("purchaseLegacyText").textContent = editable ? "" : (folder.order?.extra_blocks || folder.extra_blocks || {})["Закупки и затраты"] || "";
  $("purchaseAddForm").hidden = !editable;
  $("purchaseEmpty").hidden = !editable || Boolean(items.length);
  $("purchaseCount").textContent = editable ? items.filter((item) => item.done).length + " / " + items.length : "";
  $("purchaseList").innerHTML = editable ? items.map((item, index) => '<div class="todo-row' + (item.done ? ' done' : '') + '" data-purchase-index="' + index + '">' +
    '<input class="todo-check" type="checkbox" aria-label="Закупка выполнена: ' + escapeHtml(item.text) + '"' + (item.done ? ' checked' : '') + '>' +
    '<input class="todo-text" type="text" maxlength="1000" size="' + Math.max(4, Array.from(item.text).length + 1) + '" aria-label="Текст закупки или затраты" value="' + escapeHtml(item.text) + '">' +
    '<div class="purchase-suppliers" role="group" aria-label="Поставщики для закупки: ' + escapeHtml(item.text) + '">' + purchaseSuppliers.map((name) => '<button type="button" data-purchase-supplier="' + name + '" aria-pressed="' + String((item.suppliers || []).includes(name)) + '" title="Отметить поставщика ' + name + '">' + name + '</button>').join("") + '</div>' +
    '<button class="todo-delete" type="button" aria-label="Удалить закупку: ' + escapeHtml(item.text) + '">×</button></div>').join("") : "";
  renderPurchaseSaveState();
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

function hasDescendantTodos(folder) {
  return Boolean(folder?.order || (folder?.folderKind === "order" && !folder.noteOnly));
}

function renderDescendantTodos() {
  const folder = state.folder;
  $("descendantTodos").hidden = !hasDescendantTodos(folder);
  if (!hasDescendantTodos(folder)) return;
  const summary = folder.descendantTodos;
  const groups = summary?.todo_groups || [];
  const completed = groups.some((group) => group.items?.some((item) => item.done));
  $("descendantCompletedLabel").hidden = !completed;
  $("descendantCompleted").checked = Boolean(folder.showCompletedTodos);
  const visible = groups.map((group) => ({ ...group, items: group.items?.filter((item) => folder.showCompletedTodos || !item.done) ?? null }))
    .filter((group) => group.items === null || group.items.length);
  $("descendantTodoCount").textContent = groups.reduce((total, group) => total + (group.items || []).filter((item) => !item.done).length, 0);
  const markup = visible.length ? visible.map(renderOrderTodoGroup).join("") : '<p class="order-todo-empty">' + (summary ? "Во вложенных папках актуальных задач нет." : "Загружаю задачи вложенных папок…") + '</p>';
  if (folder.descendantTodoMarkup !== markup) {
    const scroll = $("descendantTodoList").scrollTop;
    $("descendantTodoList").innerHTML = markup;
    $("descendantTodoList").scrollTop = scroll;
    folder.descendantTodoMarkup = markup;
  }
  $("descendantTodoState").textContent = folder.descendantTodoError || (summary ? orderTodoSummary(summary).warning : "");
}

async function loadDescendantTodos(folder) {
  if (!hasDescendantTodos(folder) || folder.descendantTodoLoading) return;
  folder.descendantTodoLoading = true;
  try {
    const summary = await request(apiUrl("/api/order-todos", folder.path));
    if (state.folder !== folder || summary.path !== folder.path) return;
    folder.descendantTodos = summary;
    folder.descendantTodoError = "";
  } catch (error) {
    if (state.folder === folder) folder.descendantTodoError = "Не удалось обновить задачи: " + error.message;
  } finally {
    folder.descendantTodoLoading = false;
    if (state.folder === folder) renderDescendantTodos();
  }
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
    (!needle || normalize(file.name + " " + (file.title || "") + " " + (file.description || "") + " " + file.folder).includes(needle)));
  if (state.fileSort === "modified") files.sort((a, b) => b.modified - a.modified);
  if (state.fileSort === "name") files.sort((a, b) => a.name.localeCompare(b.name, "ru", { numeric: true }));
  return files;
}

function fileCard(file) {
  const url = apiUrl(file.preview === "cdr" ? "/api/freza-preview" : "/api/preview", file.path);
  const media = ["image", "cdr"].includes(file.preview)
    ? '<img class="' + (file.preview === "cdr" ? "cdr-preview" : "") + '" src="' + escapeHtml(url) + '" alt="" loading="lazy" decoding="async"><span class="thumbnail-fallback">' + icon("file") + '<small>' + escapeHtml(file.extension) + "</small></span>"
    : '<span class="file-symbol">' + icon("file") + '<span>' + escapeHtml(file.extension) + "</span></span>";
  return '<article class="file-card type-' + file.type + (state.selectedFiles.has(file.path) ? ' selected' : '') + '"><label class="file-select-label"><input type="checkbox" class="file-select" data-select-file="' + escapeHtml(file.path) + '" aria-label="Выбрать файл: ' + escapeHtml(file.name) + '"' + (state.selectedFiles.has(file.path) ? ' checked' : '') + '></label><button class="file-main" data-file="' + escapeHtml(file.path) + '" data-comment-key="' + escapeHtml(file.comment_key || "") + '" title="' +
    escapeHtml(file.name + (file.folder ? "\n" + file.folder : "")) + '" aria-label="' + escapeHtml(file.name) + '"><div class="file-thumbnail">' + media +
    '</div><span class="file-name">' + escapeHtml(file.name) + '</span>' + (file.comment?.trim() ? '<span class="file-comment-caption">' + escapeHtml(file.comment) + '</span>' : '') + '</button></article>';
}

function updateFileCommentCaption(path, text, key) {
  const file = state.folder?.files.find((item) => item.path === path);
  if (!file || !key || file.comment_key !== key) return;
  file.comment = text;
  const button = [...$("files").querySelectorAll("[data-file]")].find((item) => item.dataset.file === path);
  if (!button || button.dataset.commentKey !== key) return;
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
  const data = await request(state.trashEventsOnly ? "/api/event-trash-list" : "/api/files-trash-list", {});
  const events = (data.events || []).map((session) => '<section class="file-trash-session"><strong>Событие · ' +
    escapeHtml(new Date(session.created).toLocaleString("ru", { timeZone: "Europe/Moscow" })) + '</strong><p>' + escapeHtml(session.path) +
    '</p>' + (session.pending ? '<p>Операция прервана. Доступно восстановление.</p>' : '') + '<button class="secondary-button" data-restore-event="' + escapeHtml(session.session) + '">Восстановить событие</button></section>').join("");
  $("fileTrashList").innerHTML = events + data.sessions.map((session) => '<section class="file-trash-session"><strong>' +
    escapeHtml(new Date(session.created).toLocaleString("ru", { timeZone: "Europe/Moscow" })) + ' · файлов: ' + session.count + '</strong><p>' + escapeHtml(session.folder) +
    '</p><ul class="file-operation-list">' + session.files.map((path) => '<li>' + escapeHtml(path) + '</li>').join("") + '</ul><button class="secondary-button" data-restore-session="' + session.session + '">Восстановить</button></section>').join("") || (data.warning ? '<p>Список файлов сейчас недоступен.</p>' : '<p>Корзина пуста.</p>');
  $("fileTrashWarning").hidden = !data.warning;
  $("fileTrashWarning").textContent = data.warning || "";
}

async function openFileTrash(eventsOnly = false) {
  state.trashEventsOnly = eventsOnly;
  $("fileTrashTitle").textContent = eventsOnly ? "Корзина событий" : "Корзина менеджера";
  $("fileTrashDialogState").textContent = "";
  await loadFileTrash();
  if (!$("fileTrashDialog").open) $("fileTrashDialog").showModal();
}

async function confirmEventRemoval() {
  const folder = state.folder;
  if (!folder?.canDeleteEvent || state.eventRemoving) return;
  await saveCurrentStatus();
  const preview = await request("/api/event-trash-preview", { path: folder.path });
  if (state.folder !== folder) return;
  state.eventRemoval = { ...preview, folder };
  $("deleteEventPath").textContent = preview.path;
  $("deleteEventCount").textContent = "Вложенных файлов и папок: " + preview.count;
  $("deleteEventError").hidden = true;
  $("deleteEventDialog").showModal();
  $("cancelDeleteEvent").focus();
}

async function removeEvent() {
  const removal = state.eventRemoval;
  if (!removal || state.eventRemoving) return;
  state.eventRemoving = true;
  ["confirmDeleteEvent", "cancelDeleteEvent"].forEach((id) => { $(id).disabled = true; });
  $("deleteEventError").hidden = true;
  let result;
  try {
    result = await request("/api/event-trash", { path: removal.path, revision: removal.revision, confirmed: true });
  } catch (error) {
    $("deleteEventError").textContent = error.message;
    $("deleteEventError").hidden = false;
    return;
  } finally {
    state.eventRemoving = false;
    ["confirmDeleteEvent", "cancelDeleteEvent"].forEach((id) => { $(id).disabled = false; });
  }
  $("deleteEventDialog").close();
  state.expanded = new Set([...state.expanded].filter((path) => path !== removal.path && !path.startsWith(removal.path + "/")));
  await reloadClientTrees();
  if (state.folder === removal.folder) {
    // The saved editor belongs to the old path and must never save there again.
    state.dirty = false;
    await navigate(result.path);
  }
  await loadOrders();
  notify("Событие перемещено в корзину. Восстановление — «Корзина событий»");
}

async function restoreEventSession(session) {
  if (state.trashRestoring) return;
  state.trashRestoring = true;
  $("fileTrashList").querySelectorAll("button").forEach((button) => { button.disabled = true; });
  try {
    await request("/api/event-trash-restore", { session });
    await loadFileTrash();
    await reloadClientTrees();
    if (state.folder) {
      await loadOrderFiles(state.folder.path, state.navigation);
      await loadDescendantTodos(state.folder);
    }
    await loadOrders();
    $("fileTrashDialogState").classList.remove("error");
    $("fileTrashDialogState").textContent = "Событие, вложения и заметки восстановлены.";
  } catch (error) {
    $("fileTrashDialogState").classList.add("error");
    $("fileTrashDialogState").textContent = error.message;
  } finally {
    state.trashRestoring = false;
    $("fileTrashList").querySelectorAll("button").forEach((button) => { button.disabled = false; });
  }
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
  return state.folder.files.filter((file) => !needle || normalize(file.name + " " + (file.title || "") + " " + (file.description || "") + " " + file.folder).includes(needle))
    .sort((a, b) => b.modified - a.modified || b.name.localeCompare(a.name, "ru", { numeric: true }));
}

function renderPrintList() {
  $("printTaskCount").textContent = state.folder.fileCount;
  const files = printFiles();
  $("printTaskList").innerHTML = files.map((file) => '<button class="print-task-button' +
    (state.printTask?.path === file.path ? " active" : "") + '" data-task="' + escapeHtml(file.path) +
    '" title="' + escapeHtml(file.name) + '"><span>' + icon("file") + '<strong>' +
    escapeHtml(file.title || file.name.replace(/\.(textClipping|txt|text|md|rtf)$/i, "")) + '</strong></span><small>' +
    formatDate(file.modified) + (file.folder ? " · " + escapeHtml(file.folder) : "") + '</small></button>').join("") ||
    '<p class="tree-empty">' + (state.folder.fileCount ? "Задания не найдены" : "Заданий пока нет") + "</p>";
}

function renderPrintSaveState() {
  const task = state.printTask;
  if (!task) return;
  $("printTaskName").textContent = task.name;
  $("printSaveState").textContent = state.printSaving ? "Сохраняю…" : task.isNew ? "Новый черновик" : task.dirty ? "Есть несохранённые изменения" : task.storage === "database" ? "Черновик сохранён в базе" : "Все изменения сохранены";
  $("printSaveState").classList.toggle("unsaved", Boolean(task.dirty));
  $("savePrintTask").textContent = task.isNew ? "Создать задание" : "Сохранить";
  $("savePrintTask").disabled = Boolean(state.printSaving);
  $("publishPrintTask").hidden = state.folder?.storage !== "database";
  $("publishPrintTask").disabled = Boolean(state.printSaving);
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
  const title = $("newOrderTitle").value.trim() || (state.folder?.frezaSection ? "Название задания" : state.folder?.folderKind === "moneys_section" ? "Название записи" : "Название заказа");
  $("newOrderFolderName").textContent = date + " - " + title;
}

function openCreateObject() {
  if (!state.folder?.canCreateObjectFolder) return;
  state.newObjectParent=state.folder.path;
  $("newObjectParent").textContent=state.newObjectParent;
  $("newObjectTitle").value="";
  $("newObjectError").hidden=true;
  $("createObjectFolderDialog").showModal();
  $("newObjectTitle").focus();
}

async function createObject() {
  if (state.creatingObject || !$("createObjectFolderForm").reportValidity()) return;
  state.creatingObject=true;
  const controls=["newObjectTitle","submitCreateObject","cancelCreateObject"];
  controls.forEach(id=>$(id).disabled=true);
  $("newObjectError").hidden=true;
  let result;
  try {
    await saveCurrentStatus();
    result=await request("/api/object-folder-create",{path:state.newObjectParent,title:$("newObjectTitle").value});
  } catch(error) {
    $("newObjectError").textContent=error.message;
    $("newObjectError").hidden=false;
    return;
  } finally {
    state.creatingObject=false;
    controls.forEach(id=>$(id).disabled=false);
  }
  $("createObjectFolderDialog").close();
  await reloadClientTrees();
  await navigate(result.path);
  notify("Объект создан");
}

async function openObjectYears() {
  if (!state.folder?.canGroupOrdersByYear) return;
  await saveCurrentStatus();
  const plan=await request(apiUrl("/api/object-years",state.folder.path));
  state.objectYears=plan;
  $("objectYearsParent").textContent=plan.path;
  $("objectYearsPlan").innerHTML=plan.mappings.map(pair=>'<div class="year-group-item"><strong>'+escapeHtml(pair.source.split('/').pop())+'</strong><span>→ '+escapeHtml(pair.year)+'/</span></div>').join('')+
    plan.created_years.map(path=>'<p>Создать папку '+escapeHtml(path.split('/').pop())+'</p>').join('') || '<p>Заказы уже распределены по годам.</p>';
  $("objectYearsSkipped").hidden=!plan.skipped.length;
  $("objectYearsSkipped").textContent="Останутся на месте — год не определён: "+plan.skipped.join(' · ');
  $("objectYearsError").hidden=!plan.conflicts.length;
  $("objectYearsError").textContent=plan.conflicts.join(' · ');
  $("submitObjectYears").disabled=Boolean(plan.conflicts.length || (!plan.mappings.length && !plan.created_years.length));
  $("submitObjectYears").textContent=plan.mappings.length ? "Сгруппировать · "+plan.mappings.length : "Создать папку года";
  $("objectYearsDialog").showModal();
}

async function groupObjectYears() {
  if (!state.objectYears || state.groupingYears) return;
  state.groupingYears=true;
  $("submitObjectYears").disabled=true;
  $("cancelObjectYears").disabled=true;
  $("objectYearsError").hidden=true;
  let result;
  try {
    result=await request("/api/object-years",{path:state.objectYears.path,revision:state.objectYears.revision,confirmed:true});
  } catch(error) {
    $("objectYearsError").textContent=error.message;
    $("objectYearsError").hidden=false;
    return;
  } finally {
    state.groupingYears=false;
    $("submitObjectYears").disabled=false;
    $("cancelObjectYears").disabled=false;
  }
  $("objectYearsDialog").close();
  const moved=path=>{ const pair=state.objectYears.mappings.find(pair=>path===pair.source || path.startsWith(pair.source+'/'));return pair ? pair.destination+path.slice(pair.source.length) : path; };
  state.expanded=new Set([...state.expanded].map(moved));
  await reloadClientTrees();
  await navigate(result.path,{history:false});
  await loadOrders();
  notify(result.moved ? "Заказы распределены по годам" : "Годовая папка создана");
}

function openCreateOrderFolder() {
  if (state.folder?.canCreateOrderFolder !== true) return;
  state.newOrderParent = state.folder.path;
  const supplier = ["supplier_root", "work_section"].includes(state.folder.folderKind);
  const finance = state.folder.folderKind === "moneys_section";
  $("newOrderDateLabel").textContent = finance ? "Дата записи" : "Дата заказа";
  $("newOrderTitleLabel").textContent = finance ? "Название записи" : "Название заказа";
  $("createOrderFolderTitle").textContent = finance ? "Создать финансовую запись" : supplier ? "Создать заказ поставщику" : "Создать заказ";
  $("submitCreateOrderFolder").textContent = finance ? "Создать запись" : "Создать заказ";
  $("newOrderParentLabel").textContent = finance ? "Новая папка в финансовом разделе:" : supplier ? "Новая папка в производственном разделе:" : state.folder.folderKind === "work_root" ? "Новый заказ в корне производства:" : "Новая папка в объекте:";
  $("newOrderTitle").placeholder = finance ? "Например, сверка с поставщиком" : supplier ? "Например, заказ поставщику" : "Например, замена вывески";
  if (state.folder.frezaSection) {
    $("newOrderDateLabel").textContent = "Дата задания";
    $("newOrderTitleLabel").textContent = "Название задания";
    $("createOrderFolderTitle").textContent = "Новое задание на фрезеровку";
    $("submitCreateOrderFolder").textContent = "Создать задание";
    $("newOrderParentLabel").textContent = "Новое задание в разделе:";
    $("newOrderTitle").placeholder = "Например, Лавфиш — шаблоны";
  }
  const parts = Object.fromEntries(new Intl.DateTimeFormat("ru-RU", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date()).map((part) => [part.type, part.value]));
  const year = state.folder.folderKind === "year" ? state.folder.name : parts.year;
  $("newOrderDate").value = year + "-" + parts.month + "-" + parts.day;
  if (!$("newOrderDate").value) $("newOrderDate").value = year + "-01-01";
  $("newOrderTitle").value = "";
  $("newOrderParent").textContent = state.newOrderParent;
  $("newOrderError").hidden = true;
  renderNewOrderName();
  $("createOrderFolderDialog").showModal();
  $("newOrderTitle").focus();
}

async function createOrderFolder() {
  if (state.creatingOrderFolder || !$("createOrderFolderForm").reportValidity()) return;
  const finance = state.folder?.folderKind === "moneys_section";
  const freza = Boolean(state.folder?.frezaSection);
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
    $("submitCreateOrderFolder").textContent = freza ? "Создать задание" : finance ? "Создать запись" : "Создать заказ";
  }
  $("createOrderFolderDialog").close();
  await loadTree();
  await navigate(created.path);
  await loadOrders();
  notify(freza ? "Задание на фрезеровку создано" : finance ? "Финансовая запись создана" : isWorkOrderPath(created.path) ? "Заказ создан в производстве" : "Заказ создан и добавлен в список");
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
    const refreshed = await request(folderUrl(folder));
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
  await flushDeadlineComments();
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
  const folderNote = folder.order ? null : folder.folderNote;
  state.saving = request(folderNote ? "/api/folder-note-save" : noteOnly ? "/api/note" : folder.order ? "/api/order-save" : "/api/status", folderNote
    ? { path: folder.path, revision: folderNote.revision, ...values }
    : noteOnly
    ? { path: folder.path, note }
    : folder.order ? { path: folder.path, revision: folder.order.revision, ...values }
      : { path: folder.path, status, financial_status: values.financial_status, note, ...(values.todo_items ? { todo_items: values.todo_items } : {}),
        ...(values.purchase_items ? { purchase_items: values.purchase_items } : {}) });
  renderStatus();
  try {
    const saved = await state.saving;
    if (!noteOnly) { folder.status = status; folder.financial_status = values.financial_status; }
    folder.note = note;
    folder.statusSource = folder.order || folder.folderNote ? "database" : "manual";
    if (folder.order) folder.order = saved;
    if (folderNote) { folder.folderNote = saved; if (saved.card) folder.draftCard = saved.card; }
    state.dirty = JSON.stringify(currentOrderValues()) !== JSON.stringify(values);
    renderExportState();
    renderOrderHeading();
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
    ...(!isWorkOrderPath(state.folder?.path) && hasDescendantTodos(state.folder) && Array.isArray(state.folder?.purchase_items) ? { purchase_items: state.folder.purchase_items.map((item) => ({ ...item, suppliers: [...(item.suppliers || [])] })) } : {}),
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
  $("orderExportState").textContent = !order ? "" : order.storage === "database" ? "Сохранено в базе" : order.sync_error ? "Сохранено в базе · выгрузка в очереди: " + order.sync_error : order.sync_pending ? "Сохранено в базе · ожидает выгрузки в папку" : "Выгружено в !.txt";
  renderPurchaseSaveState();
}

function isObjectOrderList() {
  return state.view === "folder" && state.folder?.folderKind === "object";
}

function hasOrderList() {
  return state.view === "orders" || isObjectOrderList();
}

function orderListRows() {
  return isObjectOrderList() ? state.objectOrders : state.orders;
}

function findListOrder(path) {
  return orderListRows().find((order) => order.path === path) || state.orders.find((order) => order.path === path);
}

let homeFiltersOpen = false;

const orderGroupStoragePrefix = "zigzag.order-groups.v1:";

function orderGroupScope() {
  return isObjectOrderList() ? "object:" + state.folder.path.normalize("NFC") : "main";
}

function orderGroupCollapsed(scope, group) {
  const key = orderGroupStoragePrefix + JSON.stringify([scope, group]);
  if (!state.collapsedOrderGroups.has(key)) {
    let collapsed = false;
    try { collapsed = localStorage.getItem(key) === "1"; } catch (_) { /* Keep groups usable when browser storage is unavailable. */ }
    state.collapsedOrderGroups.set(key, collapsed);
  }
  return state.collapsedOrderGroups.get(key);
}

function applyOrderGroupVisibility(button) {
  const collapsed = orderGroupCollapsed(button.dataset.orderGroupScope, button.dataset.orderGroupToggle);
  button.setAttribute("aria-expanded", String(!collapsed));
  $("ordersTableBody").querySelectorAll("[data-order-group-row]").forEach((row) => {
    if (row.dataset.orderGroupRow === button.dataset.orderGroupToggle) row.hidden = collapsed;
  });
}

function toggleOrderGroup(button) {
  const scope = button.dataset.orderGroupScope, group = button.dataset.orderGroupToggle;
  const key = orderGroupStoragePrefix + JSON.stringify([scope, group]);
  const collapsed = !orderGroupCollapsed(scope, group);
  state.collapsedOrderGroups.set(key, collapsed);
  try { localStorage.setItem(key, collapsed ? "1" : "0"); }
  catch (_) { notify("Не удалось запомнить вид группы в браузере. После обновления страницы он может сброситься."); }
  applyOrderGroupVisibility(button);
}

function focusOrderGroup(group) {
  if (!hasOrderList() || !group) return;
  [...$("ordersTableBody").querySelectorAll("[data-order-group-toggle]")].find((button) => button.dataset.orderGroupToggle === group)?.focus({ preventScroll: true });
}

function mountOrderList() {
  const object = isObjectOrderList(), workspace = $("ordersWorkspace");
  const home = state.view === "orders", pane = document.querySelector(".content-pane");
  pane.classList.toggle("home-view", home);
  const heading = pane.querySelector(".order-heading");
  heading.append($("homeToolbarSlot"));
  heading.firstElementChild.append($("homeSyncSlot"));
  $("homeToolbarSlot").hidden = !home;
  $("homeSyncSlot").hidden = !home;
  const toolbarSlot = $(home ? "homeToolbarSlot" : "listToolbarSlot");
  if ($("ordersToolbar").parentElement !== toolbarSlot) toolbarSlot.append($("ordersToolbar"));
  const syncSlot = $(home ? "homeSyncSlot" : "listSyncSlot");
  if ($("ordersSyncState").parentElement !== syncSlot) syncSlot.append($("ordersSyncState"));
  $("orderListControls").open = object || homeFiltersOpen;
  $("homeCalendar").hidden = !home;
  $("objectOrdersSection").hidden = !object;
  if (object) {
    if (workspace.parentElement !== $("objectOrdersSlot")) $("objectOrdersSlot").append(workspace);
  } else if (workspace.parentElement !== $("folderView").parentElement) $("folderView").before(workspace);
  workspace.hidden = !hasOrderList();
  if (home) renderHomeCalendar();
  workspace.setAttribute("aria-label", object ? "Заказы объекта" : "Все заказы");
  $("syncOrdersButton").hidden = object;
  const scope = object ? state.folder.path : "main";
  if (hasOrderList() && scope !== state.orderListScope) {
    state.orderListScope = scope;
    state.orderFilter = "all";
    state.financialFilter = "all";
    state.orderQuery = "";
    $("orderSearch").value = "";
  }
}

async function loadOrders() {
  const version = ++state.ordersRequest;
  const objectPath = isObjectOrderList() ? state.folder.path : null;
  const result = await request("/api/orders");
  if (version !== state.ordersRequest) return;
  if (objectPath) {
    try {
      const object = await request(apiUrl("/api/object-orders", objectPath, { show_inactive: state.showInactive ? "1" : "0" }));
      if (version !== state.ordersRequest) return;
      if (isObjectOrderList() && state.folder.path === objectPath) {
        state.objectOrders = object.orders;
        state.objectOrdersError = object.error || "";
      }
    } catch (error) {
      if (version !== state.ordersRequest) return;
      if (isObjectOrderList() && state.folder.path === objectPath) state.objectOrdersError = "Показаны последние данные: " + error.message;
    }
  }
  state.orders = result.orders;
  state.deadlineWeekOptions = result.deadline_week_options || [];
  state.favoriteOrders = result.favorites || result.orders.filter((order) => order.is_favorite === true);
  state.unregistrations = result.unregistrations || [];
  state.scan = result.scan;
  state.storage = result.storage;
  $("ordersNavCount").textContent = result.orders.length;
  renderFavoriteOrders();
  if (hasOrderList()) renderOrders();
  else if (state.folder?.order) renderCardDeadlines();
}

function orderTodoText(order) {
  return (order.todo_groups || []).map((group) => [group.label, ...(group.items || []).map((item) => item.text)].join(" ")).join(" ");
}

function orderTodoSummary(order) {
  const groups = order.todo_groups || [];
  const count = groups.reduce((total, group) => total + (group.items || []).length, 0);
  const catalog = order.todo_index;
  const warning = catalog?.error ? "Сохранённые задачи · обновление папок: " + catalog.error : !catalog?.checked ? "Задачи папок обновляются…" : "";
  return { groups, count, warning };
}

function renderOrderTodoButton(order) {
  const { groups, count, warning } = orderTodoSummary(order);
  const label = "To-do: " + count + " · " + order.title;
  return '<button type="button" class="order-todo-button' + (!groups.length ? ' empty' : '') + '" data-order-todos="' + escapeHtml(order.path) + '" aria-haspopup="dialog" aria-controls="orderTodoDialog" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(warning || "Открыть актуальные задачи") + '"><span>' + count + '</span>' + icon("chevron") + '</button>';
}

function orderPurchaseSummary(order) {
  const items = order.purchase_items === null ? null : (order.purchase_items || []).filter((item) => !item.done);
  return { items, count: items?.length || 0 };
}

function orderPurchaseText(order) {
  return (orderPurchaseSummary(order).items || []).map((item) => [item.text, ...(item.suppliers || [])].join(" ")).join(" ");
}

function renderOrderPurchaseButton(order) {
  const { items, count } = orderPurchaseSummary(order);
  return '<button type="button" class="order-todo-button' + (items?.length === 0 ? ' empty' : '') + '" data-order-purchases="' + escapeHtml(order.path) + '" aria-haspopup="dialog" aria-controls="orderTodoDialog" aria-label="' + escapeHtml("Закупки: " + count + " · " + order.title) + '" title="Открыть актуальные закупки"><span>' + count + '</span>' + icon("chevron") + '</button>';
}

function renderOrderPurchases(order) {
  const { items } = orderPurchaseSummary(order);
  const contents = items === null ? '<p class="order-todo-empty">Прежние записи закупок — просмотрите в заказе.</p>' : !items.length ? '<p class="order-todo-empty">Актуальных закупок нет.</p>' :
    '<ul class="order-purchase-list">' + items.map((item) => '<li><div class="order-purchase-text"><span aria-hidden="true">○</span><span class="visually-hidden">Нужно закупить: </span><span class="order-todo-text">' + escapeHtml(item.text) + '</span></div>' +
      '<div class="order-purchase-suppliers" aria-label="Выбранные поставщики">' + ((item.suppliers || []).length ? item.suppliers.map((name) => '<span>' + escapeHtml(name) + '</span>').join("") : '<span class="no-supplier">Поставщик не выбран</span>') + '</div></li>').join("") + '</ul>';
  const sync = order.sync_pending ? '<small class="order-todo-state">' + escapeHtml(order.sync_error ? "Сохранено в базе · выгрузка: " + order.sync_error : "Сохранено в базе · ожидает выгрузки") + '</small>' : "";
  return '<div class="order-todos" aria-label="Актуальные закупки заказа">' + contents + sync + '</div>';
}

function renderOrderTodoGroup(group) {
  return '<section class="order-todo-group">' +
    '<button class="order-todo-folder" data-order="' + escapeHtml(group.path) + '" title="' + escapeHtml(group.path) + '">' + escapeHtml(group.label) + '</button>' +
      (group.items === null ? '<small class="order-todo-state">Прежние записи задач — просмотрите в папке</small>' :
        '<ul>' + group.items.map((item) => '<li' + (item.done ? ' class="done"' : '') + '><span aria-hidden="true">' + (item.done ? '✓' : '○') + '</span><span class="visually-hidden">' + (item.done ? 'Выполнено: ' : 'Нужно сделать: ') + '</span><span class="order-todo-text">' + escapeHtml(item.text) + '</span></li>').join("") + '</ul>') +
      (group.sync_pending ? '<small class="order-todo-state">' + escapeHtml(group.sync_error ? "Сохранено в базе · выгрузка: " + group.sync_error : "Сохранено в базе · ожидает выгрузки") + '</small>' : "") + '</section>';
}

function renderOrderTodos(order) {
  const { groups, warning } = orderTodoSummary(order);
  return '<div class="order-todos" aria-label="To-do заказа и вложенных папок">' +
    (groups.length ? groups.map(renderOrderTodoGroup).join("") : '<p class="order-todo-empty">Актуальных задач нет.</p>') +
    (warning ? '<small class="order-todo-state">' + escapeHtml(warning) + '</small>' : '') + '</div>';
}

function renderOrderTodoDialog() {
  if (!$("orderTodoDialog").open) return;
  const order = findListOrder(state.orderTodoPath);
  if (!order) { $("orderTodoDialog").close(); return; }
  const purchases = state.orderTodoKind === "purchases";
  $("orderTodoKindTitle").textContent = purchases ? "Закупки" : "To-do";
  $("orderTodoHint").textContent = purchases ? "Только актуальные закупки" : "Только актуальные задачи";
  $("closeOrderTodos").setAttribute("aria-label", purchases ? "Закрыть закупки" : "Закрыть To-do");
  $("orderTodoBody").setAttribute("aria-label", purchases ? "Актуальные закупки заказа" : "Актуальные задачи заказа и вложенных папок");
  $("orderTodoDialogCount").textContent = purchases ? orderPurchaseSummary(order).count : orderTodoSummary(order).count;
  $("orderTodoOrder").textContent = order.title;
  $("orderTodoOrder").title = order.title;
  $("orderTodoPath").textContent = order.path;
  $("orderTodoPath").title = order.path;
  const markup = purchases ? renderOrderPurchases(order) : renderOrderTodos(order);
  if (state.orderTodoMarkup !== markup) {
    const scroll = $("orderTodoBody").scrollTop;
    $("orderTodoBody").innerHTML = markup;
    state.orderTodoMarkup = markup;
    $("orderTodoBody").scrollTop = scroll;
  }
}

function openOrderTodos(path, kind = "todos") {
  if (!findListOrder(path)) return;
  state.orderTodoPath = path;
  state.orderTodoKind = kind;
  state.orderTodoMarkup = null;
  $("orderTodoBody").replaceChildren();
  $("orderTodoDialog").showModal();
  renderOrderTodoDialog();
  $("orderTodoBody").scrollTop = 0;
}

function orderRowSaving(path) {
  return state.flagSaving.has(path) || state.favoriteSaving.has(path) || state.orderStatusSaving.has(path) || state.deadlineSaving.has(path) || state.calendarMoving.has(path) || (state.calendarEvent?.path === path && state.calendarEvent.saving);
}

function orderDeadlineRange(weeks) {
  if (!weeks?.length) return "";
  const sorted = [...weeks].sort();
  const end = new Date(sorted.at(-1) + "T00:00:00Z");
  end.setUTCDate(end.getUTCDate() + 6);
  const startLabel = sorted[0].slice(8, 10) + "." + sorted[0].slice(5, 7);
  const endLabel = String(end.getUTCDate()).padStart(2, "0") + "." + String(end.getUTCMonth() + 1).padStart(2, "0");
  return startLabel + "-" + endLabel;
}

const deadlineMonthNames = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
const deadlineMonthHues = [335, 270, 15, 185, 135, 90, 55, 30, 10, 160, 280, 215];

function shiftDeadlineWeek(start, offset) {
  const date = new Date(start + "T00:00:00Z");
  date.setUTCDate(date.getUTCDate() + offset * 7);
  const value = date.toISOString().slice(0, 10);
  const end = new Date(date);
  end.setUTCDate(end.getUTCDate() + 6);
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && value >= "0001-01-01" && end.getUTCFullYear() <= 9999 ? value : null;
}

function deadlineWeekInfo(start) {
  // Thursday identifies the month containing most days of this ISO week.
  const thursday = new Date(start + "T00:00:00Z");
  thursday.setUTCDate(thursday.getUTCDate() + 3);
  const year = thursday.getUTCFullYear();
  const first = new Date(thursday);
  first.setUTCMonth(0, 1);
  const month = thursday.getUTCMonth();
  return { start, number: Math.ceil(((thursday - first) / 86400000 + 1) / 7), year, month,
    monthYear: year + "-" + month, hue: deadlineMonthHues[month], label: deadlineWeekDates(start),
    current: start === state.deadlineWeekOptions[0]?.start };
}

function renderDeadlineMonthLegend(options) {
  const months = [...new Map(options.map((week) => { const info = deadlineWeekInfo(week.start); return [info.monthYear, info]; })).values()];
  const years = new Set(months.map((month) => month.year));
  return '<div class="deadline-month-legend" aria-label="Цвета месяцев">' + months.map((month) =>
    '<span style="--deadline-month-hue:' + month.hue + '" title="' + deadlineMonthNames[month.month] + ' ' + month.year + '">' +
    deadlineMonthNames[month.month] + (years.size > 1 ? ' ' + month.year : '') + '</span>').join("") + '</div>';
}

function renderOrderDeadlines(order, { options = state.deadlineWeekOptions, card = false, disabled = false } = {}) {
  const unknown = order.deadline_weeks === null;
  const selected = new Set(order.deadline_weeks || []);
  const currentWeek = state.deadlineWeekOptions[0]?.start;
  if (!card && currentWeek) {
    const visible = new Set(options.map((option) => option.start));
    const overdue = [...selected].filter((week) => week < currentWeek && !visible.has(week)).sort();
    options = [...overdue.map((start) => ({ start })), ...options];
  }
  const outside = [...selected].filter((week) => !options.some((option) => option.start === week));
  const comments = card ? [] : Object.entries(order.deadline_comments || {}).filter(([, comment]) => comment.trim()).sort(([first], [second]) => first.localeCompare(second));
  const preview = comments.map(([start, comment]) => deadlineWeekInfo(start).number + '-' + comment.trim()).join(', ');
  const outsideText = unknown ? 'Неизвестный формат сроков' : outside.length ? 'Вне окна: ' + outside.length : '';
  const footer = [outsideText, preview].filter(Boolean).join(' · ');
  const footerHelp = [unknown ? outsideText : outside.length ? 'Начало выбранных недель: ' + outside.join(', ') : '',
    ...comments.map(([start, comment]) => 'Неделя ' + deadlineWeekInfo(start).number + ' · ' + deadlineWeekDates(start) + ': ' + comment)].filter(Boolean).join('\n');
  const range = orderDeadlineRange(order.deadline_weeks);
  let previous;
  return '<div class="order-deadline-line' + (card ? ' order-card-deadline-line' : '') + '"><div class="order-deadline-buttons"><div class="order-deadline-weeks" role="group" aria-label="Сроки · ' + escapeHtml(order.title) + '">' +
    options.map((option) => {
      const week = deadlineWeekInfo(option.start);
      const overdue = selected.has(week.start) && currentWeek && week.start < currentWeek;
      const comment = order.deadline_comments?.[week.start] || "";
      const help = (overdue ? "Просрочено · " : "") + week.label + (comment ? "\n" + comment : "");
      const gap = card && previous && shiftDeadlineWeek(previous, 1) !== week.start ? '<span class="deadline-week-gap" title="Между этими неделями есть пропуск">…</span>' : '';
      previous = week.start;
      return gap + '<button type="button" class="deadline-week' + (week.current ? ' current' : '') + (overdue ? ' overdue' : '') +
      '" style="--deadline-month-hue:' + week.hue +
      '" data-order-deadline="' + escapeHtml(order.path) + '" data-deadline-week="' + week.start +
      '" data-order-id="' + escapeHtml(order.id) + '" data-revision="' + order.revision + '" aria-pressed="' + selected.has(week.start) +
      '" aria-label="' + escapeHtml("Неделя " + week.number + " · " + help) + '" title="' + escapeHtml(help) +
      '"' + (disabled || unknown || order.registered === false || orderRowSaving(order.path) ? ' disabled' : '') + '>' + week.number + '</button>';
    }).join("") + '</div>' +
    (!card && footer ? '<small class="order-deadline-summary" title="' + escapeHtml(footerHelp) + '">' + escapeHtml(footer) + '</small>' : '') + '</div>' +
    (range ? '<span class="order-deadline-range">' + escapeHtml(range) + '</span>' : '') + '</div>' +
    (card && unknown ? '<small class="order-deadline-outside">Неизвестный формат сроков</small>' : card && outside.length ?
      '<small class="order-deadline-outside" title="Начало выбранных недель: ' + outside.join(', ') + '">Вне окна: ' + outside.length + '</small>' : '');
}

function deadlineWeekDates(week) {
  const end = new Date(week + "T00:00:00Z");
  end.setUTCDate(end.getUTCDate() + 6);
  const dateLabel = (value) => value.slice(8, 10) + "." + value.slice(5, 7) + "." + value.slice(0, 4);
  return dateLabel(week) + " — " + dateLabel(end.toISOString().slice(0, 10));
}

function renderCardDeadlines() {
  const folder = state.folder, order = folder?.order, panel = $("orderCardDeadlines");
  panel.hidden = !order || isWorkOrderPath(folder.path);
  if (panel.hidden) return;
  const unknown = order.deadline_weeks === null;
  const disabled = unknown || Boolean(folder.deadlineConflict) || orderRowSaving(order.path) || Boolean(state.saving);
  const visible = folder.deadlineVisibleWeeks ||= new Set();
  for (const week of state.deadlineWeekOptions) visible.add(week.start);
  for (const week of new Set([...(order.deadline_weeks || []), ...Object.keys(order.deadline_comments || {})])) {
    for (const offset of [-1, 0, 1]) { const start = shiftDeadlineWeek(week, offset); if (start) visible.add(start); }
  }
  const options = [...visible].sort().map((start) => ({ start }));
  const markup = renderDeadlineMonthLegend(options) + renderOrderDeadlines(order, { options, card: true, disabled });
  if ($("orderCardDeadlineList").innerHTML !== markup) $("orderCardDeadlineList").innerHTML = markup;
  $("orderCardDeadlineEarlier").disabled = disabled || !options.length || !shiftDeadlineWeek(options[0].start, -1);
  $("orderCardDeadlineLater").disabled = disabled || !options.length || !shiftDeadlineWeek(options.at(-1).start, 1);
  $("orderCardDeadlineState").textContent = folder.deadlineError || (unknown ? "Неизвестный формат сроков сохранён без изменений" :
    state.deadlineSaving.has(order.path) ? "Сохраняю сроки…" :
    "Нажми на номер недели, чтобы отметить или снять её. Даты — при наведении.");
  renderDeadlineComments(folder);
}

function renderDeadlineComments(folder) {
  const order = folder.order, comments = order.deadline_comments || {}, unknown = order.deadline_comments === null;
  const drafts = folder.deadlineCommentDrafts ||= new Map();
  const container = $("orderDeadlineComments"), scope = order.id + "|" + folder.path;
  if (container.dataset.scope !== scope) { container.replaceChildren(); container.dataset.scope = scope; }
  const weeks = new Set([...(order.deadline_weeks || []), ...Object.keys(comments), ...drafts.keys()]);
  const rows = new Map([...container.children].map((row) => [row.dataset.weekCommentRow, row]));
  let before = container.firstElementChild;
  for (const week of [...weeks].sort()) {
    let draft = drafts.get(week);
    if (!draft) { draft = { value: comments[week] || "", saved: comments[week] || "", dirty: false, saving: false, error: "" }; drafts.set(week, draft); }
    if (!draft.dirty && !draft.saving) draft.value = draft.saved = comments[week] || "";
    const info = deadlineWeekInfo(week);
    let row = rows.get(week);
    if (!row) {
      row = document.createElement("div");
      row.className = "deadline-comment-row";
      row.dataset.weekCommentRow = week;
      row.innerHTML = '<span class="deadline-week deadline-comment-week" role="img" aria-label="Неделя ' + info.number +
        '" style="--deadline-month-hue:' + info.hue + '">' + info.number + '</span><input type="text" maxlength="1000" autocomplete="off" data-deadline-comment="' +
        week + '" placeholder="Комментарий к неделе" aria-label="Комментарий к неделе ' + info.number + ' · ' + info.label + '">';
    }
    row.title = info.label + (order.deadline_weeks?.includes(week) ? "" : " · Отметка недели снята");
    const input = row.querySelector("input");
    if (input.value !== draft.value) input.value = draft.value;
    input.title = draft.value;
    input.disabled = unknown;
    input.readOnly = Boolean(folder.deadlineConflict);
    input.setAttribute("aria-invalid", draft.error ? "true" : "false");
    if (row !== before) container.insertBefore(row, before);
    before = row.nextElementSibling;
  }
  const values = [...drafts.values()], error = values.find((draft) => draft.error)?.error;
  $("orderDeadlineCommentsState").textContent = unknown ? "Неизвестный формат комментариев сохранён без изменений" : error ||
    (values.some((draft) => draft.saving) ? "Сохраняю комментарии…" : values.some((draft) => draft.dirty) ? "Есть несохранённые комментарии" :
      weeks.size ? "Комментарии сохранены" : "Отметь неделю, чтобы добавить комментарий");
  $("retryDeadlineComments").hidden = !error || unknown || Boolean(folder.deadlineConflict);
  $("retryDeadlineComments").disabled = Boolean(folder.deadlineCommentFlush);
}

function hasPendingDeadlineComments(folder = state.folder) {
  return Boolean(folder?.deadlineCommentFlush) || [...(folder?.deadlineCommentDrafts?.values() || [])].some((draft) => draft.dirty || draft.saving);
}

function deadlineCommentInput(event) {
  const input = event.target.closest("[data-deadline-comment]"), folder = state.folder;
  const draft = folder?.deadlineCommentDrafts?.get(input?.dataset.deadlineComment);
  if (!input || !draft) return;
  draft.value = input.value;
  draft.dirty = draft.value !== draft.saved;
  draft.error = "";
  clearTimeout(folder.deadlineCommentTimer);
  renderDeadlineComments(folder);
  if (!event.isComposing) folder.deadlineCommentTimer = setTimeout(() => run(() => flushDeadlineComments(folder)), 700);
}

function applyOrderRecord(folder, saved) {
  ++state.ordersRequest;
  for (const orders of [state.orders, state.favoriteOrders, state.objectOrders]) {
    const current = orders.find((order) => order.path === saved.path);
    if (current && current.id === saved.id && current.revision <= saved.revision) Object.assign(current, saved);
  }
  if (folder) folder.order = saved;
}

function flushDeadlineComments(folder = state.folder) {
  if (!folder?.order) return Promise.resolve();
  clearTimeout(folder.deadlineCommentTimer);
  if (folder.deadlineCommentFlush) return folder.deadlineCommentFlush;
  if (![...(folder.deadlineCommentDrafts?.values() || [])].some((draft) => draft.dirty)) return Promise.resolve();
  const pending = (async () => {
    while (true) {
      while (state.saving) await state.saving;
      if (state.folder !== folder) throw new Error("Комментарий остался в открытой карточке. Вернись к ней для сохранения.");
      const entry = [...folder.deadlineCommentDrafts].find(([, draft]) => draft.dirty);
      if (!entry) return;
      const [week, draft] = entry, value = draft.value, order = folder.order;
      if (folder.deadlineConflict) throw new Error(folder.deadlineError || "Обнови карточку перед сохранением комментария. Ввод остался в поле.");
      draft.saving = true;
      draft.error = "";
      state.deadlineSaving.add(order.path);
      ++state.ordersRequest;
      const saving = request("/api/order-deadline-comment", { path: order.path, id: order.id, revision: order.revision, week, comment: value }).then((saved) => {
        applyOrderRecord(folder, saved);
        draft.saved = value;
        draft.dirty = draft.value !== value;
      });
      state.saving = saving;
      renderOrderHeading();
      renderCardDeadlines();
      try {
        await saving;
      } catch (error) {
        folder.deadlineConflict = error.status === 409;
        draft.error = error.message + " Текст остался в поле." + (folder.deadlineConflict ? " Обнови карточку перед повтором." : "");
        if (folder.deadlineConflict) folder.deadlineError = draft.error;
        throw error;
      } finally {
        if (state.saving === saving) state.saving = null;
        state.deadlineSaving.delete(order.path);
        draft.saving = false;
        if (state.folder === folder) { renderOrderHeading(); renderStatus(); }
      }
    }
  })();
  folder.deadlineCommentFlush = pending.finally(() => {
    folder.deadlineCommentFlush = null;
    if (state.folder === folder) renderDeadlineComments(folder);
  });
  return folder.deadlineCommentFlush;
}

function expandCardDeadlineWeeks(direction) {
  const folder = state.folder;
  if (!folder?.deadlineVisibleWeeks?.size) return;
  const weeks = [...folder.deadlineVisibleWeeks].sort(), edge = direction < 0 ? weeks[0] : weeks.at(-1);
  for (let offset = 1; offset <= 10; offset++) {
    const week = shiftDeadlineWeek(edge, offset * direction);
    if (week) folder.deadlineVisibleWeeks.add(week);
  }
  renderCardDeadlines();
}

function focusOrderDeadline(path, week) {
  if (!hasOrderList() || !path || !week) return false;
  const button = [...$("ordersTableBody").querySelectorAll("[data-order-deadline]")].find((item) =>
    item.dataset.orderDeadline === path && item.dataset.deadlineWeek === week);
  button?.focus({ preventScroll: true });
  return Boolean(button);
}

async function toggleOrderDeadline(button) {
  const path = button.dataset.orderDeadline, week = button.dataset.deadlineWeek;
  const selected = button.getAttribute("aria-pressed") !== "true";
  if (state.folder?.path === path) await flushDeadlineComments();
  return changeOrderDeadline({ path, id: button.dataset.orderId, revision: Number(button.dataset.revision), week, selected }, button);
}

async function changeOrderDeadline({ path, id, revision, week, selected }, button) {
  const folder = state.folder?.path === path ? state.folder : null;
  if (orderRowSaving(path) || (folder?.order || findListOrder(path))?.registered === false || folder?.deadlineConflict) return;
  state.deadlineSaving.add(path);
  ++state.ordersRequest;
  if (folder) { folder.deadlineError = ""; renderOrderHeading(); renderCardDeadlines(); }
  $("ordersTableBody").querySelectorAll("[data-order-deadline], [data-order-status], [data-order-favorite], [data-order-flag]").forEach((control) => {
    if ((control.dataset.orderDeadline || control.dataset.orderStatus || control.dataset.orderFavorite || control.dataset.orderFlag) === path) control.disabled = true;
  });
  let saving;
  try {
    if (folder) {
      if (state.saving) await state.saving;
      if (state.folder !== folder || folder.order?.id !== id) return;
      revision = folder.order.revision;
    }
    saving = request("/api/order-deadline-week", { path, id, revision, week, selected }).then((saved) => applyOrderRecord(folder, saved));
    // Card edits wait for this partial write; editor fields and dirty state stay intact.
    if (folder) state.saving = saving;
    await saving;
    notify(selected ? "Неделя отмечена в сроках" : "Отметка недели снята");
  } catch (error) {
    if (folder) {
      folder.deadlineConflict = error.status === 409;
      folder.deadlineError = error.message + (folder.deadlineConflict ? " Обнови карточку перед следующей правкой сроков. Введённые поля остались в редакторе." : "");
    }
    try { await loadOrders(); } catch (_) { /* Keep the last loaded list while offline. */ }
    throw error;
  } finally {
    if (saving && state.saving === saving) state.saving = null;
    state.deadlineSaving.delete(path);
    if (folder && state.folder === folder) {
      renderOrderHeading();
      renderStatus();
      renderCardDeadlines();
      const focus = [...$("orderCardDeadlineList").querySelectorAll("[data-deadline-week]")].find((item) => item.dataset.deadlineWeek === week);
      if (document.activeElement === button || document.activeElement === document.body) (focus || $("orderCardDeadlineEarlier")).focus({ preventScroll: true });
    }
    if (hasOrderList()) {
      const restoreFocus = document.activeElement === button || document.activeElement === document.body;
      renderOrders({ force: true });
      if (restoreFocus && !focusOrderDeadline(path, week)) $("orderSearch").focus({ preventScroll: true });
    }
  }
}

function renderOrderFlagButton(order) {
  const unknown = order.is_flagged === null;
  const label = (order.is_flagged ? "Снять флажок" : "Поставить флажок") + " · " + order.title;
  return '<button type="button" class="order-flag-button" data-order-flag="' + escapeHtml(order.path) +
    '" data-order-id="' + escapeHtml(order.id) + '" data-revision="' + order.revision + '" aria-pressed="' + Boolean(order.is_flagged) +
    '" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(unknown ? "Неизвестная отметка флажка сохранена без изменений" : label) +
    '"' + (unknown || order.registered === false || orderRowSaving(order.path) ? ' disabled' : '') + '>' + icon("flag") + '</button>';
}

function focusOrderFlag(path) {
  if (!hasOrderList() || !path) return;
  [...$("ordersTableBody").querySelectorAll("[data-order-flag]")].find((button) => button.dataset.orderFlag === path)?.focus({ preventScroll: true });
}

async function toggleOrderFlag(button) {
  const path = button.dataset.orderFlag, order = findListOrder(path);
  if (!order || order.registered === false || order.is_flagged === null || orderRowSaving(path)) return;
  const payload = { path, id: button.dataset.orderId, revision: Number(button.dataset.revision), is_flagged: button.getAttribute("aria-pressed") !== "true" };
  state.flagSaving.add(path);
  ++state.ordersRequest;
  button.setAttribute("aria-busy", "true");
  $("ordersTableBody").querySelectorAll("[data-order-flag], [data-order-favorite], [data-order-status], [data-order-deadline]").forEach((control) => {
    if ((control.dataset.orderFlag || control.dataset.orderFavorite || control.dataset.orderStatus || control.dataset.orderDeadline) === path) control.disabled = true;
  });
  try {
    applyOrderRecord(null, await request("/api/order-flag", payload));
  } catch (error) {
    try { await loadOrders(); } catch (_) { /* Keep the last loaded list while offline. */ }
    throw error;
  } finally {
    state.flagSaving.delete(path);
    if (hasOrderList()) {
      const restoreFocus = document.activeElement === button || document.activeElement === document.body;
      renderOrders();
      if (restoreFocus) focusOrderFlag(path);
    }
  }
}

function renderOrderFavoriteButton(order) {
  const unknown = order.is_favorite === null;
  const label = (order.is_favorite ? "Убрать из избранного" : "Добавить в избранное") + " · " + order.title;
  return '<button type="button" class="order-favorite-button" data-order-favorite="' + escapeHtml(order.path) + '" aria-pressed="' + Boolean(order.is_favorite) + '" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(unknown ? "Неизвестный раздел «Избранное» в !.txt сохранён без изменений" : label) + '"' + (unknown || order.registered === false || orderRowSaving(order.path) ? ' disabled' : '') + '><span aria-hidden="true">' + (order.is_favorite ? '★' : '☆') + '</span></button>';
}

function focusOrderFavorite(path) {
  if (!hasOrderList() || !path) return;
  $("ordersTableBody").querySelectorAll("[data-order-favorite]").forEach((button) => {
    if (button.dataset.orderFavorite === path) button.focus({ preventScroll: true });
  });
}

async function toggleOrderFavorite(path) {
  const folder = state.folder?.path === path ? state.folder : null;
  if (folder) await flushDeadlineComments(folder);
  let order = folder?.order || findListOrder(path);
  if (!order || order.registered === false || order.is_favorite === null || orderRowSaving(path)) return;
  state.favoriteSaving.add(path);
  ++state.ordersRequest;
  if (hasOrderList()) renderOrders();
  else renderOrderHeading();
  if (folder) renderCardDeadlines();
  let saving;
  try {
    if (folder) {
      if (state.saving) await state.saving;
      if (state.folder !== folder || !folder.order) return;
      order = folder.order;
    }
    saving = request("/api/order-favorite", { path, revision: order.revision, is_favorite: !order.is_favorite }).then((saved) => {
      ++state.ordersRequest;
      for (const records of [state.orders, state.objectOrders]) {
        const current = records.find((item) => item.path === path);
        if (current && current.id === saved.id && current.revision <= saved.revision) Object.assign(current, saved);
      }
      state.favoriteOrders = state.favoriteOrders.filter((item) => item.path !== path);
      if (saved.is_favorite === true) state.favoriteOrders.push(saved);
      if (folder) folder.order = saved;
    });
    // Serialize card saves with the star while leaving unsaved editor values intact.
    if (folder) state.saving = saving;
    await saving;
  } catch (error) {
    await loadOrders();
    throw error;
  } finally {
    if (saving && state.saving === saving) state.saving = null;
    state.favoriteSaving.delete(path);
    renderFavoriteOrders();
    if (hasOrderList()) renderOrders();
    else {
      renderOrderHeading();
      renderExportState();
      renderStatus();
    }
    focusOrderFavorite(path);
  }
}

function orderShownOnMain(order) {
  return order.registered !== false && !["cancelled", "done"].includes(order.status);
}

function orderMatchesProduction(order, filter) {
  if (filter === "unregistered") return order.registered === false;
  return filter === "all" ? isObjectOrderList() || orderShownOnMain(order) : order.status === filter;
}

function orderListGroups() {
  const object = isObjectOrderList();
  const groups = orderStatusGroups.map((group, index) => {
    let statuses = group.length ? group : Object.keys(statusLabels).filter((status) => !orderStatusGroups.some((group) => group.includes(status)));
    if (object) statuses = statuses.filter((status) => orderShownOnMain({ status }));
    return { key: ["preparation", "production", "other"][index], statuses, label: index < 2 ? statuses.map((status) => statusLabels[status]).join(" · ") : "Остальные" };
  });
  if (object) {
    const statuses = Object.keys(statusLabels).filter((status) => !orderShownOnMain({ status }));
    groups.push({ key: "hidden", statuses, label: [...statuses.map((status) => statusLabels[status]), "Не добавлены"].join(" · ") });
  }
  return groups;
}

function renderProductionStatusOptions(selected) {
  return orderListGroups().map((group, index) => {
    return '<optgroup label="— ' + (index + 1) + '-я группа —">' + group.statuses.map((status) =>
      '<option value="' + status + '"' + (selected === status ? ' selected' : '') + '>' +
      statusLabels[status] + '</option>').join("") + '</optgroup>';
  }).join("");
}

function renderOrderProductionStatus(order) {
  if (order.registered === false) return '<span class="status-badge" data-status="' + escapeHtml(order.status) + '">' + escapeHtml(statusLabels[order.status] || order.status || "—") + '</span>';
  const known = Object.hasOwn(statusLabels, order.status);
  return '<select class="status-badge order-status-select" data-status="' + escapeHtml(order.status) +
    '" data-order-status="' + escapeHtml(order.path) + '" data-revision="' + order.revision +
    '" aria-label="Производственный статус · ' + escapeHtml(order.title) + '"' +
    (orderRowSaving(order.path) || !known ? ' disabled' : '') + '>' +
    (!known ? '<option selected>' + escapeHtml(order.status) + '</option>' : '') +
    renderProductionStatusOptions(order.status) + '</select>';
}

async function changeOrderProductionStatus(select) {
  const path = select.dataset.orderStatus, status = select.value, revision = Number(select.dataset.revision);
  if (orderRowSaving(path) || findListOrder(path)?.registered === false) return;
  state.orderStatusSaving.add(path);
  ++state.ordersRequest;
  select.disabled = true;
  select.setAttribute("aria-busy", "true");
  $("ordersTableBody").querySelectorAll("[data-order-favorite], [data-order-deadline], [data-order-flag]").forEach((button) => {
    if ((button.dataset.orderFavorite || button.dataset.orderDeadline || button.dataset.orderFlag) === path) button.disabled = true;
  });
  try {
    const saved = await request("/api/order-status", { path, revision, status });
    ++state.ordersRequest;
    for (const orders of [state.orders, state.favoriteOrders, state.objectOrders]) {
      const current = orders.find((order) => order.path === path);
      if (current && current.revision <= saved.revision) Object.assign(current, saved);
    }
    renderFavoriteOrders();
    notify("Статус: " + statusLabels[saved.status]);
  } catch (error) {
    try { await loadOrders(); } catch (_) { /* Keep the last loaded list if the server is unavailable. */ }
    throw error;
  } finally {
    state.orderStatusSaving.delete(path);
    if (hasOrderList()) {
      const restoreFocus = document.activeElement === select || document.activeElement === document.body;
      renderOrders({ force: true });
      if (restoreFocus) {
        const next = [...$("ordersTableBody").querySelectorAll("[data-order-status]")].find((item) => item.dataset.orderStatus === path);
        (next || $("orderSearch")).focus({ preventScroll: true });
      }
    }
  }
}

function renderOrderComment(order) {
  const firstLine = String(order.note || "").split(/\r\n?|\n/, 1)[0].trim();
  return '<span class="order-row-comment' + (!firstLine ? ' empty' : '') + '" title="' + escapeHtml(firstLine) + '">' + escapeHtml(firstLine || "—") + '</span>';
}

function renderOrderLocationLink(label, path) {
  return path ? '<a class="order-location-link" data-order-location="' + escapeHtml(path) + '" href="?path=' +
    encodeURIComponent(path) + '">' + escapeHtml(label || "—") + '</a>' : escapeHtml(label || "—");
}

function compareOrderText(first, second) {
  first = String(first ?? "").normalize("NFC");
  second = String(second ?? "").normalize("NFC");
  return first.localeCompare(second, "ru", { numeric: true }) || (first < second ? -1 : first > second ? 1 : 0);
}

function compareOrders(a, b, key = state.orderSort, direction = state.orderDirection) {
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
    const labels = key === "status" ? statusLabels : key === "financial_status" ? financialStatusLabels : null;
    const first = labels ? labels[a[key]] || a[key] : a[key];
    const second = labels ? labels[b[key]] || b[key] : b[key];
    const valueOrder = typeof first === "string" ? compareOrderText(first, second) : first - second;
    if (valueOrder) return direction * valueOrder;
  }
  return compareOrderText(a.title, b.title) || compareOrderText(a.path, b.path) || compareOrderText(a.id, b.id);
}

function renderHomeCalendar() {
  HomeCalendar.show([...state.orders].sort((a, b) => compareOrders(a, b, "title", 1)));
}

function renderCalendarEventControls() {
  const edit = state.calendarEvent;
  if (!edit) return;
  $("calendarEventText").disabled = Boolean(edit.saving);
  $("saveCalendarEvent").disabled = Boolean(edit.saving || edit.conflict);
  $("deleteCalendarEvent").hidden = !edit.previous;
  $("deleteCalendarEvent").disabled = Boolean(edit.saving || edit.conflict);
  $("cancelCalendarEvent").disabled = Boolean(edit.saving);
  $("refreshCalendarEvent").hidden = !edit.conflict;
  $("refreshCalendarEvent").disabled = Boolean(edit.saving);
}

function closeCalendarEventMenu(restoreFocus = true) {
  const menu = state.calendarMenu;
  state.calendarMenu = null;
  $("calendarEventMenu").hidden = true;
  if (restoreFocus && menu) (menu.slot.isConnected ? menu.slot : $("calendarViewport")).focus({ preventScroll: true });
}

function calendarEventEntries(order, period) {
  return period === "week" ? order.calendar_week_events : order.calendar_events;
}

function openCalendarEventMenu(slot, x, y) {
  const order = findListOrder(slot.dataset.calendarEvent), date = slot.dataset.calendarDate;
  const period = slot.dataset.calendarPeriod || "day";
  const entries = order && calendarEventEntries(order, period);
  if (!entries?.[date] || order.registered === false || orderRowSaving(order.path)) return;
  closeCalendarEventMenu(false);
  state.calendarMenu = { path: order.path, id: order.id, revision: order.revision, date, period, slot };
  const menu = $("calendarEventMenu");
  $("calendarEventMenuName").textContent = entries[date];
  menu.querySelectorAll('[data-calendar-move="1"], [data-calendar-move="-1"], hr').forEach((item) => { item.hidden = period === "week"; });
  menu.hidden = false;
  const bounds = menu.getBoundingClientRect();
  menu.style.left = Math.max(8, Math.min(x, window.innerWidth - bounds.width - 8)) + "px";
  menu.style.top = Math.max(8, Math.min(y, window.innerHeight - bounds.height - 8)) + "px";
  menu.querySelector("button:not([hidden])").focus({ preventScroll: true });
}

async function moveCalendarEvent(days) {
  const menu = state.calendarMenu;
  if (!menu || orderRowSaving(menu.path)) return;
  closeCalendarEventMenu();
  state.calendarMoving.add(menu.path);
  ++state.ordersRequest;
  try {
    const saved = await request("/api/order-calendar-move", { path: menu.path, id: menu.id, revision: menu.revision, date: menu.date, days, period: menu.period });
    applyOrderRecord(null, saved);
    const target = new Date(menu.date + "T00:00:00Z");
    target.setUTCDate(target.getUTCDate() + days);
    notify((menu.period === "week" ? "Событие перенесено на неделю с " : "Событие перенесено на ") + target.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }));
  } catch (error) {
    notify(error.message, true);
    if (error.status === 409) { try { await loadOrders(); } catch (_) { /* Retain the last loaded calendar. */ } }
  } finally {
    state.calendarMoving.delete(menu.path);
    renderOrders({ force: true });
  }
}

function openCalendarEvent(slot) {
  closeCalendarEventMenu(false);
  const order = findListOrder(slot.dataset.calendarEvent), date = slot.dataset.calendarDate;
  if (!order || order.registered === false || orderRowSaving(order.path)) return;
  const period = slot.dataset.calendarPeriod || "day", entries = calendarEventEntries(order, period);
  if (entries === null) { notify("События этого заказа имеют неизвестный формат и сохранены без изменений", true); return; }
  const previous = entries?.[date] || "";
  state.calendarEvent = { path: order.path, id: order.id, revision: order.revision, date, period, previous, saving: false, conflict: false };
  $("calendarEventTitle").textContent = period === "week" ? "Событие на неделю" : "Событие календаря";
  $("calendarEventOrder").textContent = [order.title, order.client, order.object].filter(Boolean).join(" · ");
  const start = new Date(date + "T00:00:00Z");
  const format = new Intl.DateTimeFormat("ru-RU", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const end = new Date(start); end.setUTCDate(end.getUTCDate() + 6);
  $("calendarEventDate").textContent = period === "week" ? "На неделю: " + format.format(start) + " — " + format.format(end) : format.format(start);
  $("calendarEventText").value = previous;
  $("calendarEventState").textContent = "";
  renderCalendarEventControls();
  $("calendarEventDialog").showModal();
  $("calendarEventText").focus();
}

function closeCalendarEvent() {
  if (state.calendarEvent?.saving) return;
  state.calendarEvent = null;
  $("calendarEventDialog").close();
}

async function saveCalendarEvent(remove = false) {
  const edit = state.calendarEvent;
  if (!edit || edit.saving || edit.conflict) return;
  const text = remove ? "" : $("calendarEventText").value;
  if (!remove && !text.trim()) { $("calendarEventState").textContent = "Введи название события"; return; }
  edit.saving = true;
  ++state.ordersRequest;
  $("calendarEventState").textContent = "Сохраняю…";
  renderCalendarEventControls();
  try {
    const saved = await request("/api/order-calendar-event", { path: edit.path, id: edit.id, revision: edit.revision, date: edit.date, text, period: edit.period });
    applyOrderRecord(null, saved);
    edit.saving = false;
    closeCalendarEvent();
    renderOrders({ force: true });
    notify(remove ? "Событие удалено" : "Событие сохранено");
  } catch (error) {
    edit.conflict = error.status === 409;
    $("calendarEventState").textContent = error.message + (edit.conflict ? " Нажми «Проверить изменения» перед повторным сохранением. Твой текст оставлен в поле." : " Твой текст оставлен в поле.");
  } finally {
    edit.saving = false;
    renderCalendarEventControls();
  }
}

async function refreshCalendarEvent() {
  const edit = state.calendarEvent;
  if (!edit || edit.saving) return;
  edit.saving = true;
  renderCalendarEventControls();
  try {
    const order = await request(apiUrl("/api/order", edit.path));
    if (order.id !== edit.id || calendarEventEntries(order, edit.period) === null) throw new Error("Заказ или формат событий изменён. Ввод сохранён; открой заказ заново.");
    edit.revision = order.revision;
    edit.previous = calendarEventEntries(order, edit.period)?.[edit.date] || "";
    edit.conflict = false;
    applyOrderRecord(null, order);
    $("calendarEventState").textContent = "В базе сейчас: " + (edit.previous || "события нет") + ". Твой текст оставлен в поле; проверь его перед сохранением.";
    renderOrders({ force: true });
  } catch (error) {
    $("calendarEventState").textContent = error.message;
  } finally {
    edit.saving = false;
    renderCalendarEventControls();
    renderOrders({ force: true });
  }
}

function renderOrders({ force = false } = {}) {
  // Replacing a focused native select would close its menu during background polling.
  if (!force && (state.orderStatusSaving.size || state.deadlineSaving.size || state.flagSaving.size || state.calendarMoving.size || state.calendarEvent?.saving || document.activeElement?.dataset.orderStatus)) return;
  const focusedFlag = document.activeElement?.dataset.orderFlag;
  const focusedGroup = document.activeElement?.dataset.orderGroupToggle;
  const focusedFavorite = document.activeElement?.dataset.orderFavorite;
  const focusedDeadline = document.activeElement?.dataset.orderDeadline, focusedWeek = document.activeElement?.dataset.deadlineWeek;
  const orders = orderListRows(), object = isObjectOrderList();
  if (!object) renderHomeCalendar();
  const needle = normalize(state.orderQuery.trim());
  const matching = orders.filter((order) => !needle || normalize([order.client, order.object, order.title, order.path, order.note, orderTodoText(order), orderPurchaseText(order)].join(" ")).includes(needle));
  const productionMatching = matching.filter((order) => state.financialFilter === "all" || order.financial_status === state.financialFilter);
  const financeMatching = matching.filter((order) => orderMatchesProduction(order, state.orderFilter));
  const filtered = productionMatching.filter((order) => orderMatchesProduction(order, state.orderFilter));
  const { orderSort: key, orderDirection: direction } = state;
  filtered.sort((a, b) => compareOrders(a, b, key, direction));
  $(object ? "objectOrdersSummary" : "folderSummary").textContent = filtered.length + " из " + orders.length + " заказов · данные из локальной базы";
  $("orderStatusFilters").innerHTML = Object.entries({ all: object ? "Все" : "Основные", ...statusLabels, ...(object ? { unregistered: "Не добавлены" } : {}) }).map(([status, label]) =>
    '<button data-status="' + status + '" aria-pressed="' + (state.orderFilter === status) + '" class="file-filter' + (state.orderFilter === status ? " active" : "") + '">' + label + '<span>' + productionMatching.filter((order) => orderMatchesProduction(order, status)).length + '</span></button>').join("");
  $("financialStatusFilter").innerHTML = Object.entries({ all: "Все", ...financialStatusLabels }).map(([status, label]) =>
    '<option value="' + status + '">' + label + ' · ' + financeMatching.filter((order) => status === "all" || order.financial_status === status).length + '</option>').join("");
  $("financialStatusFilter").value = state.financialFilter;
  $("orderListControlsLabel").textContent = "Фильтры и итоги" +
    (state.orderFilter !== "all" ? " · " + (statusLabels[state.orderFilter] || "Не добавлены") : "") +
    (state.financialFilter !== "all" ? " · " + financialStatusLabels[state.financialFilter] : "");
  $("orderTotals").innerHTML = [["amount", "Сумма заказов"], ["costs", "Затраты"], ["profit", "Расчётная прибыль"], ["paid", "Оплачено"], ["debt", "Остаток оплаты"]].map(([field, label]) => {
    const known = filtered.filter((order) => order[field] != null);
    const total = known.reduce((sum, order) => sum + order[field], 0);
    return '<div class="order-total"><span>' + label + '</span><strong>' + rubles(known.length ? total : null) + '</strong><small>' + (known.length === filtered.length && filtered.length ? "По всем выбранным заказам" : "Указано: " + known.length + " из " + filtered.length) + '</small></div>';
  }).join("");
  const groupScope = orderGroupScope();
  const groups = orderListGroups().map((group) => ({ ...group, collapsed: orderGroupCollapsed(groupScope, group.key), orders: [] }));
  filtered.forEach((order) => {
    const group = object && !orderShownOnMain(order) ? groups[3] : groups.find((group) => group.statuses.includes(order.status)) || groups[2];
    group.orders.push(order);
  });
  $("ordersTableBody").innerHTML = groups.filter((group) => group.orders.length).map((group) =>
    '<tr class="order-group-divider"><th colspan="8"><button type="button" class="order-group-toggle" data-order-group-toggle="' + group.key +
    '" data-order-group-scope="' + escapeHtml(groupScope) + '" aria-expanded="' + !group.collapsed +
    '"><span class="order-group-chevron" aria-hidden="true">▸</span><span>' + escapeHtml(group.label) +
    '</span><span class="count-badge">' + group.orders.length + '</span></button></th><td class="order-deadline-column">' + renderDeadlineMonthLegend(state.deadlineWeekOptions) + '</td><td colspan="8"></td></tr>' +
    group.orders.map((order) => '<tr data-order-group-row="' + group.key + '"' + (group.collapsed ? ' hidden' : '') + '><td class="order-flag-column">' + renderOrderFlagButton(order) + '</td><td class="order-favorite-column">' + renderOrderFavoriteButton(order) + '</td><td class="order-todo-column">' + renderOrderTodoButton(order) + '</td><td class="order-todo-column">' + renderOrderPurchaseButton(order) + '</td><td class="order-client-column">' + renderOrderLocationLink(order.client, order.client_path) + '</td><td class="order-object-column">' + renderOrderLocationLink(order.object, order.object_path) + '</td><td><button class="order-row-link" data-order="' + escapeHtml(order.path) + '">' + escapeHtml(order.title) + '</button>' + (order.registered === false ? '<span class="order-unregistered-label">Не добавлен</span>' : '') + '<span class="order-row-path">' + escapeHtml(order.path) + '</span></td><td class="order-comment-column">' + renderOrderComment(order) + '</td><td class="order-deadline-column">' + renderOrderDeadlines(order) + '</td><td>' + renderOrderProductionStatus(order) + '</td><td><span class="status-badge" data-financial-status="' + escapeHtml(order.financial_status) + '">' + escapeHtml(financialStatusLabels[order.financial_status] || "Не указан") + '</span></td>' +
    ["amount", "costs", "profit", "paid", "debt"].map((field) => '<td class="order-money' + (order[field] < 0 ? " negative" : "") + '">' + rubles(order[field]) + '</td>').join("") +
    '<td class="order-updated">' + (order.updated ? formatDate(order.updated) : '—') + (order.sync_pending ? '<span class="sync-pending" title="' + escapeHtml(order.sync_error || "Ожидает выгрузки в папку") + '">' + (order.sync_error ? "В очереди · автоповтор" : "Ожидает выгрузки") + '</span>' : '<span class="sync-complete">' + (order.storage === 'database' ? 'В базе' : 'Выгружено') + '</span>') + '</td></tr>').join("")).join("");
  $("ordersEmpty").hidden = Boolean(filtered.length);
  $("ordersEmptyTitle").textContent = orders.length ? "Нет заказов по этому фильтру" : "Заказов пока нет";
  $("ordersEmptyHint").textContent = orders.length ? "Выберите другой статус или измените поисковый запрос." : object ? "Создай заказ в этом объекте или обнови его папки." : "Открой папку заказа в дереве слева и нажми «Добавить в список заказов».";
  const pending = orders.filter((order) => order.sync_pending), errors = pending.filter((order) => order.sync_error);
  const scan = state.scan;
  $("ordersSyncState").textContent = scan?.running ? "Поиск карточек в фоне · просмотрено папок: " + scan.folders + " · добавлено: " + scan.added :
    [scan?.folders ? "Поиск завершён: добавлено " + scan.added + (scan.errors.length ? ", ошибок: " + scan.errors.length : "") : "", errors.length ? "Сохранено в базе · в очереди выгрузки: " + pending.length + " · ошибок: " + errors.length + " · повторим автоматически" : pending.length ? "Ожидает выгрузки: " + pending.length : "Изменения выгружены в папки"].filter(Boolean).join(" · ");
  if (state.storage?.database_only) {
    const storage = state.storage;
    $("ordersSyncState").textContent = "Изменения сохранены в базе" + (storage.running ? " · переношу прежние данные…" : "") +
      (storage.errors.length ? " · перенос ожидает повтора: " + storage.errors.length + " · " + storage.errors.slice(0, 2).map(item => item.path + ": " + item.error).join(" · ") : "") +
      (storage.pending_documents ? " · документов в очереди: " + storage.pending_documents : "") +
      (storage.document_errors.length ? " · " + storage.document_errors[0].error : "");
    const backup = storage.recovery_backup;
    if (backup?.error) $("ordersSyncState").textContent += " · Резервная копия ожидает повтора: " + backup.error;
    else if (backup?.created_at) $("ordersSyncState").textContent += " · Копия в папке iCloud: " + formatDate(Date.parse(backup.created_at) / 1000);
  }
  if (scan?.errors.length) $("ordersSyncState").textContent += " · " + scan.errors.slice(0, 3).join(" · ");
  if (state.unregistrations.length) $("ordersSyncState").textContent += " · Сохранение снятой регистрации: " + state.unregistrations.length + (state.unregistrations.some((item) => item.sync_error) ? " · есть ошибки, повторим выгрузку" : "");
  if (object && state.objectOrdersError) $("ordersSyncState").textContent += " · Список папок неполный: " + state.objectOrdersError;
  $("ordersWorkspace").querySelectorAll("th").forEach((th) => {
    const button = th.querySelector("button[data-sort]");
    if (!button) return;
    const selected = button.dataset.sort === key;
    th.setAttribute("aria-sort", selected ? direction === 1 ? "ascending" : "descending" : "none");
    button.textContent = button.textContent.replace(/ [↕↑↓]$/, "") + (selected ? direction === 1 ? " ↑" : " ↓" : " ↕");
  });
  renderOrderTodoDialog();
  focusOrderFlag(focusedFlag);
  focusOrderFavorite(focusedFavorite);
  focusOrderDeadline(focusedDeadline, focusedWeek);
  focusOrderGroup(focusedGroup);
}

async function showOrders({ history = true } = {}) {
  if ($("orderTodoDialog").open) $("orderTodoDialog").close();
  if ($("previewDialog").open) await closePreview();
  await saveCurrentPrintTask();
  await saveCurrentStatus();
  ++printReadVersion;
  ++state.navigation;
  state.folderRequest?.abort();
  state.view = "orders";
  state.folder = null;
  mountOrderList();
  state.selectedFiles.clear();
  state.imageReport = null;
  state.printTask = null;
  state.selected = "";
  $("folderView").hidden = true;
  $("ordersWorkspace").hidden = false;
  $("openFolderButton").hidden = true;
  $("addOrderButton").hidden = true;
  $("removeOrderButton").hidden = true;
  $("createObjectFolderButton").hidden = true;
  $("groupObjectYearsButton").hidden = true;
  $("createOrderFolderButton").hidden = true;
  $("createEventFolderButton").hidden = true;
  $("renameFolderButton").hidden = true;
  $("deleteEventButton").hidden = true;
  $("openEventTrash").hidden = true;
  $("notice").hidden = true;
  $("loadOrderFilesButton").hidden = true;
  $("breadcrumbs").innerHTML = '<button aria-current="page">Все заказы</button>';
  $("workSupplierName").hidden = true;
  $("folderTitleText").textContent = "Все заказы";
  $("orderFolderName").hidden = true;
  $("orderPageFavorite").hidden = true;
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
  if ($("orderTodoDialog").open) $("orderTodoDialog").close();
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
    if (path) {
      try { order = await request(apiUrl("/api/order", path)); }
      catch (error) { if (error.status !== 404) throw error; }
    }
    let data;
    if (order) {
      const parts = path.split("/");
      data = { path, name: parts.at(-1), client: order.client, status: order.status, financial_status: order.financial_status, note: order.note, todo_items: order.todo_items, purchase_items: order.purchase_items, order,
        breadcrumbs: [{ name: $("rootLabel").textContent, path: "" }, ...parts.map((name, index) => ({ name, path: parts.slice(0, index + 1).join("/") }))],
        directories: [], files: [], counts: {}, warnings: [], fileCount: 0, folderCount: 0, totalSize: 0, view: "files", filesScope: "events", filesLoading: true };
    } else {
      const response = await fetch(folderUrl(path), { signal: state.folderRequest.signal });
      data = await response.json();
      if (!response.ok) throw new Error(data.error || "Не удалось открыть папку");
    }
    if (navigation !== state.navigation) return;
    data.service = Boolean(data.service);
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
    if (data.folderKind === "object") {
      state.objectOrders = data.objectOrders?.orders || [];
      state.objectOrdersError = data.objectOrders?.error || "";
      if (data.objectOrders?.deadline_week_options) state.deadlineWeekOptions = data.objectOrders.deadline_week_options;
    }
    $("fileTrashState").textContent = "";
    state.selectedFiles.clear();
    state.imageReport = null;
    state.printTask = null;
    $("frezaTaskSearch").value = "";
    $("frezaLegacyFolders").open = false;
    state.selected = data.path;
    state.fileType = "all";
    state.fileQuery = "";
    state.limit = 120;
    state.dirty = false;
    if (history) window.history.pushState(null, "", data.path ? "?path=" + encodeURIComponent(data.path) : window.location.pathname);
    renderTree();
    renderFolder();
    run(async () => {
      if (hasDescendantTodos(data) && !data.order) await request("/api/todos-refresh", { path: data.path });
      await loadDescendantTodos(data);
    });
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
    const response = await fetch(folderUrl(path), { signal: state.folderRequest.signal });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Не удалось открыть папку");
    if (navigation !== state.navigation) return;
    const { order, status, financial_status, note, todo_items, purchase_items, noteOnly, registrationPending, registrationError } = state.folder;
    Object.assign(state.folder, data, { order, status, financial_status, note, todo_items, purchase_items, noteOnly, registrationPending, registrationError, filesLoading: false, filesUnavailable: false });
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

function renderFolderRename() {
  const parent = folderParent(state.folderRename.path);
  $("renameFolderDestination").textContent = (parent ? parent + "/" : "") + $("renameFolderName").value.trim().normalize("NFC");
}

async function openFolderRename() {
  if (!state.folder?.canRenameFolder) return;
  await saveCurrentPrintTask();
  await saveCurrentStatus();
  state.folderRename = await request(apiUrl("/api/folder-rename", state.folder.path));
  $("renameFolderSource").textContent = state.folderRename.path;
  $("renameFolderName").value = state.folderRename.name;
  $("renameFolderError").hidden = true;
  renderFolderRename();
  $("renameFolderDialog").showModal();
  $("renameFolderName").focus();
  $("renameFolderName").select();
}

async function submitFolderRename() {
  if (!state.folderRename || state.folderRenaming) return;
  state.folderRenaming = true;
  const controls = ["renameFolderName", "submitRenameFolder", "cancelRenameFolder"];
  controls.forEach((id) => { $(id).disabled = true; });
  $("renameFolderError").hidden = true;
  let result;
  try {
    await saveCurrentStatus();
    result = await request("/api/folder-rename", { path: state.folderRename.path, revision: state.folderRename.revision, name: $("renameFolderName").value });
  } catch (error) {
    $("renameFolderError").textContent = error.message;
    $("renameFolderError").hidden = false;
    return;
  } finally {
    state.folderRenaming = false;
    controls.forEach((id) => { $(id).disabled = false; });
  }
  $("renameFolderDialog").close();
  const moved = (path) => path === result.source || path.startsWith(result.source + "/") ? result.path + path.slice(result.source.length) : path;
  state.expanded = new Set([...state.expanded].map(moved));
  window.history.replaceState(null, "", "?path=" + encodeURIComponent(result.path));
  await reloadClientTrees();
  await navigate(result.path, { history: false });
  await loadOrders();
  notify("Папка переименована");
}

async function showPreview(path) {
  await saveFileComment();
  const file = state.folder.files.find((item) => item.path === path);
  if (!file) return;
  SpreadsheetPreview.close();
  const version = ++previewVersion;
  state.preview = file;
  $("previewNative").hidden = false;
  $("fileCommentLabel").textContent = "Комментарий к файлу";
  $("fileCommentText").maxLength = 100000;
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
  if (["image", "cdr"].includes(file.preview)) {
    media = document.createElement("img");
    media.src = apiUrl(file.preview === "cdr" ? "/api/freza-preview" : "/api/preview", path);
    media.alt = file.name;
    media.addEventListener("error", () => {
      if (version === previewVersion) previewUnavailable("Не удалось показать изображение. Откройте оригинал на Mac.");
    }, { once: true });
  } else if (file.preview === "spreadsheet") {
    SpreadsheetPreview.open($("previewBody"), apiUrl("/api/spreadsheet", path), (message) => {
      if (version === previewVersion) previewUnavailable(message);
    });
    return;
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

async function showInvoicePreview(record) {
  await saveFileComment();
  SpreadsheetPreview.close();
  const version = ++previewVersion;
  const file = { path: record.path, invoice: record.id, name: record.data.original_name, extension: ".pdf" };
  state.preview = file;
  $("previewTitle").textContent = file.name;
  $("previewPath").textContent = record.path;
  $("previewMeta").textContent = "Внешний счёт · " + record.data.date.split("-").reverse().join(".");
  $("previewDownload").href = apiUrl("/api/invoice-pdf", record.path, { id: record.id, download: "1" });
  $("previewFolderNotePath").textContent = state.folder?.path || record.path;
  $("previewFolderNote").value = $("orderNote").value;
  $("previewPrevious").disabled = $("previewNext").disabled = true;
  $("previewNative").hidden = true;
  $("fileCommentLabel").textContent = "Комментарий к счёту";
  $("fileCommentText").maxLength = 5000;
  $("previewBody").textContent = "Загрузка PDF…";
  if (!$("previewDialog").open) $("previewDialog").showModal();
  run(() => loadFileComment(record.path, version));
  try {
    const info = await request(apiUrl("/api/invoice-pdf-info", record.path, { id: record.id }));
    if (version !== previewVersion) return;
    if (!info.pages) throw new Error("В PDF нет страниц");
    showPdfPages(file, info.pages, version);
  } catch (error) {
    if (version === previewVersion) previewUnavailable(error.message);
  }
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
  const invoice = state.preview?.invoice;
  const file = state.folder?.files.find((item) => item.path === path);
  const comment = state.fileComment = { path, invoice, comment_key: file?.comment_key, comment: "", draft: "", loaded: false, loading: true, dirty: false, error: "" };
  $("fileCommentText").value = "";
  renderFileComment();
  try {
    const result = await request(apiUrl(invoice ? "/api/invoice" : "/api/file-comment", path, invoice ? { id: invoice } : {}));
    if (version !== previewVersion || state.fileComment !== comment) return;
    if (state.preview?.path !== path || result.path !== path || (invoice ? result.id !== invoice || result.state !== "external" : !comment.comment_key || result.comment_key !== comment.comment_key)) {
      throw new Error("Комментарий не соответствует файлу и папке. Обновите список файлов");
    }
    const text = invoice ? result.data.comment : result.comment;
    Object.assign(comment, { comment: text, revision: result.revision, loaded: true, loading: false, draft: text });
    if (!invoice) updateFileCommentCaption(path, text, comment.comment_key);
    $("fileCommentText").value = text;
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
  if (state.preview?.path !== comment.path || (comment.invoice ? state.preview.invoice !== comment.invoice : !comment.comment_key)) throw new Error("Откройте нужный файл перед сохранением комментария");
  state.fileCommentSaving = comment.invoice
    ? request("/api/invoice-comment", { path: comment.path, id: comment.invoice, comment: draft, revision: comment.revision })
    : request("/api/file-comment", { path: comment.path, comment_key: comment.comment_key, comment: draft, revision: comment.revision });
  comment.error = "";
  renderFileComment();
  try {
    const saved = await state.fileCommentSaving;
    if (saved.path !== comment.path || (comment.invoice ? saved.id !== comment.invoice : saved.comment_key !== comment.comment_key)) throw new Error("Ответ сохранения относится к другому файлу; ваш текст остался в поле");
    const text = comment.invoice ? saved.data.comment : saved.comment;
    Object.assign(comment, { comment: text, revision: saved.revision, dirty: comment.draft !== text });
    if (comment.invoice) document.dispatchEvent(new Event("manager-invoice-updated"));
    else updateFileCommentCaption(comment.path, text, comment.comment_key);
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
    image.src = apiUrl(file.invoice ? "/api/invoice-pdf-page" : "/api/pdf-page", file.path, { page: current, ...(file.invoice ? { id: file.invoice } : {}) });
    canvas.scrollTop = 0;
  }
  image.addEventListener("error", () => {
    if (version === previewVersion) previewUnavailable(file.invoice ? "Не удалось показать страницу PDF. Повтори открытие или скачай оригинал." : "Не удалось показать страницу PDF. Откройте оригинал на Mac.");
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
  const invoice = state.preview.invoice;
  const button = document.createElement(invoice ? "a" : "button");
  button.className = "primary-button";
  button.textContent = invoice ? "Скачать PDF" : "Открыть на Mac";
  if (invoice) button.href = $("previewDownload").href;
  else button.addEventListener("click", () => run(() => openNative(state.preview.path)));
  wrapper.append(label, text, button);
  $("previewBody").replaceChildren(wrapper);
}

function setPreviewExpanded(expanded) {
  $("previewDialog").classList.toggle("preview-expanded", expanded);
  $("previewExpand").textContent = expanded ? "Свернуть" : "Развернуть";
  $("previewExpand").setAttribute("aria-pressed", String(expanded));
  $("previewExpand").title = expanded ? "Вернуть комментарии" : "Документ на всё окно";
}

function stepPreview(direction) {
  if (!state.preview || state.preview.invoice) return;
  const files = filteredFiles();
  const index = files.findIndex((item) => item.path === state.preview.path);
  if (files[index + direction]) run(() => showPreview(files[index + direction].path));
}

function run(action) {
  Promise.resolve().then(action).catch((error) => notify(error.message || "Не удалось выполнить действие", true));
}

$("folderTree").addEventListener("click", (event) => {
  const group = event.target.closest("[data-catalog-group]");
  if (group) { run(() => navigate(group.dataset.catalogGroup)); return; }
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
  const rows = [...row.closest('[role="tree"]').querySelectorAll(".tree-row")], index = rows.indexOf(row);
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
for (const id of ["auxiliaryButtons", "favoriteOrders", "breadcrumbs", "subfolders", "workOrderFolders", "printLegacyFolderList", "frezaLegacyList"]) {
  $(id).addEventListener("click", (event) => {
    const button = event.target.closest("[data-path]");
    if (button) run(() => navigate(button.dataset.path));
  });
}
$("subfolders").addEventListener("click", (event) => {
  const star = event.target.closest("[data-supplier-favorite]");
  if (star) { run(() => toggleSupplierFavorite(star.dataset.supplierFavorite)); return; }
  const button = event.target.closest("[data-relevance]");
  if (button) run(() => saveEventRelevance(button.dataset.eventPath, button.dataset.relevance));
});
$("frezaTaskSearch").addEventListener("input", renderSubfolders);
$("subfolders").addEventListener("error", (event) => {
  if (event.target instanceof HTMLImageElement) {
    event.target.hidden = true;
    event.target.closest(".freza-task-picture")?.classList.add("preview-unavailable");
  }
}, true);
$("sketchTiles").addEventListener("click", (event) => {
  const status = event.target.closest("[data-sketch-status]");
  const file = event.target.closest("[data-sketch-open]");
  if (status) run(() => saveSketchRelevance(status.dataset.sketchFile, status.dataset.sketchStatus));
  else if (file) run(() => openSketch(file.dataset.sketchOpen, file.dataset.sketchKey));
});
$("sketchTiles").addEventListener("error", (event) => {
  if (event.target instanceof HTMLImageElement) event.target.closest(".sketch-picture")?.classList.add("no-preview");
}, true);
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
    const result = await request(treeUrl("", { q: state.treeQuery }));
    if (version !== treeSearchVersion) return;
    state.searchTree = { children: result.children, groups: result.groups || [] };
    registerNodes([...state.searchTree.children, ...state.searchTree.groups]);
    renderTree();
  }), 250);
});
$("showInactiveClients").addEventListener("click", () => run(async () => {
  const button = $("showInactiveClients");
  button.disabled = true;
  state.showInactive = !state.showInactive;
  button.setAttribute("aria-pressed", String(state.showInactive));
  button.textContent = state.showInactive ? "Скрыть неактивных" : "Показать неактивных";
  try {
    await reloadClientTrees();
    if (state.folder && ["root", "catalog_group"].includes(state.folder.folderKind)) await navigate(state.folder.path, { history: false });
  } finally { button.disabled = false; }
}));
$("clientInactive").addEventListener("change", (event) => run(() => saveClientActivity(event.target.checked)));
$("clientActivityAcceptFile").addEventListener("click", () => run(() => saveClientActivity(false, true)));
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
$("openEventTrash").addEventListener("click", () => run(() => openFileTrash(true)));
$("deleteEventButton").addEventListener("click", () => run(confirmEventRemoval));
$("deleteEventForm").addEventListener("submit", (event) => { event.preventDefault(); run(removeEvent); });
$("cancelDeleteEvent").addEventListener("click", () => $("deleteEventDialog").close());
$("deleteEventDialog").addEventListener("cancel", (event) => { if (state.eventRemoving) event.preventDefault(); });
$("deleteEventDialog").addEventListener("close", () => { state.eventRemoval = null; });
$("closeFileTrash").addEventListener("click", () => $("fileTrashDialog").close());
$("fileTrashList").addEventListener("click", (event) => {
  const eventButton = event.target.closest("[data-restore-event]");
  if (eventButton) { run(() => restoreEventSession(eventButton.dataset.restoreEvent)); return; }
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
$("orderListControls").addEventListener("toggle", () => { if (state.view === "orders") homeFiltersOpen = $("orderListControls").open; });
$("calendarWeeks").addEventListener("click", (event) => {
  const slot = event.target.closest("[data-calendar-event]");
  if (slot && !slot.disabled) { openCalendarEvent(slot); return; }
  const link = event.target.closest("[data-calendar-order]");
  if (link && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) {
    event.preventDefault();
    run(() => navigate(link.dataset.calendarOrder));
  }
});
$("calendarEventForm").addEventListener("submit", (event) => { event.preventDefault(); run(() => saveCalendarEvent()); });
$("calendarWeeks").addEventListener("contextmenu", (event) => {
  const slot = event.target.closest(".calendar-event-slot.has-event");
  if (!slot || slot.disabled) return;
  event.preventDefault();
  openCalendarEventMenu(slot, event.clientX, event.clientY);
});
$("calendarWeeks").addEventListener("keydown", (event) => {
  const slot = event.target.closest(".calendar-event-slot.has-event");
  if (!slot || slot.disabled || !(event.key === "ContextMenu" || (event.shiftKey && event.key === "F10"))) return;
  event.preventDefault();
  const bounds = slot.getBoundingClientRect();
  openCalendarEventMenu(slot, bounds.left, bounds.bottom);
});
$("calendarEventMenu").addEventListener("click", (event) => {
  const button = event.target.closest("[data-calendar-move]");
  if (button) run(() => moveCalendarEvent(Number(button.dataset.calendarMove)));
});
$("calendarEventMenu").addEventListener("keydown", (event) => {
  if (event.key === "Escape") { event.preventDefault(); closeCalendarEventMenu(); return; }
  if (event.key === "Tab") { closeCalendarEventMenu(); return; }
  if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const buttons = [...$("calendarEventMenu").querySelectorAll("button")].filter((item) => !item.hidden), current = buttons.indexOf(document.activeElement);
  const index = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (current + (event.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length;
  buttons[index].focus({ preventScroll: true });
});
document.addEventListener("pointerdown", (event) => { if (state.calendarMenu && !$("calendarEventMenu").contains(event.target)) closeCalendarEventMenu(false); });
window.addEventListener("resize", () => closeCalendarEventMenu(false));
window.addEventListener("scroll", () => { if (state.calendarMenu) closeCalendarEventMenu(false); }, true);
window.addEventListener("blur", () => closeCalendarEventMenu(false));
$("deleteCalendarEvent").addEventListener("click", () => run(() => saveCalendarEvent(true)));
$("refreshCalendarEvent").addEventListener("click", () => run(refreshCalendarEvent));
$("cancelCalendarEvent").addEventListener("click", closeCalendarEvent);
$("calendarEventDialog").addEventListener("cancel", (event) => { event.preventDefault(); closeCalendarEvent(); });
$("financialStatusFilter").addEventListener("change", (event) => { state.financialFilter = event.target.value; renderOrders(); });
$("ordersTableBody").addEventListener("change", (event) => {
  const select = event.target.closest("[data-order-status]");
  if (select) run(() => changeOrderProductionStatus(select));
});
$("ordersTableBody").addEventListener("click", (event) => {
  const groupButton = event.target.closest("[data-order-group-toggle]");
  if (groupButton) { toggleOrderGroup(groupButton); return; }
  const locationLink = event.target.closest("[data-order-location]");
  if (locationLink) {
    if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) {
      event.preventDefault();
      run(() => navigate(locationLink.dataset.orderLocation));
    }
    return;
  }
  const deadlineButton = event.target.closest("[data-order-deadline]");
  if (deadlineButton) { run(() => toggleOrderDeadline(deadlineButton)); return; }
  const flagButton = event.target.closest("[data-order-flag]");
  if (flagButton) { run(() => toggleOrderFlag(flagButton)); return; }
  const favoriteButton = event.target.closest("[data-order-favorite]");
  if (favoriteButton) { run(() => toggleOrderFavorite(favoriteButton.dataset.orderFavorite)); return; }
  const purchaseButton = event.target.closest("[data-order-purchases]");
  if (purchaseButton) { openOrderTodos(purchaseButton.dataset.orderPurchases, "purchases"); return; }
  const todoButton = event.target.closest("[data-order-todos]");
  if (todoButton) { openOrderTodos(todoButton.dataset.orderTodos); return; }
  const button = event.target.closest("[data-order]");
  if (button) run(() => navigate(button.dataset.order));
});
$("closeOrderTodos").addEventListener("click", () => $("orderTodoDialog").close());
$("orderTodoDialog").addEventListener("close", () => {
  const path = state.orderTodoPath;
  const kind = state.orderTodoKind;
  state.orderTodoPath = null;
  state.orderTodoMarkup = null;
  state.orderTodoKind = "todos";
  $("ordersTableBody").querySelectorAll(kind === "purchases" ? "[data-order-purchases]" : "[data-order-todos]").forEach((button) => {
    if (hasOrderList() && (button.dataset.orderPurchases || button.dataset.orderTodos) === path) button.focus({ preventScroll: true });
  });
});
$("orderTodoDialog").addEventListener("click", (event) => {
  if (event.target !== $("orderTodoDialog")) return;
  const rect = $("orderTodoDialog").getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) $("orderTodoDialog").close();
});
$("orderTodoBody").addEventListener("click", (event) => {
  const button = event.target.closest("[data-order]");
  if (!button) return;
  $("orderTodoDialog").close();
  run(() => navigate(button.dataset.order));
});
$("openTodoOrder").addEventListener("click", () => {
  const path = state.orderTodoPath;
  $("orderTodoDialog").close();
  if (path) run(() => navigate(path));
});
$("ordersWorkspace").querySelector("thead").addEventListener("click", (event) => {
  const button = event.target.closest("[data-sort]");
  if (!button) return;
  state.orderDirection = state.orderSort === button.dataset.sort ? -state.orderDirection : 1;
  state.orderSort = button.dataset.sort;
  renderOrders();
});
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
    delete state.folder.folderNote;
    delete state.folder.draftCard;
    state.folder.note = state.folder.order.note;
    state.folder.status = state.folder.order.status;
    state.folder.financial_status = state.folder.order.financial_status;
    state.folder.todo_items = state.folder.order.todo_items;
    state.folder.noteOnly = false;
    state.folder.registrationPending = false;
    renderFolder();
    notify(isWorkOrderPath(state.folder.path) ? "Заказ добавлен в производство" : "Заказ добавлен в общий список");
    await loadOrders();
  } finally { $("addOrderButton").disabled = false; }
}));
function askRemoveOrder(path) {
  const order = state.folder?.path === path ? state.folder.order : state.orders.find((item) => item.path === path);
  if (!order) { notify("Обновите список заказов перед снятием регистрации", true); return; }
  state.removeOrder = { ...order };
  $("removeOrderName").textContent = order.title;
  $("removeOrderPath").textContent = order.path;
  $("removeOrderTitle").textContent = isWorkOrderPath(order.path) ? "Убрать заказ из производства?" : "Убрать из списка заказов?";
  $("confirmRemoveOrder").textContent = isWorkOrderPath(order.path) ? "Убрать из производства" : "Убрать из списка";
  $("removeOrderDescription").textContent = isWorkOrderPath(order.path) ? "Папка, вложения и данные карточки сохранятся. Связанные заказы поставщиков останутся в производстве. Добавить этот заказ обратно можно вручную." : "Папка, вложения и данные карточки сохранятся. Вложенные заказы останутся в списке. Добавить эту папку обратно можно вручную.";
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
        if (removed.folderNote) Object.assign(state.folder,{folderNote:removed.folderNote,draftCard:removed.folderNote.card});
        state.dirty = false;
        renderFolder();
      }
      state.orders = state.orders.filter((item) => item.path !== order.path);
      state.favoriteOrders = state.favoriteOrders.filter((item) => item.path !== order.path);
      renderFavoriteOrders();
      $("ordersNavCount").textContent = state.orders.length;
      if (state.view === "orders") renderOrders();
      $("removeOrderDialog").close();
      notify(isWorkOrderPath(order.path) ? "Заказ убран из производства" : "Папка убрана из списка заказов");
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
  if (folderActivity(state.folder) && !state.clientActivitySaving) {
    const folder = state.folder;
    request(apiUrl(activityRoute(folder), folder.path)).then((activity) => {
      if (state.folder !== folder || state.clientActivitySaving) return;
      const changed = activity.inactive !== folderActivity(folder).inactive;
      updateFolderActivity(folder, activity);
      renderClientActivity();
      if (changed) run(async () => { await reloadClientTrees(); await loadOrders(); });
    }).catch(() => {});
  }
  if (state.view !== "orders" && state.folder?.canCreateEventFolder) refreshEventRelevance(state.folder).catch(() => {});
  if (state.view !== "orders" && state.folder?.sketches?.length) refreshSketchRelevance(state.folder).catch(() => {});
  if (state.view !== "orders" && state.folder?.folderKind === "work_root") refreshSupplierFavorites(state.folder).catch(() => {});
  if (state.view !== "orders") loadDescendantTodos(state.folder);
  loadOrders().catch(() => { if (hasOrderList()) $("ordersSyncState").textContent = "Нет связи с сервером · показаны последние загруженные данные"; });
  if (state.view !== "orders" && !state.folder?.order && state.folder?.folderNote && !state.dirty && !state.saving) {
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
$("orderPageFavorite").addEventListener("click", () => run(() => toggleOrderFavorite(state.folder?.path)));
$("orderCardDeadlineList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-order-deadline]");
  if (button) run(() => toggleOrderDeadline(button));
});
$("orderCardDeadlineEarlier").addEventListener("click", () => expandCardDeadlineWeeks(-1));
$("orderCardDeadlineLater").addEventListener("click", () => expandCardDeadlineWeeks(1));
$("orderDeadlineComments").addEventListener("input", deadlineCommentInput);
$("orderDeadlineComments").addEventListener("compositionend", deadlineCommentInput);
$("orderDeadlineComments").addEventListener("focusout", (event) => {
  if (event.target.closest("[data-deadline-comment]")) run(() => flushDeadlineComments());
});
$("orderDeadlineComments").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.isComposing) { event.preventDefault(); run(() => flushDeadlineComments()); }
});
$("retryDeadlineComments").addEventListener("click", () => run(() => flushDeadlineComments()));
$("createOrderFolderButton").addEventListener("click", openCreateOrderFolder);
$("createObjectFolderButton").addEventListener("click",openCreateObject);
$("createObjectFolderForm").addEventListener("submit",event=>{event.preventDefault();run(createObject);});
$("cancelCreateObject").addEventListener("click",()=>$("createObjectFolderDialog").close());
$("createObjectFolderDialog").addEventListener("cancel",event=>{if(state.creatingObject)event.preventDefault();});
$("groupObjectYearsButton").addEventListener("click",()=>run(openObjectYears));
$("submitObjectYears").addEventListener("click",()=>run(groupObjectYears));
$("cancelObjectYears").addEventListener("click",()=>$("objectYearsDialog").close());
$("objectYearsDialog").addEventListener("cancel",event=>{if(state.groupingYears)event.preventDefault();});
$("createEventFolderButton").addEventListener("click", () => run(openCreateEventFolder));
$("renameFolderButton").addEventListener("click", () => run(openFolderRename));
$("renameFolderName").addEventListener("input", renderFolderRename);
$("renameFolderForm").addEventListener("submit", (event) => { event.preventDefault(); run(submitFolderRename); });
$("cancelRenameFolder").addEventListener("click", () => { if (!state.folderRenaming) $("renameFolderDialog").close(); });
$("renameFolderDialog").addEventListener("cancel", (event) => { if (state.folderRenaming) event.preventDefault(); });
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
    await request("/api/clients-refresh", {});
    await loadTree();
    if (state.view === "orders") await loadOrders();
    else await navigate(state.selected, { history: false });
  } finally { $("refreshButton").disabled = false; }
}));
$("statusSelect").addEventListener("change", () => { state.dirty = true; renderStatus(); });
$("financialStatusSelect").addEventListener("change", () => { state.dirty = true; renderStatus(); });
$("orderNote").addEventListener("input", () => { state.dirty = true; resizeOrderNote(); renderStatus(); });
$("orderDetails").addEventListener("toggle", resizeOrderNote);
window.addEventListener("resize", resizeOrderNote);
$("descendantTodoList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-order]");
  if (button) run(() => navigate(button.dataset.order));
});
$("descendantCompleted").addEventListener("change", () => {
  state.folder.showCompletedTodos = $("descendantCompleted").checked;
  renderDescendantTodos();
});
$("refreshDescendantTodos").addEventListener("click", () => run(async () => {
  const folder = state.folder;
  $("refreshDescendantTodos").disabled = true;
  try {
    await request("/api/todos-refresh", { path: folder.path });
    await loadDescendantTodos(folder);
    if (state.folder === folder) $("descendantTodoState").textContent = "Обновление карточек папок запущено…";
  } finally { $("refreshDescendantTodos").disabled = false; }
}));
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
$("purchaseAddForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const text = $("purchaseNewText").value.trim();
  if (!text || !Array.isArray(state.folder?.purchase_items)) return;
  state.folder.purchase_items.push({ text, done: false, suppliers: [] });
  $("purchaseNewText").value = "";
  renderPurchases(); saveTodosSoon(); $("purchaseNewText").focus();
});
$("purchaseList").addEventListener("input", (event) => {
  if (!event.target.matches(".todo-text")) return;
  const row = event.target.closest("[data-purchase-index]");
  const item = state.folder.purchase_items[Number(row.dataset.purchaseIndex)];
  item.text = event.target.value;
  event.target.size = Math.max(4, Array.from(item.text).length + 1);
  row.querySelector(".todo-check").setAttribute("aria-label", "Закупка выполнена: " + item.text);
  row.querySelector(".todo-delete").setAttribute("aria-label", "Удалить закупку: " + item.text);
  row.querySelector(".purchase-suppliers").setAttribute("aria-label", "Поставщики для закупки: " + item.text);
  saveTodosSoon(700);
});
$("purchaseList").addEventListener("change", (event) => {
  if (!event.target.matches(".todo-check")) return;
  const row = event.target.closest("[data-purchase-index]");
  state.folder.purchase_items[Number(row.dataset.purchaseIndex)].done = event.target.checked;
  row.classList.toggle("done", event.target.checked);
  $("purchaseCount").textContent = state.folder.purchase_items.filter((item) => item.done).length + " / " + state.folder.purchase_items.length;
  saveTodosSoon();
});
$("purchaseList").addEventListener("click", (event) => {
  const supplier = event.target.closest("[data-purchase-supplier]");
  if (supplier) {
    const item = state.folder.purchase_items[Number(supplier.closest("[data-purchase-index]").dataset.purchaseIndex)];
    const selected = new Set(item.suppliers || []), name = supplier.dataset.purchaseSupplier;
    if (selected.has(name)) selected.delete(name); else selected.add(name);
    item.suppliers = purchaseSuppliers.filter((value) => selected.has(value));
    supplier.setAttribute("aria-pressed", String(selected.has(name)));
    saveTodosSoon();
    return;
  }
  if (!event.target.closest(".todo-delete")) return;
  state.folder.purchase_items.splice(Number(event.target.closest("[data-purchase-index]").dataset.purchaseIndex), 1);
  renderPurchases(); saveTodosSoon();
});
$("purchaseList").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && event.target.matches(".todo-text")) { event.preventDefault(); event.target.blur(); saveTodosSoon(); }
});
$("statusForm").addEventListener("submit", (event) => { event.preventDefault(); run(async () => { await saveCurrentStatus(); notify(state.folder?.folderNote ? "Заметка и задачи сохранены в базе" : state.folder?.service || state.folder?.noteOnly ? "Заметка сохранена" : state.folder?.order ? "Карточка сохранена в базе, выгрузка в папку поставлена в очередь" : "Статус и заметка сохранены"); }); });
$("newPrintTask").addEventListener("click", () => run(newPrintTask));
$("publishPrintTask").addEventListener("click", () => run(async () => {
  await saveCurrentPrintTask(true);
  const task = state.printTask;
  if (!task || task.isNew) return;
  const result = await request("/api/print-publish", {path:task.path, revision:task.revision});
  $("printSaveState").textContent = result.pending ? "Задание выпущено · сохраняется в папку" : "Задание уже сохранено в папке";
}));
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
$("previewDialog").addEventListener("close", () => { ++previewVersion; SpreadsheetPreview.close(); setPreviewExpanded(false); $("previewBody").replaceChildren(); state.preview = null; state.fileComment = null; });
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
$("previewExpand").addEventListener("click", () => setPreviewExpanded(!$("previewDialog").classList.contains("preview-expanded")));
$("previewDialog").addEventListener("keydown", (event) => {
  if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName) || event.target.closest(".spreadsheet-viewer")) return;
  if (event.key === "ArrowLeft") { event.preventDefault(); stepPreview(-1); }
  if (event.key === "ArrowRight") { event.preventDefault(); stepPreview(1); }
});
window.addEventListener("popstate", () => run(() => openLocation()));
window.addEventListener("beforeunload", (event) => { if (hasPendingDeadlineComments() || state.dirty || state.printTask?.dirty || state.printSaving || state.fileComment?.dirty || state.fileCommentSaving || state.upload?.busy || (state.calendarEvent && (state.calendarEvent.saving || $("calendarEventText").value !== state.calendarEvent.previous))) { event.preventDefault(); event.returnValue = ""; } });

$("chooseUploadFiles").addEventListener("click", () => $("uploadFileInput").click());
$("uploadFileInput").addEventListener("change", (event) => {
  const files = Array.from(event.target.files || []);
  event.target.value="";
  run(() => uploadFiles(files));
});
$("closeUploadPanel").addEventListener("click", () => { if (!state.upload?.busy) { state.upload=null; renderUpload(); } });
$("uploadDestination").addEventListener("click", () => { if (state.upload) run(() => navigate(state.upload.path)); });
document.addEventListener("dragover", (event) => {
  if (!Array.from(event.dataTransfer?.types || []).includes("Files")) return;
  event.preventDefault();
  document.querySelector(".content-pane").classList.toggle("upload-dragging", Boolean(state.view==="folder" && state.folder?.upload && !state.upload?.busy));
});
document.addEventListener("dragleave", (event) => { if (!event.relatedTarget) document.querySelector(".content-pane").classList.remove("upload-dragging"); });
document.addEventListener("dragend", () => document.querySelector(".content-pane").classList.remove("upload-dragging"));
document.addEventListener("drop", (event) => {
  if (!Array.from(event.dataTransfer?.types || []).includes("Files")) return;
  event.preventDefault();
  document.querySelector(".content-pane").classList.remove("upload-dragging");
  if (Array.from(event.dataTransfer.items || []).some((item) => item.webkitGetAsEntry?.()?.isDirectory)) {
    notify("Перетащи отдельные файлы. Загрузка папок пока не поддерживается",true); return;
  }
  const files=Array.from(event.dataTransfer.files || []);
  run(() => uploadFiles(files));
});

run(async () => {
  try {
    run(loadTree);
    await openLocation();
    if (state.view !== "orders") await loadOrders();
  } catch (error) {
    $("notice").textContent = error.message;
    $("notice").hidden = false;
    $("folderSummary").textContent = "Проверьте путь в manager.ini";
    document.querySelector(".content-pane").setAttribute("aria-busy", "false");
    throw error;
  }
});

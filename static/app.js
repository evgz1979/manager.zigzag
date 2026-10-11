const statusLabels = {
  all: "Все",
  new: "Новый",
  measure: "Замеры",
  process: "В работе",
  workshop: "В цех",
  install: "Монтаж",
  done: "Готово",
};

const state = {
  data: null,
  query: "",
  client: "all",
  status: "all",
  sort: "modified",
  year: new URLSearchParams(window.location.search).get("year") || "",
};

const elements = {
  rootPath: document.querySelector("#rootPath"),
  yearSelect: document.querySelector("#yearSelect"),
  refreshButton: document.querySelector("#refreshButton"),
  searchInput: document.querySelector("#searchInput"),
  statusFilters: document.querySelector("#statusFilters"),
  clientList: document.querySelector("#clientList"),
  projectList: document.querySelector("#projectList"),
  resultTitle: document.querySelector("#resultTitle"),
  resultSubtitle: document.querySelector("#resultSubtitle"),
  sortSelect: document.querySelector("#sortSelect"),
  template: document.querySelector("#projectTemplate"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} б`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
}

function searchableText(project) {
  return [
    project.client,
    project.name,
    project.path,
    project.note,
    ...project.stages,
    ...project.latestFiles.map((file) => file.name),
  ]
    .join(" ")
    .toLowerCase();
}

function filteredProjects() {
  if (!state.data) return [];
  const query = state.query.trim().toLowerCase();
  const projects = state.data.projects.filter((project) => {
    const matchesQuery = !query || searchableText(project).includes(query);
    const matchesClient = state.client === "all" || project.client === state.client;
    const matchesStatus = state.status === "all" || project.status === state.status;
    return matchesQuery && matchesClient && matchesStatus;
  });

  return projects.sort((a, b) => {
    if (state.sort === "client") return `${a.client} ${a.name}`.localeCompare(`${b.client} ${b.name}`, "ru");
    if (state.sort === "name") return a.name.localeCompare(b.name, "ru");
    if (state.sort === "files") return b.fileCount - a.fileCount;
    return b.modified - a.modified;
  });
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

function renderFilters() {
  elements.statusFilters.innerHTML = Object.entries(statusLabels)
    .map(([status, label]) => {
      const active = state.status === status ? " active" : "";
      return `<button class="filter-button${active}" data-status="${escapeHtml(status)}">${escapeHtml(label)}</button>`;
    })
    .join("");

  elements.clientList.innerHTML = [
    `<button class="client-button${state.client === "all" ? " active" : ""}" data-client="all"><span>Все клиенты</span><small>${state.data.projects.length}</small></button>`,
    ...state.data.clients.map((client, index) => {
      const active = state.client === client.name ? " active" : "";
      return `<button class="client-button${active}" data-client-index="${index}"><span>${escapeHtml(client.name)}</span><small>${client.projectCount}</small></button>`;
    }),
  ].join("");
}

function chip(text, className = "") {
  return `<span class="chip ${escapeHtml(className)}">${escapeHtml(text)}</span>`;
}

function renderProjects() {
  const projects = filteredProjects();
  elements.resultTitle.textContent = state.client === "all" ? "Проекты" : state.client;
  elements.resultSubtitle.textContent = `${projects.length} найдено, сканирование: ${state.data.scannedAt}`;
  elements.projectList.innerHTML = "";

  if (!projects.length) {
    elements.projectList.innerHTML = `<div class="empty">Ничего не найдено</div>`;
    return;
  }

  for (const project of projects) {
    const node = elements.template.content.firstElementChild.cloneNode(true);
    node.querySelector(".client").textContent = project.client;
    node.querySelector("h3").textContent = project.name;
    node.querySelector(".path").textContent = project.path;
    node.querySelector(".updated").textContent = `Обновлено: ${project.modifiedText}`;

    const statusText = statusLabels[project.status] || project.status;
    const statusSource = project.statusSource === "manual" ? "ручной" : "авто";
    node.querySelector(".chips").innerHTML = [
      chip(`${statusText} · ${statusSource}`, `status-${project.status}`),
      chip(`${project.fileCount} файлов`),
      chip(`${project.stageCount} папок`),
      chip(`${project.fileCounts.pdf} PDF`),
      chip(`${project.fileCounts.design} макетов`),
      chip(`${project.fileCounts.images} фото`),
    ].join("");

    node.querySelector(".stages").innerHTML = project.stages
      .slice(0, 8)
      .map((stage) => `<span class="stage">${escapeHtml(stage)}</span>`)
      .join("");

    node.querySelector(".latest").innerHTML = project.latestFiles
      .slice(0, 5)
      .map((file) => `<span class="file-pill" title="${escapeHtml(file.path)}">${escapeHtml(file.name)} · ${formatSize(file.size)}</span>`)
      .join("");

    const statusSelect = node.querySelector(".status-select");
    statusSelect.innerHTML = Object.entries(statusLabels)
      .filter(([value]) => value !== "all")
      .map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`)
      .join("");
    statusSelect.value = project.status;

    const note = node.querySelector(".note");
    note.value = project.note || "";

    node.querySelector(".open-folder").addEventListener("click", async () => {
      await postJson("/api/open", { year: state.data.year, path: project.path });
    });

    node.querySelector(".save-status").addEventListener("click", async (event) => {
      event.currentTarget.textContent = "Сохранено";
      await postJson("/api/status", {
        id: project.id,
        year: state.data.year,
        status: statusSelect.value,
        note: note.value,
      });
      await loadData();
    });

    elements.projectList.appendChild(node);
  }
}

function render() {
  if (!state.data) return;
  elements.rootPath.textContent = state.data.yearRoot;
  elements.yearSelect.innerHTML = state.data.years
    .map((year) => `<option value="${escapeHtml(year)}">${escapeHtml(year)}</option>`)
    .join("");
  elements.yearSelect.value = state.data.year;
  renderFilters();
  renderProjects();
}

async function loadData() {
  elements.refreshButton.disabled = true;
  elements.refreshButton.textContent = "…";
  const query = state.year ? `?year=${encodeURIComponent(state.year)}` : "";
  const response = await fetch(`/api/projects${query}`);
  state.data = await response.json();
  if (!response.ok) throw new Error(state.data.error || "Не удалось загрузить проекты");
  state.year = state.data.year;
  window.history.replaceState(null, "", `?year=${encodeURIComponent(state.year)}`);
  elements.refreshButton.disabled = false;
  elements.refreshButton.textContent = "↻";
  render();
}

elements.refreshButton.addEventListener("click", loadData);
elements.yearSelect.addEventListener("change", (event) => {
  state.year = event.target.value;
  state.client = "all";
  loadData();
});
elements.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderProjects();
});
elements.sortSelect.addEventListener("change", (event) => {
  state.sort = event.target.value;
  renderProjects();
});
elements.statusFilters.addEventListener("click", (event) => {
  const button = event.target.closest("[data-status]");
  if (!button) return;
  state.status = button.dataset.status;
  render();
});
elements.clientList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-client], [data-client-index]");
  if (!button) return;
  state.client = button.dataset.client || state.data.clients[Number(button.dataset.clientIndex)].name;
  render();
});

loadData();

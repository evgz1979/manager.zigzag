(() => {
  const endpoint = "/api/object-move";
  const storageKey = "manager.objectMove";
  const dialog = $("moveObjectDialog"), form = $("moveObjectForm"), client = $("moveObjectClient");
  const meter = $("moveObjectMeter"), launcher = $("showMoveObjectProgress");
  const labels = {
    preparing: "Подготовка переноса…",
    scanning: "Собираю список файлов и папок…",
    reading: "Читаю файлы по исходному пути…",
    moving: "Перемещаю папку объекта…",
    verifying: "Сверяю файлы по новому пути…",
    metadata: "Обновляю пути заказов и связанных данных…",
    rollback: "Возвращаю папку на исходное место…",
    complete: "Объект перенесён. Файлы проверены на M4.",
    failed: "Перенос остановлен",
  };
  let proposal, current;

  // Читает или сохраняет номер операции в текущей вкладке.
  // Прогресс на сервере продолжается даже без доступа к sessionStorage.
  function storedJob(value) {
    try {
      if (value === undefined) return JSON.parse(sessionStorage.getItem(storageKey));
      if (value === null) sessionStorage.removeItem(storageKey);
      else sessionStorage.setItem(storageKey, JSON.stringify(value));
    } catch {}
    return null;
  }

  // Обновляет точный путь назначения перед подтверждением.
  // Использует полные пути клиента, включая его числовую группу.
  function showDestination() {
    const destination = $("moveObjectDestination");
    destination.hidden = !client.value;
    destination.textContent = client.value ? "Новый путь · " + client.value + "/" + proposal.name : "";
    $("submitMoveObject").disabled = !client.value;
  }

  // Открывает подтверждение для объекта, который всё ещё открыт после загрузки формы.
  // Сохраняет заметку и запрашивает только версию папки и каталог клиентов.
  async function openForm() {
    if (current) {
      dialog.showModal();
      return;
    }
    const folder = state.folder;
    if (!folder?.canMoveObject) return;
    await saveCurrentStatus();
    const view = await request(apiUrl(endpoint, folder.path));
    if (state.folder?.path !== folder.path || dialog.open) return;
    proposal = view;
    $("moveObjectSource").textContent = view.path;
    client.replaceChildren(new Option("Выбери клиента", ""), ...view.clients.map(item => new Option(item.path, item.path)));
    $("moveObjectError").hidden = view.clients.length > 0;
    $("moveObjectError").textContent = view.clients.length ? "" : "Других клиентов нет";
    form.hidden = false;
    $("moveObjectProgress").hidden = true;
    showDestination();
    dialog.showModal();
    client.focus();
  }

  // Показывает актуальную фазу, число файлов, прочитанные байты и текущий путь.
  // Показывает неопределённый прогресс там, где долю работы ещё нельзя измерить.
  function renderProgress(job, connectionError = "") {
    const complete = job.phase === "complete", failed = job.phase === "failed";
    form.hidden = true;
    $("moveObjectProgress").hidden = false;
    $("moveObjectSource").textContent = complete ? job.path : job.source;
    const phase = $("moveObjectPhase");
    const message = connectionError || labels[job.phase];
    if (phase.textContent !== message) phase.textContent = message;
    const reading = job.phase === "reading" || job.phase === "verifying";
    meter.hidden = complete || failed;
    if (reading && job.total_bytes > 0) {
      meter.max = job.total_bytes;
      meter.value = job.bytes;
    } else {
      meter.removeAttribute("value");
    }
    let counts = "";
    if (reading && Number.isInteger(job.total_files)) {
      counts = job.files + " из " + job.total_files + " файлов · " + formatSize(job.bytes) + " из " + formatSize(job.total_bytes);
    } else if (complete || job.phase === "scanning") {
      counts = (job.files || 0) + " файлов · " + (job.folders || 0) + " папок" +
        (job.links ? " · " + job.links + " ссылок" : "") + (complete ? " · " + formatSize(job.bytes) : "");
    }
    $("moveObjectCounts").textContent = counts;
    $("moveObjectCurrent").hidden = !job.current;
    $("moveObjectCurrent").textContent = job.current || "";
    $("moveObjectProgressError").hidden = !failed;
    $("moveObjectProgressError").textContent = failed ? job.error : "";
    $("closeMoveObject").textContent = complete || failed ? "Закрыть" : "Свернуть";
    $("openMovedObject").hidden = !complete;
    launcher.textContent = complete ? "Объект перенесён" : failed ? "Перенос остановлен" : "Перенос объекта";
    launcher.hidden = false;
  }

  // Получает прогресс с M4, пока операция не завершится или сервер не вернёт отсутствие задания.
  // При потере сети повторяет только чтение статуса, сохраняя последнее известное состояние.
  async function monitor(job) {
    let delay = 700;
    while (current === job) {
      try {
        Object.assign(job, await request(apiUrl(endpoint + "-status", "", { id: job.id }),
          undefined, { signal: AbortSignal.timeout(15000) }));
        delay = 700;
        renderProgress(job);
        if (job.phase === "complete" || job.phase === "failed") return;
      } catch (error) {
        if (error.status === 404 && !job.unconfirmed) {
          Object.assign(job, { phase: "failed", error: error.message });
          renderProgress(job);
          return;
        }
        job.unconfirmed = false;
        renderProgress(job, "Жду подтверждение от M4…");
        delay = 2500;
      }
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  // Отправляет одно подтверждение и начинает опрос под тем же идентификатором.
  // При неопределённом сетевом ответе не отправляет перенос повторно.
  async function submit() {
    const recipient = proposal?.clients.find(item => item.path === client.value);
    if (!recipient || current) return;
    const id = Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, "0")).join("");
    const job = { id, source: proposal.path, phase: "preparing" };
    const payload = { id, path: proposal.path, client: recipient.path, revision: proposal.revision,
      client_revision: recipient.revision, confirmed: true };
    current = job;
    storedJob(job);
    renderProgress(job);
    try {
      const response = await fetch(endpoint, { method: "POST", body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json", "X-Manager-Object-Move": "1" }, signal: AbortSignal.timeout(15000) });
      const result = await response.json();
      if (response.status >= 400 && response.status < 500) {
        Object.assign(job, { phase: "failed", error: result.error });
        renderProgress(job);
        return;
      }
      if (!response.ok) throw new Error(result.error);
      Object.assign(job, result);
    } catch {
      job.unconfirmed = true;
    }
    await monitor(job);
  }

  // Закрывает окно и оставляет доступ к прогрессу, если перенос идёт.
  // При подтверждённом завершении результат можно открыть по отдельной кнопке.
  function close() {
    dialog.close();
    if (current?.phase === "failed") {
      storedJob(null);
      current = null;
      launcher.hidden = true;
    }
  }

  $("moveObjectButton").addEventListener("click", () => run(openForm));
  launcher.addEventListener("click", () => dialog.showModal());
  client.addEventListener("change", showDestination);
  form.addEventListener("submit", event => { event.preventDefault(); run(submit); });
  $("cancelMoveObject").addEventListener("click", close);
  $("closeMoveObject").addEventListener("click", close);
  dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
  $("openMovedObject").addEventListener("click", () => {
    const result = current;
    close();
    run(async () => {
      await openRelocatedFolder(result);
      storedJob(null);
      current = null;
      launcher.hidden = true;
    });
  });
  const saved = storedJob();
  if (saved?.id) {
    current = saved;
    renderProgress(saved);
    run(() => monitor(saved));
  }
})();

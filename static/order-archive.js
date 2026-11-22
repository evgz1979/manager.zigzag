(() => {
  const endpoint = "/api/order-archive";
  const storageKey = "manager.orderArchive";
  const dialog = $("archiveOrderDialog"), form = $("archiveOrderForm");
  const submit = $("submitArchiveOrder"), cancel = $("cancelArchiveOrder");
  const status = $("archiveOrderStatus"), failure = $("archiveOrderError");
  const phases = {
    preparing: "Готовлю архивацию…",
    reading: "Читаю файлы заказа…",
    copying: "Записываю ZIP на NAS…",
    verifying: "Проверяю ZIP на NAS…",
    moving: "Убираю исходную папку…",
  };
  let proposal, job, opening = false;

  // Сохраняет номер принятой операции для повторного открытия вкладки.
  // При недоступном хранилище серверная работа продолжается.
  function remember(value) {
    try {
      if (value === undefined) return JSON.parse(sessionStorage.getItem(storageKey));
      if (value) sessionStorage.setItem(storageKey, JSON.stringify(value));
      else sessionStorage.removeItem(storageKey);
    } catch {}
    return null;
  }

  // Показывает исходный путь и точный путь ZIP перед подтверждением.
  // Сохраняет заметку и проверяет, что за это время пользователь остался в заказе.
  async function openConfirmation() {
    const folder = state.folder;
    if ($("archiveOrderButton").hidden || opening || dialog.open) return;
    opening = true;
    try {
      await saveCurrentStatus();
      const view = await request(apiUrl(endpoint, folder.path));
      if (state.folder !== folder) return;
      proposal = view;
      $("archiveOrderSource").textContent = view.path;
      $("archiveOrderDestination").textContent = view.nas_path;
      status.hidden = failure.hidden = true;
      submit.disabled = submit.hidden = cancel.disabled = false;
      cancel.textContent = "Отмена";
      dialog.showModal();
      cancel.focus();
    } finally {
      opening = false;
    }
  }

  // Показывает текущую фазу архивации или ошибку соединения.
  // Подтверждение блокируется до завершения уже принятого действия.
  function showProgress(message) {
    status.hidden = false;
    if (status.textContent !== message) status.textContent = message;
    failure.hidden = true;
    submit.disabled = cancel.disabled = true;
  }

  // Прекращает опрос и показывает ошибку рядом с исходным путём.
  // Новая попытка всегда открывает новое подтверждение.
  function showFailure(message) {
    job = proposal = null;
    remember(null);
    status.hidden = true;
    failure.hidden = false;
    failure.textContent = message;
    submit.hidden = true;
    cancel.disabled = false;
    cancel.textContent = "Закрыть";
    cancel.focus();
  }

  // Опрашивает состояние принятого задания, не отправляя повторную запись.
  // После успешной проверки возвращает страницу к родительской папке.
  async function monitor() {
    let missing = 0;
    while (job) {
      let result;
      try {
        result = await request(apiUrl(endpoint + "-status", "", { id: job.id }), undefined,
          { signal: AbortSignal.timeout(12000) });
      } catch (error) {
        if (error.status === 404 && ++missing >= 3) {
          showFailure("Архивация не подтверждена. Проверь исходную папку.");
          return;
        }
        showProgress("Жду ответ сервера…");
        await new Promise(resolve => setTimeout(resolve, 1800));
        continue;
      }
      missing = 0;
      if (result.phase === "failed") {
        showFailure(result.error);
        return;
      }
      if (result.phase === "complete") {
        job = proposal = null;
        remember(null);
        dialog.close();
        if ((state.folder?.path || new URLSearchParams(location.search).get("path")) === result.source) {
          state.dirty = false;
          await navigate(result.path);
        }
        await reloadClientTrees();
        await loadOrders();
        notify(result.warning || "Заказ в архиве NAS · " + result.nas_path, Boolean(result.warning));
        return;
      }
      showProgress(phases[result.phase]);
      await new Promise(resolve => setTimeout(resolve, 850));
    }
  }

  // Отправляет подтверждение один раз и сохраняет номер для чтения результата.
  // При неопределённом ответе продолжает только опрос.
  async function confirm() {
    if (!proposal || job) return;
    const id = proposal.id;
    job = { id, path: proposal.path, nas_path: proposal.nas_path };
    remember(job);
    showProgress(phases.preparing);
    try {
      await request(endpoint, { id, path: proposal.path, revision: proposal.revision, confirmed: true },
        { headers: { "X-Manager-Order-Archive": "1" }, signal: AbortSignal.timeout(12000) });
    } catch (error) {
      if (error.status >= 400 && error.status < 500) {
        showFailure(error.message);
        return;
      }
    }
    await monitor();
  }

  $("archiveOrderButton").addEventListener("click", () => run(openConfirmation));
  form.addEventListener("submit", event => { event.preventDefault(); run(confirm); });
  cancel.addEventListener("click", () => dialog.close());
  dialog.addEventListener("cancel", event => { if (job) event.preventDefault(); });
  const saved = remember();
  if (saved?.id) {
    job = saved;
    $("archiveOrderSource").textContent = saved.path;
    $("archiveOrderDestination").textContent = saved.nas_path;
    showProgress(phases.preparing);
    dialog.showModal();
    run(monitor);
  }
})();

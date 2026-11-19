/* Seller defaults are shared in SQLite; password inputs never enter browser storage. */
(() => {
  const button = document.getElementById('managerSettingsButton');
  const dialog = document.getElementById('managerSettingsDialog');
  const form = document.getElementById('managerSettingsForm');
  const fields = document.getElementById('managerSettingsFields');
  const current = document.getElementById('managerCurrentPassword');
  const password = document.getElementById('managerNewPassword');
  const confirmation = document.getElementById('managerConfirmPassword');
  const status = document.getElementById('managerSettingsState');
  const close = document.getElementById('managerSettingsClose');
  const tablist = document.getElementById('managerSettingsTabs');
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];
  const content = document.getElementById('managerSettingsContent');
  const sellerTab = document.getElementById('managerSellerTab');
  const caldavTab = document.getElementById('managerCalDAVTab');
  const highlightTab = document.getElementById('managerDeadlineHighlightsTab');
  const plotterTab = document.getElementById('managerPlotterTab');
  const plotterForm = document.getElementById('plotterSettingsForm');
  const plotterFields = document.getElementById('plotterSettingsFields');
  const plotterStatus = document.getElementById('plotterSettingsState');
  const plotterSave = document.getElementById('savePlotterSettings');
  const plotterReload = document.getElementById('reloadPlotterSettings');
  let plotterRevision = null, plotterBusy = false;
  const highlightWeeks = document.getElementById('deadlineHighlightWeeks');
  const highlightEarlier = document.getElementById('deadlineHighlightEarlier');
  const highlightLater = document.getElementById('deadlineHighlightLater');
  const highlightStatus = document.getElementById('deadlineHighlightState');
  const highlightSave = document.getElementById('saveDeadlineHighlights');
  const highlightReload = document.getElementById('reloadDeadlineHighlights');
  let highlightEdit = null;
  let csrf = '', busy = false, request = 0;
  let sellerRevision = null, sellerBusy = false, sellerLoading = 0;
  let caldavBusy = false;
  const caldavPanel = document.getElementById('managerCalDAVSettings');
  const caldavGenerate = document.getElementById('managerCalDAVGenerate');
  const caldavRevoke = document.getElementById('managerCalDAVRevoke');
  const caldavPassword = document.getElementById('managerCalDAVPassword');
  const caldavStatus = document.getElementById('managerCalDAVState');
  const sellerForm = document.getElementById('invoiceSellerSettingsForm');
  const sellerFields = document.getElementById('invoiceSellerSettingsFields');
  const sellerStatus = document.getElementById('invoiceSellerSettingsState');
  const sellerSave = document.getElementById('saveInvoiceSellerSettings');
  const sellerLabels = { name: 'Исполнитель', inn: 'ИНН', kpp: 'КПП', address: 'Адрес', bank: 'Банк', bik: 'БИК', account: 'Расчётный счёт', correspondent: 'Корреспондентский счёт', signer: 'Подписант' };
  for (const [key, caption] of Object.entries(sellerLabels)) {
    const label = document.createElement('label'), input = document.createElement('input');
    label.textContent = caption; input.dataset.sellerField = key; input.maxLength = key === 'address' ? 500 : 300;
    if (['inn', 'kpp', 'bik', 'account', 'correspondent'].includes(key)) input.inputMode = 'numeric';
    label.append(input); sellerFields.append(label);
  }

  // Показывает выбранный раздел настроек и обновляет доступность вкладок для клавиатуры.
  // Скрытые формы остаются в окне вместе с введёнными значениями и состоянием запросов.
  function selectSettingsTab(selected) {
    for (const tab of tabs) {
      const active = tab === selected;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      document.getElementById(tab.getAttribute('aria-controls')).hidden = !active;
    }
    content.scrollTop = 0;
    if (selected === highlightTab && !highlightEdit) {
      highlightEdit = { currentWeek: null, firstWeek: null, pageSize: 0, weeks: new Set(), saved: [], revision: null };
      loadWeekHighlights();
    }
    if (selected === plotterTab && plotterRevision === null && !plotterReload.disabled) loadPlotterSettings();
  }

  // Загружает общий масштаб плоттера для двух выходных осей.
  // Устаревший ответ после закрытия окна не затирает открытую форму.
  async function loadPlotterSettings() {
    const version = request;
    plotterReload.disabled = plotterSave.disabled = plotterFields.disabled = true;
    plotterStatus.textContent = 'Загрузка…';
    try {
      const data = await window.fetch('/api/plotter-settings', { cache: 'no-store' });
      const values = await data.json();
      if (!dialog.open || version !== request) return;
      if (!data.ok) throw new Error(values.error || 'Не удалось загрузить масштаб');
      plotterRevision = values.revision;
      for (const axis of ['x_percent', 'y_percent']) plotterForm.elements[axis].value = String(values[axis]).replace('.', ',');
      plotterSave.disabled = plotterFields.disabled = false;
      plotterStatus.textContent = '';
    } catch (error) {
      if (dialog.open && version === request) plotterStatus.textContent = error.message;
    } finally {
      if (version === request) plotterReload.disabled = false;
    }
  }

  // Сохраняет обе поправки плоттера одним запросом по прочитанной версии.
  // При конфликте оставляет введённые значения и просит загрузить сохранённые.
  async function savePlotterSettings(event) {
    event.preventDefault();
    if (busy || sellerBusy || caldavBusy || highlightEdit?.saving || plotterBusy || plotterSave.disabled) return;
    const payload = { revision: plotterRevision, ...Object.fromEntries(new FormData(plotterForm)) };
    plotterBusy = true;
    plotterFields.disabled = plotterSave.disabled = plotterReload.disabled = close.disabled = true;
    plotterStatus.textContent = 'Сохранение…';
    let conflict = false;
    try {
      const response = await fetch('/api/plotter-settings', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Manager-Plotter': '1' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      conflict = response.status === 409;
      if (!response.ok) throw new Error(data.error || 'Не удалось сохранить масштаб');
      plotterRevision = data.revision;
      plotterStatus.textContent = 'Масштаб сохранён для следующих конвертаций.';
    } catch (error) {
      plotterStatus.textContent = error.message + (conflict ? ' Нажми «Обновить», чтобы загрузить сохранённые значения.' : '');
    } finally {
      plotterBusy = false;
      plotterFields.disabled = plotterReload.disabled = close.disabled = false;
      plotterSave.disabled = conflict;
    }
  }

  // Обновляет выбор недель и доступность действий, сохраняя фокус внутри сетки.
  // Полоса отражает черновик, запись разрешена только после чтения версии.
  function updateWeekHighlights(edit) {
    const editable = !edit.loading && !edit.saving && !edit.blocked && edit.revision !== null;
    for (const week of highlightWeeks.children) {
      const start = week.dataset.highlightWeek;
      week.className = week.dataset.baseClass + deadlineHighlightClass(edit.weeks, start, week.nextElementSibling?.dataset.highlightWeek);
      week.setAttribute('aria-pressed', String(edit.weeks.has(start)));
      week.disabled = !editable;
    }
    highlightEarlier.disabled = !edit.firstWeek || edit.loading || edit.saving || !shiftDeadlineWeek(edit.firstWeek, -edit.pageSize);
    highlightLater.disabled = !edit.firstWeek || edit.loading || edit.saving || !shiftDeadlineWeek(edit.firstWeek, edit.pageSize);
    highlightSave.disabled = !editable || (edit.weeks.size === edit.saved.length && edit.saved.every(week => edit.weeks.has(week)));
    highlightReload.hidden = !edit.blocked;
    highlightReload.disabled = Boolean(edit.loading);
  }

  // Строит страницу из недель того же размера и с той же легендой, что в списке заказов.
  // Перелистывание меняет видимые недели и сохраняет весь черновик.
  function renderWeekHighlights(edit) {
    const options = edit.firstWeek ? Array.from({ length: edit.pageSize }, (_, index) => ({
      start: shiftDeadlineWeek(edit.firstWeek, index),
    })).filter(week => week.start) : [];
    document.getElementById('deadlineHighlightMonths').innerHTML = renderDeadlineMonthLegend(options);
    highlightWeeks.innerHTML = options.map(({ start }) => {
      const week = deadlineWeekInfo(start);
      const classes = 'deadline-week' + (start === edit.currentWeek ? ' current' : start < edit.currentWeek ? ' past' : '');
      return '<button type="button" data-highlight-week="' + start + '" data-base-class="' + classes +
        '" style="--deadline-month-hue:' + week.hue + '" title="' + week.label +
        '" aria-label="Неделя ' + week.number + ' · ' + week.label + '">' + week.number + '</button>';
    }).join('');
    highlightWeeks.parentElement.scrollLeft = 0;
    updateWeekHighlights(edit);
  }

  // Читает актуальную версию при открытии вкладки или явной загрузке сохранённых недель.
  // Переключение разделов настроек сохраняет редактор и черновик в том же сеансе.
  async function loadWeekHighlights() {
    const edit = highlightEdit;
    edit.loading = true;
    highlightStatus.textContent = 'Загрузка недель…';
    if (edit.firstWeek) updateWeekHighlights(edit);
    else renderWeekHighlights(edit);
    try {
      const response = await fetch('/api/deadline-highlights', { cache: 'no-store' });
      const data = await response.json();
      if (!dialog.open || edit !== highlightEdit) return;
      if (!response.ok) throw new Error(data.error || 'Не удалось загрузить недели.');
      edit.pageSize = data.week_options.length;
      edit.currentWeek = data.week_options[0].start;
      edit.firstWeek ||= edit.currentWeek;
      edit.saved = data.weeks || [];
      edit.weeks = new Set(edit.saved);
      edit.revision = data.weeks === null ? null : data.revision;
      edit.blocked = false;
      highlightStatus.textContent = data.weeks === null ? 'Неизвестный формат сохранённых недель.' : '';
      applyDeadlineHighlights(data, true);
    } catch (error) {
      if (!dialog.open || edit !== highlightEdit) return;
      edit.blocked = true;
      highlightStatus.textContent = error.message;
    } finally {
      edit.loading = false;
      if (dialog.open && edit === highlightEdit) renderWeekHighlights(edit);
    }
  }

  // Сохраняет сразу все отмеченные недели по прочитанной версии.
  // При конфликте и потере ответа оставляет черновик видимым до загрузки текущих отметок.
  async function saveWeekHighlights() {
    const edit = highlightEdit;
    if (busy || sellerBusy || caldavBusy || plotterBusy || highlightSave.disabled) return;
    edit.saving = true;
    close.disabled = true;
    updateWeekHighlights(edit);
    highlightStatus.textContent = 'Сохранение…';
    try {
      const response = await fetch('/api/deadline-highlights', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Manager-Deadline-Highlights': '1' },
        body: JSON.stringify({ revision: edit.revision, weeks: [...edit.weeks].sort() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Не удалось сохранить недели.');
      edit.revision = data.revision;
      edit.saved = data.weeks;
      highlightStatus.textContent = 'Отметки сохранены.';
      applyDeadlineHighlights(data, true);
    } catch (error) {
      edit.blocked = true;
      highlightStatus.textContent = error.message + ' Нажми «Загрузить сохранённые», чтобы проверить текущие отметки и выбрать недели заново.';
    } finally {
      edit.saving = false;
      close.disabled = false;
      updateWeekHighlights(edit);
    }
  }

  // Загружает общие реквизиты отдельно от настроек пароля и открытого счёта.
  // Явная проверка конфликта сохраняет ввод и показывает актуальные значения перед повторной записью.
  async function loadSeller(preserve = false) {
    const version = ++sellerLoading;
    sellerStatus.textContent = 'Загрузка реквизитов…';
    try {
      const response = await fetch('/api/invoice-seller', { cache: 'no-store' }), data = await response.json();
      if (!dialog.open || version !== sellerLoading) return;
      if (!response.ok) throw new Error(data.error || 'Не удалось открыть реквизиты');
      sellerRevision = data.revision;
      if (!preserve) for (const input of sellerFields.querySelectorAll('input')) input.value = data.seller[input.dataset.sellerField] || '';
      sellerFields.disabled = false; sellerSave.disabled = false;
      sellerStatus.textContent = preserve ? 'Сейчас сохранено: ' + Object.entries(sellerLabels).map(([key, caption]) => caption + ': ' + (data.seller[key] || '—')).join('; ') + '. Твой ввод оставлен. Проверь и сохрани.' : '';
    } catch (error) { if (version === sellerLoading) sellerStatus.textContent = error.message; }
  }

  // Сохраняет единые реквизиты по ожидаемой версии, не переписывая счета.
  // Ошибка оставляет поля; ни конфликт, ни потеря ответа не вызывают автоматического повтора.
  async function saveSeller(event) {
    event.preventDefault();
    if (sellerBusy || busy || caldavBusy || plotterBusy || highlightEdit?.saving || sellerRevision === null) return;
    const seller = Object.fromEntries([...sellerFields.querySelectorAll('input')].map(input => [input.dataset.sellerField, input.value]));
    sellerBusy = true; sellerFields.disabled = true; sellerSave.disabled = true; close.disabled = true;
    sellerStatus.textContent = 'Сохранение…';
    try {
      const response = await fetch('/api/invoice-seller', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Manager-Invoice-Preferences': '1' }, body: JSON.stringify({ revision: sellerRevision, seller }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Не удалось сохранить реквизиты');
      sellerRevision = data.revision; sellerStatus.textContent = 'Реквизиты сохранены для новых счетов.';
    } catch (error) { sellerStatus.textContent = error.message + ' Ввод остался в форме. Нажми «Обновить», чтобы проверить сохранённые реквизиты.'; }
    finally { sellerBusy = false; sellerFields.disabled = false; sellerSave.disabled = false; close.disabled = busy; }
  }

  // Открывает настройки без замены содержимого страницы или её черновиков.
  // Токен и режим смены пароля загружаются только при явном открытии окна.
  async function openSettings() {
    const version = ++request;
    form.reset(); csrf = ''; fields.disabled = true; status.textContent = 'Загрузка…';
    caldavTab.hidden = true;
    selectSettingsTab(sellerTab);
    dialog.showModal();
    sellerRevision = null; sellerFields.disabled = true; sellerSave.disabled = true; loadSeller();
    try {
      const response = await fetch('/api/manager-settings', { cache: 'no-store' });
      const data = await response.json();
      if (!dialog.open || version !== request) return;
      if (!response.ok) { status.textContent = data.error || 'Не удалось открыть настройки'; return; }
      if (!data.enabled) { status.textContent = 'Внешний вход ещё не подключён.'; return; }
      csrf = data.csrf;
      if (data.caldav_path) {
        document.getElementById('managerCalDAVAddress').textContent = `Сервер ${data.public_host} · путь ${data.caldav_path} · имя пользователя ${data.caldav_username}`;
        document.getElementById('managerCalDAVHTTPSLink').href = 'https://' + data.public_host + '/';
        document.getElementById('managerCalDAVHTTPS').hidden = data.require_current_password;
        document.getElementById('managerCalDAVControls').hidden = !data.require_current_password;
        caldavTab.hidden = false;
      }
      document.getElementById('managerSettingsAddress').textContent = 'Для входа через ' + data.public_host;
      document.getElementById('managerCurrentPasswordLabel').hidden = !data.require_current_password;
      current.required = data.require_current_password;
      fields.disabled = false; status.textContent = '';
    } catch (_) { if (dialog.open && version === request) status.textContent = 'Не удалось открыть настройки. Проверь соединение.'; }
  }

  // Отправляет одну явную смену пароля и очищает поля после подтверждения.
  // При ошибке соединения не повторяет запрос, поскольку пароль мог уже измениться.
  async function saveSettings(event) {
    event.preventDefault();
    if (busy || sellerBusy || caldavBusy || plotterBusy || highlightEdit?.saving || !csrf) return;
    if (password.value !== confirmation.value) {
      status.textContent = 'Новые пароли должны совпадать.'; confirmation.focus(); return;
    }
    const payload = { csrf, current_password: current.value, new_password: password.value, confirmation: confirmation.value };
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    busy = true; fields.disabled = true; close.disabled = true; status.textContent = 'Сохранение…';
    try {
      const response = await fetch('/api/manager-settings/password', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Manager-Settings': '1' },
        body: JSON.stringify(payload), signal: controller.signal,
      });
      const data = await response.json();
      if (!response.ok) { status.textContent = data.error || 'Не удалось сменить пароль'; return; }
      csrf = data.csrf; form.reset();
      caldavPassword.value = ''; caldavPassword.parentElement.hidden = true;
      caldavStatus.textContent = 'Создай новый пароль для CalDAV.';
      status.textContent = 'Пароль изменён. Используй новый пароль для внешнего входа.';
    } catch (_) {
      status.textContent = 'Ответ не получен. Проверь вход с новым паролем перед повтором.';
    } finally { window.clearTimeout(timeout); busy = false; fields.disabled = false; close.disabled = false; }
  }

  // Меняет отдельный пароль приложения через текущую сессию настроек.
  // Показывает пароль один раз и сохраняет его только до закрытия окна.
  async function changeCalendarPassword(action) {
    if (busy || sellerBusy || caldavBusy || plotterBusy || highlightEdit?.saving || !csrf) return;
    if (action === 'revoke' && !window.confirm('Отключить синхронизацию CalDAV на всех устройствах?')) return;
    caldavBusy = true; caldavGenerate.disabled = true; caldavRevoke.disabled = true; close.disabled = true;
    caldavStatus.textContent = 'Сохранение…';
    try {
      const response = await fetch('/api/manager-settings/caldav', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Manager-Settings': '1' },
        body: JSON.stringify({ csrf, action }),
      });
      const data = await response.json();
      if (!response.ok) { caldavStatus.textContent = data.error || 'Не удалось изменить пароль CalDAV'; return; }
      caldavPassword.value = data.password || '';
      caldavPassword.parentElement.hidden = !data.password;
      caldavStatus.textContent = data.password ? 'Скопируй пароль перед закрытием окна.' : 'Пароль CalDAV отозван.';
      if (data.password && !caldavPanel.hidden) { caldavPassword.focus(); caldavPassword.select(); }
    } catch (_) { caldavStatus.textContent = 'Ответ не получен. При необходимости создай новый пароль.'; }
    finally { caldavBusy = false; caldavGenerate.disabled = false; caldavRevoke.disabled = false; close.disabled = false; }
  }

  button.addEventListener('click', openSettings);
  tablist.addEventListener('click', event => {
    const tab = event.target.closest('[role="tab"]');
    if (!tab || tab.hidden) return;
    selectSettingsTab(tab);
    tab.focus();
  });
  tablist.addEventListener('keydown', event => {
    const visibleTabs = tabs.filter(tab => !tab.hidden);
    const index = visibleTabs.indexOf(event.target);
    if (index < 0) return;
    const positions = {
      ArrowLeft: (index + visibleTabs.length - 1) % visibleTabs.length,
      ArrowRight: (index + 1) % visibleTabs.length,
      Home: 0,
      End: visibleTabs.length - 1,
    };
    if (!Object.hasOwn(positions, event.key)) return;
    event.preventDefault();
    const next = visibleTabs[positions[event.key]];
    selectSettingsTab(next);
    next.focus();
  });
  sellerForm.addEventListener('submit', saveSeller);
  document.getElementById('reloadInvoiceSellerSettings').addEventListener('click', () => { if (!sellerBusy) loadSeller(sellerRevision !== null); });
  form.addEventListener('submit', saveSettings);
  caldavGenerate.addEventListener('click', () => changeCalendarPassword('generate'));
  caldavRevoke.addEventListener('click', () => changeCalendarPassword('revoke'));
  highlightWeeks.addEventListener('click', event => {
    const week = event.target.closest('[data-highlight-week]')?.dataset.highlightWeek;
    if (!week) return;
    const edit = highlightEdit;
    if (!edit.weeks.delete(week)) edit.weeks.add(week);
    highlightStatus.textContent = '';
    updateWeekHighlights(edit);
  });
  for (const [control, direction] of [[highlightEarlier, -1], [highlightLater, 1]]) {
    control.addEventListener('click', () => {
      const edit = highlightEdit;
      edit.firstWeek = shiftDeadlineWeek(edit.firstWeek, direction * edit.pageSize);
      renderWeekHighlights(edit);
    });
  }
  highlightSave.addEventListener('click', saveWeekHighlights);
  highlightReload.addEventListener('click', loadWeekHighlights);
  plotterForm.addEventListener('submit', savePlotterSettings);
  plotterReload.addEventListener('click', loadPlotterSettings);
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('cancel', event => { if (busy || sellerBusy || caldavBusy || plotterBusy || highlightEdit?.saving) event.preventDefault(); });
  dialog.addEventListener('close', () => {
    ++request; ++sellerLoading; form.reset(); sellerForm.reset(); csrf = ''; status.textContent = ''; sellerStatus.textContent = '';
    highlightEdit = null;
    plotterRevision = null;
    plotterForm.reset();
    plotterFields.disabled = plotterSave.disabled = true;
    plotterReload.disabled = false;
    plotterStatus.textContent = '';
    caldavPassword.value = ''; caldavPassword.parentElement.hidden = true; caldavStatus.textContent = '';
  });
})();

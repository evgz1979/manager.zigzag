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
    if (sellerBusy || busy || caldavBusy || sellerRevision === null) return;
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
    caldavPanel.hidden = true;
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
        caldavPanel.hidden = false;
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
    if (busy || sellerBusy || caldavBusy || !csrf) return;
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
    if (busy || sellerBusy || caldavBusy || !csrf) return;
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
      if (data.password) { caldavPassword.focus(); caldavPassword.select(); }
    } catch (_) { caldavStatus.textContent = 'Ответ не получен. При необходимости создай новый пароль.'; }
    finally { caldavBusy = false; caldavGenerate.disabled = false; caldavRevoke.disabled = false; close.disabled = false; }
  }

  button.addEventListener('click', openSettings);
  sellerForm.addEventListener('submit', saveSeller);
  document.getElementById('reloadInvoiceSellerSettings').addEventListener('click', () => { if (!sellerBusy) loadSeller(sellerRevision !== null); });
  form.addEventListener('submit', saveSettings);
  caldavGenerate.addEventListener('click', () => changeCalendarPassword('generate'));
  caldavRevoke.addEventListener('click', () => changeCalendarPassword('revoke'));
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('cancel', event => { if (busy || sellerBusy || caldavBusy) event.preventDefault(); });
  dialog.addEventListener('close', () => {
    ++request; ++sellerLoading; form.reset(); sellerForm.reset(); csrf = ''; status.textContent = ''; sellerStatus.textContent = '';
    caldavPassword.value = ''; caldavPassword.parentElement.hidden = true; caldavStatus.textContent = ''; caldavPanel.open = false;
  });
})();

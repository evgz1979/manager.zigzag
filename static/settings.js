/* Password settings stay in this dialog and are never stored in browser storage. */
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

  // Открывает настройки без замены содержимого страницы или её черновиков.
  // Токен и режим смены пароля загружаются только при явном открытии окна.
  async function openSettings() {
    const version = ++request;
    form.reset(); csrf = ''; fields.disabled = true; status.textContent = 'Загрузка…';
    dialog.showModal();
    try {
      const response = await fetch('/api/manager-settings', { cache: 'no-store' });
      const data = await response.json();
      if (!dialog.open || version !== request) return;
      if (!response.ok) { status.textContent = data.error || 'Не удалось открыть настройки'; return; }
      if (!data.enabled) { status.textContent = 'Внешний вход ещё не подключён.'; return; }
      csrf = data.csrf;
      document.getElementById('managerSettingsAddress').textContent = 'Для входа через ' + data.public_host;
      document.getElementById('managerCurrentPasswordLabel').hidden = !data.require_current_password;
      current.required = data.require_current_password;
      fields.disabled = false; status.textContent = '';
      (data.require_current_password ? current : password).focus();
    } catch (_) { if (dialog.open && version === request) status.textContent = 'Не удалось открыть настройки. Проверь соединение.'; }
  }

  // Отправляет одну явную смену пароля и очищает поля после подтверждения.
  // При ошибке соединения не повторяет запрос, поскольку пароль мог уже измениться.
  async function saveSettings(event) {
    event.preventDefault();
    if (busy || !csrf) return;
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
      status.textContent = 'Пароль изменён. Используй новый пароль для внешнего входа.';
    } catch (_) {
      status.textContent = 'Ответ не получен. Проверь вход с новым паролем перед повтором.';
    } finally { window.clearTimeout(timeout); busy = false; fields.disabled = false; close.disabled = false; }
  }

  button.addEventListener('click', openSettings);
  form.addEventListener('submit', saveSettings);
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('cancel', event => { if (busy) event.preventDefault(); });
  dialog.addEventListener('close', () => { ++request; form.reset(); csrf = ''; status.textContent = ''; });
})();

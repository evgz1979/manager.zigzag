/* Included by the protected listener only. Authentication errors preserve drafts. */
(() => {
  const fetchOriginal = window.fetch.bind(window);
  let notice;
  // Строит безопасный адрес входа с возвратом к текущей странице.
  // Использует `encodeURIComponent`.
  const loginUrl = () => '/_auth/login?next=' + encodeURIComponent(location.pathname + location.search + location.hash);
  // Показывает необходимость входа в отдельной вкладке, сохраняя текущую форму.
  // Использует `document.createElement`, `notice.setAttribute`, `notice.append`.
  function requireLogin() {
    if (notice || !document.body) return;
    notice = document.createElement('div');
    notice.setAttribute('role', 'alert');
    notice.style.cssText = 'position:fixed;bottom:18px;left:50%;transform:translateX(-50%);z-index:20000;padding:14px 18px;background:white;color:#263738;border:1px solid #ccd9d3;border-radius:10px;box-shadow:0 3px 20px #0002;max-width:calc(100vw - 24px);font:14px -apple-system,sans-serif';
    notice.append('Вход завершён. Введённый текст остаётся на этой странице. ');
    const link = document.createElement('a');
    link.href = loginUrl(); link.target = '_blank'; link.rel = 'noopener'; link.textContent = 'Войти снова';
    notice.append(link); document.body.append(notice);
  }
  window.fetch = async (...args) => {
    const response = await fetchOriginal(...args);
    if (response.status === 401 && response.headers.get('X-Manager-Login') === 'required') requireLogin();
    return response;
  };
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = 'Выйти'; button.title = 'Выйти из менеджера на этом устройстве';
    button.style.cssText = 'font:inherit;font-size:11px;color:#667570;background:transparent;border:0;cursor:pointer;margin-left:auto;padding:5px 8px';
    const footer = document.querySelector('.sidebar-footer');
    if (footer) footer.append(button);
    else { button.style.cssText += ';position:fixed;top:8px;right:8px;z-index:100'; document.body.append(button); }
    button.addEventListener('click', async () => {
      if (!window.confirm('Выйти из менеджера? Несохранённые изменения будут потеряны.')) return;
      button.disabled = true;
      try {
        const session = await fetchOriginal('/_auth/session');
        if (session.status === 401) { location.assign(loginUrl()); return; }
        if (!session.ok) throw new Error();
        const { csrf } = await session.json();
        const result = await fetchOriginal('/_auth/logout', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: new URLSearchParams({ csrf }) });
        if (!result.ok) throw new Error();
        location.assign('/_auth/login');
      } catch (_) { window.alert('Не удалось выйти. Проверь соединение и попробуй снова.'); }
      finally { button.disabled = false; }
    });
  });
  document.addEventListener('visibilitychange', async () => {
    if (!notice || document.visibilityState !== 'visible') return;
    try {
      const result = await fetchOriginal('/_auth/session');
      if (result.ok) { notice.remove(); notice = null; }
    } catch (_) { /* Keep the draft and the sign-in link. */ }
  });
})();

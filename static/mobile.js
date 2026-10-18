/* This panel only configures the Mac bridge; the phone is a native offline app. */
(() => {
  const byId = id => document.getElementById(id);
  let poll;
  async function refresh() {
    try {
      const response = await fetch('/api/mobile-status', { cache: 'no-store' });
      const status = await response.json();
      if (!response.ok) throw new Error(status.error || 'Не удалось прочитать состояние');
      const date = status.last_sync ? new Date(status.last_sync * 1000).toLocaleString('ru-RU') : 'ещё не было';
      byId('mobileStatus').textContent = `${status.enabled ? 'Обмен включён' : 'Обмен приостановлен'}. ${status.running ? 'Обновление… ' : ''}Последняя подготовка: ${date}. Заказов: ${status.orders}. Требуют разбора: ${status.conflicts}.${status.error ? '\n' + status.error : ''}`;
      byId('mobileEnable').hidden = status.enabled;
      byId('mobilePause').hidden = !status.enabled;
      byId('mobileRefresh').disabled = !status.enabled || status.running;
    } catch (error) { byId('mobileStatus').textContent = error.message; }
  }
  async function update(payload) {
    try {
      const response = await fetch('/api/mobile-sync', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Обмен не запущен');
      await refresh();
    } catch (error) { byId('mobileStatus').textContent = error.message; }
  }
  byId('mobileButton').addEventListener('click', () => {
    byId('mobileDialog').showModal(); refresh(); poll = setInterval(refresh, 2000);
  });
  byId('mobileDialog').addEventListener('close', () => clearInterval(poll));
  byId('mobileClose').addEventListener('click', () => byId('mobileDialog').close());
  byId('mobileEnable').addEventListener('click', () => update({ enabled: true }));
  byId('mobilePause').addEventListener('click', () => update({ enabled: false }));
  byId('mobileRefresh').addEventListener('click', () => update({}));
})();

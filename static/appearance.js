(() => {
  const root = document.documentElement;
  const key = 'zigzag.manager.appearance';
  let storage;
  let choices = [];

  // Применяет выбранное оформление и синхронизирует переключатель в настройках.
  // Отсутствующее или неизвестное значение означает автоматическую тему.
  function apply(mode) {
    root.dataset.appearance = mode === 'light' || mode === 'dark' ? mode : 'auto';
    for (const choice of choices) choice.checked = choice.value === root.dataset.appearance;
  }

  try {
    storage = window.localStorage;
    apply(storage.getItem(key));
  } catch (_) { apply('auto'); }

  window.addEventListener('storage', event => {
    if (event.storageArea === storage && (event.key === key || event.key === null)) {
      apply(storage.getItem(key));
    }
  });

  document.addEventListener('DOMContentLoaded', () => {
    const panel = document.getElementById('managerAppearanceSettings');
    if (!panel) return;
    choices = [...panel.querySelectorAll('input[name="appearance"]')];
    const status = document.getElementById('managerAppearanceState');
    apply(root.dataset.appearance);
    for (const choice of choices) choice.addEventListener('change', () => {
      apply(choice.value);
      try {
        storage.setItem(key, root.dataset.appearance);
        status.textContent = '';
      } catch (_) { status.textContent = 'Браузер не сохранил выбор. Тема действует в этой вкладке.'; }
    });
  }, { once: true });
})();

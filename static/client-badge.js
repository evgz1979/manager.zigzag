const ClientBadge = (() => {
  const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  let colors = new Map(), stylesheet;

  // Выбирает читаемый цвет текста для заданного фона RGB.
  // Сравнивает яркость фона с порогом контраста для чёрного и белого текста.
  function foreground(color) {
    const [r, g, b] = color.slice(1).match(/../g).map(channel => {
      const value = parseInt(channel, 16) / 255;
      return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.179 ? '#000' : '#fff';
  }

  // Обновляет общие стили по сохранённым путям клиентов.
  // Меняет только таблицу стилей, сохраняя узлы ссылок, выделение и фокус.
  function render() {
    if (!stylesheet) {
      stylesheet = document.createElement('style');
      document.head.append(stylesheet);
    }
    const css = [...colors].filter(([, color]) => /^#[0-9a-f]{6}$/.test(color)).map(([path, color]) =>
      `[data-client-badge="${CSS.escape(path)}"]{--client-badge-bg:${color};--client-badge-fg:${foreground(color)};--client-badge-padding:5px;--client-badge-row-padding:2px;--client-badge-edge:inset 0 0 0 1px #0002}`
    ).join('\n');
    if (stylesheet.textContent !== css) stylesheet.textContent = css;
  }

  // Применяет свежий полный снимок вручную заданных цветов.
  // Отсутствующий путь сбрасывает оформление плашки.
  function replace(records) {
    colors = new Map(Object.entries(records || {}));
    render();
  }

  // Применяет подтверждённое сервером изменение одного клиента.
  // Пустой цвет убирает оформление во всех уже отрисованных подписях.
  function set(path, color) {
    const key = path.normalize('NFC');
    if (color) colors.set(key, color);
    else colors.delete(key);
    render();
  }

  // Экранирует подпись и связывает её с полным NFC-путём клиента.
  // Без пути возвращает обычный текст, а цвет берётся из общих стилей.
  function markup(label, path) {
    const value = String(label ?? '').replace(/[&<>"']/g, character => entities[character]);
    if (!value || !path || /^[.#]/.test(path)) return value;
    const key = path.normalize('NFC').replace(/[&<>"']/g, character => entities[character]);
    return `<span class="client-badge" data-client-badge="${key}">${value}</span>`;
  }

  return { replace, set, markup };
})();

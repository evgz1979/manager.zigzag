/* Closing documents stay inside their invoice row; pending File objects survive polling. */
const InvoiceDocuments = (() => {
  const uploads = new Map();
  let hooks;
  const size = (bytes) => bytes < 1024 ? bytes + ' Б' : new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format(bytes / (bytes >= 1048576 ? 1048576 : 1024)) + (bytes >= 1048576 ? ' МБ' : ' КБ');
  const row = (id) => $('invoiceList').invoiceRecords?.find((item) => item.id === id && item.path === state.folder?.path);
  const attr = (record, action, document = '') => ' data-doc-invoice="' + record.id + '" data-doc-action="' + action + '"' + (document ? ' data-doc-document="' + document + '"' : '');
  const uiFor = (record) => {
    if (!uploads.has(record.id)) uploads.set(record.id, { path: record.path, revision: record.revision, files: [], open: false, busy: false, conflict: false, message: '', error: false });
    return uploads.get(record.id);
  };
  const repaint = () => hooks.render($('invoiceList').invoiceRecords || []);

  function button(record) {
    const ui = uploads.get(record.id);
    return '<button class="secondary-button" type="button"' + attr(record, 'toggle') + ' aria-expanded="' + Boolean(ui?.open) + '"' + (!record.closing_documents_editable || ui?.busy ? ' disabled' : '') + '>Закрывашки +' + (ui?.files.length ? ' (' + ui.files.length + ')' : '') + '</button>';
  }

  function markup(record) {
    const ui = uploads.get(record.id);
    const items = record.closing_documents || [], trash = record.closing_documents_trash || [];
    const links = items.map((document) => {
      const url = apiUrl('/api/invoice-document', record.path, { id: record.id, document_id: document.id });
      const copy = document.sync_error ? 'Копия в # bills: ' + document.sync_error + ' · автоповтор' : document.exported ? 'Копия в # bills' : 'Копия в # bills ожидает сохранения';
      return '<div class="invoice-closing-file"><div class="invoice-closing-name"><a href="' + escapeHtml(url) + '" target="_blank" rel="noopener">' + escapeHtml(document.name) + '</a><small class="invoice-closing-copy' + (document.sync_error ? ' error' : '') + '">' + escapeHtml(copy) + '</small></div><small>' + size(document.size) + '</small><button type="button" class="secondary-button invoice-remove"' + attr(record, 'remove', document.id) + ' aria-label="Убрать закрывающий документ · ' + escapeHtml(document.name) + '"' + (ui?.busy ? ' disabled' : '') + '>×</button></div>';
    }).join('');
    const removed = trash.length ? '<details class="invoice-closing-trash" data-doc-invoice="' + record.id + '"' + (ui?.trashOpen ? ' open' : '') + '><summary>Корзина закрывающих (' + trash.length + ')</summary>' + trash.map((document) => '<div class="invoice-closing-file"><span>' + escapeHtml(document.name) + '</span><button class="secondary-button" type="button"' + attr(record, 'restore', document.id) + (ui?.busy ? ' disabled' : '') + '>Восстановить</button></div>').join('') + '</details>' : '';
    let form = '';
    if (ui?.open) {
      const disabled = ui.busy ? ' disabled' : '';
      form = '<div class="invoice-document-upload"><label>Выбрать файлы<input type="file" multiple' + attr(record, 'files') + disabled + '></label><small>Или перетащи документы в эту строку. До 20 МБ на файл.</small>' +
        ui.files.map((pending) => '<div class="invoice-closing-file"><span>' + escapeHtml(pending.file.name) + '</span><small>' + size(pending.file.size) + '</small><button class="secondary-button invoice-remove" type="button"' + attr(record, 'unselect', pending.id) + ' aria-label="Убрать из выбранных · ' + escapeHtml(pending.file.name) + '"' + disabled + '>×</button></div>').join('') +
        '<p class="invoice-document-state' + (ui.error ? ' error' : '') + '" role="status">' + escapeHtml(ui.message) + '</p><div class="invoice-document-actions">' +
        (ui.conflict ? '<button type="button" class="secondary-button"' + attr(record, 'review') + disabled + '>Проверить изменения</button>' : '') +
        '<button type="button" class="secondary-button"' + attr(record, 'upload') + (ui.busy || ui.conflict || !ui.files.length ? ' disabled' : '') + '>Прикрепить</button><button type="button" class="secondary-button"' + attr(record, 'toggle') + disabled + '>Свернуть</button></div></div>';
    }
    return (links ? '<div class="invoice-closing-documents"><small>Закрывающие</small>' + links + '</div>' : '') + removed + (!record.closing_documents_editable ? '<small class="invoice-document-state error">Неизвестный формат закрывающих сохранён без изменений</small>' : '') + form;
  }

  function queue(record, files) {
    const ui = uiFor(record);
    if (ui.busy || !record.closing_documents_editable) return;
    if (!ui.files.length) { ui.path = record.path; ui.revision = record.revision; ui.conflict = false; }
    ui.open = true; ui.message = ''; ui.error = false;
    for (const file of files) {
      if (!file.size || file.size > 20 * 1024 * 1024) { ui.message = 'Выбери непустые документы до 20 МБ каждый.'; ui.error = true; continue; }
      ui.files.push({ id: freeCalendarIdentity(), file });
    }
    if (document.activeElement?.matches('input[type="file"][data-doc-action="files"]')) document.activeElement.blur();
    repaint();
  }

  function encoded(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(new Error('Не удалось прочитать файл. Выбери его ещё раз.'));
      reader.onload = () => resolve(String(reader.result).split(',')[1]);
      reader.readAsDataURL(file);
    });
  }

  async function upload(record) {
    const ui = uiFor(record);
    if (ui.busy || ui.conflict || !ui.files.length) return;
    ui.busy = true; ui.error = false;
    try {
      while (ui.files.length) {
        const pending = ui.files[0];
        ui.message = 'Прикрепляю: ' + pending.file.name; repaint();
        const saved = await request('/api/invoice-document-upload', { path: ui.path, id: record.id, revision: ui.revision,
          document_id: pending.id, name: pending.file.name, content: await encoded(pending.file) });
        ui.revision = saved.revision;
        ui.files.shift();
        hooks.accept(saved);
      }
      ui.open = false; ui.message = '';
      notify('Закрывающие прикреплены к счёту');
      await hooks.refresh();
    } catch (error) {
      ui.conflict = error.status === 409;
      ui.message = error.message + ' Выбранные файлы остались в строке.';
      ui.error = true;
    } finally { ui.busy = false; repaint(); }
  }

  async function review(record) {
    const ui = uiFor(record);
    if (ui.busy) return;
    ui.busy = true;
    try {
      const saved = await request(apiUrl('/api/invoice', record.path, { id: record.id }));
      if (!saved.closing_documents_editable) throw new Error('Неизвестный формат закрывающих сохранён без изменений');
      hooks.accept(saved); ui.path = saved.path; ui.revision = saved.revision; ui.conflict = false; ui.error = false;
      ui.message = 'Сейчас у счёта: ' + (saved.closing_documents.map((item) => item.name).join(', ') || 'закрывающих нет') + '. Проверь строку и нажми «Прикрепить» ещё раз.';
    } catch (error) { ui.message = error.message; ui.error = true; }
    finally { ui.busy = false; repaint(); }
  }

  async function change(record, documentId, deleted) {
    const ui = uiFor(record);
    if (ui.busy) return;
    ui.busy = true; repaint();
    try {
      const saved = await request(deleted ? '/api/invoice-document-remove' : '/api/invoice-document-restore',
        { path: record.path, id: record.id, revision: record.revision, document_id: documentId });
      ui.revision = saved.revision; hooks.accept(saved);
      notify(deleted ? 'Закрывающий документ убран из строки' : 'Закрывающий документ восстановлен', false,
        deleted ? { label: 'Отменить', run: () => change(saved, documentId, false) } : null);
      await hooks.refresh();
    } catch (error) { await hooks.refresh(); throw error; }
    finally { ui.busy = false; repaint(); }
  }

  function init(options) {
    hooks = options;
    $('invoiceList').addEventListener('toggle', (event) => {
      if (!event.target.matches('.invoice-closing-trash')) return;
      const record = row(event.target.dataset.docInvoice);
      if (record) uiFor(record).trashOpen = event.target.open;
    }, true);
    $('invoiceList').addEventListener('change', (event) => {
      const input = event.target.closest('[data-doc-action="files"]'), record = input && row(input.dataset.docInvoice);
      if (record) queue(record, [...input.files]);
    });
    $('invoiceList').addEventListener('click', (event) => {
      const control = event.target.closest('[data-doc-action]'), record = control && row(control.dataset.docInvoice);
      if (!record) return;
      const ui = uiFor(record), action = control.dataset.docAction;
      if (ui.busy) return;
      if (action === 'toggle') {
        if (!ui.files.length) { ui.path = record.path; ui.revision = record.revision; ui.conflict = false; }
        ui.open = !ui.open; repaint();
      } else if (action === 'unselect') { ui.files = ui.files.filter((item) => item.id !== control.dataset.docDocument); repaint(); }
      else if (action === 'upload') upload(record);
      else if (action === 'review') review(record);
      else if (action === 'remove' || action === 'restore') change(record, control.dataset.docDocument, action === 'remove').catch((error) => notify(error.message, true));
    });
    $('invoiceList').addEventListener('dragover', (event) => {
      if (![...event.dataTransfer?.types || []].includes('Files')) return;
      const element = event.target.closest('[data-invoice-row]'), record = element && row(element.dataset.invoiceRow);
      if (!record?.closing_documents_editable) return;
      event.preventDefault(); event.stopPropagation(); event.dataTransfer.dropEffect = uploads.get(record.id)?.busy ? 'none' : 'copy';
      element.classList.add('invoice-document-drag');
    });
    $('invoiceList').addEventListener('dragleave', (event) => {
      const element = event.target.closest('[data-invoice-row]');
      if (element && !element.contains(event.relatedTarget)) element.classList.remove('invoice-document-drag');
    });
    $('invoiceList').addEventListener('drop', (event) => {
      if (![...event.dataTransfer?.types || []].includes('Files')) return;
      const element = event.target.closest('[data-invoice-row]'), record = element && row(element.dataset.invoiceRow);
      if (!record?.closing_documents_editable) return;
      event.preventDefault(); event.stopPropagation(); element.classList.remove('invoice-document-drag');
      if ([...event.dataTransfer.items || []].some((item) => item.webkitGetAsEntry?.()?.isDirectory)) { notify('Выбери документы без папок', true); return; }
      queue(record, [...event.dataTransfer.files]);
    });
    window.addEventListener('beforeunload', (event) => { if ([...uploads.values()].some((ui) => ui.busy || ui.files.length)) { event.preventDefault(); event.returnValue = ''; } });
  }

  function focusKey() {
    const element = document.activeElement?.closest('[data-doc-action]');
    return element ? { action: element.dataset.docAction, id: element.dataset.docInvoice, document: element.dataset.docDocument || '' } : null;
  }

  function restoreFocus(key) {
    if (!key || document.activeElement !== document.body) return;
    [...$('invoiceList').querySelectorAll('[data-doc-action]')].find((element) => element.dataset.docAction === key.action && element.dataset.docInvoice === key.id && (element.dataset.docDocument || '') === key.document)?.focus({ preventScroll: true });
  }

  return { init, markup, button, focusKey, restoreFocus, isBusy: (id) => Boolean(uploads.get(id)?.busy) };
})();

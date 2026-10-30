/* Regression: crossing an adjacent calendar row must not replace the popup. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');

function fixture() {
  let now = 0, nextTimer = 0;
  const timers = new Map(), elements = new Map();
  function element(id, parent = null) {
    const item = { id, parent, dataset: {}, hidden: true, style: {}, handlers: {}, scrollTop: 0,
      rect: { left: 100, top: 100, bottom: 112, width: 300, height: 12 },
      contains(other) { for (; other; other = other.parent) if (other === this) return true; return false; },
      closest() { for (let node = this; node; node = node.parent) if (node.dataset.calendarTodos) return node; return null; },
      addEventListener(name, handler) { (this.handlers[name] ||= []).push(handler); },
      removeAttribute() {}, setAttribute() {}, getBoundingClientRect() { return this.rect; },
      focus() { context.document.activeElement = this; },
    };
    elements.set(id, item);
    return item;
  }
  const weeks = element('calendarWeeks'), popup = element('calendarTodoPreview');
  popup.rect = { width: 390, height: 150 };
  const body = element('calendarTodoPreviewBody', popup), outside = element('outside');
  const first = element('first', weeks), second = element('second', weeks);
  first.dataset.calendarTodos = 'first-order'; second.dataset.calendarTodos = 'second-order';
  const child = element('second-icon', second);
  const context = vm.createContext({
    $: (id) => elements.get(id), document: { activeElement: outside }, state: { calendarMenu: null },
    innerWidth: 1000, innerHeight: 600,
    setTimeout(callback, delay) { const id = ++nextTimer; timers.set(id, { callback, at: now + delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
  });
  const start = source.indexOf('const calendarTodoPreview =');
  const end = source.indexOf('function renderCalendarEventControls()', start);
  assert(start >= 0 && end > start);
  vm.runInContext(source.slice(start, end), context);
  vm.runInContext('renderCalendarTodoPreview = function () {};', context);
  const handlers = source.indexOf('$("calendarWeeks").addEventListener(\'pointerover\'');
  const handlersEnd = source.indexOf('$("closeCalendarTodoPreview").addEventListener', handlers);
  assert(handlers >= 0 && handlersEnd > handlers);
  vm.runInContext(source.slice(handlers, handlersEnd), context);
  function event(node, name, target = node, relatedTarget = null) {
    for (const handler of node.handlers[name] || []) handler({ target, relatedTarget });
  }
  function tick(ms) {
    const through = now + ms;
    while (true) {
      const next = [...timers].filter(([, timer]) => timer.at <= through).sort((a, b) => a[1].at - b[1].at)[0];
      if (!next) break;
      now = next[1].at; timers.delete(next[0]); next[1].callback();
    }
    now = through;
  }
  const preview = vm.runInContext('calendarTodoPreview', context);
  return { context, weeks, popup, body, first, second, child, outside, event, tick, preview };
}

{
  const f = fixture();
  f.event(f.weeks, 'pointerover', f.first);
  assert.equal(f.preview.anchor, f.first);
  f.event(f.weeks, 'pointerout', f.first, f.second);
  f.event(f.weeks, 'pointerover', f.second, f.first);
  f.tick(200);
  assert.equal(f.preview.anchor, f.first, 'briefly crossing the lower row keeps the original order');
  f.event(f.weeks, 'pointerout', f.second, f.popup);
  f.event(f.popup, 'pointerenter');
  f.tick(1000);
  assert.equal(f.preview.anchor, f.first, 'entering the popup cancels the pending replacement');
  assert.equal(f.popup.hidden, false);
  f.event(f.popup, 'pointerleave');
  f.tick(499); assert.equal(f.popup.hidden, false);
  f.tick(1); assert.equal(f.popup.hidden, true);
}
{
  const f = fixture();
  f.event(f.weeks, 'pointerover', f.first);
  f.event(f.weeks, 'pointerout', f.first, f.second);
  f.event(f.weeks, 'pointerover', f.second, f.first);
  f.tick(200); f.event(f.weeks, 'pointerover', f.child, f.second);
  f.tick(150);
  assert.equal(f.preview.anchor, f.second, 'deliberately hovering another event still opens its tasks');
  f.event(f.weeks, 'pointerover', f.first);
  f.event(f.weeks, 'focusin', f.second);
  f.tick(1000);
  assert.equal(f.preview.anchor, f.second, 'keyboard focus cancels a queued mouse switch');
  f.context.openCalendarTodoPreview(f.first, true);
  f.event(f.weeks, 'pointerover', f.second); f.tick(1000);
  assert.equal(f.preview.anchor, f.first, 'a pinned popup stays on its selected order');
}
{
  const f = fixture();
  f.event(f.weeks, 'pointerover', f.first);
  f.event(f.weeks, 'pointerover', f.second);
  f.context.document.activeElement = f.body;
  f.event(f.popup, 'focusin'); f.tick(1000);
  assert.equal(f.preview.anchor, f.first, 'focusing popup controls cancels a pending switch');
  f.context.positionCalendarTodoPreview();
  assert.equal(f.popup.style.top, '112px', 'the popup touches the bottom edge of the event');
  f.first.rect = { left: 100, top: 550, bottom: 562 };
  f.context.positionCalendarTodoPreview();
  assert.equal(f.popup.style.top, '400px', 'when above, the popup touches the top edge');
  f.context.document.activeElement = f.outside;
  f.event(f.weeks, 'pointerover', f.second);
  f.context.closeCalendarTodoPreview(); f.tick(1000);
  assert.equal(f.popup.hidden, true, 'dismissal never reopens a queued popup');
}
console.log('Calendar To-do hover regression checks passed');

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const context = vm.createContext({ Intl, Date });
vm.runInContext(fs.readFileSync(path.join(__dirname, "../static/home-calendar.js"), "utf8") + "\nthis.calendar = HomeCalendar;", context);
const now = new Date("2026-11-01T12:00:00Z");
const order = {
  path: "client/order", registered: true, deadline_weeks: ["2026-11-02"],
  calendar_events: { "2027-01-05": "Hidden small event" }, calendar_compact: true,
};
let range = context.calendar.calendarRange(now, [order]);
assert.equal(range.end.toISOString().slice(0, 10), "2026-11-08");
assert.equal(range.start.toISOString().slice(0, 10), "2026-10-26");
range = context.calendar.calendarRange(now, [{ ...order, calendar_compact: false }]);
assert.equal(range.end.toISOString().slice(0, 10), "2027-01-10");
range = context.calendar.calendarRange(now, [{ ...order, calendar_compact: null }]);
assert.equal(range.end.toISOString().slice(0, 10), "2027-01-10");
range = context.calendar.calendarRange(now, [{ ...order, deadline_weeks: ["2027-01-04"] }]);
assert.equal(range.end.toISOString().slice(0, 10), "2027-01-10");

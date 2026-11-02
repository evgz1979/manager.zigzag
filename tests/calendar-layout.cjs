const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const context = vm.createContext({ Intl, Date });
const source = fs.readFileSync(path.join(__dirname, "../static/home-calendar.js"), "utf8");
vm.runInContext(source.replace("return { show, calendarRange, createSnapshot, snapshotRange };", "return { show, calendarRange, createSnapshot, snapshotRange, visibleOrderWeeks, moscowDate };") + "\nthis.calendar = HomeCalendar;", context);
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

// A selected week retains its rows throughout Sunday in Moscow. From Monday,
// only rows with an active unfinished weekly or daily event remain in that week.
const week = "2026-10-26", next = "2026-11-02";
const base = { path: "client/order", deadline_weeks: [week, next], calendar_events: {}, calendar_week_events: {}, calendar_completed: { day: [], week: [] } };
const weeksAt = (record, at) => Array.from(context.calendar.visibleOrderWeeks(record, context.calendar.moscowDate(new Date(at))));
const sunday = "2026-11-01T20:59:59Z", monday = "2026-11-01T21:00:00Z";
assert.deepEqual(weeksAt(base, sunday), [week, next]);
assert.deepEqual(weeksAt(base, monday), [next]);
const finished = { ...base, calendar_events: { "2026-10-27": "Done", "2026-11-02": "Future done" }, calendar_week_events: { [week]: "Weekly done", [next]: "Future weekly done" }, calendar_completed: { day: ["2026-10-27", "2026-11-02"], week: [week, next] } };
assert.deepEqual(weeksAt(finished, sunday), [week, next]);
assert.deepEqual(weeksAt(finished, monday), [next]);
assert.deepEqual(weeksAt({ ...finished, calendar_events: { ...finished.calendar_events, "2026-11-01": "Still to do" } }, monday), [week, next]);
assert.deepEqual(weeksAt({ ...finished, calendar_completed: { day: finished.calendar_completed.day, week: [next] } }, monday), [week, next]);
assert.deepEqual(weeksAt({ ...base, calendar_events: { "2026-10-27": "  " } }, monday), [next]);
// Suppliers use the same rule, while small-order links have no event row.
assert.deepEqual(weeksAt({ ...finished, work_supplier: "glass" }, monday), [next]);
assert.deepEqual(weeksAt({ ...finished, calendar_compact: true }, monday), [week, next]);
// Completed and irrelevant events together must not retain a past row.
// Exercise the same mixed weekly/daily data as supplier orders in production.
const closed = { ...base,
  calendar_events: { "2026-10-27": "Delivered", "2026-10-28": "Old reminder" },
  calendar_week_events: { [week]: "Old payment reminder" },
  calendar_completed: { day: ["2026-10-27"], week: [] },
  calendar_inactive: { day: ["2026-10-28"], week: [week] },
};
for (const supplier of [undefined, "glass", "antares"]) {
  const row = { ...closed, work_supplier: supplier };
  assert.deepEqual(weeksAt(row, sunday), [week, next]);
  assert.deepEqual(weeksAt(row, monday), [next]);
  assert.deepEqual(weeksAt({ ...row, calendar_events: { ...row.calendar_events, "2026-10-31": "Still needed" } }, monday), [week, next]);
  assert.deepEqual(weeksAt({ ...row, calendar_inactive: { day: ["2026-10-28"], week: [] } }, monday), [week, next]);
  assert.deepEqual(weeksAt({ ...row, calendar_inactive: null }, monday), [week, next]);
}
// Unknown text or completion formats must not silently hide potentially open work.
assert.deepEqual(weeksAt({ ...finished, calendar_completed: null }, monday), [week, next]);
assert.deepEqual(weeksAt({ ...finished, calendar_events: null }, monday), [week, next]);
assert.deepEqual(weeksAt({ ...finished, calendar_week_events: null }, monday), [week, next]);
// Removing completion restores a past row; different weeks stay independent.
assert.deepEqual(weeksAt({ ...finished, calendar_completed: { day: [], week: [week, next] } }, monday), [week, next]);
const boundary = { ...base, deadline_weeks: ["2026-12-28", "2027-01-04"] };
assert.deepEqual(weeksAt(boundary, "2027-01-03T20:59:59Z"), ["2026-12-28", "2027-01-04"]);
assert.deepEqual(weeksAt(boundary, "2027-01-03T21:00:00Z"), ["2027-01-04"]);
assert.deepEqual(weeksAt({ ...base, registered: false }, monday), []);

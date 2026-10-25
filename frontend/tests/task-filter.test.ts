import assert from "node:assert/strict";
import test from "node:test";
import { filterTasks } from "../src/task-filter.ts";

const tasks = [
  { id: "f424f62b-4081", experiment_name: "2024沪深300历史四因子研究", status: "success", marker: 1 },
  { id: "858c2667-19b8", experiment_name: "动量单因子", status: "failed", marker: 2 },
  { id: "321b313b-218a", experiment_name: "动量单因子", status: "success", marker: 3 },
];

test("task search matches run ID or research name case-insensitively and preserves order", () => {
  assert.deepEqual(filterTasks(tasks, "F424", "all").map(item => item.marker), [1]);
  assert.deepEqual(filterTasks(tasks, "  动量  ", "all").map(item => item.marker), [2, 3]);
  assert.deepEqual(filterTasks(tasks, "", "all"), tasks);
});

test("task status and search combine without leaking unmatched details", () => {
  assert.deepEqual(filterTasks(tasks, "动量", "success").map(item => item.id), ["321b313b-218a"]);
  assert.deepEqual(filterTasks(tasks, "missing", "all"), []);
  assert.deepEqual(filterTasks(tasks, "", "pending"), []);
});

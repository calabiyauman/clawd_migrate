"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

const root = path.join(__dirname, "..");
const parent = path.join(root, "..");
const env = { ...process.env, PYTHONPATH: parent };

const r = spawnSync(
  "python",
  ["-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
  { cwd: root, env, stdio: "inherit" }
);

process.exit(r.status !== null ? r.status : 1);

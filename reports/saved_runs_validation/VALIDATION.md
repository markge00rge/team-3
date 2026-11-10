# Saved-run application validation ? 10 November 2026

Application, persistence and presentation update only. Branch remains `v5-development`.
The validated src/ engine/source fingerprint is unchanged. All 146 protected source
and historical-report fingerprints match. Existing dirty changes were preserved.

## Tests

- Full suite: **209 passed** in 309.93 seconds (`saved_runs_full_tests.log`).
- Final targeted persistence, UI and mapping checks: **65 passed** (`saved_runs_final_validation.log`).
- Final long-name comparison check: **1 passed** (`saved_runs_long_name_test.log`).
- Individual and comparison financial-card Chrome audits: five requested widths
  each (1024, 1280, 1366, 1440, 1920), respectively five and ten cards; no measured
  clipping or horizontal overflow. JSON/screenshots in `reports/saved_runs_ui_layout/`
  and `reports/saved_runs_comparison_layout/`. These are browser component checks;
  complete Streamlit screens are covered with AppTest.
- Exact comparison of every persisted result table against its exported CSV passed
  for both real original/salary validation runs. No numeric rounding was introduced.

## Real end-to-end saved runs

Both runs execute the current Pyomo/HiGHS engine, with audits and financial
reconciliation before transactional SQLite saving. Every one of the seven stages
is status `ok`, termination `optimal`, reported relative gap 0. Both serve
3,095/3,095 MSU. Neither is a cached or fabricated baseline.

- original: ID `fbb1b59cb6f14c2fafc11e694531ed4c`, cost $10,941,467.50; files `reports\app_runs\saved_history_original_8399e5ea3c`. Exact saved name: `Original Venus ? Saved History Validation`.
- salary: ID `b087f5600c6f4032b522a7a679cef11d`, cost $10,857,467.50; files `reports\app_runs\saved_history_salary_7bb90d5742`. Exact saved name: `Lower Salary ? Saved History Validation`.

The customized run changes only salary from $1,000 to $900/operator/month.
Comparison correctly finds that nested input difference and approximately $84,000
lower annual cost (about ?0.768%). Service is identical; there is no service sacrifice.

## Persistence / usage

Local database: `app_data/runs.sqlite3` (Git-ignored). Saved records contain complete
effective inputs, scenario configuration, all result tables, proof/audit data and
version metadata. Read-only reopening and seven-section input inspection make no
solver calls, do not load historical values from current defaults and preserve the
active draft. Duplicate names have separate UUIDs. Two distinct same-category runs
are required for comparison; zero-reference percentages are unavailable. Different
financial definitions suppress monetary differences and show a warning.

Operating Expenses and Total Delivery Cost now display exact formatted dollars;
materials can be compact. All full-precision values remain in saved records and
exports. Full implementation/usage details: SAVED_RUNS_GUIDE.md.

## Scope / remaining limitations

General Plant remains future-only. Pre-SQLite result folders are not automatically
imported when complete effective-input provenance is unavailable; they remain
unchanged on disk. Older saved records missing new report fields are shown with
availability notices, never recomputed. History is local single-application storage;
no cloud sync, user authentication or general-purpose plant model was introduced.
All existing Venus modeling limitations remain unchanged.

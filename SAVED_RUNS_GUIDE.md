# Saved runs and scenario comparison

Launch the existing application:

```powershell
.venv\Scripts\python.exe -m streamlit run app/main.py
```

## Name, optimize and save

For original inputs, choose **Venus Case Study → Run Original Case**, enter a
**Scenario Run Name**, then select **Run Optimization**. For customized inputs,
enter the run name on **Review & Optimize**, then select **Optimize Supply Chain**.
Names are trimmed and limited to 100 characters. Duplicate display names receive
a notice and separate UUIDs; they never overwrite an earlier plan. Name drafts
survive questionnaire navigation. The editable draft remains separate from a run.

The same Pyomo/HiGHS engine runs. Only after solution and financial validation does
the worker automatically save the run. A fully optimal plan and a valid feasible
incumbent retain their distinct solver status, bounds and gaps. Failed solves with
no validated solution are not saved. A database error is displayed explicitly;
the checked file-based solve remains available, without claiming it was saved.

## Persistent local snapshots

The default SQLite database is **`app_data/runs.sqlite3`**. It is created on first
use. `CAIRO_RUN_DB` can select another local database, principally for testing.
No new dependency is needed: SQLite is in the Python standard library.

Each append-only record stores:

- UUID, name, Venus/General Plant category, original/customized type and UTC
  creation timestamp. The run list displays Cairo local time.
- Snapshot schema version, mathematical version, engine/source fingerprint and
  financial-definition version.
- The complete serialized scenario plus **all effective model inputs**: months,
  calendar/rules, products/families, lines/profiles, hubs/priorities, BOM/valuations,
  opening stocks, fixed receipts, procurement/prices, staffing, warehouse,
  transport and the complete regional/family forecast. This is not a change list.
- Original result tables, derived financial/operational tables, transition/IDE,
  numerical audit and full solver outcome. Captured assumptions are retained too.

JSON serialization preserves Python floating-point precision. Undefined diagnostic
ratios are JSON null, not invented zero values. There is no pickle or recalculation
inside storage. SQLite transactions commit each record atomically. SHA-256
checksums detect snapshot corruption; metadata is cross-checked. The application
provides no update/delete operation for saved records. Exact identical retries are
idempotent; attempts to replace an existing ID are rejected.

Database files and user-generated `reports/app_runs/` outputs are Git-ignored.
Data stays local. Keep a backup of `app_data/` if moving the application; with the
application stopped, copying the database retains the history. This local storage
is not an encrypted multi-user database or a cloud synchronization service.

## Reopen and inspect

Select **Compare Runs** in the sidebar from any page. The **Venus Case Study Runs**
tab lists saved names, dates, original/customized labels, service, saved cost and
solver status. Sort by date, name or cost. Choose a run and **Open Saved Dashboard**.

The regular results dashboard reads the database snapshot only. It does not call
the loader, build a model, rerun a solver or apply new defaults. It is explicitly
marked as a read-only saved result. **View Configured Parameters**, at the upper
right, opens seven read-only sections; **Back to Saved Results** returns to that
same run. This does not modify the active editable scenario. Complete snapshots,
scenario configurations, CSV tables and Excel reports can be downloaded.

Older records missing newer reporting tables show their available saved tables
with a clear notice. They are not backfilled with current formulas. Pre-SQLite
report folders/baselines are preserved on disk and are **not silently imported**:
older folders may lack the complete effective input snapshot, and reconstructing
one from today's defaults would misrepresent their provenance.

## Compare two plans

Select exactly two distinct Venus runs and choose **Compare Selected Runs**.
The first selection is **Scenario A / Reference**, the second **Scenario B**.
Differences are B − A; percentage change is `(B − A) / A × 100`. A zero reference
has no defined percentage. General Plant history remains a clearly labelled
future capability; no general-purpose optimizer was added.

The comparison shows metadata, all five headline costs and detailed financial
categories, input changes, the input demand forecast, monthly/annual/regional
service, workforce assumptions and decisions, production/capacity/qualification,
materials/orders/arrivals/scrap, inventory/warehouse/cash and distribution/trucks.
Seven focused charts compare demand, production, total cost, cost composition,
service, employment and holding expense. Full historical inputs remain accessible.
Changed nested parameters and individual demand cells receive readable labels.

Different demand or service triggers a prominent trade-off warning. A lower cost
is not labelled a saving automatically. Different model fingerprints are disclosed.
Different financial-definition versions withhold monetary differences/percentages;
the original saved figures remain visible. Missing metrics stay unavailable.

## Financial cards

**Operating Expenses** and **Total Delivery Cost** use full dollar amounts with
thousands separators and two decimals, in both individual and comparison views.
They are placed prominently above the three material cards. Material figures may
be compact; exact unrounded values remain in tooltips/details and numeric exports.
Only presentation is rounded. Responsive grids, container queries and bounded font
sizes prevent the five cards from being forced into one narrow row. Increase/decrease
colors describe direction, not whether a decision is better.

## Code boundaries

| File | Responsibility |
| --- | --- |
| `app/run_store.py` | SQLite, complete input/table serialization, integrity, immutable save/list/get APIs |
| `app/comparisons.py` | Pure saved-data differences, percentages, demand/service comparisons and compatibility warnings |
| `app/history.py` | History, read-only parameter viewer and detailed comparison screens |
| `app/optimizer_adapter.py` | Capture effective inputs before building; save actual validated results after solving |
| `app/jobs.py`, `app/worker.py` | Named run metadata/type propagation and independent worker execution |
| `app/main.py`, `app/pages/questionnaire.py`, `app/components/fields.py` | Required names, persistent drafts and navigation |
| `app/dashboard.py` | Reuse the results interface with stored data; no historical recomputation |
| `app/components/financial_cards.py`, `app/theme.py` | Exact/compact responsive cards and long-name wrapping |
| `app/check_financial_layout.py` | Actual headless Chrome individual/comparison component audits |

No `src/` mathematical, accounting, input-loader or solver files changed for this
milestone. Original P&G documents and historical checkpoints/reports are preserved.

## Validation

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m app.check_financial_layout
.venv\Scripts\python.exe -m app.check_financial_layout --comparison --output-dir reports/saved_runs_comparison_layout
```

The complete suite passed **209 tests**. Subsequent focused checks cover the final
name-draft, historical-title and compatibility presentation changes. Tests cover
database restart/immutability/errors, status preservation, complete snapshots,
read-only navigation without solver calls, two-run selection, nested/demand and
financial comparisons, exact formatting, and real worker automatic saves. Browser
component audits pass at 1024/1280/1366/1440/1920 requested widths in both layouts;
these are component checks, alongside Streamlit AppTest screen checks.

Two real end-to-end validation runs are saved in the local history:

| Run | Service | Total Delivery Cost | Proof |
| --- | ---: | ---: | --- |
| Original Venus — Saved History Validation | 100% | $10,941,467.50 | All seven stages optimal; zero reported gaps |
| Lower Salary — Saved History Validation | 100% | $10,857,467.50 | All seven stages optimal; zero reported gaps |

The second run uses $900/operator/month instead of $1,000. Saved comparisons find
that single input change and an approximately $84,000 lower annual cost. These are
real new solves, not cached baseline substitutions. The original result matches
the validated V6 objective; the engine fingerprint is unchanged.

Run IDs, exact file locations, audits and final test logs are recorded in
`reports/saved_runs_validation/VALIDATION.md`.

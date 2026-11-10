# V7: explicit Product B procurement, stock, space and purchase expense

V7 extends the existing Venus MILP; it does not generalize plant structure.
The unchanged Word/Excel loader retains original source facts. A separate
`planning_case()` adapter adopts **B RM 200,000 kg / PM 750,000 EA** as opening
planning assumptions following the user's clarification. These are not numerical
stocks discovered in the original documents. Both are editable and may be zero.
Original opening FP stays A=10, B=15, C=0 MSU. No fixed B shipments are introduced.

## Shared material formulation

The existing material-product set now contains A, B and C. For each product,
RM/PM and month, ending stock equals opening + original fixed arrivals + valid
additional arrivals - actual-production BOM consumption - A scrap where applicable.
The same conservation is enforced daily, using receipts only on planning day 1;
monthly stocks are linked to day 28. All inventories are nonnegative. Thus B cannot
borrow future arrivals, use A/C materials or manufacture without its own materials.
Only A is scrapped at qualification. B continues through the A/C transition, subject
to the same full-plant shutdown and L2 sequencing restrictions as before.

B BOM remains 600 kg RM and 2,000 EA PM/MSU, now also editable. Every additional
ABC RM order is an integer multiple of 50,000 kg; PM orders use 125,000 EA. Shared
procurement inputs retain their supported customization; defaults are three
planning months and the stated lots. October orders arrive in January, at month
start. There are no pre-horizon invented orders or orders arriving after September.
The three original A/C shipments retain their dates and quantities.

Each positive product/material/month order has one binary event, with finite
capacity-derived lot bounds. RM and PM events are separate physical categories.
The event sum and MSU-equivalent quantity tie-break now cover all six categories.
Scenario A remains annual regional service lexicography with independent monthly
family/hub priorities, then strict monetary cost, events, quantities and cleanup.
An unproven stage stops progression; no cost tolerance or weighted surrogate exists.

## Warehouse and holding

Month-end tracked space equals all ABC FP × 4 pallets/MSU, plus all ABC RM / 1,000
and all ABC PM / 5,000. Capacity is 1,200 pallets plus integer 100-pallet external
blocks at $45/pallet/month, charging $4,500 for a whole block. Reports split all
nine product/inventory categories. B opening RM/PM adds 350 pallets; its opening
15 FP MSU already contributes 60 pallets in the existing FP model, exactly once.
September-30 total tracked opening occupancy is 645 pallets, before October receipts.

FP holding remains product-specific ending FP value × 1.5%/month. B uses $5,500/MSU,
or $82.50 per ending MSU/month. B RM/PM is not charged FP holding. No material
carrying fee, maritime freight, terminal disposal or salvage value is invented.
Warehouse feasibility remains a month-end measure; intramonth peaks are not proven.

## Financial definition

All three products now use **additional order quantity × product-specific unit
price**, charged in the placement month. Default RM $5/kg and PM $0.40/EA remain
editable for each product. The former B-production-linked expense is removed in
V7. B consumption and receipts are quantity reports, not another expense.
Opening materials and fixed precommitted receipts are excluded from new purchases;
opening B FP and later FP shipments generate no new material purchase expense.

The five cards reconcile operating expenses excluding purchases, additional A,
additional C, additional B, and Total Delivery Cost. Full A IDE is retained with
the existing exact newly purchased A scrap-value overlap adjustment. Disposal is
never subtracted. No physical A scrap quantity or legacy-first provenance rule changes.
Operating Expense and Total Delivery Cost use full dollars; material cards may be
compact with exact values retained in details/exports.

## Versions, persistence and historical compatibility

Current input schema is **3**. V6 schema 2 remains reproducible programmatically
under its original smooth-B rules. Loading an old parameter JSON for a *new* UI
run explicitly upgrades the editable draft with a visible notice and B defaults.
Saved historical results are read directly, never migrated or recalculated.
New snapshots use model `Venus V7 / explicit ABC procurement / strict Scenario A`
and financial definition `venus-v7-abc-additional-purchases-1`. Comparisons with V6
warn that B accounting changed and withhold monetary differences/percentage savings.
SQLite records and original case documents are not rewritten or deleted.

## Retained assumptions and limitations

Exactly 28 manufacturing days per month; optimized consecutive three-day
qualification; permanent A manufacturing cessation; A FP sell-through; one routine
L2 changeover/month; optional trained crews with dismissal/rehire; transport,
inventory and service constraints remain. Packaging usability is unverified:
batch ages are unavailable and expiry is not modeled. C:D metrics are diagnostic.
No intramonth warehouse simulation, GUI generalization, unsupported overtime rate
or numerical headcount cap is added. B physical material stock is now tracked;
the former B warehouse-footprint exclusion no longer applies to V7.

## Reproduction and validation

```powershell
.venv\Scripts\python.exe -m streamlit run app/main.py
.venv\Scripts\python.exe -m src.solve --output-dir reports/v7_new --time-limit 300
.venv\Scripts\python.exe -m src.reporting --report-dir reports/v7
.venv\Scripts\python.exe -m src.validation --report-dir reports/v7
.venv\Scripts\python.exe -m pytest -q
```

Use fresh run directories; historical reports remain preserved. Actual run IDs,
financial values, procurement schedules, independent reconciliations and solver
bounds/gaps are documented in `reports/v7_validation/VALIDATION.md`. Mathematical
optimality comes from solver status, not from passing tests.

## Procurement-event proof mode

`python -m src.procurement_proof --source reports/v7 --output-dir reports/new_proof --seconds 600 --strengthen`
tests successively smaller event caps on the complete model, using the saved
proven service/cost locks. Use a fresh directory. Manufacturing, transition and
staffing decisions remain free. Optional integer-rounded B prefix cover cuts
follow from full service and material conservation. A timeout is inconclusive;
only an infeasibility certificate at one fewer event proves the incumbent count.
See `PROCUREMENT_EVENT_OPTIMALITY_AUDIT.md` for actual tests, logs and outcomes.
Historical saved statuses are not rewritten by a separate proof attempt.

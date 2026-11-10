# V6: flexible crews and complete material-cost Scenario A

The existing daily MILP and Streamlit application are extended, not replaced.
Original Word/Excel sources and historical V2–V5 outputs remain unchanged.
Only strict Scenario A is supported. Service priorities precede monetary cost,
then additional material-specific events and procurement quantities. No cost
tolerance is allowed. An unproven tie-break stops further lexicographic stages.

## Workforce formulation

For each line/month, binary employed E, hire H and dismissal D satisfy
E[t] = E[t-1] + H[t] - D[t], H <= 1-E[t-1], D <= E[t-1], H+D <= 1.
Qualified/upgraded status requires employment and no hire during the preceding
T full training months, including the current month. Training provides no
additional days. Every rehire pays its fee and repeats all training. Salaries
are charged for every employed month, including training; dismissal at month
start removes salary and upgraded capacity immediately. The base 70 workers
remain permanent. Disabling dismissal fixes D=0, preserving permanent hiring.
Crew size, integer training months, salaries, hiring fees and dismissal expense
are editable. Default dismissal expense $0/operator is a new assumption, not
an original case fact. No overtime or unsupported severance rule is inferred.

## Monetary objective and five financial cards

Total Delivery Cost = reconciled operating expense + new A material expense +
new C material expense + B production-linked material expense.

A/C costs use additional ORDER quantities times their respective configurable
product/material prices, charged in the placement month. Opening stocks and
original fixed receipts are excluded. B uses actual production times its BOM
(600 kg and 2,000 EA/MSU) and product-specific prices: $3,800/MSU at defaults.
B has no material stock or procurement variables, and opening B FP is not
charged again. Inventory asset value is not another operating expense.

Full original IDE remains reported: A RM value plus PM value and both disposal
expenses. Material provenance uses **legacy-first consumption**. All original A
opening/fixed stocks precede new A receipts in the supported Venus scenario.
Newly purchased A scrap equals min(total A scrap, total new A purchases), for
each material. An exact bounded binary MILP formulation enforces this minimum
independently of objective direction. Its purchase value is subtracted once
from full-IDE operating expense; disposal is never subtracted. Thus procurement
and the same newly purchased material write-off are not counted twice. This
provenance convention must be revisited before changing original receipt dates.
Monthly reports show full IDE, overlap adjustment and reconciled subtotal.

## Retained assumptions and limitations

All existing 28-day calendars, qualification, permanent A manufacturing stop,
A FP sell-through, L2 sequencing, monthly family/hub priorities, material balances,
lot increments, lead times, fixed receipts, warehouse and trucking rules remain.
Packaging usability is unverified; no aging model is added. Physical B material
stock/space is unspecified and excluded, not physically zero. Warehouse capacity
is enforced at month end; intramonth physical peaks are not fully established.
No arbitrary plant structural generalization is supported.

## Validation and reproduction

- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m src.solve --output-dir reports/v6_new --time-limit 240`
- `.venv\Scripts\python.exe -m src.validation --report-dir reports/v6_new`
- `.venv\Scripts\python.exe -m streamlit run app/main.py`

Saved real run: `reports/v6/ANALYSIS.md`, monthly CSVs and independent audit.
100% service and minimum monetary cost $10,941,467.50 are proven. Operating
expense $1,215,467.50; A $0; C $3,950,000; B $5,776,000. Full IDE $30,300;
overlap $0. No additional crews are selected. Qualification is December days
17–19. Event minimization stopped after 240 seconds: incumbent 4, bound 3,
25% gap. Quantity and cleanup stages were not advanced to. This is not a proven
minimum event count. Passing tests and feasibility audits do not prove optimality.

The former $1,215,467.50 operating-only objective is a historical financial
definition, not the new objective target. The default operating subtotal happens
to match it; the added $9,726,000 comprises C purchasing and B consumption.
Financial cards use compact display and exact-value details. Actual Chrome
component layout checks at five desktop/laptop widths are in
`reports/v6_ui_layout/`; these are component checks, not full-browser user tests.


## Latest resumed application validation

The fresh run in `reports/app_runs/v6_original_resumed/` proves **all seven stages optimal**, including four order events and 2,300 MSU-equivalent procurement quantities; all reported gaps are zero. The earlier `reports/v6/` timeout remains preserved as historical. Cost and operational decisions agree with that earlier plan. Independent reconstruction audit: 12,608 constraints, 6,811 variable levels, maximum violation 7.04e-8 (tolerance 1e-5). All 146 protected source/historical-file fingerprints match.

## Comparison with the historical V5 plan

Both runs serve 3,095 MSU and produce A=230, B=1,520, C=1,320 MSU. Both select no additional crews, four new procurement events, no external storage, $289,000 transport and $30,300 full IDE. All annual operating cost categories agree within numerical tolerance. The exported qualification shifts from December days 10?12 to days 17?19; this is one selected optimal schedule, not proof that its date is unique or solely caused by the new costs. The new objective adds $3,950,000 C orders and $5,776,000 B consumption. No temporary crew is economical in this original scenario; known-outcome synthetic tests verify the temporary-hiring and rehiring options.

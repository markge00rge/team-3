# Procurement event optimality audit

## Conclusion

Best feasible event count: **10**. Strongest preserved proven lower bound:
**8**. Remaining relative gap: **20.0%**.
Minimum event count proven: **False**.

Baseline source: `reports\v7`. Selected feasible plan: `reports\v7`.
Service remains 100%; minimum Total Delivery Cost remains **$9,865,467.50**.
Service and monetary optima were proven by the baseline solver. No business
cost tolerance, daily schedule fix, workforce fix or qualification fix was added.

## Original formulation and diagnostics

The most recent baseline stopped at the 300-second event-stage limit with
10 events, lower bound 7 and 30% gap. The preserved published V7 run already
has lower bound 8 and 20% gap. The stronger bound is retained rather than lost.
Original `integer_lots <= finite_bound * event`, `integer_lots >= event`, and
`quantity = lot_size * integer_lots` are exact. Impossible receipt windows are
fixed to zero; presolve removes their variables. Existing upper bounds use
eligible upgraded production capacity after receipt, and total useful purchases.
They are conservative, finite bounds, not arbitrary supplier capacities.

The full feasibility MILP has 7,579 columns and 2,417 integer columns including
2,048 binaries in HiGHS' raw input. Excluding already fixed levels, there are
2,186 integer decisions, including those 2,048 binaries. The mixed scheduling/material model has
many equivalent production and order-timing plans. Matrix coefficients span
approximately 2e-4 through 1e7. HiGHS warns about large material/monetary bounds;
this is a conditioning concern, not evidence of mathematical invalidity.
Exact empirical attribution of the runtime to degeneracy versus conditioning
is not established. The full-model infeasibility search remains necessary.

## Process and valid strengthening

`src.procurement_proof` rebuilds the same model and restores actual saved levels
only as a starting point. It preserves annual service equality locks and the
unscaled monetary upper bound at the proven optimum. No monetary epsilon is
added. MIP feasibility tolerance is 1e-8; independent export audit tolerance is
1e-5. Dollar scaling that would loosen effective cost feasibility was avoided.

Each cap check sets a constant objective and restricts only the sum of all six
material-specific event categories. A feasible solution is a candidate, not a
minimum certificate. Infeasibility at one fewer event plus an audited feasible
incumbent certifies the minimum. A timeout establishes neither feasibility nor
infeasibility. Messages about an infeasible MIP-start repair in the log are not
the final model termination condition.

The strengthened check adds B prefix cover cuts. With full B service, cumulative
B production is at least cumulative B demand minus opening B FP. Subtract
opening/fixed material from the corresponding BOM requirement; divide by lot
size and round upward. The resulting lower bound on cumulative arriving lots
is valid because the lot sum is integral. These cuts do not fix any order date,
production schedule, qualification, material quantity or workforce decision.
No tighter general upper bound was assumed without proof.

Installed solver: HiGHS 1.15.1 / Pyomo 6.10.1. Both checks use presolve on,
one thread, MIP starts, zero relative/absolute MIP gap requests and a 600-second
total budget per check. One thread makes the process reproducible; no claim
that it is universally fastest is made. Detailed node/LP/incumbent diagnostics
are retained in each `cap_9.log`. The two budgets total 1,200 solver seconds.

## Feasibility checks

| directory | cap | status | termination | seconds | feasible | integer_cover_cuts |
| --- | --- | --- | --- | --- | --- | --- |
| reports/procurement_proof_1 | 9.00 | aborted | maxTimeLimit | 602.50 | 0.00 | 0.00 |
| reports/procurement_proof_strengthened | 9.00 | aborted | maxTimeLimit | 605.20 | 0.00 | 18.00 |

Only the final solver termination is used as a certificate. If a cap times
out, lower caps are not attempted because the current feasibility question is
unresolved. Quantity minimization and cleanup are not advanced while the event
minimum remains unproven. The standard solver and Streamlit workflow retain
their original strict lexicographic behavior and truthful historical statuses.

## Selected material orders

| product | material | order_month | arrival_month | quantity | integer_lots | purchase_expense_usd |
| --- | --- | --- | --- | --- | --- | --- |
| B | RM | 2026-10 | 2027-01 | 200,000.00 | 4.00 | 1,000,000.00 |
| B | RM | 2027-01 | 2027-04 | 200,000.00 | 4.00 | 1,000,000.00 |
| B | RM | 2027-03 | 2027-06 | 350,000.00 | 7.00 | 1,750,000.00 |
| B | PM | 2026-10 | 2027-01 | 1,250,000.00 | 10.00 | 500,000.00 |
| B | PM | 2027-03 | 2027-06 | 1,125,000.00 | 9.00 | 450,000.00 |
| C | RM | 2026-10 | 2027-01 | 200,000.00 | 4.00 | 1,000,000.00 |
| C | RM | 2027-02 | 2027-05 | 200,000.00 | 4.00 | 1,000,000.00 |
| C | RM | 2027-03 | 2027-06 | 150,000.00 | 3.00 | 750,000.00 |
| C | PM | 2026-11 | 2027-02 | 1,375,000.00 | 11.00 | 550,000.00 |
| C | PM | 2027-02 | 2027-05 | 1,625,000.00 | 13.00 | 650,000.00 |

The three original precommitted shipments are separate constants, not new
events. No additional A orders occur in this selected plan.

## Independent validation and financial reconciliation

| component | usd |
| --- | --- |
| operating_expenses | 1,215,467.50 |
| a_materials | 0.00 |
| c_materials | 3,950,000.00 |
| b_materials | 4,700,000.00 |
| total_delivery_cost | 9,865,467.50 |

The selected plan passed independent reconstruction of 13,376
constraints and 7,579 variable levels; maximum violation
1.3969839e-09. Financial calculations retain full precision. Monthly
material balances, warehouse occupancy and costs remain in the selected source
folder. New proof outputs do not overwrite source files, SQLite saved runs or
historical reports. The interface event count remains the actual 10-event plan;
no unproven secondary optimum is relabeled as proven.

Relevant tests: 31 passed for procurement/proof/material/editor/history checks,
65 passed for model/reconciliation/saved-run/app-page compatibility, and the final
4 proof tests passed including timeout semantics. See `procurement_proof_tests.log`
and `procurement_compat_tests.log`.

## Reproduction and remaining uncertainty

```powershell
.venv\Scripts\python.exe -m src.procurement_proof --source reports/v7 --output-dir reports/new_proof --seconds 600 --strengthen
```

Use a fresh directory. A longer budget is configurable with `--seconds`; the
baseline cost and service locks remain unchanged. If the interval above has
not closed, more search or additional proven-valid cuts are required. No claim
that 10 events is the global minimum is justified without that certificate.

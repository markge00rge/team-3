# Active V7: explicit A/B/C material procurement

See [V7_SCOPE.md](V7_SCOPE.md) for the current formulation. Product B now has
editable adopted opening stocks (200,000 kg RM / 750,000 EA PM), explicit
procurement, conservation and warehouse space. All new ABC material orders
are charged at placement; the former B production expense is removed. Older
V6 sections below are historical. Saved runs retain their original versions.

---

# Current model: V6 flexible workforce and complete material costs

See [V6_SCOPE.md](V6_SCOPE.md) for the active extension and financial definitions.
The V5/V4 and V2.1 text below is historical. New A/C orders and B production-linked
materials now enter the monetary objective. Optional dismissal and full retraining
after rehire are supported. Reports: `reports/v6/`. Proven service: 100%; proven
minimum Total Delivery Cost: $10,941,467.50. The latest fresh application run proves all seven stages optimal
(four events, zero gaps): `reports/app_runs/v6_original_resumed/`. The earlier
V6 run with an unproven event minimum is preserved separately.

---

# Current model: V5 integrated Scenario A

The Streamlit application now wraps this unchanged mathematical scope. See
[APP_GUIDE.md](APP_GUIDE.md) for supported input controls and launch instructions,
and [APP_VALIDATION.md](APP_VALIDATION.md) for real-solver acceptance results.

V5 preserves V4 manufacturing/material/staffing/IDE rules and adds exact monthly
regional priorities independently for A/C and B. Both cumulative C:D definitions
are diagnostic metrics, not constraints. See [V5_SCOPE.md](V5_SCOPE.md), the
central [assumptions register](ASSUMPTIONS.md), and
[backend readiness matrix](FINAL_OPTIMIZER_READINESS.md). Current results are
in `reports/v5/`; V4 and V2.1 below are historical, preserved baselines.

---

# Historical V4 integrated Scenario A

The current default model optimizes qualification, L2 sequencing, optional
crews/profile upgrades and chronological A-material scrap on exactly 28 days
per month. See [V4_SCOPE.md](V4_SCOPE.md) for the active formulation, assumptions,
solver safeguards, reporting and remaining limitations. Only strict Scenario A
is run; there is no current Scenario B or monetary tolerance option.

Latest results and their actual optimality status are in `reports/v4/`.
The current run proves 100% service and minimum monetary cost $1,215,467.50.
Procurement-event minimization timed out at 180 seconds with incumbent 4,
bound 2 and a 50% gap. Quantity minimization and final cleanup were not
advanced to because the event optimum is unproven. See
[the verified analysis](reports/v4/ANALYSIS.md). The exported plan passed an
independent audit of 12,286 active constraints and 6,663 variable levels.
Historical V2.1 Scenario A files are preserved unchanged. The text below is
**historical V2.1 documentation**, including its obsolete fixed January date,
no-hiring policy, lack of IDE and earlier 2% sensitivity. It does not describe
V4's current restrictions or authorize a new sensitivity run.

---

# Historical V2.1: A/C ordering lots, international consolidation and tracked warehouse

This model tests monthly production/inventory/service/transport with detailed
A/C material feasibility, integer procurement lots, material-specific order
events and month-end tracked warehouse/overflow. It does **not** solve the complete
P&G case or establish the true total supply chain cost. All source values
come from `load_case()`; no duplicate case-input dataset is introduced.
Unresolved source issues remain in `DATA_REVIEW.md`.

## Fixed scenario (explicit modeling choices, not missing case facts)

- Horizon: October 2026–September 2027, from the loader.
- Base crews only: L1 30 operators, 24/5; L2 40 operators, 24/6.
  No hiring, training, overtime or profile upgrades.
- Qualification occupies the first three **scheduled production days** of
  January 2027 simultaneously on both lines. These days reduce each line's
  monthly capacity; remaining January capacity can make C. No intramonth
  production or dispatch timing is represented.
- A may be made and delivered through December; C may be made and delivered
  from January. Either belongs to pooled A/C demand, subject to these fixed
  sales windows. B is available throughout. This deliberately selects one
  transition policy while the case's exact substitution policy is unresolved.
  Residual A FP cannot be sold after transition, is carried/charged holding
  costs if present, and has no modeled disposal option in this milestone.
- Reserve one L2 routine-changeover day **every month**, including January,
  in addition to qualification downtime. L2 may split remaining capacity
  between B and the active A/C product. The reserve is conservative in months
  when only one product is made; it is fixed rather than optimized. A-to-C
  qualification itself is not counted as the routine changeover. Detailed
  sequencing and boundary changeovers are omitted.
- Normal monthly limits are L1=120, L2=184 MSU (304 combined), versus the
  source no-changeover base of 312. January limits are L1=102, L2=160
  (262 combined). Thus the full 312 is not available in this test scenario.
- Production, inventory, shipments and shortages are continuous in MSU.
  Dedicated and spot truck counts are nonnegative integers by hub/month.
- Shipments arrive at their hub in the same month; no transit delay, hub
  stock, early customer delivery or backlog. Unserved demand is a lost sale
  in that month. Initial FP is available at the plant before October dispatch.
- Trucks may mix products within one hub, but not different hubs. A partial
  truck is charged at full cost through integer truck counts. Spot supply has
  no stated upper bound; none is invented. All monthly dedicated trucks share
  the 65-truck fleet. Cost minimization uses cheaper dedicated trucks first.
- No terminal stock target or salvage value is imposed, since none is given.
  A nonmonetary procurement tie-break prevents unnecessary purchases instead.

`FixedScenario` keeps transition timing separate from source data. Mutable
capacity/fleet parameters allow controlled diagnostic tests; they are not
additional case-study values. Tests using artificial inventory explicitly
label those changes as synthetic stress cases.

## Formulation

For line l, product p, hub h, family f and month t:

- Total line production <= fixed available days × source MSU/day.
- Ineligible line/product and out-of-window production is fixed to zero.
- Ending FP[p,t] = preceding FP + sum of production - sum of shipments.
  The first month uses the source opening stocks A=10, B=15, C=0 MSU.
- Sum of shipments of family members + unserved[h,f,t] = demand[h,f,t].
  There is no invented monthly split of A/C demand.
- Sum of all product shipments to one hub <= 5 × (dedicated + spot trucks).
- Sum of dedicated trucks across hubs <= 65 in each month.

All stock/flow variables are nonnegative, preventing shipment of unavailable
FP and preventing over-service. Inventory may prebuild at the plant for summer.

## Material balances and procurement

Only Products A and C have separate RM (kg) and PM (EA) inventory and order
variables. No material can substitute across products or types. Consumption is
actual summed line production times the loader's BOM (500 kg and 2,500 EA/MSU).
For each A/C product, material and month:

`ending = opening + fixed arrivals + additional arrivals - BOM consumption`

Opening stock is the previous month's ending stock, or original September 30
stock in October: A RM=115,000 kg, A PM=400,000 EA, C RM=0, C PM=0.
All ending stocks are nonnegative. There is no material-shortage slack, borrowing,
substitution or automatic relaxation. A production requirement inconsistent
with this equation is infeasible; ordinary shortages instead reduce customer
fulfillment through the existing unserved-demand variables.

The three fixed arrivals are unchanged: A PM=250,000 EA October 1, C PM=375,000
EA October 1 and C RM=150,000 kg November 1. They are available for production
in those months. New orders arrive three month indices after placement:
October -> January, November -> February, etc. Assume placement/receipt at the
start of each month for this monthly convention; no invented pre-horizon orders
are allowed. The original September-to-October contradiction remains recorded
in `DATA_REVIEW.md`; it does not override lead time for new orders.

All additional **A and C** quantities equal nonnegative integer increments of
50,000 kg RM or 125,000 EA PM, per the V2.1 user instruction. This explicitly
extends the source's phase-out increments to C; it supersedes V2's continuous
C orders. It is a requested modeling policy, not a newly discovered case fact.
The three existing receipts are constants and are not rounded or re-lotted.
No supplier capacity or numerical stock target is invented.
Orders whose arrival is beyond September 2027 are fixed to
zero, as there is no modeled demand beyond the horizon. A orders arriving in or
after January are also fixed to zero because A production ends in December.
In this default scenario **no useful A procurement can arrive before phase-out**;
the A increment logic is tested using a clearly synthetic later-transition case.

Residual A material remains visible in the balances after phase-out; it is not
consumed by C, discarded for free or silently removed. Actual scrap/IDE is deferred.
The default run leaves 75,000 EA A PM and zero A RM at phase-out/end-horizon.
New and opening PM aging/expiry is not modeled.

For every product/material/month, `quantity = lot_size * integer_lots` and
`event <= integer_lots <= U * event`, with binary `event` and nonnegative
integer lots. Thus an event is active if and only if at least one lot is ordered.
Any number of lots up to U can share that one event. There is no assumed fixed
international freight charge. Each RM and PM event is counted separately;
simultaneous RM/PM orders do **not** imply a shared physical shipment.

U is finite and data-derived: sum maximum line production eligible for that
product from the receipt month through its last active month, multiply by its
BOM factor and divide by the lot size, rounding upward. An order exceeding this
cannot be usefully consumed and is excluded as gratuitous over-ordering. This
is a bound on useful replenishment, not an invented supplier limit. It ignores
opening stocks/other receipts when bounding, so it is conservative. Impossible
receipt windows have U=0. Bounds are calculated at build time: rebuild if
increasing capacities or changing product availability in a diagnostic scenario.

### Product B interpretation

The original case permits B RM/PM to be replenished smoothly according to its
production plan. B therefore has **no material stock or procurement decision
variables and no RM/PM availability constraints**. Its FP production, capacity,
inventory, service, transport and costs continue normally. Its RM/PM consumption
is reported as information only: B production times 600 kg RM/MSU and 2,000 EA
PM/MSU. This does not mean zero physical material stock: actual B stocks/pipeline
are unspecified and outside detailed material optimization. They are not an
input blocker. Their physical warehouse footprint is unspecified and excluded
from the tracked warehouse model, **not physically zero**.

## Month-end tracked warehouse and overflow

Tracked pallets equal `4 * ending FP(A+B+C) + ending RM(A+C)/1000 +
ending PM(A+C)/5000`. Source capacity is 1,200 pallets, with constraints
`tracked_pallets <= 1200 + 100 * external_blocks`. External blocks are
nonnegative integers and cost `100 * $45 = $4,500` per block/month even when
partly occupied. There is no material carrying cost. Monthly reporting splits
FP/RM/PM requirements and shows minimum overflow, on-site pallets and blocks.
On-site pallets reported as `min(tracked, 1200)` describe a feasible allocation;
individual products are not assigned to warehouse locations. Final cost cleanup
selects the minimum paid blocks needed for each selected plan.

This is a **month-end** measure and does not verify within-month peak inventory,
receiving/unloading space or daily movements. B material space is excluded as
specified above. These limitations prevent a claim of full physical warehouse
feasibility for the whole case.

## Lexicographic service and costs

The lexicographic stages run in order:

1. Annual unserved MSU at Cairo (P1).
2. Annual unserved MSU at Alexandria/Delta (P2), fixing P1's optimum.
3. Annual unserved MSU at Upper Egypt/Red Sea (P3), fixing P1 and P2.
4. Modeled USD cost, fixing all three service optima.
5. Material-specific additional order events, preserving service and a cost ceiling.
6. Additional procurement quantity, fixing the best event count and service.
7. Monetary cost cleanup, fixing event and quantity optima as well as service.

Stage 4 establishes minimum monetary cost C*. The cost ceiling is
`C* * (1 + cost_tolerance)`, where tolerance is a finite nonnegative fraction
defaulting to zero. Scenario A uses 0; Scenario B uses 0.02 as a sensitivity,
not a case requirement. Both recompute the same C* on the same data/model.
Service optima remain equality-locked regardless of tolerance. Stages 5–7
cannot exceed the ceiling. Stage 7 only removes gratuitous spending among
solutions tied on the requested priorities; it cannot increase event count or
procurement quantity. No arbitrary weighted objectives are used.

The quantity tie-break sums order quantity divided by the corresponding
BOM factor, giving MSU-equivalent RM and PM quantities rather than adding kg to
EA. It is not a material purchasing cost, does not enter the reported USD total
and cannot trade away service or breach the allowed cost ceiling. Positive weights prevent gratuitous
over-ordering; necessary A increment residuals are allowed. Equivalent order
timings and production schedules can remain because no raw-material holding
cost is introduced. The report shows one optimal plan, not a uniquely required
ordering schedule.

The priorities apply to annual hub totals, not a separate temporal or
product-family ordering within each hub. Each service optimum is locked by
equality, subject to numerical solver feasibility tolerances. Each stage must
return solver status `ok` and termination `optimal` before values are loaded;
both relative and absolute MILP gap targets are zero. Time limits, infeasibility,
unboundedness, solver errors and unavailable solvers prevent results extraction.
A failed re-solve also invalidates previously extracted model state for reporting.

Modeled cost consists of:

- Fixed base labor: 70 × $1,000 × 12 = $840,000.
- FP holding: 1.5%/month × source product value × ending product inventory.
- Transport: hub-specific dedicated cost; spot cost = 1.6 × that hub's rate.
- Service failure: hub-specific penalty × unserved MSU. This is included in
  cost, but is constant once annual service by hub has been fixed.
- External storage: $4,500 per rented 100-pallet block/month.

Material purchasing is **not** an independent objective term. FP source values
are used only as the basis for FP holding costs. IDE remains `None`/`omitted`.
External storage is now modeled; a reported zero means no blocks are rented.

## Temporarily omitted constraints and decisions

- PM expiry/age tracking; physical B material stocks and procurement (excluded
  deliberately under the smooth-replenishment assumption, not assumed zero).
- Residual A RM/PM scrap and IDE.
- Hiring, paid training, labor ceiling, overtime, profile selection and crewing changes.
- Optimized qualification date, detailed sequence/changeover decisions and launch choice.
- Cumulative C:D constraint, whose formal definition remains unresolved.
- Intramonth scheduling, backlog, hub stock and terminal inventory policy.

No missing numerical input is filled with an assumed cost or capacity.

## V1 baseline (historical)

HiGHS solved all four stages to optimality. It serves all 3,095 MSU (P1=1,525,
P2=1,000, P3=570), using 3,070 MSU of production and 25 MSU opening FP.
FP prebuild reaches 238 MSU at end-April. Dedicated fleet capacity is binding
in May–July; spot counts are 6, 16 and 13 respectively (35 total).

| Modeled category | USD |
| --- | ---: |
| Fixed labor | 840,000.00 |
| FP holding | 58,987.50 |
| Transportation | 289,000.00 |
| Service failure | 0.00 |
| Total modeled | 1,187,987.50 |
| IDE | Omitted |
| External storage | Omitted |

Equivalent optimal line/product allocations may exist. These costs and full
service were valid only for the V1 relaxed test scenario. Material limitations
and combined warehouse space can change both service and cost substantially.

## V2 baseline (historical, before V2.1 lots and warehouse)

All five HiGHS stages return status `ok`, termination `optimal`. Annual service
is 3,070/3,095 = **99.1922%**. Cairo receives 1,525/1,525 MSU; Alex/Delta
1,000/1,000; Upper Egypt/Red Sea 545/570. B demand is completely served.
Production is A=230, C=1,295, B=1,520 MSU, plus 25 MSU initial FP.

The 25 MSU shortage is unavoidable under the fixed January policy: pre-January
A/C demand is 265 MSU, whereas A RM supports only 230 MSU production, plus
10 MSU opening A FP. New October orders arrive only in January. C cannot be
made/sold before January. Strict priority puts all 25 unserved MSU at P3.
The model remains feasible; it does not relax material constraints to meet demand.

| Cost category | V1 USD | V2 USD |
| --- | ---: | ---: |
| Fixed labor | 840,000.00 | 840,000.00 |
| FP holding | 58,987.50 | 58,987.50 |
| Transportation | 289,000.00 | 285,000.00 |
| Service failure | 0.00 | 30,000.00 |
| Total modeled | 1,187,987.50 | 1,213,987.50 |
| IDE | Omitted | Omitted |
| External storage | Omitted | Omitted |

Modeled cost rises $26,000. The 25 lost P3 MSU save five $800 dedicated trucks
($4,000), but incur $30,000 penalties. Summer spot trucks remain 35. Additional
C procurement totals 497,500 kg RM and 2,862,500 EA PM. A procurement is zero.
The fifth objective is 2,140 MSU-equivalent material quantities, not dollars.
Ending C material stocks are zero under the minimal-quantity tie-break.
B theoretical consumption totals 912,000 kg RM and 3,040,000 EA PM.

The historical `reports/v2/` files are preserved. Use
`python -m src.solve --compare --output-dir reports/v2_1` with the project's
Python to generate both **current** scenarios and their comparison. Each folder
contains `summary.txt`, solver-stage JSON and CSVs for service, production,
materials, orders/events, fixed receipts, B usage and warehouse occupation.
Material balances must reconcile and be nonnegative within numerical tolerance;
no separate positive material shortage is permitted. Customer shortages are
shown separately in `service.csv`.

## Verified V2.1 results

Both scenarios solve all seven stages with status `ok`, termination `optimal`.
Service remains 3,070/3,095 MSU (99.1922%), with all 25 MSU shortages at P3.
A=230, C=1,295, B=1,520 MSU production remains sufficient for these service optima.
The year-end A material residual is 0 kg RM / 75,000 EA PM. In both scenarios,
C orders now total 500,000 kg RM (10 lots) and 2,875,000 EA PM (23 lots), leaving
2,500 kg RM / 12,500 EA PM at year-end. These replace V2's arbitrary continuous
orders of 497,500 kg and 2,862,500 EA. There are no new A events.

| Metric | V2 historical | A: strict cost | B: 2% tolerance |
| --- | ---: | ---: | ---: |
| Additional material-specific events | 15 (not minimized) | 4 | 3 |
| Fixed arrivals (separate) | 3 | 3 | 3 |
| Fixed labor USD | 840,000 | 840,000 | 840,000 |
| FP holding USD | 58,987.50 | 58,987.50 | 59,670.00 |
| Transportation USD | 285,000 | 285,000 | 285,000 |
| Service penalty USD | 30,000 | 30,000 | 30,000 |
| External storage USD | Omitted | 0 | 18,000 |
| Total modeled USD | 1,213,987.50 | 1,213,987.50 | 1,232,670.00 |
| Allowed maximum USD | — | 1,213,987.50 | 1,238,267.25 |

One optimal Scenario A procurement schedule is C RM orders of 200,000 kg in
October (January receipt), 300,000 kg in February (May receipt); C PM orders of
2,000,000 EA in November (February receipt), 875,000 EA in April (July receipt).
Tracked peak month-end occupancy is 1,197 pallets with no external blocks.

One optimal Scenario B schedule orders C RM 500,000 kg in December (March
receipt); C PM 1,375,000 EA in November (February receipt) and 1,500,000 EA in
February (May receipt). March/April/May need 2/1/1 external blocks respectively:
tracked occupancy is 1,372/1,279/1,237 pallets, costing $9,000/$4,500/$4,500.
The extra $18,000 warehouse expense is induced by the more consolidated plan;
Scenario A meets the same service at strict minimum cost without it. FP holding
also rises $682.50. The total increment is $18,682.50 (about 1.539%), within 2%.
Alternative optimal monthly allocations/timings may exist; none represents a
shared RM/PM international shipment or an inferred freight price.

## Next implementation steps and remaining assumptions

Add A phase-out disposal and IDE, with an agreed treatment of residual A FP.
Add PM age/expiry once opening ages are available. Resolve the warehouse
footprint of unspecified B physical material stocks rather than treating it
as zero, and verify intramonth peaks if detailed scheduling is introduced. Extend qualification and
crew decisions after confirming overtime rates, headcount limits and scheduling
conventions. Agree the cumulative C:D definition before adding it. Detailed
shipping lead time, hub stocks, daily sequencing and terminal targets remain
outside this scenario. Re-run reconciliation and lexicographic tests at each step.

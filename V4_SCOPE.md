# V4 integrated manufacturing, staffing and IDE — Scenario A only

V4 is the default `build_model(load_case())`. The loader remains independent;
neither original document is modified. Historical V2.1 Scenario A artifacts
remain in `reports/v2_1/scenario_a/`. Explicit `FixedScenario` arguments are
retained only to regression-test the historical monthly formulation. The
current CLI has no Scenario B or cost-tolerance option. No 2% scenario is run.

## Calendar and manufacturing chronology

Each of the 12 months has **exactly 28 planning days**, numbered 1–28 and
repeating Monday–Sunday four times. Positions 1–5 are the base L1 workweek;
1–6 are the base L2 workweek. Upgrades add position 6 for L1 and position 7
for L2. Gregorian dates and month lengths are never used for daily capacity.
At 6/8 MSU per day this gives 120/192 MSU base and 144/224 MSU upgraded
monthly capacities before actual downtime. Daily quantities can be fractional
MSU; configuring a product does not force production on an otherwise idle day.

Qualification occurs exactly once, for three consecutive planning days common
to both **base** operating schedules. Only week positions 1, 2 or 3 may start
the three-day period: 144 candidates across 12 months. Both lines lose all
three scheduled days even if upgraded. There is no overlap with routine L2
changeover downtime. Qualification is not given an unspecified fee or a hard
January deadline; timing is an optimization decision anywhere in the horizon.

Binary `transitioned[d]` increases by `qualification_start[d]` and never falls.
A production is prohibited from the start day onward. `qualified[d]` is the
transition state three days earlier, so C may only be produced on a later
scheduled day after all three shutdown days. All products, including B, stop
during the full-plant shutdown. Daily quantities aggregate exactly to monthly
line/product production, which feeds the original FP, service and transport
balances. Additional monthly capacity inequalities strengthen the daily model.

## L2 sequence

L2 has one A/B/C configuration on every planning day, carried over weekends,
idle days and month boundaries. Opening configuration is unspecified by the
case: the solver may select A or B before day 1, without assuming an opening
changeover cost. No subsequent free change is allowed.

A configuration change requires one full operating day of no production and
at most one such routine event per month. The transition inequalities allow
only **A -> C on the qualification-start day** as an exemption. B must remain
B throughout qualification and must pay a normal changeover on another
scheduled day to become C. A line already configured B is not given a free
B-to-C conversion. Same configuration implies no routine event. The selected
target configuration applies on the downtime day, but output is zero that day.
No added changeover fee is invented: its cost is lost capacity only.

## Hiring and profiles

Each line may hire one ten-person crew, or none. Hiring month is the full
training month with zero additional productive days. The upgrade is available
from the following month onward and cannot reverse. Activation immediately
after training adds optional available days; actual production can still be
idle. Last-month hiring is prohibited because no associated upgrade could
activate within the horizon. There is no pre-horizon hiring/training or firing.

Base salary is 70 x $1,000 x 12 = $840,000. Every hired crew adds $10,000 for
the training month and **every** remaining employment month, plus $5,000 hiring
once. Labor reporting separates these components without adding them twice
to total cost. Training has no invented fee, overtime rate or dismissal cost.
The unspecified strict plant headcount ceiling remains unresolved; only the
two explicitly supported ten-person upgrades are permitted (at most 90 total
operators). This is not a claim that 90 is the missing case headcount ceiling.

## Materials, A scrap and pooled demand

A/C RM and PM have daily physical inventory balances. Only A/C have material
stock, procurement, lot and event variables. B retains smooth material supply;
its calculated 600 kg RM/MSU and 2,000 EA PM/MSU are information only. B's
physical material stocks and their warehouse footprint remain unspecified and
excluded, not physically zero.

Original opening stocks and all three fixed receipts are unchanged. All fixed
and new receipts occur at the **start of planning day 1** of the receipt month,
before production or scrapping that day. Additional orders still take three
planning months (October -> January). A/C orders use integer 50,000 kg RM or
125,000 EA PM lots. Separate product/material/month binaries count events;
there is no invented shared international shipment or freight cost.

At qualification start, all residual A RM/PM is scrapped **after all earlier
days' A production and any start-of-day receipts**. Scrap can be positive only
on the chosen start day, and usable A stocks must be zero thereafter. Daily
conservation is `ending = opening + receipts - consumption - scrap`. Finite
source-derived stock bounds linearize the state restrictions; there is no
binary-times-stock product. A orders cannot arrive after the transition:
receipt is bounded to zero if the prior day is already transitioned. If
qualification starts on receipt day 1, that receipt is included before scrap,
so it cannot disappear. Original A PM arrives in October, never silently moves.

IDE is A RM x $5/kg + A RM/1,000 x $200/ton + A PM x $0.40/EA +
A PM x 0.02 kg/EA /1,000 x $200/ton. Thus RM scrap costs $5.20/kg and PM scrap
$0.404/EA. Material value is charged only here, with **no independent material
purchasing term**. C/B materials and A finished goods are not scrapped.

A and C shipments share the single source A/C forecast. Existing A finished
goods may sell through after qualification; only **manufacturing** of A stops.
There is no imposed monthly A/C split, duplicated demand or extra launch demand.
FP availability and transport remain monthly; an end-of-month dispatch of all
shipments provides a chronological interpretation consistent with daily
production. The model does not promise customer deliveries earlier in a month.

Finite useful-order bounds use full upgraded eligible capacity from receipt
through horizon end, since transition is now endogenous. Total useful lots are
also bounded by full upgraded horizon production rounded upward. Opening and
fixed stocks plus that purchase limit yield conservative scrap/stock bounds.
These are useful-volume bounds, not invented supplier capacities. Rebuild
after changing source capacities or inventories in diagnostic tests.

## Warehouse, objective and solver safeguards

Retain month-end 1,200 on-site pallets, four pallets/MSU FP, 1,000 kg RM/pallet,
5,000 EA PM/pallet and integer 100-pallet overflow blocks at $4,500/block/month.
All A/B/C FP and A/C usable materials are tracked. A scrap leaves usable storage
immediately; there is no invented waste-staging footprint or disposal delay.

The seven strict lexicographic stages are P1 unserved, P2 unserved, P3 unserved,
monetary cost, additional international material-specific events, MSU-equivalent
procurement quantities, then monetary cleanup. Each proven optimum is locked;
**no monetary tolerance** is allowed. Monetary categories are total base/new
salary and hiring, FP holding, transport, service penalties, overflow and IDE.
No independent purchase, carrying, qualification, changeover or overtime fee
is added. Quantity normalization is by each material's source BOM.

The HiGHS APPsi interface warm-starts later stages from earlier feasible plans.
An optional schedule-fixed **primal heuristic** can improve procurement starting
values, but it never fixes or relaxes the original scheduling model. Original
decisions remain free in the global event solve. A heuristic result is not a
global proof. Default CLI limit is 120 seconds **per stage**, configurable with
`--time-limit`; zero relative and absolute gap targets are requested.

Every stage must be proven optimal before advancing. If a stage times out,
later lexicographic stages do not run because locking an unproven optimum
would change the requested problem. Report the last-stage incumbent/bound/gap
and all earlier proven optima. If no new incumbent exists, the preceding proven
stage's feasible plan is explicitly identified as fallback. Ordinary extraction
rejects unsuccessful solves; explicit incumbent extraction/reporting is labelled
**not fully lexicographic optimal** and the command returns nonzero. Numerical
auditing checks active constraint residuals, bounds and integrality before
normal CLI export. Solver status, proof gap and physical feasibility are
different claims and are reported separately.

## Reporting and remaining limits

Run `python -m src.solve --output-dir reports/v4 --time-limit 180` with the
project environment. `summary.txt`, `solve_status.json`, `transition_ide.json`,
`historical_comparison.json` and CSVs cover daily schedules/materials, actual
changeovers, qualification days, first C/last A production, A sell-through,
staffing/training, monthly capacities, inventories, orders, event counts,
warehouse and transport. `solution_audit.json` records numerical verification.

Monthly checks do not prove intramonth warehouse peaks. `storage_peaks.csv`
adds a conservative **diagnostic** using daily material receipts/consumption
and assuming all FP shipments leave at month-end; it flags excess over booked
space but does not impose new storage charges or assert an actual daily
dispatch schedule. Same-month A shipments are reported separately from
unambiguously later-month sell-through, since monthly shipment variables do
not date individual deliveries within the qualification month.

Still omitted/unresolved: cumulative C:D definition, PM opening ages and expiry,
B material footprint, unspecified headcount/overtime rules, daily dispatch/hub
inventories/transit and waste-staging space. The September-order/October-receipt
lead-time contradiction remains recorded; fixed receipts are preserved and new
orders use three months. V4 does not claim to solve every original case rule.

See `reports/v4/solve_status.json` for the **actual** latest proof status rather
than assuming the final incumbent has optimal event count or procurement.

## Latest validation result

The complete suite passed **71 tests**. This includes two small cases with free
optimization decisions and independently known monetary optima: $140,300 for
consuming one MSU of A materials before qualification, and $187,800 for an
L2-only hire required to serve 380 MSU B over two synthetic months.
Targeted rechecks of export roundtrip,
strict Scenario A rejection and incumbent labeling passed after the final
reporting updates. Reconstructing the exported production/material/scheduling
levels in a fresh V4 model passed all 12,286 active constraints and 6,663
variable bounds/integrality checks at tolerance 1e-5 (maximum residual about
2.51e-8). This certifies numerical feasibility, not unproven secondary optima.

The 180-second-per-stage run proved zero unserved demand at every hub and a
minimum monetary objective of $1,215,467.50 with zero gap. The event stage
returned `aborted / maxTimeLimit`, incumbent 4, lower bound 2, gap 50%.
Stages 6 and 7 were not advanced because stage 5 is unproven. The complete
report remains labelled incumbent-only with respect to full lexicographic
optimization. The selected cost-optimal plan qualifies in December on planning
days 16–18, hires no crew, and incurs $30,300 IDE for 75,000 EA A PM.
See `reports/v4/ANALYSIS.md` for the full interpretation and baseline comparison.

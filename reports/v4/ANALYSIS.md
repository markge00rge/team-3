# V4 Scenario A: verified result and proof limits

**Service and minimum monetary cost are proven optimal. Full lexicographic optimality is NOT proven.**

Validation: the complete test suite passed **71 tests**. The exported plan
passed an independent numerical audit of 12,286 active constraints and 6,663
variable levels (maximum residual about 2.51e-8 at a 1e-5 tolerance).

P1, P2 and P3 each have zero unserved MSU with zero proof gap. Stage 4 has equal mathematical lower and upper bounds of $1,215,467.50 (zero gap). Stage 5 stopped at its 180-second limit: incumbent 4 international material-specific events, lower bound 2, gap 50%. Stages 6 and 7 were not run because the event optimum was not established. The exit code is nonzero. No service or cost constraint was relaxed.

The saved plan is a feasible monetary-cost optimum, with a heuristic-improved procurement schedule. The four-event count and final quantity optimality must not be claimed proven. Earlier 90/180-second diagnostic attempts are separate from this latest status.

## Comparison with historical V2.1 Scenario A

| Metric | V2.1 A | V4 reported plan |
| --- | ---: | ---: |
| Served MSU | 3,070 | 3,095 |
| Annual service | 99.1922% | 100% |
| labor | $840,000.00 | $840,000.00 |
| fp_holding | $58,987.50 | $56,167.50 |
| transportation | $285,000.00 | $289,000.00 |
| service_failure | $30,000.00 | $0.00 |
| external_storage | $0.00 | $0.00 |
| ide | Omitted | $30,300.00 |
| total_modeled | $1,213,987.50 | $1,215,467.50 |

The $1,480 cost increase is $30,300 new IDE, minus $30,000 service penalties, plus $4,000 transport for the recovered 25 MSU, minus $2,820 FP holding. Both plans use no external blocks and no new crew. The baseline omitted IDE, so this is a comparison of modeled categories, not a claim about equal full-case scope.

## Qualification, transition, sell-through and staffing

The reported plan qualifies in 2026-12, planning days 16?18 (horizon days 72?74). C first runs on planning day 19; A last runs on planning day 11 in that month. These are standardized planning days, not Gregorian dates.

The plan consumes all 115,000 kg A cartridges and 575,000 EA A packaging before qualification. It scraps 0 kg RM and 75,000 EA PM at the start of qualification. Usable A stocks remain zero afterward; C/B stocks are not scrapped.

IDE: RM material $0 + RM disposal $0 + PM material $30,000 + PM disposal $300 = **$30,300**. The 75,000 EA PM weighs 1,500 kg. No material purchase expenditure is separately charged.

A/C share one demand family. A finished stock is retained, not scrapped: 80 MSU A is shipped in the transition month and zero in later months in this plan. Monthly shipments are not individually dated. Under the documented month-end dispatch convention, those 80 MSU sell through after qualification. Synthetic tests also verify later-month A finished-goods sales.

Neither line hires or upgrades in this monetary-optimal plan. Base salaries are $840,000; new salaries/training salary and hiring fees are $0. Full service is feasible on base profiles with actual L2 sequencing and prebuild. Crew upgrades would add a $5,000 hiring fee plus $10,000 per employment month, including training; the optimum found no net monetary advantage from those costs.

Why this timing works: consuming A before conversion uses all cartridges and limits IDE to unmatched packaging. Qualifying during December permits C to cover the pre-January gap that forced 25 MSU lost sales in V2.1. Actual changeovers recover capacity in months that do not need a switch, while retaining three real base-profile shutdown days. These are observed trade-offs of the monetary-optimal plan; the date and detailed schedule are not proven unique.

## Actual L2 routine changes

| Month | Planning day | Target configuration |
| --- | ---: | --- |
| 2026-10 | 8 | B |
| 2026-11 | 27 | A |
| 2026-12 | 5 | B |
| 2027-01 | 27 | C |
| 2027-02 | 12 | B |
| 2027-03 | 18 | C |
| 2027-04 | 8 | B |
| 2027-07 | 20 | C |
| 2027-08 | 3 | B |
| 2027-09 | 17 | C |

The initial L2 configuration is A. Each listed routine switch consumes one entire scheduled day. There are no routine changes in May or June in this plan; configurations carry through boundaries. The three qualification days have no routine changeover.

## Additional orders and fixed receipts

| Product/material | Order month | Arrival month | Quantity | Lots |
| --- | --- | --- | ---: | ---: |
| C RM | 2026-11 | 2027-02 | 300,000 | 6 |
| C RM | 2027-03 | 2027-06 | 250,000 | 5 |
| C PM | 2026-10 | 2027-01 | 1,750,000 | 14 |
| C PM | 2027-03 | 2027-06 | 1,250,000 | 10 |

All orders use three-month lead times and mandatory A/C lot sizes. There are no A orders. The displayed C totals are 550,000 kg RM and 3,000,000 EA PM; ending C material is 40,000 kg RM and 75,000 EA PM. These quantities suffice for this plan and are lot-rounded, but the global final quantity objective is unproven.

The three original fixed receipts are unchanged and separate from the optimized new-event count: A PM 250,000 EA on October planning day 1; C PM 375,000 EA on October planning day 1; C RM 150,000 kg on November planning day 1.

## Complete monthly and daily detail

- `summary.txt`: monthly hub service, product production, staffing, capacities, changeovers, orders, material balances, warehouse and costs.
- `daily_schedule.csv`: both lines on all 336 planning days.
- `daily_material.csv`: chronological inventories, receipts, consumption and scrap.
- `line_capacity.csv`, `staffing.csv`, `material_orders.csv`, `material_balances.csv`, `inventory.csv`, `service.csv`, `transport.csv`, `warehouse.csv`: machine-readable reconciliation tables.
- `transition_ide.json`, `solve_status.json`, `historical_comparison.json`: exact transition, financial breakdown and proof metadata.
- `solution_audit.json`: numerical audit reconstructed from the exported plan; physical feasibility does not imply event-count optimality.

## Limitations

Only month-end tracked storage is constrained. `storage_peaks.csv` flags conservative intramonth peaks with all shipments deferred to month-end; it is not a verified daily dispatch plan and does not charge unmodeled peak storage. B physical material footprint is unspecified/excluded, not zero. PM ages/expiry, cumulative C:D, unspecified plant headcount/overtime restrictions, daily dispatch/transit/hub inventory and waste-staging space remain omitted. The initial L2 setup choice and start-of-month receipt convention are explicit assumptions. See ../../V4_SCOPE.md and ../../DATA_REVIEW.md.

No Scenario B was run, no cost tolerance was used, no original source was changed, and no GUI was built.

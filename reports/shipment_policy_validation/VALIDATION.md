# Shipment policy acceptance validation

- Corrected full regression run: **251 passed** in 516.64 seconds
  (`../../shipment_full_verified_tests.log`).
- Final policy/proof recheck: **16 passed** in 28.14 seconds
  (`../../shipment_final_focused_tests.log`). This includes two tests added
  after the full run: all six material categories in one allowed batch and
  the actual consolidated-result dashboard. All 253 current cases are covered
  across these runs.
- The first full run had three failures: an obsolete 12-card assertion and two
  HiGHS process-wide thread-setting conflicts in proof tests. The assertion now
  verifies 14 cards including the two new metrics; proof tests use the existing
  automatic scheduler. No business constraints or solver proof criteria were
  relaxed. The corrected full run is green.
- All original 172 protected source/historical file digests match. The three
  original saved SQLite payload digests also match. Historical V7 reports and
  previous procurement proof runs were read only, not overwritten.
- All three actual default Venus solves prove 100% service and minimum monetary
  cost $9,865,467.50. Shipment stages reached their 300-second limits: independent
  10/bound 5/gap 50%; per-product 6/bound 4/gap 33.3333%; all-products 4/bound
  1/gap 75%. These are fresh-run bounds; the stronger historical independent
  lower bound 8 remains preserved separately. No shipment minimum is claimed.
- Independent exported-schedule reconstructions passed for all three policies;
  maximum violations are below 1e-5. Group indicators and selected shipment locks
  are included in reconstruction. Independent material/financial reconciliations
  and exact shipment-schedule aggregation passed.
- Known-outcome full synthetic MILPs prove identical service and monetary cost
  across all policies, with shipment optima 2/1/1 and the same two order lines.
  Separate tests verify the four-line 4/2/1 example, all-six-material grouping,
  A/C separation, different dispatch months, no empty batches, zero orders and
  incompatible-arrival rejection.
- AppTest verifies original naming-page selection reaches the actual model,
  custom selection persists through review without a duplicate selector, reset
  and JSON compatibility, actual consolidated-result counts, and five financial
  cards with exact monetary values. Existing responsive financial-card CSS was
  preserved; earlier desktop/laptop financial layout audits remain applicable.
- Temporary SQLite tests verify policies, actual schedules, financial metadata
  and comparison warnings survive round trips. Historical dashboard tests remain
  read only. No model runs when viewing saved results.
- Syntax compilation and Git whitespace checks passed.

Read `RESULTS.md` / `comparison.csv` for actual outputs and
`../../SHIPMENT_CONSOLIDATION_POLICIES.md` for model assumptions, file mapping,
launch and test commands. Dispatch batches are not physical containers. No new
inbound freight cost, inbound pallet limit or general-plant model was introduced.

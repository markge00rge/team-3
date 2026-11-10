# Product B upgrade: interruption recovery audit

Branch: `product-b-upgrade`. Existing working changes were retained; no reset,
revert, source-document edits or historical-result replacement was performed.

## Completed before resuming

The existing V7 work implements explicit A/B/C material balances and daily
availability, B opening RM 200,000 kg / PM 750,000 EA, editable B stocks/BOM/prices,
integer lots, three-month replenishment, all six material-specific event categories,
ABC warehouse footprints and order-placement purchasing expenses. Flexible
workforce, A transition/IDE reconciliation, five financial cards, saved-run
versioning and historical comparison safeguards remain implemented.

The original Product B prompt was reviewed against `tests/test_v7.py`,
`tests/test_v7_app.py`, existing regression tests and the actual reports. See
`VALIDATION.md` and `../../V7_SCOPE.md` for detailed formulation and provenance.

## Completed after resuming

- Reviewed Git status/diff, implementation, original attached requirements,
  saved solver stages, financial reports and test coverage.
- Corrected three stale descriptions: procurement lots now explicitly name
  A/B/C in the central register; original-case naming identifies the adopted B
  stocks; summary nonnegativity wording covers all tracked materials.
- Syntax compilation passed. Complete suite: **237 passed**, no failures
  (`../../v7_resume_tests.log`).
- Rechecked all 172 protected original/historical file digests: unchanged.
- Ran the real optimizer in fresh `../v7_resume_validation/`, preserving
  `../v7/` and all historical application runs.
- Reconstructed and independently audited the fresh exported schedule:
  **13,376 constraints**, **7,579 variable levels**, maximum violation
  **1.396984e-9**, tolerance **1e-5**, passed.

## Fresh solve and financial reconciliation

| Financial KPI | USD |
| --- | ---: |
| Reconciled operating expenses | 1,215,467.50 |
| Additional A material purchases | 0.00 |
| Additional C material purchases | 3,950,000.00 |
| Additional B material purchases | 4,700,000.00 |
| Total Delivery Cost | 9,865,467.50 |

Monthly independent financial calculations reconcile to the five annual KPIs
and the monetary objective. Opening/fixed material stocks are not purchases;
B consumption, receipts and FP shipments create no duplicate purchasing charge.
Existing responsive card audits cover laptop/desktop widths with no clipping
or horizontal overflow; exact operating/total values remain visible.

Service is **100% (3,095 MSU)**. All three service stages and the monetary stage
are proven optimal with zero reported gap. Event minimization reached its
300-second limit: **10-event incumbent, lower bound 7, gap 30%**. Quantity and
cleanup stages were not advanced. This is a valid service- and monetary-optimal
plan, not a proven full lexicographic optimum. The earlier preserved published
run has a stronger event bound of 8 (20% gap); neither proves the minimum.

No additional mathematical implementation gaps were found. Remaining limits:
unproven procurement-event minimum, packaging-age assumptions, intramonth
warehouse peaks and diagnostic-only C:D definitions. Do not describe these as
fully verified real-world constraints.

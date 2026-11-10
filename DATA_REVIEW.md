# V7 clarification / adopted assumptions

The user adopted B opening RM 200,000 kg and PM 750,000 EA following P&G
clarification. These numerical stocks are not in the original Word/Excel files.
V7 supersedes the original smooth-B modeling policy with explicit B inventory,
new orders, lots, three-month lead time and tracked warehouse footprint. There
are no fixed B receipts. Original source documents and historical reports are
unchanged. See V7_SCOPE.md; source observations below remain historical facts.

# Source extraction and validation

V5 active interpretation is centralized in [ASSUMPTIONS.md](ASSUMPTIONS.md).
C:D now has two diagnostic definitions, not an imposed feasibility constraint.
Packaging usability remains unverified without opening batch ages. The loader's
calendar extraction was corrected from the first number in `1 Month = 4 Weeks`
to the number after `=` (four); V4 already scheduled 28 days, so this correction
does not change original manufacturing capacity. Monthly family priorities are
an explicit V5 policy. Historical issues below retain source provenance.

Sources are read only: `data/Venus_PS_Case_Study_2026.docx` and
`data/Venus_PS_Supporting_Data_2026.xlsx`. Units are MSU (1,000 statistical
units), kg, EA, pallets, USD, days and months. Opening stocks are dated
30 September 2026; the horizon is October 2026 through September 2027.

## Complete table inventory and provenance

The seven business tables match across both files after calculating demand
totals from detail. The Word document also includes an abbreviation appendix.
The loader preserves every Word table, Word body paragraph, workbook sheet and
all 23 assumption rows as well as normalized data.

| Word table | Workbook sheet and cells | Structured destination |
| --- | --- | --- |
| 1 Assumptions & Rules | Assumptions & Rules A3:B26 | `raw_rules`, `rules` |
| 2A Line & Crewing | Line & BOM Profiles A4:H6 | `lines` |
| 2B BOM, Costs & Pallet Factors | Line & BOM Profiles A9:F12 | `bom`, `products`, `rules` |
| 3A Finished Product Stocks | Stocks Closure (30 Sep) A4:B7 | `initial_fp` |
| 3B Material Stocks and Pipeline | Stocks Closure (30 Sep) A10:E14 | `initial_materials`, `arrivals` |
| 3C Phase-Out MOQ | Stocks Closure (30 Sep) A17:B19 | `rules` |
| 4 Demand | 12M Demand Forecast A3:O12 | `demand`, `months`, `families`, `hubs` |
| Abbreviations | Word only | `word_tables[-1]` |

Pandas/openpyxl reads input detail; openpyxl separately reads cached formula
results. The loader does not execute Excel formulas. Validation recomputes
demand aggregates, checks cached monthly/annual results, and compares the
business tables to Word. Missing/stale formula caches produce validation errors.
This is an explicit adapter for the supplied workbook layout; changed sheet
layouts require review. Text quantities use their first numeric value, with
named markers for prose rules. Source comparisons guard changes to that prose.
Launch dates, family membership, line capability codes and qualitative rule
flags are explicit transcriptions of the cited source rows.

## Extracted business rules

- Calendar: four weeks/month; cumulative capacity-to-demand must remain at
  least 1.0. The precise C:D definition is unresolved.
- L1 makes A or C at 6 MSU/day, 24/5, 20 days/month, 120 MSU/month,
  30 operators/3 crews. L2 makes A, C and B at 8 MSU/day, 24/6,
  24 days/month, 192 MSU without changeover or 184 with one,
  40 operators/4 crews. Total base capacity is 312 MSU/month.
- L2 permits at most one routine changeover/month, losing 24 hours/one day.
  A-to-C conversion is exempt because it occurs in the qualification shutdown.
  C requires three simultaneous full shutdown days on both lines before
  production. Target launch is January 2027, with earlier launch permitted
  when ready; May–July is the commercial peak.
- Standard sea freight lead time is three months. The existing September
  order dates conflict with this (see unresolved inputs).
- A/C RM use 500 kg/MSU; B uses 600. A/C PM use 2,500 EA/MSU;
  B uses 2,000. RM costs $5/kg and occupies one pallet/1,000 kg.
  PM costs $0.40/EA and occupies one pallet/5,000 EA. FP occupies
  four pallets/MSU, valued at $4,000/$4,200/$5,500 per MSU for A/C/B.
- Opening FP: A=10, B=15, C=0 MSU. Opening A RM=115,000 kg,
  A PM=400,000 EA, C RM/PM=0. B material stocks are not supplied.
  Fixed arrivals: A PM=250,000 EA on October 1; C PM=375,000 EA on
  October 1; C RM=150,000 kg on November 1. These support total
  A RM=230, A PM=260, C RM=300 and C PM=150 MSU respectively.
- Extra phase-out orders have RM truckload MOQ=50,000 kg and PM=125,000 EA.
  Whether MOQ means a minimum quantity or mandatory integer multiples
  requires clarification before modeling. PM expires after one year.
  Residual A RM/PM is scrapped at phase-out: 100% material value plus
  $200/ton disposal. Each 1,000 EA of PM weighs 20 kg.
  B RM/PM is separate and assumed smoothly replenished with standard lead time.
- Base labor costs $1,000/operator/month for 70 operators. L1 upgrade to
  24/6 adds four days/24 MSU per month; L2 upgrade to 24/7 adds four
  days/32 MSU. Each upgrade requires ten additional operators. Hiring
  requires one paid training month ($1,000/operator, zero output) plus
  $500/operator hiring fee. Prose also permits premium overtime and
  mentions strict headcount rules without supplying their numeric limits.
- Combined end-of-month FP+RM+PM warehouse ceiling is 1,200 pallets.
  Overflow costs $45/pallet/month, booked in 100-pallet blocks. Monthly
  cash holding charge is 1.5% of ending FP dollar value only.
- A truck carries 5 MSU/20 pallets, cannot mix hubs, and a partial load
  pays for the full truck (no additional separate LTL rate is given).
  Dedicated fleet limit is 65 trucks/month across all hubs. Cairo,
  Alex/Delta and Upper Egypt/Red Sea cost $300/$500/$800 per dedicated
  truck. Spot trucks beyond the fleet limit incur a 60% surcharge.
- Strict service order: Cairo modern retail/quick commerce (P1,
  $3,000/unserved MSU), Alex/Delta pharmacies/e-commerce (P2, $2,000),
  Upper Egypt traditional trade/university sampling (P3, $1,200).
- Demand is supplied for the pooled A/C family and separate B at each
  hub in each month (72 detail records), not individual A and C demand.
  Annual demand is A/C=1,560 and B=1,535, totaling 3,095 MSU.

Word-only context: the campaign begins October 2026, targets 1.5 million
new users and expansion from 17,000 to 60,000 traditional-trade stores,
from a stated 19% category penetration among ABC1 women. These are
commercial context, not additional numeric demand constraints. The five
requested deliverables cover capacity/crewing, transition/scrap, warehouse/cash,
transport/service and financial comparison. They are retained in `word_paragraphs`.

## Missing, inconsistent or ambiguous inputs

1. Three-month standard lead time conflicts with Sep 1 order/Oct 1 arrival.
   Preserve the three explicit arrivals; do not infer a new standard lead time.
2. No overtime premium, overtime ceiling or numeric plant headcount limit.
3. No B opening material stocks or pre-horizon replenishment pipeline.
4. No ages of opening PM to calculate expiry.
5. No exact A/C transition date, monthly A/C split, substitution policy or
   disposition rule for residual A finished goods.
6. No formal C:D numerator or convention for including opening stocks.
7. No shutdown calendar or rule for overlap with normal nonworking days
   and changeovers; further operating-profile upgrades are unspecified.
8. Strict channel priorities versus penalty-weighted service, and lost-sales
   versus backlog treatment, need clarification.
9. MOQ minimum versus integer truckload multiples needs clarification.
10. No explicit cash/cost/service tradeoff, target ending inventory or
    conversion costs beyond labor/materials. These are modeling choices
    or missing inputs, not grounds to invent numbers.

Unavailable numeric inputs are `None`, never assumed zero. Other unresolved
policies remain documented and are not resolved by this extraction milestone.
Validation PASS means source consistency checks pass, not that optimization
inputs are complete. Findings are displayed separately; data errors return
exit status 1, while source warnings alone return 0.

## Interpretation register (source text unchanged)

**V4 supersedes the historical fixed-scenario choices below.** See
[V4_SCOPE.md](V4_SCOPE.md): 28-day calendars; endogenous three-day common-base
qualification; permanent end of A manufacturing; A FP sell-through; actual L2
changeovers; optional ten-person crews with a full paid training month; and A
RM/PM scrap/IDE at qualification. Current runs use strict Scenario A only.
Opening L2 configuration is unspecified and may be A or B; subsequent state
changes are never free. Source headcount limits, PM ages/expiry and C:D remain
unresolved. B material footprint remains unspecified/excluded. No original
source text, shipment or numeric input is changed by these decisions.

- New orders use the documented three-month sea lead time. Fixed October/
  November arrivals remain exactly as provided despite the September-order
  inconsistency. No new pre-horizon purchases are inferred.
- V2.1 explicitly requires integer 50,000 kg RM / 125,000 EA PM increments
  for both A and C additional orders. This user-directed policy supersedes
  V2's continuous C replenishment; the source labels these phase-out MOQs.
  Existing fixed receipts stay unchanged and are not subject to re-lotting.
- B smooth replenishment is accepted as the case permits: its materials are
  always available for planned B production. No detailed B material inventory
  or procurement variables are created. Physical stocks are unspecified, not
  zero. Missing B opening stocks/pipeline do not block the model. Their
  physical footprint is unspecified and explicitly excluded from V2.1's
  tracked month-end warehouse, not described as physically zero.
- Fixed January qualification, A/C sales windows and lost-sales interpretation
  continue from V1; annual P1/P2/P3 service ordering is explicit. These are test
  scenario choices where the original case leaves operational details open.
- PM ages, overtime/headcount details, C:D definition, residual A FP policy,
  warehouse footprint of B materials and full-case terminal/tradeoff policy
  remain unresolved. See `MODEL_SCOPE.md` for exact active/omitted constraints.
- Warehouse uses original capacity/footprints and full 100-pallet overflow
  blocks at $45/pallet/month. Month-end limits do not verify intramonth peaks.
- International events count each product/material/month separately. No joint
  RM/PM shipping capability or fixed international shipment cost is assumed.
- The 2% cost allowance is a sensitivity only; default cost tolerance is zero.
  Cost excludes material purchasing and material carrying charges. Event count
  is optimized after service and permitted cost, followed by quantity and a
  final cost cleanup; no weighted tradeoff or invented freight rate is used.

# V4 financial reconciliation of the saved plan

Reporting only: no solver was run and no formulation, assumptions, rates or decisions were changed.

Service is 100%. Monetary-stage termination is `optimal`. Full lexicographic proof flag remains `False`. Procurement-event minimization remains unproven: `maxTimeLimit`, incumbent 4.0, bound 2.0, 50% gap. Later quantity/cleanup stages did not run. This report does not change or reinterpret solver proof status.

Independently recalculated total: **$1,215,467.50**. User Excel total: **$1,217,953.00**. Unexplained Excel-minus-model difference: **$2,485.50**. Recalculation minus saved objective: 0 USD.

## Formulas and annual cost components

All rates come from the original workbook through load_case(); all quantities come from the saved V4 CSVs. Binary floating-point values are read with round-trip precision. Nothing is rounded or clamped before calculations. CSV precision is retained; readable tables show two decimals and display numerical near-zero noise as zero only.

| Component | Independent formula and saved quantities | Annual USD |
| --- | --- | ---: |
| Base salaries | sum source line operators (70) x $1,000 x 12 | 840,000.00 |
| New crew salaries | sum staffing.employed_crews x 10 x $1,000, including training | 0.00 |
| Hiring | sum staffing.hired_crew x 10 x $500 | 0.00 |
| A RM scrap value | monthly A RM scrap kg x $5/kg | 0.00 |
| A PM scrap value | monthly A PM scrap EA x $0.40/EA | 30,000.00 |
| A RM disposal | A RM scrap kg / 1,000 x $200/ton | 0.00 |
| A PM disposal | A PM scrap EA x 0.02 kg/EA / 1,000 x $200/ton | 300.00 |
| FP holding / working capital | sum all product/month ending FP x product value x 0.015 | 56,167.50 |
| Dedicated transport | sum hub/month dedicated trucks x $300/$500/$800 per hub | 272,200.00 |
| Spot transport | sum hub/month spot trucks x hub rate x 1.6 | 16,800.00 |
| Service penalties | sum unserved hub/family/month MSU x $3,000/$2,000/$1,200 | 0.00 |
| External rental | sum monthly external_blocks x 100 pallets x $45 | 0.00 |
| **Total** | Sum the twelve categories once | **1,215,467.50** |

FP values are A=$4,000/MSU, B=$5,500/MSU and C=$4,200/MSU. There is no separate material purchasing cost. New-crew salaries already include training salaries; neither is counted twice. Scrap material values are charged once in IDE. No holding charge is applied to raw materials, packaging, demand or pallet counts.

Difference from the separately proven monetary minimum (stage 4): 8.381903171539307e-09 USD. The few-billionths-of-a-dollar residual is floating-point noise in the saved later-stage plan, not $2,485.50.

## Holding-cost investigation

The product-specific month-end method is correct for the modeled objective. The saved plan's recomputed holding cost matches solve_status.json within numerical tolerance. Product contributions:

- A: $0.00
- B: $7,342.50
- C: $48,825.00

If all other Excel components agree, Excel would imply **$58,653.00** holding expense. That is a conditional inference only: the Excel component breakdown has not been supplied.

| Diagnostic calculation (not a model change) | Holding USD |
| --- | ---: |
| Correct ending product-specific stock | 56,167.50 |
| Opening stock instead of ending | 58,005.00 |
| Only September ending stock instead of twelve months | 0.00 |
| All FP at C's $4,200 value | 54,432.00 |
| A/C stock at A's $4,000 value; B at $5,500 | 53,842.50 |
| Round each product's MSU to an integer first | 56,167.50 |

Opening-versus-ending changes annual holding by the opening FP value less September closing FP value, times 1.5%. Opening FP is A=10 and B=15 MSU: $122,500, or $1,837.50 holding. This does not explain $2,485.50 alone. Using A's value for C stock understates rather than explains a higher Excel total. A and C share demand, but never a common valuation.

The monthly ending stocks sum to 864.000000 MSU-months. This is a holding exposure, not September stock or annual physical inventory. Prebuilt stock is charged again in each month it remains held. Negative net changes in May–July are drawdowns, not negative ending inventories. Tiny signed floating-point residues are numerical noise; integer rounding changes this plan's financial total only below the displayed cent, not by $2,485.50.

Plan version matters: historical V2.1 holding was $58,987.50; current V4 holding is $56,167.50, a $2,820 change, which is also not $2,485.50. ANALYSIS.md, summary.txt, raw saved stocks and solve_status.json agree on the current V4 cost. Alternative schedules can have different product inventory composition; a copied monthly plan must be compared to the same saved solution.

The CSVs contain the saved event-stage incumbent, not a separately archived copy of every stage-4 decision. It is monetary-cost optimal because its independently reconstructed cost equals the proven stage-4 minimum within tolerance. An exact vector-by-vector comparison with the original stage-4 plan is unavailable; multiple monetary-optimal plans may exist. There is no evidence here that an inconsistent plan caused the Excel difference.

The discrepancy cannot be conclusively attributed to working capital from a single Excel grand total. For complete reconciliation, provide Excel's twelve monthly FP holding totals (ideally the 36 product/month opening/ending MSU, valuation and formula cells), base salaries, new salaries including training, hiring fees, four IDE components, dedicated transport, spot transport, service penalties and external storage totals. Also identify the source plan/version, truck counts, scrap quantities, rounding conventions, and whether opening, average or ending stock was charged. These components should sum to $1,217,953.00.

## Monthly production and inventory

| month | ac_demand_msu | b_demand_msu | total_demand_msu | a_production_msu | c_production_msu | b_production_msu | total_production_msu | opening_fp_msu | shipments_msu | unserved_msu | net_fp_change_msu | ending_fp_msu | fp_pallets |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | 85.00 | 105.00 | 190.00 | 75.00 | 0.00 | 90.00 | 165.00 | 25.00 | 190.00 | 0.00 | -25.00 | 0.00 | 0.00 |
| 2026-11 | 75.00 | 110.00 | 185.00 | 75.00 | 0.00 | 110.00 | 185.00 | 0.00 | 185.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 2026-12 | 105.00 | 120.00 | 225.00 | 80.00 | 25.00 | 120.00 | 225.00 | 0.00 | 225.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 2027-01 | 85.00 | 95.00 | 180.00 | 0.00 | 115.00 | 100.00 | 215.00 | 0.00 | 180.00 | 0.00 | 35.00 | 35.00 | 140.00 |
| 2027-02 | 95.00 | 105.00 | 200.00 | 0.00 | 200.00 | 104.00 | 304.00 | 35.00 | 200.00 | 0.00 | 104.00 | 139.00 | 556.00 |
| 2027-03 | 120.00 | 120.00 | 240.00 | 0.00 | 184.00 | 120.00 | 304.00 | 139.00 | 240.00 | 0.00 | 64.00 | 203.00 | 812.00 |
| 2027-04 | 150.00 | 135.00 | 285.00 | 0.00 | 168.00 | 136.00 | 304.00 | 203.00 | 285.00 | 0.00 | 19.00 | 222.00 | 888.00 |
| 2027-05 | 190.00 | 165.00 | 355.00 | 0.00 | 120.00 | 192.00 | 312.00 | 222.00 | 355.00 | 0.00 | -43.00 | 179.00 | 716.00 |
| 2027-06 | 220.00 | 185.00 | 405.00 | 0.00 | 120.00 | 192.00 | 312.00 | 179.00 | 405.00 | 0.00 | -93.00 | 86.00 | 344.00 |
| 2027-07 | 215.00 | 175.00 | 390.00 | 0.00 | 168.00 | 136.00 | 304.00 | 86.00 | 390.00 | 0.00 | -86.00 | 0.00 | 0.00 |
| 2027-08 | 135.00 | 120.00 | 255.00 | 0.00 | 135.00 | 120.00 | 255.00 | 0.00 | 255.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 2027-09 | 85.00 | 100.00 | 185.00 | 0.00 | 85.00 | 100.00 | 185.00 | 0.00 | 185.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ANNUAL | 1,560.00 | 1,535.00 | 3,095.00 | 230.00 | 1,320.00 | 1,520.00 | 3,070.00 | 25.00 | 3,095.00 | 0.00 | -25.00 | 0.00 | 0.00 |

ANNUAL sums demand/production/shipments/unserved/net flows. Its opening stock is October's opening, and its ending stock/pallets are September's ending balances, not sums of monthly stocks.

## Monthly monetary breakdown (USD)

| month | base_salaries_usd | new_crew_salaries_usd | hiring_fees_usd | a_rm_scrap_value_usd | a_pm_scrap_value_usd | a_rm_disposal_usd | a_pm_disposal_usd | fp_holding_usd | dedicated_transport_usd | spot_transport_usd | service_penalties_usd | external_storage_usd | total_modeled_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 17,300.00 | 0.00 | 0.00 | 0.00 | 87,300.00 |
| 2026-11 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 16,800.00 | 0.00 | 0.00 | 0.00 | 86,800.00 |
| 2026-12 | 70,000.00 | 0.00 | 0.00 | 0.00 | 30,000.00 | 0.00 | 300.00 | 0.00 | 20,300.00 | 0.00 | 0.00 | 0.00 | 120,600.00 |
| 2027-01 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 2,302.50 | 16,000.00 | 0.00 | 0.00 | 0.00 | 88,302.50 |
| 2027-02 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 8,835.00 | 18,400.00 | 0.00 | 0.00 | 0.00 | 97,235.00 |
| 2027-03 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 12,867.00 | 22,400.00 | 0.00 | 0.00 | 0.00 | 105,267.00 |
| 2027-04 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 14,083.50 | 26,200.00 | 0.00 | 0.00 | 0.00 | 110,283.50 |
| 2027-05 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 11,901.00 | 30,600.00 | 2,880.00 | 0.00 | 0.00 | 115,381.00 |
| 2027-06 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 6,178.50 | 32,600.00 | 7,680.00 | 0.00 | 0.00 | 116,458.50 |
| 2027-07 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 31,900.00 | 6,240.00 | 0.00 | 0.00 | 108,140.00 |
| 2027-08 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 23,200.00 | 0.00 | 0.00 | 0.00 | 93,200.00 |
| 2027-09 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 16,500.00 | 0.00 | 0.00 | 0.00 | 86,500.00 |
| ANNUAL | 840,000.00 | 0.00 | 0.00 | 0.00 | 30,000.00 | 0.00 | 300.00 | 56,167.50 | 272,200.00 | 16,800.00 | 0.00 | 0.00 | 1,215,467.50 |

## Monthly product inventory and holding (MSU / USD)

| month | product | opening_fp_msu | production_msu | shipments_msu | ending_fp_msu | valuation_usd_per_msu | ending_fp_value_usd | holding_expense_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | A | 10.00 | 75.00 | 85.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2026-11 | A | 0.00 | 75.00 | 75.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2026-12 | A | 0.00 | 80.00 | 80.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-01 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-02 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-03 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-04 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-05 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-06 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-07 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-08 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2027-09 | A | 0.00 | 0.00 | 0.00 | 0.00 | 4,000.00 | 0.00 | 0.00 |
| 2026-10 | C | 0.00 | 0.00 | 0.00 | 0.00 | 4,200.00 | 0.00 | 0.00 |
| 2026-11 | C | 0.00 | 0.00 | 0.00 | 0.00 | 4,200.00 | 0.00 | 0.00 |
| 2026-12 | C | 0.00 | 25.00 | 25.00 | 0.00 | 4,200.00 | 0.00 | 0.00 |
| 2027-01 | C | 0.00 | 115.00 | 85.00 | 30.00 | 4,200.00 | 126,000.00 | 1,890.00 |
| 2027-02 | C | 30.00 | 200.00 | 95.00 | 135.00 | 4,200.00 | 567,000.00 | 8,505.00 |
| 2027-03 | C | 135.00 | 184.00 | 120.00 | 199.00 | 4,200.00 | 835,800.00 | 12,537.00 |
| 2027-04 | C | 199.00 | 168.00 | 150.00 | 217.00 | 4,200.00 | 911,400.00 | 13,671.00 |
| 2027-05 | C | 217.00 | 120.00 | 190.00 | 147.00 | 4,200.00 | 617,400.00 | 9,261.00 |
| 2027-06 | C | 147.00 | 120.00 | 220.00 | 47.00 | 4,200.00 | 197,400.00 | 2,961.00 |
| 2027-07 | C | 47.00 | 168.00 | 215.00 | 0.00 | 4,200.00 | 0.00 | 0.00 |
| 2027-08 | C | 0.00 | 135.00 | 135.00 | 0.00 | 4,200.00 | 0.00 | 0.00 |
| 2027-09 | C | 0.00 | 85.00 | 85.00 | 0.00 | 4,200.00 | 0.00 | 0.00 |
| 2026-10 | B | 15.00 | 90.00 | 105.00 | 0.00 | 5,500.00 | 0.00 | 0.00 |
| 2026-11 | B | 0.00 | 110.00 | 110.00 | 0.00 | 5,500.00 | 0.00 | 0.00 |
| 2026-12 | B | 0.00 | 120.00 | 120.00 | 0.00 | 5,500.00 | 0.00 | 0.00 |
| 2027-01 | B | 0.00 | 100.00 | 95.00 | 5.00 | 5,500.00 | 27,500.00 | 412.50 |
| 2027-02 | B | 5.00 | 104.00 | 105.00 | 4.00 | 5,500.00 | 22,000.00 | 330.00 |
| 2027-03 | B | 4.00 | 120.00 | 120.00 | 4.00 | 5,500.00 | 22,000.00 | 330.00 |
| 2027-04 | B | 4.00 | 136.00 | 135.00 | 5.00 | 5,500.00 | 27,500.00 | 412.50 |
| 2027-05 | B | 5.00 | 192.00 | 165.00 | 32.00 | 5,500.00 | 176,000.00 | 2,640.00 |
| 2027-06 | B | 32.00 | 192.00 | 185.00 | 39.00 | 5,500.00 | 214,500.00 | 3,217.50 |
| 2027-07 | B | 39.00 | 136.00 | 175.00 | 0.00 | 5,500.00 | 0.00 | 0.00 |
| 2027-08 | B | 0.00 | 120.00 | 120.00 | 0.00 | 5,500.00 | 0.00 | 0.00 |
| 2027-09 | B | 0.00 | 100.00 | 100.00 | 0.00 | 5,500.00 | 0.00 | 0.00 |

## Reproduce without optimizing

```powershell
.\.venv\Scripts\python.exe -m src.results --report-dir reports/v4
```

This command reads existing results and source rates, overwrites only these generated reconciliation files and replaces the generated reconciliation appendix in summary.txt. Solver status and raw decision CSVs remain untouched. V2.1 historical results are not written.

## Input SHA-256 fingerprints

- `production.csv`: `8b522d9f722d9badc05a1eba079db22324d64de0cc9f4c9677612818cf60efa9`
- `inventory.csv`: `e2f6356aa9c6b3fd41c68d32a6f3d53efbe1475079021fd96f754452daa5c1fa`
- `shipments.csv`: `f8970c437025403272c4631f9b8d83abb5b19153fe0266ba5cfbc3c94daf09b0`
- `service.csv`: `9e77d6f36925376b2fe93551614b9967e6d5604335e9363b225ef714ea6d488b`
- `transport.csv`: `854b44d51710c5de67160a19d393c3d264a0fde1c9e9e498362db316cc488462`
- `staffing.csv`: `6b356e933d84c4a133c69b6847e2e2a19eaf80363a18df9f147a133a5a278469`
- `material_balances.csv`: `4e97b4359e40f92d17e179f453ae8fa5cfe3eda8e3dcd9854e49d6647ebc3169`
- `warehouse.csv`: `6edd2e5f3e4b1c1de60957f506d4bf4bff5417c9299b5bb7371d18e3979c6ec9`
- `solve_status.json`: `4be6617c51c9a22b92d5ba590b15af7348b319e4a3f5d6a5a5f0180b4fb559cd`
- `Venus_PS_Case_Study_2026.docx`: `43f35a41060c381eb377705ff43d15b1a68c313e9e189e60cfa8151aac6f9e24`
- `Venus_PS_Supporting_Data_2026.xlsx`: `76adc219f83c76dfb7b35c4b6123eb60e3460ba73dba5e6b17223c72625b4234`

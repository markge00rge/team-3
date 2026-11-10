# V7 final original-case results

Actual fresh Pyomo/HiGHS execution. All three service objectives and monetary cost are proven optimal, with zero gaps. The procurement-event stage reached 300 seconds: **incumbent 10, lower bound 8, gap 20%**. Quantity and cleanup stages were not run. This is a service- and monetary-optimal plan, not a proven minimum-event plan.

## Financial figures (USD)

| Category | USD |
| --- | --- |
| Operating Expenses excluding purchases | 1,215,467.50 |
| Additional A purchases | 0.00 |
| Additional B purchases | 4,700,000.00 |
| Additional C purchases | 3,950,000.00 |
| Total Delivery Cost | 9,865,467.50 |

All new ABC orders are charged at placement. No charge on opening stocks, fixed shipments, consumption or receipt. B consumption-based expense is removed. The five figures reconcile within solver tolerance.

## Service by hub

| hub | demand_msu | served_msu | unserved_msu |
| --- | --- | --- | --- |
| H1 | 1,525.00 | 1,525.00 | 0.00 |
| H2 | 1,000.00 | 1,000.00 | 0.00 |
| H3 | 570.00 | 570.00 | 0.00 |

Annual service is 3,095/3,095 MSU (100%). Full monthly hub/family details are in service.csv. Annual production is A=230, B=1,520 and C=1,320 MSU, plus 25 MSU original opening FP.

## First three months: Product B

| month | msu |
| --- | --- |
| 2026-10 | 90.00 |
| 2026-11 | 110.00 |
| 2026-12 | 120.00 |

October/November/December B production is 90/110/120 MSU: 320 total, plus opening FP 15, serving demand 105/110/120. It consumes 192,000 kg RM and 640,000 EA PM. End-December B stocks are RM 8,000 kg / PM 110,000 EA. No B receipts occur before January. The original stocks 200,000 kg / 750,000 EA are adopted clarification assumptions, not figures inserted into original source files.

## B raw materials: kg and order-placement USD

| month | opening | new_order_placed | new_order_cost_usd | fixed_arrival | additional_arrival | consumption | ending |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | 200,000.00 | 200,000.00 | 1,000,000.00 | 0.00 | 0.00 | 54,000.00 | 146,000.00 |
| 2026-11 | 146,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 66,000.00 | 80,000.00 |
| 2026-12 | 80,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 72,000.00 | 8,000.00 |
| 2027-01 | 8,000.00 | 200,000.00 | 1,000,000.00 | 0.00 | 200,000.00 | 60,000.00 | 148,000.00 |
| 2027-02 | 148,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 62,400.00 | 85,600.00 |
| 2027-03 | 85,600.00 | 350,000.00 | 1,750,000.00 | 0.00 | 0.00 | 72,000.00 | 13,600.00 |
| 2027-04 | 13,600.00 | 0.00 | 0.00 | 0.00 | 200,000.00 | 81,600.00 | 132,000.00 |
| 2027-05 | 132,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 115,200.00 | 16,800.00 |
| 2027-06 | 16,800.00 | 0.00 | 0.00 | 0.00 | 350,000.00 | 115,200.00 | 251,600.00 |
| 2027-07 | 251,600.00 | 0.00 | 0.00 | 0.00 | 0.00 | 81,600.00 | 170,000.00 |
| 2027-08 | 170,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 72,000.00 | 98,000.00 |
| 2027-09 | 98,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 60,000.00 | 38,000.00 |

## B packaging: EA and order-placement USD

| month | opening | new_order_placed | new_order_cost_usd | fixed_arrival | additional_arrival | consumption | ending |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | 750,000.00 | 1,250,000.00 | 500,000.00 | 0.00 | 0.00 | 180,000.00 | 570,000.00 |
| 2026-11 | 570,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 220,000.00 | 350,000.00 |
| 2026-12 | 350,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 240,000.00 | 110,000.00 |
| 2027-01 | 110,000.00 | 0.00 | 0.00 | 0.00 | 1,250,000.00 | 200,000.00 | 1,160,000.00 |
| 2027-02 | 1,160,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 208,000.00 | 952,000.00 |
| 2027-03 | 952,000.00 | 1,125,000.00 | 450,000.00 | 0.00 | 0.00 | 240,000.00 | 712,000.00 |
| 2027-04 | 712,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 272,000.00 | 440,000.00 |
| 2027-05 | 440,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 384,000.00 | 56,000.00 |
| 2027-06 | 56,000.00 | 0.00 | 0.00 | 0.00 | 1,125,000.00 | 384,000.00 | 797,000.00 |
| 2027-07 | 797,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 272,000.00 | 525,000.00 |
| 2027-08 | 525,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 240,000.00 | 285,000.00 |
| 2027-09 | 285,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 200,000.00 | 85,000.00 |

New B purchases total RM 750,000 kg (15 lots; $3,750,000) and PM 2,375,000 EA (19 lots; $950,000). Year-end B stock is RM 38,000 kg / PM 85,000 EA. It is not scrapped or given a terminal salvage value.

## Positive additional procurement events (all products)

| product | material | unit | order_month | arrival_month | quantity | integer_lots | order_event | unit_price_usd | purchase_expense_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | RM | kg | 2026-10 | 2027-01 | 200,000.00 | 4.00 | 1.00 | 5.00 | 1,000,000.00 |
| B | RM | kg | 2027-01 | 2027-04 | 200,000.00 | 4.00 | 1.00 | 5.00 | 1,000,000.00 |
| B | RM | kg | 2027-03 | 2027-06 | 350,000.00 | 7.00 | 1.00 | 5.00 | 1,750,000.00 |
| B | PM | EA | 2026-10 | 2027-01 | 1,250,000.00 | 10.00 | 1.00 | 0.40 | 500,000.00 |
| B | PM | EA | 2027-03 | 2027-06 | 1,125,000.00 | 9.00 | 1.00 | 0.40 | 450,000.00 |
| C | RM | kg | 2026-10 | 2027-01 | 200,000.00 | 4.00 | 1.00 | 5.00 | 1,000,000.00 |
| C | RM | kg | 2027-02 | 2027-05 | 200,000.00 | 4.00 | 1.00 | 5.00 | 1,000,000.00 |
| C | RM | kg | 2027-03 | 2027-06 | 150,000.00 | 3.00 | 1.00 | 5.00 | 750,000.00 |
| C | PM | EA | 2026-11 | 2027-02 | 1,375,000.00 | 11.00 | 1.00 | 0.40 | 550,000.00 |
| C | PM | EA | 2027-02 | 2027-05 | 1,625,000.00 | 13.00 | 1.00 | 0.40 | 650,000.00 |

The selected plan has five B events and five C events; A orders are zero. These are separate material-specific events, not assumed shared maritime shipments. The 10-event minimum is unproven. The three original fixed A/C incoming shipments are separate constants in fixed_receipts.csv.

## Month-end warehouse and external storage

| month | fp_pallets | rm_pallets | pm_pallets | tracked_pallets | onsite_capacity | minimum_external_pallets | onsite_pallets | external_blocks | external_storage_usd | a_fp_pallets | c_fp_pallets | b_fp_pallets | a_rm_pallets | a_pm_pallets | b_rm_pallets | b_pm_pallets | c_rm_pallets | c_pm_pallets |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | 0.00 | 223.50 | 281.50 | 505.00 | 1,200.00 | 0.00 | 505.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 77.50 | 92.50 | 146.00 | 114.00 | 0.00 | 75.00 |
| 2026-11 | 0.00 | 270.00 | 200.00 | 470.00 | 1,200.00 | 0.00 | 470.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 | 55.00 | 80.00 | 70.00 | 150.00 | 75.00 |
| 2026-12 | 0.00 | 145.50 | 84.50 | 230.00 | 1,200.00 | 0.00 | 230.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 8.00 | 22.00 | 137.50 | 62.50 |
| 2027-01 | 140.00 | 428.00 | 237.00 | 805.00 | 1,200.00 | 0.00 | 805.00 | 0.00 | 0.00 | 0.00 | 120.00 | 20.00 | 0.00 | 0.00 | 148.00 | 232.00 | 280.00 | 5.00 |
| 2027-02 | 556.00 | 265.60 | 370.40 | 1,192.00 | 1,200.00 | 0.00 | 1,192.00 | 0.00 | 0.00 | 0.00 | 540.00 | 16.00 | 0.00 | 0.00 | 85.60 | 190.40 | 180.00 | 180.00 |
| 2027-03 | 812.00 | 101.60 | 230.40 | 1,144.00 | 1,200.00 | 0.00 | 1,144.00 | 0.00 | 0.00 | 0.00 | 796.00 | 16.00 | 0.00 | 0.00 | 13.60 | 142.40 | 88.00 | 88.00 |
| 2027-04 | 888.00 | 136.00 | 92.00 | 1,116.00 | 1,200.00 | 0.00 | 1,116.00 | 0.00 | 0.00 | 0.00 | 868.00 | 20.00 | 0.00 | 0.00 | 132.00 | 88.00 | 4.00 | 4.00 |
| 2027-05 | 716.00 | 160.80 | 280.20 | 1,157.00 | 1,200.00 | 0.00 | 1,157.00 | 0.00 | 0.00 | 0.00 | 588.00 | 128.00 | 0.00 | 0.00 | 16.80 | 11.20 | 144.00 | 269.00 |
| 2027-06 | 344.00 | 485.60 | 368.40 | 1,198.00 | 1,200.00 | 0.00 | 1,198.00 | 0.00 | 0.00 | 0.00 | 188.00 | 156.00 | 0.00 | 0.00 | 251.60 | 159.40 | 234.00 | 209.00 |
| 2027-07 | 0.00 | 320.00 | 230.00 | 550.00 | 1,200.00 | 0.00 | 550.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 170.00 | 105.00 | 150.00 | 125.00 |
| 2027-08 | 0.00 | 180.50 | 114.50 | 295.00 | 1,200.00 | 0.00 | 295.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 98.00 | 57.00 | 82.50 | 57.50 |
| 2027-09 | 0.00 | 78.00 | 32.00 | 110.00 | 1,200.00 | 0.00 | 110.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 38.00 | 17.00 | 40.00 | 15.00 |

All nine category columns are included exactly once. Peak tracked occupancy is 1,198 pallets; external blocks and rental cost are zero in all months. Opening B RM/PM adds 350 pallets; B FP adds 60 pallets already included in FP. Initial tracked plant occupancy is 645 pallets before October fixed receipts. These are month-end constraints, not proof of intramonth peak space.

## Product B FP inventory and holding

| month | product | opening_fp_msu | production_msu | shipments_msu | ending_fp_msu | valuation_usd_per_msu | ending_fp_value_usd | holding_expense_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
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

B FP holding totals $7,342.50, using ending B FP times $5,500/MSU times 1.5% ($82.50 per ending MSU/month). Total all-product FP holding is $56,167.50. B RM/PM is not charged this holding rate.

## Qualification, workforce and IDE

Qualification: December planning days 17-19. First C production: day 22; last A manufacture: day 16. No crews hired, dismissed or upgraded. The 70 original operators remain permanent. Base salaries $840,000; additional salaries/hiring/dismissal $0. Full A IDE is $30,300: RM value $0, PM value $30,000, RM disposal $0, PM disposal $300. Purchased-A overlap adjustment is $0. B materials are not scrapped.

## Complete monthly financial reconciliation

| month | base_salaries_usd | new_crew_salaries_usd | hiring_fees_usd | a_rm_scrap_value_usd | a_pm_scrap_value_usd | a_rm_disposal_usd | a_pm_disposal_usd | fp_holding_usd | dedicated_transport_usd | spot_transport_usd | service_penalties_usd | external_storage_usd | total_modeled_cost_usd | dismissal_expense_usd | full_ide_usd | operating_full_ide_usd | ide_overlap_adjustment_usd | operating_expenses_usd | a_rm_order_usd | a_pm_order_usd | a_material_cost_usd | b_rm_order_usd | b_pm_order_usd | b_material_cost_usd | c_rm_order_usd | c_pm_order_usd | c_material_cost_usd | total_delivery_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 17,300.00 | 0.00 | 0.00 | 0.00 | 2,587,300.00 | 0.00 | 0.00 | 87,300.00 | 0.00 | 87,300.00 | 0.00 | 0.00 | 0.00 | 1,000,000.00 | 500,000.00 | 1,500,000.00 | 1,000,000.00 | 0.00 | 1,000,000.00 | 2,587,300.00 |
| 2026-11 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 16,800.00 | 0.00 | 0.00 | 0.00 | 636,800.00 | 0.00 | 0.00 | 86,800.00 | 0.00 | 86,800.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 550,000.00 | 550,000.00 | 636,800.00 |
| 2026-12 | 70,000.00 | 0.00 | 0.00 | 0.00 | 30,000.00 | 0.00 | 300.00 | 0.00 | 20,300.00 | 0.00 | 0.00 | 0.00 | 120,600.00 | 0.00 | 30,300.00 | 120,600.00 | 0.00 | 120,600.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 120,600.00 |
| 2027-01 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 2,302.50 | 16,000.00 | 0.00 | 0.00 | 0.00 | 1,088,302.50 | 0.00 | 0.00 | 88,302.50 | 0.00 | 88,302.50 | 0.00 | 0.00 | 0.00 | 1,000,000.00 | 0.00 | 1,000,000.00 | 0.00 | 0.00 | 0.00 | 1,088,302.50 |
| 2027-02 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 8,835.00 | 18,400.00 | 0.00 | 0.00 | 0.00 | 1,747,235.00 | 0.00 | 0.00 | 97,235.00 | 0.00 | 97,235.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1,000,000.00 | 650,000.00 | 1,650,000.00 | 1,747,235.00 |
| 2027-03 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 12,867.00 | 22,400.00 | 0.00 | 0.00 | 0.00 | 3,055,267.00 | 0.00 | 0.00 | 105,267.00 | 0.00 | 105,267.00 | 0.00 | 0.00 | 0.00 | 1,750,000.00 | 450,000.00 | 2,200,000.00 | 750,000.00 | 0.00 | 750,000.00 | 3,055,267.00 |
| 2027-04 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 14,083.50 | 26,200.00 | 0.00 | 0.00 | 0.00 | 110,283.50 | 0.00 | 0.00 | 110,283.50 | 0.00 | 110,283.50 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 110,283.50 |
| 2027-05 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 11,901.00 | 30,600.00 | 2,880.00 | 0.00 | 0.00 | 115,381.00 | 0.00 | 0.00 | 115,381.00 | 0.00 | 115,381.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 115,381.00 |
| 2027-06 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 6,178.50 | 32,600.00 | 7,680.00 | 0.00 | 0.00 | 116,458.50 | 0.00 | 0.00 | 116,458.50 | 0.00 | 116,458.50 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 116,458.50 |
| 2027-07 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 31,900.00 | 6,240.00 | 0.00 | 0.00 | 108,140.00 | 0.00 | 0.00 | 108,140.00 | 0.00 | 108,140.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 108,140.00 |
| 2027-08 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 23,200.00 | 0.00 | 0.00 | 0.00 | 93,200.00 | 0.00 | 0.00 | 93,200.00 | 0.00 | 93,200.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 93,200.00 |
| 2027-09 | 70,000.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 16,500.00 | 0.00 | 0.00 | 0.00 | 86,500.00 | 0.00 | 0.00 | 86,500.00 | 0.00 | 86,500.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 86,500.00 |
| ANNUAL | 840,000.00 | 0.00 | 0.00 | 0.00 | 30,000.00 | 0.00 | 300.00 | 56,167.50 | 272,200.00 | 16,800.00 | 0.00 | 0.00 | 9,865,467.50 | 0.00 | 30,300.00 | 1,215,467.50 | 0.00 | 1,215,467.50 | 0.00 | 0.00 | 0.00 | 3,750,000.00 | 950,000.00 | 4,700,000.00 | 2,750,000.00 | 1,200,000.00 | 3,950,000.00 | 9,865,467.50 |

Annual transportation $289,000, service failure $0, external storage $0. Full source-based monthly category reconciliation is retained with unrounded CSV numbers; presentation is rounded only.

## Comparison with V6 smooth replenishment

V6 total was $10,941,467.50, including B production consumption $5,776,000. V7 total is $9,865,467.50, including B new orders $4,700,000. Operating expense and A/C purchasing totals are unchanged. The $1,076,000 difference reflects different opening-stock and purchasing-accounting assumptions; it is not a like-for-like efficiency saving. Prepaid B opening materials are excluded; paid lot rounding leaves $224,000 of B materials at year end.

Both plans serve 100%, produce the same annual product quantities and hire no crews. This selected V7 schedule retains December 17-19 qualification. V6 tracked warehouse peak was 1,063 pallets excluding B materials; V7 peak is 1,198 including B. V6 had four C-only procurement events; this V7 incumbent has five C plus five B events. Procurement timings change to accommodate tracked B stock with no extra monetary cost. Timing/allocation alternatives may exist.

## Solver bounds and termination

| name | status | termination | lower_bound | upper_bound | relative_gap | optimum | incumbent_objective | incumbent_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| service_H1 | ok | optimal | 0.00 | 0.00 | 0.00 | 0.00 | nan | nan |
| service_H2 | ok | optimal | 0.00 | 0.00 | 0.00 | 0.00 | nan | nan |
| service_H3 | ok | optimal | 0.00 | 0.00 | 0.00 | 0.00 | nan | nan |
| modeled_cost | ok | optimal | 9,865,467.50 | 9,865,467.50 | 0.00 | 9,865,467.50 | nan | nan |
| international_order_events | aborted | maxTimeLimit | 8.00 | 10.00 | 0.20 | nan | 10.00 | 0.20 |

## Limits and reproducibility

Packaging ages/expiry remain unverified; intramonth warehouse peaks are not fully established; C:D is diagnostic; arbitrary plant generalization and unsupported labor rates/caps are not added. No Scenario B or monetary tolerance is enabled. Historical source files, reports and saved records are unchanged.

Published files are a copy of reports/app_runs/v7_final_original_20261110, saved run ID fbf7d657d22141d4b70ab346a9aeb1a0; this publication is not another solve. Use python -m src.reporting --report-dir reports/v7 to regenerate reports without optimization. Use a fresh output directory for a new solve.

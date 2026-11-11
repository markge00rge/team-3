# Three-policy real Venus validation

All runs use identical original Venus numerical inputs and adopted B stocks. Only shipment policy differs. Each executes the real Pyomo/HiGHS model, with a 300-second per-stage limit; no historical result is presented as a fresh solve.

| policy | service_percent | minimum_monetary_usd | money_proven | international_shipments | material_order_lines | shipment_lower_bound | shipment_gap | shipment_termination | shipment_proven | peak_warehouse_pallets | external_storage_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| independent_materials | 100.00% | 9,865,467.50 | Proven | 10.00 | 10.00 | 5.00 | 50.00% | maxTimeLimit | Unproven | 1,198.00 | 0.00 |
| per_product | 100.00% | 9,865,467.50 | Proven | 6.00 | 12.00 | 4.00 | 33.33% | maxTimeLimit | Unproven | 1,198.00 | 0.00 |
| all_products | 100.00% | 9,865,467.50 | Proven | 4.00 | 14.00 | 1.00 | 75.00% | maxTimeLimit | Unproven | 1,198.00 | 0.00 |

All service and monetary optima agree. The shipment counts are feasible incumbents, not proven minima. Different group definitions do not establish physical container savings. Policy 3 assumes a common international consolidation hub; no container size or new freight cost is imposed. The historical independent-policy lower bound of 8 remains preserved separately; the table shows each fresh solve's actual bound, without replacing it.

The five financial figures retain the same definitions. Opening stocks/fixed receipts are not new purchases, and consolidating orders adds no cost term. Material stocks, lead times and warehouse constraints remain separate from batch grouping.

## Independent RM/PM Shipments

Actual new solve: `../v8_independent/`. All three service stages are proven optimal. Shipment status: `aborted` / `maxTimeLimit`. Later quantity/cleanup stages were not run because shipment optimality is unproven.

### Selected dispatch batches

| batch_id | policy | dispatch_month | arrival_month | products | materials | individual_quantities | rm_pallets | pm_pallets | material_pallets | purchase_cost_usd | material_order_lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B_PM_2026-10 | independent_materials | 2026-10 | 2027-01 | B | B PM | B PM: 1250000 | 0.00 | 250.00 | 250.00 | 500,000.00 | 1.00 |
| B_PM_2027-03 | independent_materials | 2027-03 | 2027-06 | B | B PM | B PM: 1125000 | 0.00 | 225.00 | 225.00 | 450,000.00 | 1.00 |
| B_RM_2026-10 | independent_materials | 2026-10 | 2027-01 | B | B RM | B RM: 200000 | 200.00 | 0.00 | 200.00 | 1,000,000.00 | 1.00 |
| B_RM_2027-01 | independent_materials | 2027-01 | 2027-04 | B | B RM | B RM: 200000 | 200.00 | 0.00 | 200.00 | 1,000,000.00 | 1.00 |
| B_RM_2027-03 | independent_materials | 2027-03 | 2027-06 | B | B RM | B RM: 350000 | 350.00 | 0.00 | 350.00 | 1,750,000.00 | 1.00 |
| C_PM_2026-11 | independent_materials | 2026-11 | 2027-02 | C | C PM | C PM: 1375000 | 0.00 | 275.00 | 275.00 | 550,000.00 | 1.00 |
| C_PM_2027-02 | independent_materials | 2027-02 | 2027-05 | C | C PM | C PM: 1625000 | 0.00 | 325.00 | 325.00 | 650,000.00 | 1.00 |
| C_RM_2026-10 | independent_materials | 2026-10 | 2027-01 | C | C RM | C RM: 200000 | 200.00 | 0.00 | 200.00 | 1,000,000.00 | 1.00 |
| C_RM_2027-02 | independent_materials | 2027-02 | 2027-05 | C | C RM | C RM: 200000 | 200.00 | 0.00 | 200.00 | 1,000,000.00 | 1.00 |
| C_RM_2027-03 | independent_materials | 2027-03 | 2027-06 | C | C RM | C RM: 150000 | 150.00 | 0.00 | 150.00 | 750,000.00 | 1.00 |

### Underlying material orders

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

### Monthly warehouse

| month | tracked_pallets | external_blocks | external_storage_usd |
| --- | --- | --- | --- |
| 2026-10 | 505.00 | 0.00 | 0.00 |
| 2026-11 | 470.00 | 0.00 | 0.00 |
| 2026-12 | 230.00 | 0.00 | 0.00 |
| 2027-01 | 805.00 | 0.00 | 0.00 |
| 2027-02 | 1,192.00 | 0.00 | 0.00 |
| 2027-03 | 1,144.00 | 0.00 | 0.00 |
| 2027-04 | 1,116.00 | 0.00 | 0.00 |
| 2027-05 | 1,157.00 | 0.00 | 0.00 |
| 2027-06 | 1,198.00 | 0.00 | 0.00 |
| 2027-07 | 550.00 | 0.00 | 0.00 |
| 2027-08 | 295.00 | 0.00 | 0.00 |
| 2027-09 | 110.00 | 0.00 | 0.00 |

### Financial reconciliation

| month | base_salaries_usd | new_crew_salaries_usd | hiring_fees_usd | a_rm_scrap_value_usd | a_pm_scrap_value_usd | a_rm_disposal_usd | a_pm_disposal_usd | fp_holding_usd | dedicated_transport_usd | spot_transport_usd | service_penalties_usd | external_storage_usd | total_modeled_cost_usd | dismissal_expense_usd | full_ide_usd | operating_full_ide_usd | ide_overlap_adjustment_usd | operating_expenses_usd | a_rm_order_usd | a_pm_order_usd | a_material_cost_usd | b_rm_order_usd | b_pm_order_usd | b_material_cost_usd | c_rm_order_usd | c_pm_order_usd | c_material_cost_usd | total_delivery_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ANNUAL | 840,000.00 | 0.00 | 0.00 | 0.00 | 30,000.00 | 0.00 | 300.00 | 56,167.50 | 272,200.00 | 16,800.00 | 0.00 | 0.00 | 9,865,467.50 | 0.00 | 30,300.00 | 1,215,467.50 | 0.00 | 1,215,467.50 | 0.00 | 0.00 | 0.00 | 3,750,000.00 | 950,000.00 | 4,700,000.00 | 2,750,000.00 | 1,200,000.00 | 3,950,000.00 | 9,865,467.50 |

Independent reconstruction: 13,376 constraints, 7,579 variables; maximum violation 1.3969839e-09. Passed. Monthly materials, production, service, costs and inventories remain in the run folder's CSVs.

## Consolidate Within Each Product

Actual new solve: `../v8_per_product/`. All three service stages are proven optimal. Shipment status: `aborted` / `maxTimeLimit`. Later quantity/cleanup stages were not run because shipment optimality is unproven.

### Selected dispatch batches

| batch_id | policy | dispatch_month | arrival_month | products | materials | individual_quantities | rm_pallets | pm_pallets | material_pallets | purchase_cost_usd | material_order_lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B_2026-10 | per_product | 2026-10 | 2027-01 | B | B RM, B PM | B RM: 300000; B PM: 625000 | 300.00 | 125.00 | 425.00 | 1,750,000.00 | 2.00 |
| B_2027-01 | per_product | 2027-01 | 2027-04 | B | B RM, B PM | B RM: 100000; B PM: 625000 | 100.00 | 125.00 | 225.00 | 750,000.00 | 2.00 |
| B_2027-03 | per_product | 2027-03 | 2027-06 | B | B RM, B PM | B RM: 350000; B PM: 1125000 | 350.00 | 225.00 | 575.00 | 2,200,000.00 | 2.00 |
| C_2026-11 | per_product | 2026-11 | 2027-02 | C | C RM, C PM | C RM: 200000; C PM: 1500000 | 200.00 | 300.00 | 500.00 | 1,600,000.00 | 2.00 |
| C_2027-02 | per_product | 2027-02 | 2027-05 | C | C RM, C PM | C RM: 200000; C PM: 250000 | 200.00 | 50.00 | 250.00 | 1,100,000.00 | 2.00 |
| C_2027-03 | per_product | 2027-03 | 2027-06 | C | C RM, C PM | C RM: 150000; C PM: 1250000 | 150.00 | 250.00 | 400.00 | 1,250,000.00 | 2.00 |

### Underlying material orders

| product | material | unit | order_month | arrival_month | quantity | integer_lots | order_event | unit_price_usd | purchase_expense_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | RM | kg | 2026-10 | 2027-01 | 300,000.00 | 6.00 | 1.00 | 5.00 | 1,500,000.00 |
| B | RM | kg | 2027-01 | 2027-04 | 100,000.00 | 2.00 | 1.00 | 5.00 | 500,000.00 |
| B | RM | kg | 2027-03 | 2027-06 | 350,000.00 | 7.00 | 1.00 | 5.00 | 1,750,000.00 |
| B | PM | EA | 2026-10 | 2027-01 | 625,000.00 | 5.00 | 1.00 | 0.40 | 250,000.00 |
| B | PM | EA | 2027-01 | 2027-04 | 625,000.00 | 5.00 | 1.00 | 0.40 | 250,000.00 |
| B | PM | EA | 2027-03 | 2027-06 | 1,125,000.00 | 9.00 | 1.00 | 0.40 | 450,000.00 |
| C | RM | kg | 2026-11 | 2027-02 | 200,000.00 | 4.00 | 1.00 | 5.00 | 1,000,000.00 |
| C | RM | kg | 2027-02 | 2027-05 | 200,000.00 | 4.00 | 1.00 | 5.00 | 1,000,000.00 |
| C | RM | kg | 2027-03 | 2027-06 | 150,000.00 | 3.00 | 1.00 | 5.00 | 750,000.00 |
| C | PM | EA | 2026-11 | 2027-02 | 1,500,000.00 | 12.00 | 1.00 | 0.40 | 600,000.00 |
| C | PM | EA | 2027-02 | 2027-05 | 250,000.00 | 2.00 | 1.00 | 0.40 | 100,000.00 |
| C | PM | EA | 2027-03 | 2027-06 | 1,250,000.00 | 10.00 | 1.00 | 0.40 | 500,000.00 |

### Monthly warehouse

| month | tracked_pallets | external_blocks | external_storage_usd |
| --- | --- | --- | --- |
| 2026-10 | 505.00 | 0.00 | 0.00 |
| 2026-11 | 470.00 | 0.00 | 0.00 |
| 2026-12 | 230.00 | 0.00 | 0.00 |
| 2027-01 | 580.00 | 0.00 | 0.00 |
| 2027-02 | 1,192.00 | 0.00 | 0.00 |
| 2027-03 | 1,144.00 | 0.00 | 0.00 |
| 2027-04 | 1,141.00 | 0.00 | 0.00 |
| 2027-05 | 907.00 | 0.00 | 0.00 |
| 2027-06 | 1,198.00 | 0.00 | 0.00 |
| 2027-07 | 550.00 | 0.00 | 0.00 |
| 2027-08 | 295.00 | 0.00 | 0.00 |
| 2027-09 | 110.00 | 0.00 | 0.00 |

### Financial reconciliation

| month | base_salaries_usd | new_crew_salaries_usd | hiring_fees_usd | a_rm_scrap_value_usd | a_pm_scrap_value_usd | a_rm_disposal_usd | a_pm_disposal_usd | fp_holding_usd | dedicated_transport_usd | spot_transport_usd | service_penalties_usd | external_storage_usd | total_modeled_cost_usd | dismissal_expense_usd | full_ide_usd | operating_full_ide_usd | ide_overlap_adjustment_usd | operating_expenses_usd | a_rm_order_usd | a_pm_order_usd | a_material_cost_usd | b_rm_order_usd | b_pm_order_usd | b_material_cost_usd | c_rm_order_usd | c_pm_order_usd | c_material_cost_usd | total_delivery_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ANNUAL | 840,000.00 | 0.00 | 0.00 | 0.00 | 30,000.00 | 0.00 | 300.00 | 56,167.50 | 272,200.00 | 16,800.00 | 0.00 | 0.00 | 9,865,467.50 | 0.00 | 30,300.00 | 1,215,467.50 | 0.00 | 1,215,467.50 | 0.00 | 0.00 | 0.00 | 3,750,000.00 | 950,000.00 | 4,700,000.00 | 2,750,000.00 | 1,200,000.00 | 3,950,000.00 | 9,865,467.50 |

Independent reconstruction: 13,484 constraints, 7,615 variables; maximum violation 8.1490725e-10. Passed. Monthly materials, production, service, costs and inventories remain in the run folder's CSVs.

## Consolidate All Products

Actual new solve: `../v8_all_products/`. All three service stages are proven optimal. Shipment status: `aborted` / `maxTimeLimit`. Later quantity/cleanup stages were not run because shipment optimality is unproven.

### Selected dispatch batches

| batch_id | policy | dispatch_month | arrival_month | products | materials | individual_quantities | rm_pallets | pm_pallets | material_pallets | purchase_cost_usd | material_order_lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_2026-10 | all_products | 2026-10 | 2027-01 | B, C | B RM, B PM, C RM, C PM | B RM: 250000; B PM: 875000; C RM: 150000; C PM: 500000 | 400.00 | 275.00 | 675.00 | 2,550,000.00 | 4.00 |
| ALL_2026-12 | all_products | 2026-12 | 2027-03 | B, C | B RM, C RM, C PM | B RM: 50000; C RM: 50000; C PM: 1000000 | 100.00 | 200.00 | 300.00 | 900,000.00 | 3.00 |
| ALL_2027-02 | all_products | 2027-02 | 2027-05 | B, C | B RM, B PM, C RM, C PM | B RM: 100000; B PM: 375000; C RM: 100000; C PM: 1500000 | 200.00 | 375.00 | 575.00 | 1,750,000.00 | 4.00 |
| ALL_2027-03 | all_products | 2027-03 | 2027-06 | B, C | B RM, B PM, C RM | B RM: 350000; B PM: 1125000; C RM: 250000 | 600.00 | 225.00 | 825.00 | 3,450,000.00 | 3.00 |

### Underlying material orders

| product | material | unit | order_month | arrival_month | quantity | integer_lots | order_event | unit_price_usd | purchase_expense_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | RM | kg | 2026-10 | 2027-01 | 250,000.00 | 5.00 | 1.00 | 5.00 | 1,250,000.00 |
| B | RM | kg | 2026-12 | 2027-03 | 50,000.00 | 1.00 | 1.00 | 5.00 | 250,000.00 |
| B | RM | kg | 2027-02 | 2027-05 | 100,000.00 | 2.00 | 1.00 | 5.00 | 500,000.00 |
| B | RM | kg | 2027-03 | 2027-06 | 350,000.00 | 7.00 | 1.00 | 5.00 | 1,750,000.00 |
| B | PM | EA | 2026-10 | 2027-01 | 875,000.00 | 7.00 | 1.00 | 0.40 | 350,000.00 |
| B | PM | EA | 2027-02 | 2027-05 | 375,000.00 | 3.00 | 1.00 | 0.40 | 150,000.00 |
| B | PM | EA | 2027-03 | 2027-06 | 1,125,000.00 | 9.00 | 1.00 | 0.40 | 450,000.00 |
| C | RM | kg | 2026-10 | 2027-01 | 150,000.00 | 3.00 | 1.00 | 5.00 | 750,000.00 |
| C | RM | kg | 2026-12 | 2027-03 | 50,000.00 | 1.00 | 1.00 | 5.00 | 250,000.00 |
| C | RM | kg | 2027-02 | 2027-05 | 100,000.00 | 2.00 | 1.00 | 5.00 | 500,000.00 |
| C | RM | kg | 2027-03 | 2027-06 | 250,000.00 | 5.00 | 1.00 | 5.00 | 1,250,000.00 |
| C | PM | EA | 2026-10 | 2027-01 | 500,000.00 | 4.00 | 1.00 | 0.40 | 200,000.00 |
| C | PM | EA | 2026-12 | 2027-03 | 1,000,000.00 | 8.00 | 1.00 | 0.40 | 400,000.00 |
| C | PM | EA | 2027-02 | 2027-05 | 1,500,000.00 | 12.00 | 1.00 | 0.40 | 600,000.00 |

### Monthly warehouse

| month | tracked_pallets | external_blocks | external_storage_usd |
| --- | --- | --- | --- |
| 2026-10 | 505.00 | 0.00 | 0.00 |
| 2026-11 | 470.00 | 0.00 | 0.00 |
| 2026-12 | 230.00 | 0.00 | 0.00 |
| 2027-01 | 830.00 | 0.00 | 0.00 |
| 2027-02 | 942.00 | 0.00 | 0.00 |
| 2027-03 | 1,194.00 | 0.00 | 0.00 |
| 2027-04 | 966.00 | 0.00 | 0.00 |
| 2027-05 | 1,057.00 | 0.00 | 0.00 |
| 2027-06 | 1,198.00 | 0.00 | 0.00 |
| 2027-07 | 550.00 | 0.00 | 0.00 |
| 2027-08 | 295.00 | 0.00 | 0.00 |
| 2027-09 | 110.00 | 0.00 | 0.00 |

### Financial reconciliation

| month | base_salaries_usd | new_crew_salaries_usd | hiring_fees_usd | a_rm_scrap_value_usd | a_pm_scrap_value_usd | a_rm_disposal_usd | a_pm_disposal_usd | fp_holding_usd | dedicated_transport_usd | spot_transport_usd | service_penalties_usd | external_storage_usd | total_modeled_cost_usd | dismissal_expense_usd | full_ide_usd | operating_full_ide_usd | ide_overlap_adjustment_usd | operating_expenses_usd | a_rm_order_usd | a_pm_order_usd | a_material_cost_usd | b_rm_order_usd | b_pm_order_usd | b_material_cost_usd | c_rm_order_usd | c_pm_order_usd | c_material_cost_usd | total_delivery_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ANNUAL | 840,000.00 | 0.00 | 0.00 | 0.00 | 30,000.00 | 0.00 | 300.00 | 56,167.50 | 272,200.00 | 16,800.00 | 0.00 | 0.00 | 9,865,467.50 | 0.00 | 30,300.00 | 1,215,467.50 | 0.00 | 1,215,467.50 | 0.00 | 0.00 | 0.00 | 3,750,000.00 | 950,000.00 | 4,700,000.00 | 2,750,000.00 | 1,200,000.00 | 3,950,000.00 | 9,865,467.50 |

Independent reconstruction: 13,460 constraints, 7,591 variables; maximum violation 1.3969839e-09. Passed. Monthly materials, production, service, costs and inventories remain in the run folder's CSVs.

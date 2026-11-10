# Independent monthly financial reconciliation

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

Computed from unrounded solver quantities and loader rates, independently of model expressions. Salaries = employed operators x monthly wage, hiring = new operators x hiring fee; FP holding = ending MSU x individual product value x holding rate; transport = integer trucks x hub rate (spot x 1.6); penalty = unserved MSU x hub penalty; storage = blocks x 100 x $45. RM IDE = scrap kg x ($5 + $200/1000); PM IDE = scrap EA x ($0.40 + 0.02 x $200/1000). No material purchase cost, inventory-value expense or intermediate rounding.

{
  "annual_costs": {
    "labor": 840000.0,
    "fp_holding": 56167.50000000001,
    "transportation": 289000.0,
    "ide": 30300.000000000455,
    "service_failure": 0.0,
    "external_storage": 0.0,
    "total_modeled": 1215467.5000000005
  },
  "holding_by_product": {
    "A": 7.673861546209082e-12,
    "B": 7342.500000000027,
    "C": 48824.99999999996
  },
  "opening_basis_holding_usd": 58005.0,
  "ending_basis_holding_usd": 56167.50000000001,
  "annual_ending_only_holding_usd": 1.7905676941154525e-12,
  "all_fp_at_c_value_holding_usd": 54432.0,
  "ac_stock_at_a_value_holding_usd": 53842.5,
  "rounded_integer_msu_holding_usd": 56167.5,
  "residual_vs_reported_usd": 0.0,
  "residual_vs_proven_minimum_usd": 4.656612873077393e-10,
  "monthly_ending_inventory_sum_msu": 864.0
}
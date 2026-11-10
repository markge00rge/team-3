# V5 strict Scenario A: operational and financial reconciliation

Monetary termination: **optimal**; minimum $1,215,467.50. All-stage optimality: **True**. Secondary status is not a monetary proof.

## Solver stages

| name | status | termination | lower_bound | upper_bound | relative_gap | optimum |
| --- | --- | --- | --- | --- | --- | --- |
| service_H1 | ok | optimal | 0.00 | 0.00 | 0.00 | 0.00 |
| service_H2 | ok | optimal | 0.00 | 0.00 | 0.00 | 0.00 |
| service_H3 | ok | optimal | 0.00 | 0.00 | 0.00 | 0.00 |
| modeled_cost | ok | optimal | 1,215,467.50 | 1,215,467.50 | 0.00 | 1,215,467.50 |
| international_order_events | ok | optimal | 4.00 | 4.00 | 0.00 | 4.00 |
| procurement_quantity_tiebreak | ok | optimal | 2,300.00 | 2,300.00 | 0.00 | 2,300.00 |
| cost_cleanup | ok | optimal | 1,215,467.50 | 1,215,467.50 | 0.00 | 1,215,467.50 |

## 1. Capacity and manufacturing plan

| month | available_capacity_msu | cumulative_capacity_msu | total_production_msu | cumulative_supply_msu | cumulative_demand_msu | capacity_to_demand | supply_to_demand | monthly_service_fraction | cumulative_service_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | 304.00 | 304.00 | 165.00 | 190.00 | 190.00 | 1.60 | 1.00 | 1.00 | 1.00 |
| 2026-11 | 304.00 | 608.00 | 185.00 | 375.00 | 375.00 | 1.62 | 1.00 | 1.00 | 1.00 |
| 2026-12 | 262.00 | 870.00 | 225.00 | 600.00 | 600.00 | 1.45 | 1.00 | 1.00 | 1.00 |
| 2027-01 | 304.00 | 1,174.00 | 215.00 | 815.00 | 780.00 | 1.51 | 1.04 | 1.00 | 1.00 |
| 2027-02 | 304.00 | 1,478.00 | 304.00 | 1,119.00 | 980.00 | 1.51 | 1.14 | 1.00 | 1.00 |
| 2027-03 | 304.00 | 1,782.00 | 304.00 | 1,423.00 | 1,220.00 | 1.46 | 1.17 | 1.00 | 1.00 |
| 2027-04 | 304.00 | 2,086.00 | 304.00 | 1,727.00 | 1,505.00 | 1.39 | 1.15 | 1.00 | 1.00 |
| 2027-05 | 312.00 | 2,398.00 | 312.00 | 2,039.00 | 1,860.00 | 1.29 | 1.10 | 1.00 | 1.00 |
| 2027-06 | 312.00 | 2,710.00 | 312.00 | 2,351.00 | 2,265.00 | 1.20 | 1.04 | 1.00 | 1.00 |
| 2027-07 | 304.00 | 3,014.00 | 304.00 | 2,655.00 | 2,655.00 | 1.14 | 1.00 | 1.00 | 1.00 |
| 2027-08 | 304.00 | 3,318.00 | 255.00 | 2,910.00 | 2,910.00 | 1.14 | 1.00 | 1.00 | 1.00 |
| 2027-09 | 312.00 | 3,630.00 | 185.00 | 3,095.00 | 3,095.00 | 1.17 | 1.00 | 1.00 | 1.00 |

Capacity is physically available line-day capacity after qualification/changeovers and training. Production is actual manufacturing. Supply includes initial FP once; shipments are actual customer deliveries. Ratios below one are flagged in cumulative_indicators.csv. Zero-demand ratios are undefined, not zero. Both C:D interpretations are diagnostics, not feasibility constraints; full service alone does not prove both ratios exceed one.

## 2. Transition and IDE

```json
{
  "qualification_start": {
    "month": "2026-12",
    "planning_day": 10,
    "horizon_day": 66
  },
  "shutdown_days": [
    {
      "month": "2026-12",
      "planning_day": 10,
      "horizon_day": 66
    },
    {
      "month": "2026-12",
      "planning_day": 11,
      "horizon_day": 67
    },
    {
      "month": "2026-12",
      "planning_day": 12,
      "horizon_day": 68
    }
  ],
  "c_first_production": {
    "month": "2026-12",
    "planning_day": 15,
    "horizon_day": 71
  },
  "a_last_production": {
    "month": "2026-12",
    "planning_day": 9,
    "horizon_day": 65
  },
  "a_fp_sellthrough_later_months_msu": 0.0,
  "a_fp_shipments_in_transition_month_msu": 79.99999999999974,
  "a_rm_consumed_before_kg": 114999.99999999978,
  "a_pm_consumed_before_ea": 574999.9999999988,
  "a_rm_before_scrap_kg": 0.0,
  "a_pm_before_scrap_ea": 75000.00000000112,
  "a_rm_scrap_kg": 0.0,
  "a_pm_scrap_ea": 75000.00000000112,
  "rm_scrap_value_usd": 0.0,
  "pm_scrap_value_usd": 30000.00000000045,
  "rm_disposal_usd": 0.0,
  "pm_disposal_usd": 300.00000000000443,
  "total_ide_usd": 30300.000000000455,
  "base_salary_usd": 840000.0,
  "new_salary_usd": 0.0,
  "hiring_usd": 0.0,
  "initial_l2_configuration": "A"
}
```

## 3. Inventory, cash and warehouse

| month | ending_fp_value_usd | cash_tied_up_fp_usd | tracked_ac_material_value_usd | working_capital_holding_expense_usd |
| --- | --- | --- | --- | --- |
| 2026-10 | 0.00 | 0.00 | 722,500.00 | 0.00 |
| 2026-11 | 0.00 | 0.00 | 1,210,000.00 | 0.00 |
| 2026-12 | 0.00 | 0.00 | 812,500.00 | 0.00 |
| 2027-01 | 153,500.00 | 153,500.00 | 2,660,000.00 | 2,302.50 |
| 2027-02 | 589,000.00 | 589,000.00 | 1,960,000.00 | 8,835.00 |
| 2027-03 | 857,800.00 | 857,800.00 | 1,316,000.00 | 12,867.00 |
| 2027-04 | 938,900.00 | 938,900.00 | 728,000.00 | 14,083.50 |
| 2027-05 | 793,400.00 | 793,400.00 | 758,000.00 | 11,901.00 |
| 2027-06 | 411,900.00 | 411,900.00 | 1,588,000.00 | 6,178.50 |
| 2027-07 | 0.00 | 0.00 | 1,000,000.00 | 0.00 |
| 2027-08 | 0.00 | 0.00 | 527,500.00 | 0.00 |
| 2027-09 | 0.00 | 0.00 | 230,000.00 | 0.00 |

Inventory value is a balance-sheet KPI and is not added to expenses. FP holding is 1.5% of product-specific ending value. A/C RM/PM valuation uses source $5/kg and $0.40/EA. B physical material value/space is unspecified and excluded. Month-end storage is constrained; intramonth peaks are not verified. See storage_peaks.csv for a conservative dispatch diagnostic.

## 4. Regional service and distribution

service.csv separates hub/family/month demand, shipments and shortages; transport.csv shows dedicated/spot trucks. Exact monthly priorities apply separately to A/C and B, including every higher/lower regional pair.

## 5. Annual costs and comparison

| metric | v4 | v5 | difference |
| --- | --- | --- | --- |
| labor | 840,000.00 | 840,000.00 | 0.00 |
| fp_holding | 56,167.50 | 56,167.50 | 0.00 |
| transportation | 289,000.00 | 289,000.00 | 0.00 |
| service_failure | 0.00 | 0.00 | 0.00 |
| ide | 30,300.00 | 30,300.00 | 0.00 |
| external_storage | 0.00 | 0.00 | 0.00 |
| total_modeled | 1,215,467.50 | 1,215,467.50 | 0.00 |

## Monthly production / inventory

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

## Monthly financial reconciliation (USD)

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

## Productivity

| month | line | scheduled_days | available_days | actual_manufacturing_days | equivalent_full_rate_days | qualification_days | changeover_days | available_capacity_msu | production_msu | capacity_utilization | hired_crew | training | upgraded | upgrade_theoretical_gain_msu | employed_operators |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10 | L1 | 20.00 | 20.00 | 10.00 | 10.00 | 0.00 | 0.00 | 120.00 | 60.00 | 0.50 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2026-11 | L1 | 20.00 | 20.00 | 13.00 | 12.50 | 0.00 | 0.00 | 120.00 | 75.00 | 0.62 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2026-12 | L1 | 20.00 | 17.00 | 12.00 | 11.17 | 3.00 | 0.00 | 102.00 | 67.00 | 0.66 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-01 | L1 | 20.00 | 20.00 | 20.00 | 19.17 | 0.00 | 0.00 | 120.00 | 115.00 | 0.96 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-02 | L1 | 20.00 | 20.00 | 20.00 | 20.00 | 0.00 | 0.00 | 120.00 | 120.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-03 | L1 | 20.00 | 20.00 | 20.00 | 20.00 | 0.00 | 0.00 | 120.00 | 120.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-04 | L1 | 20.00 | 20.00 | 20.00 | 20.00 | 0.00 | 0.00 | 120.00 | 120.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-05 | L1 | 20.00 | 20.00 | 20.00 | 20.00 | 0.00 | 0.00 | 120.00 | 120.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-06 | L1 | 20.00 | 20.00 | 20.00 | 20.00 | 0.00 | 0.00 | 120.00 | 120.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-07 | L1 | 20.00 | 20.00 | 20.00 | 20.00 | 0.00 | 0.00 | 120.00 | 120.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-08 | L1 | 20.00 | 20.00 | 20.00 | 19.83 | 0.00 | 0.00 | 120.00 | 119.00 | 0.99 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2027-09 | L1 | 20.00 | 20.00 | 15.00 | 14.17 | 0.00 | 0.00 | 120.00 | 85.00 | 0.71 | 0.00 | 0.00 | 0.00 | 0.00 | 30.00 |
| 2026-10 | L2 | 24.00 | 23.00 | 14.00 | 13.12 | 0.00 | 1.00 | 184.00 | 105.00 | 0.57 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2026-11 | L2 | 24.00 | 23.00 | 14.00 | 13.75 | 0.00 | 1.00 | 184.00 | 110.00 | 0.60 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2026-12 | L2 | 24.00 | 20.00 | 20.00 | 19.75 | 3.00 | 1.00 | 160.00 | 158.00 | 0.99 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-01 | L2 | 24.00 | 23.00 | 13.00 | 12.50 | 0.00 | 1.00 | 184.00 | 100.00 | 0.54 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-02 | L2 | 24.00 | 23.00 | 23.00 | 23.00 | 0.00 | 1.00 | 184.00 | 184.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-03 | L2 | 24.00 | 23.00 | 23.00 | 23.00 | 0.00 | 1.00 | 184.00 | 184.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-04 | L2 | 24.00 | 23.00 | 23.00 | 23.00 | 0.00 | 1.00 | 184.00 | 184.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-05 | L2 | 24.00 | 24.00 | 24.00 | 24.00 | 0.00 | 0.00 | 192.00 | 192.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-06 | L2 | 24.00 | 24.00 | 24.00 | 24.00 | 0.00 | 0.00 | 192.00 | 192.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-07 | L2 | 24.00 | 23.00 | 23.00 | 23.00 | 0.00 | 1.00 | 184.00 | 184.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-08 | L2 | 24.00 | 23.00 | 17.00 | 17.00 | 0.00 | 1.00 | 184.00 | 136.00 | 0.74 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |
| 2027-09 | L2 | 24.00 | 24.00 | 13.00 | 12.50 | 0.00 | 0.00 | 192.00 | 100.00 | 0.52 | 0.00 | 0.00 | 0.00 | 0.00 | 40.00 |

Available-day utilization is production/capacity. Manufacturing days count days with positive output; equivalent full-rate days account for partial days. MSU per employed operator includes paid trainees and is a separate labor KPI.

## Assumptions and reproduction

See ../../ASSUMPTIONS.md and ../../FINAL_OPTIMIZER_READINESS.md. Packaging usability is unverified; no detailed expiry. No overtime/headcount ceiling is invented. No material purchase expense or daily customer dispatch is introduced.

`python -m src.reporting --report-dir reports/v5` regenerates these derived reports without solving. `python -m src.solve --output-dir reports/v5 --time-limit 180` rebuilds and solves strict Scenario A.

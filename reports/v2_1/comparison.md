# V2.1 strict-cost versus 2% consolidation sensitivity

Both scenarios solved all service, cost, event and quantity stages to optimality.

| Metric | Scenario A: zero tolerance | Scenario B: 2% tolerance |
| --- | ---: | ---: |
| labor USD | 840,000.0000 | 840,000.0000 |
| fp_holding USD | 58,987.5000 | 59,670.0000 |
| transportation USD | 285,000.0000 | 285,000.0000 |
| service_failure USD | 30,000.0000 | 30,000.0000 |
| external_storage USD | 0.0000 | 18,000.0000 |
| total_modeled USD | 1,213,987.5000 | 1,232,670.0000 |
| Minimum monetary cost USD | 1,213,987.5000 | 1,213,987.5000 |
| Allowed cost ceiling USD | 1,213,987.5000 | 1,238,267.2500 |
| Additional material-specific events | 4.0000 | 3.0000 |
| Fixed incoming shipments (separate) | 3.0000 | 3.0000 |
| Served MSU | 3,070.0000 | 3,070.0000 |
| Service % | 99.1922 | 99.1922 |
| External block-months | 0.0000 | 4.0000 |
| Peak tracked month-end pallets | 1,197.0000 | 1,372.0000 |
| Additional A RM total (kg/EA) | 0.0000 | 0.0000 |
| Year-end A RM (kg/EA) | 0.0000 | 0.0000 |
| Additional A PM total (kg/EA) | 0.0000 | 0.0000 |
| Year-end A PM (kg/EA) | 75,000.0000 | 75,000.0000 |
| Additional C RM total (kg/EA) | 500,000.0000 | 500,000.0000 |
| Year-end C RM (kg/EA) | 2,500.0000 | 2,500.0000 |
| Additional C PM total (kg/EA) | 2,875,000.0000 | 2,875,000.0000 |
| Year-end C PM (kg/EA) | 12,500.0000 | 12,500.0000 |

The more consolidated plan adds $18,682.50 in total modeled cost, including $18,000.00 in external storage. This expense is induced by the consolidated procurement plan; Scenario A needs no paid overflow for this case.

The final cost cleanup removes gratuitous spending after event count and procurement quantity are fixed. Alternative monthly schedules can remain optimal.

Each scenario folder contains summary.txt plus CSVs for hub/month service, production, orders and arrival months, material balances, warehouse blocks/costs, fixed receipts and B theoretical usage.

B physical material footprint is unspecified/excluded, not zero. Month-end storage does not verify intramonth peaks. IDE, expiry, optimized hiring/qualification and daily sequencing remain omitted; see ../../MODEL_SCOPE.md.

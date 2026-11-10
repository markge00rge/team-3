# Central active assumptions register — V6 strict Scenario A

This register describes the current model. Historical V2/V2.1 documentation
does not override it. Original Word/Excel inputs are read only.

| Topic | Accepted treatment | Verification / limitation |
| --- | --- | --- |
| Calendar | Each month has four weeks, 28 planning days; weekdays repeat 1–7. Profiles 24/5, 24/6, 24/7 provide 20, 24, 28 scheduled days. | Not Gregorian capacity. Loader now extracts four from `1 Month = 4 Weeks`, correcting an unused V4 metadata parsing error. |
| Receipts | Original three arrivals unchanged; receipts at start of planning day 1. Additional orders arrive three month indices after placement. No invented pre-horizon orders. | September-to-October source contradiction remains; it does not override new-order lead time. |
| Demand | One pooled A/C family and a separate B family per hub/month. Annual hub lexicographic objectives plus exact monthly priorities within each family. | Every higher/lower pair is enforced, including a zero-demand middle hub. No family-to-family priority is invented. |
| Service | Same-month delivery, lost sales rather than backlog; no hub stock, early customer delivery or detailed daily dispatch. | Transportation remains integer trucks with 5 MSU capacity and separate destinations. |
| Transition | Qualification once, consecutive common base working days; A production stops permanently at start; C starts after completion. | No hard January deadline or extra qualification fee. |
| A finished goods | Existing A FP can sell through after transition to satisfy pooled A/C demand. | No unsupported A finished-goods sales deadline or automatic FP scrap. |
| A materials | All usable A RM/PM is scrapped at qualification start after preceding daily consumption. Receipts on that start day are included; later A receipts prohibited. | Exact daily conservation; no substitution to C, no material disappearance. IDE includes material value plus disposal. |
| Procurement lots | RM 50,000 kg and PM 125,000 EA for both A and C. | Extending original phase-out lots to C is an explicit accepted policy. Fixed receipts are not rounded. |
| Consolidation | One separate binary event per product/material/order month; several lots may share it. | No assumed common RM/PM physical shipment; fixed receipts reported separately; no fictitious freight fee. |
| B materials | Smooth replenishment according to production; theoretical BOM usage reported. | Physical B RM/PM stocks and their value/warehouse footprint are unspecified and excluded, **not physically zero**. No invented stock cover. |
| Packaging | Packaging is assumed usable over the relevant planning period. No batch aging or expiry constraints. | **Unverified assumption**: source shelf life is one year, opening ages unavailable. |
| Warehouse | End-of-month ABC FP and AC RM/PM tracked against 1,200 pallets plus integer 100-pallet blocks at $45/pallet/month. | Intramonth peaks not independently established. Conservative end-month-dispatch diagnostic is not an imposed dispatch schedule or additional storage charge. |
| L2 sequence | Configuration carries through weekends, idleness and month ends; one scheduled production-day routine switch at most per month. Only A→C at qualification start is exempt. | Opening A/B configuration is unspecified and freely selected once. No double downtime. |
| Staffing | Optional one ten-person crew per line, configurable complete paid training months, activation after training; optional dismissal and rehire with repeated fees/retraining; no pre-horizon training. | Only supported profile upgrades modeled. Unknown headcount ceiling/overtime rates are not invented. Default dismissal expense $0/operator is a new configurable assumption; base 70 workers remain permanent. No overtime or extra training fees. |
| Costs | Salaries, hiring, FP holding, transport, service failure, external storage and four IDE components. | New A/C orders are charged on placement; B materials on actual production. Opening stocks and fixed receipts excluded. Full IDE reported; exact newly purchased A scrap-value overlap is subtracted once under legacy-first consumption. Inventory cash is not another expense. No RM/PM carrying cost. |
| Terminal policy | No source-supported terminal stock target, salvage or future demand. No orders arriving outside horizon. | Positive nonmonetary quantity tie-break minimizes unnecessary procurement only after earlier objectives are proven. |
| C:D | Report both cumulative available capacity/demand and (opening FP + cumulative actual production)/demand. | Diagnostics only. Source numerator insufficiently formal; do not impose a third definition or infer both ≥1 from full service. Zero-demand ratios are undefined. |
| Numerical proof | Zero requested absolute/relative MILP gaps; stop lexicographic progression at an unproven stage. | Feasibility audit is not proof of optimality. A proven monetary-optimal plan can be published with an explicitly unproven secondary count. |

These accepted simplifications support an editable backend; they do not establish
complete real-world physical feasibility. See DATA_REVIEW.md for source provenance
and FINAL_OPTIMIZER_READINESS.md for constraint/test traceability.

V6 provenance: original A opening/fixed stocks precede additional receipts. Legacy-first consumption makes newly purchased A scrap min(total A scrap, new A purchases). Its book value overlap is adjusted once; disposal remains charged. Six product-specific prices are editable. See V6_SCOPE.md.

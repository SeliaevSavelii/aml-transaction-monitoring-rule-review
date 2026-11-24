# Release sign-off checklist: R2 / R1 scenario change

Use with the [decision proposal](02_decision_proposal.md). Each item needs an owner and evidence before go-live.

## Before go-live

| # | Check | Owner | Evidence |
|---|---|---|---|
| 1 | Decision recorded (option and accepted detection impact) | Compliance | Signed decision note |
| 2 | Change specification approved (rule logic, parameters, alert unit) | Data science, AML experts | Specification document |
| 3 | Open findings that affect the change are closed or accepted (F-002, F-003, F-008, F-010, F-011) | Analytics translator | Findings log |
| 4 | Code reviewed and unit-tested, including the test cases from the specification | Engineering | Pull request, test report |
| 5 | Back-test on at least 6 months of history matches the expected alert volume (within ±10%) and precision | Data science | Back-test report |
| 6 | R1 has 182 days of transaction history available at go-live | Engineering | Data availability check |
| 7 | Parallel run of 4–8 weeks completed; differences between old and new alerts explained | Data science, investigations | Parallel-run report |
| 8 | Investigations team briefed on the new alert reasons and expected volumes | Investigations lead | Briefing notes |
| 9 | Rule documentation and model inventory updated | Analytics translator | Updated documents |
| 10 | Rollback plan tested (switch back to old parameters) | Engineering | Rollback test |
| 11 | Approvals recorded | Model owner, compliance | Sign-off record |

## Go-live

| # | Check | Owner |
|---|---|---|
| 12 | Deployed in a planned release window; first alert run checked manually | Engineering, data science |
| 13 | Alert volume of the first week compared with the back-test | Data science |

## After go-live

| # | What to monitor | Expected (option E) | Action if outside range |
|---|---|---|---|
| 14 | R2 alerts per month | about 9,400 (−44%) | Investigate if more than 20% above or below |
| 15 | R1 alerts per month | about 13,300 | Same |
| 16 | Share of alerts escalated after review | above the current level | Review with investigations if lower |
| 17 | Review after 3 months: volumes, precision, feedback from investigators | – | Report to decision makers; close or reopen the change |

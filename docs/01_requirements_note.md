# Requirements note: review of the rapid pass-through scenario

Status: draft for comment · Author: Savelii Seliaev · 24 November 2026
This is a simulated request on synthetic data (SAML-D). All thresholds and assumptions are illustrative, not real bank or regulatory values.

## Request

Investigators report that the rapid pass-through scenario (R2) produces many alerts that turn out to be normal activity, and ask whether its thresholds can be tightened. Compliance needs to know which laundering patterns would then no longer be caught, and whether other scenarios cover them.

**Question for this review:** can R2 produce clearly fewer alerts while still catching the laundering patterns it is meant for, and if not, which combination of changes gives the best balance?

## Stakeholders

| Who | What they need from this review |
|---|---|
| Investigators | Fewer alerts, a higher share of real cases, a clear reason for each alert |
| AML / compliance experts | Coverage of key laundering patterns, a documented rationale, a decision on acceptable detection loss |
| Data scientists | A precise change specification and test results |
| Engineers / DevOps | An implementable change with a test and rollback plan |
| Product owner | Priority, effort and timeline |

## Scope

- **In:** three scenarios, threshold changes only: R1 below-threshold inflows (structuring, smurfing), R2 rapid pass-through, R3 large or widely spread cross-border payments.
- **Out:** new scenarios, machine-learning models, customer risk scoring, case-handling process.

## Definitions

- **Alert:** one account flagged by one scenario in one calendar week; repeated hits in the same week count once.
- **True alert:** laundering appears in the activity the rule checks: for R1 a laundering payment into the account within its lookback, for R2 any laundering transaction of the account in the alert week, for R3 a laundering cross-border payment from the account in the alert week (finding F-010).
- **Precision:** true alerts ÷ all alerts.
- **Detection:** share of the 7,902 laundering accounts that receive at least one true alert in the period; also reported per laundering type. Whether to count every account in a scheme or only the collecting account is open (finding F-008).
- **Workload:** alerts × review minutes per alert, in hours and FTE.

## Success criteria (proposed, to be agreed)

1. R2 alert volume down by at least 30%.
2. Overall detection down by at most 2 percentage points; no key laundering type loses more than 5 points unless another scenario covers it.
3. Results stable from month to month.

## Open questions and working assumptions

| # | Question | Who to ask | Working assumption |
|---|---|---|---|
| 1 | Average review time per alert? | Investigations lead | 20 minutes; 1 FTE = 120 review hours per month |
| 2 | Which laundering types are "must catch"? | AML experts | Deposit-Send, layered fan-in/fan-out, structuring, smurfing |
| 3 | How much detection loss is acceptable for fewer alerts? | Compliance (risk appetite) | At most 2 points overall |
| 4 | Which locations count as higher-risk for R3? | Compliance (official list) | No list available; R3 uses all cross-border payments, because a list derived from this data's laundering labels would be circular (F-006) |
| 5 | What lookback window per scenario? | Data scientists, AML experts | R1 at least 90 days, because structuring spreads over about 6 months (F-004); R2 and R3 7 days |
| 6 | Is "one alert per account per week" the right unit for case handling? | Investigations lead | Yes |

## Data

SAML-D: 9.5 million transactions from 7 October 2022 to 23 August 2023; 0.10% laundering, 17 laundering types and 11 normal behaviours that resemble them. Data issues are tracked in `04_findings_log.csv`.

# Decision proposal: changing the rapid pass-through scenario (R2)

Status: for decision · Author: Savelii Seliaev · 24 November 2026
Simulated case on synthetic data (SAML-D). Thresholds and workload figures are illustrative, not real bank or regulatory values. Background and definitions: [requirements note](01_requirements_note.md).

## Background

Investigators asked whether the rapid pass-through scenario (R2) can produce fewer alerts. Today R2 creates about 13,800 alerts a month, the most of any scenario, and only 1.3% of them involve laundering. It still matters: R2 is the only scenario that catches 952 of the 1,916 laundering accounts our three scenarios find.

## What I found

- **Raising R2's amount thresholds does not work.** I tested 26 combinations of minimum amount, share of money passed on, and a cap on outflow. Every setting that cuts R2 alerts by 30% or more loses between 4.8 and 11 points of overall detection.
- **What separates real from false R2 alerts is how the money moves, not how much.** Weeks with a cash deposit or a cross-border payment are much more often laundering. Limiting R2 to those weeks (option C) halves R2 alerts and raises its precision from 1.3% to 2.1%, but loses schemes that only use domestic transfers.
- **A longer history window for R1 (structuring) wins most of that detection back**, but R1 then produces twice as many alerts.

## Options

Workload is measured in steady state (May–July 2023), with 20 minutes per alert and 120 review hours per FTE per month.

| Option | Alerts/month (all scenarios) | Investigator FTE | Laundering accounts found | Detection | Worst key laundering type | Meets agreed criteria |
|---|---|---|---|---|---|---|
| A. Keep current rules | 34,900 | 97 | 1,916 | 24.2% | – | baseline |
| B. Raise R2 minimum to £10,000 | 28,700 | 80 | 1,537 | 19.5% | −15.8 pts | no |
| C. R2 only with cash or cross-border payment | 25,700 | 71 | 1,513 | 19.1% | −11.0 pts | no |
| **D.** C, plus R2 alerts on inflows of £30,000+ | 27,600 | **77** | 1,589 | 20.1% | −10.5 pts | no |
| **E.** D, plus R1 looks back 182 instead of 91 days | 34,600 | 96 | **1,854** | **23.5%** | −4.6 pts | **yes** |

The agreed criteria were: R2 alerts down by at least 30%, overall detection down by at most 2 points, and no key laundering type down by more than 5 points. They limit R2's alerts but not total workload, which is why option E passes even though total workload hardly changes (finding F-011).

## The decision

The choice is between two reasonable options:

- **Option D: fewer people, less detection.** It saves about 20 FTE. In exchange, about 330 fewer laundering accounts are found, which is 4.1 points of detection, and layered fan-in, layered fan-out and deposit-send schemes lose 2 to 10 points each.
- **Option E: same workload, better alerts.** It keeps detection almost unchanged (−0.8 points). R2 sends 44% fewer alerts, and the share of alerts that are real laundering rises by about a third (1.21% to 1.60%). Investigators get better alerts, but not fewer alerts in total.

## Recommendation

I recommend **option E**. In transaction monitoring, a known drop in detection is hard to justify, and E meets every agreed criterion. It also addresses the investigators' main complaint, the poor quality of R2 alerts, even though it does not reduce total volume.

If the investigations team cannot sustain the current workload, option D is the fallback, but only with compliance explicitly accepting the lower detection, and with a follow-up to recover domestic layering schemes another way.

## Risks and open points

1. **Synthetic data.** The size of every effect must be re-measured on real data before any change.
2. **Definitions to confirm.** What counts as a true alert (F-010), and whether structuring is measured per account or per scheme (F-008), both affect the numbers.
3. **R1 needs 182 days of history at go-live.** Without it, R1 under-alerts for the first six months.
4. **R2's new condition relies on payment-type and location data.** Their quality issues (F-002, F-003) must be resolved first.
5. **Total workload criterion.** It should be added to the success criteria before the decision (F-011).

## Implementation

| Step | Who | What |
|---|---|---|
| 1. Decision | Compliance, investigations lead, product owner | Choose E (or D), confirm the open points above |
| 2. Specification | Data science | Final rule logic and parameters, test cases |
| 3. Build and test | Engineering / DevOps | Implement in a test environment; back-test on 6–12 months of history |
| 4. Parallel run | Data science, investigations | Old and new rules side by side for 4–8 weeks; compare alerts and outcomes |
| 5. Sign-off and go-live | Model owner, compliance | Release checklist ([03_release_signoff.md](03_release_signoff.md)) |
| 6. Review | Analytics translator | Check volumes and precision 3 months after go-live |

## Decision requested

From compliance and the investigations lead: approve option E for implementation, or choose option D and document the accepted detection loss.

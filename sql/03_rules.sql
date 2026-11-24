-- One alert = one account, one rule, one calendar week (requirements note).
CREATE OR REPLACE TABLE alerts AS
WITH band_inflows AS (
    SELECT receiver AS account, sender, tx_date, payment_type
    FROM tx
    WHERE amount >= {r1_band_low} AND amount < {r1_band_high}
),
-- R1: many below-threshold inflows to one account over a long lookback.
r1 AS (
    SELECT
        w.wk,
        b.account,
        COUNT(DISTINCT b.sender) AS senders,
        SUM(CASE WHEN b.payment_type = 'Cash Deposit' THEN 1 ELSE 0 END) AS cash_deposits,
        SUM(CASE WHEN b.tx_date >= w.wk THEN 1 ELSE 0 END) AS inflows_this_week
    FROM weeks w
    JOIN band_inflows b
      ON b.tx_date >= w.wk + 7 - {r1_lookback_days}
     AND b.tx_date < w.wk + 7
    GROUP BY ALL
)
SELECT 'R1' AS rule, account, wk
FROM r1
-- Only alert when there is new activity this week, so a pattern is not re-alerted every week.
WHERE inflows_this_week > 0
  AND (senders >= {r1_min_senders} OR cash_deposits >= {r1_min_cash_deposits})

UNION ALL

-- R2: most of the week's incoming money leaves the account again in the same week.
SELECT 'R2', account, wk
FROM flows_week
WHERE inflow >= {r2_min_inflow}
  AND outflow >= {r2_min_outflow_share} * inflow
  AND outflow <= {r2_max_outflow_share} * inflow
  -- Optional refinement: the money comes in as cash or crosses a border, unless the amount is very large.
  AND ({r2_require_risk_leg} = 0 OR cash_in OR cross_border_in OR cross_border_out OR inflow >= {r2_large_inflow_without_leg})

UNION ALL

-- R3: large or widely spread cross-border payments in one week.
SELECT 'R3', account, wk
FROM cross_border_week
WHERE amount >= {r3_min_amount}
   OR receivers >= {r3_min_receivers};

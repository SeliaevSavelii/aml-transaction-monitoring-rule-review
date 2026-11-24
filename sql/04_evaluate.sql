-- An alert is true only if laundering appears in the activity the rule checks (finding F-010):
-- R1 laundering inflows in its lookback, R2 any laundering in the week, R3 laundering cross-border outflows in the week.
CREATE OR REPLACE TABLE alerts_eval AS
WITH windows AS (
    SELECT
        rule,
        account,
        wk,
        wk + 7 - CASE rule WHEN 'R1' THEN {r1_lookback_days} ELSE 7 END AS window_start,
        wk + 7 AS window_end
    FROM alerts
)
SELECT
    w.rule,
    w.account,
    w.wk,
    COUNT(e.account) > 0 AS is_true
FROM windows w
LEFT JOIN laundering_events e
  ON e.account = w.account
 AND e.tx_date >= w.window_start
 AND e.tx_date < w.window_end
 AND (
        w.rule = 'R2'
     OR (w.rule = 'R1' AND e.direction = 'in')
     OR (w.rule = 'R3' AND e.direction = 'out' AND e.cross_border)
 )
GROUP BY ALL;

-- Laundering accounts caught by each rule (at least one true alert).
CREATE OR REPLACE TABLE detections AS
SELECT DISTINCT rule, account
FROM alerts_eval
WHERE is_true;

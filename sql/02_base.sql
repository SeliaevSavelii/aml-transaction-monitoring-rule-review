-- Helper tables shared by all rule runs (built once per session).
CREATE OR REPLACE TABLE weeks AS
SELECT DISTINCT CAST(date_trunc('week', tx_date) AS DATE) AS wk FROM tx;

-- Money in and out per account per calendar week (Monday to Sunday), with flags for higher-risk legs.
CREATE OR REPLACE TABLE flows_week AS
WITH flows AS (
    SELECT
        receiver AS account, CAST(date_trunc('week', tx_date) AS DATE) AS wk, amount AS inflow, 0.0 AS outflow,
        payment_type = 'Cash Deposit' AS cash_in,
        sender_location <> receiver_location AS cross_border_in,
        FALSE AS cross_border_out
    FROM tx
    UNION ALL
    SELECT
        sender, CAST(date_trunc('week', tx_date) AS DATE), 0.0, amount,
        FALSE, FALSE,
        sender_location <> receiver_location
    FROM tx
)
SELECT
    account, wk,
    SUM(inflow) AS inflow,
    SUM(outflow) AS outflow,
    BOOL_OR(cash_in) AS cash_in,
    BOOL_OR(cross_border_in) AS cross_border_in,
    BOOL_OR(cross_border_out) AS cross_border_out
FROM flows
GROUP BY ALL;

-- Cross-border defined by bank locations, not payment type (finding F-002).
CREATE OR REPLACE TABLE cross_border_week AS
SELECT
    sender AS account,
    CAST(date_trunc('week', tx_date) AS DATE) AS wk,
    COUNT(*) AS payments,
    COUNT(DISTINCT receiver) AS receivers,
    SUM(amount) AS amount
FROM tx
WHERE sender_location <> receiver_location
GROUP BY ALL;

-- Every laundering transaction counts for both the sending and the receiving account.
CREATE OR REPLACE TABLE laundering_events AS
SELECT sender AS account, tx_date, typology, 'out' AS direction, sender_location <> receiver_location AS cross_border
FROM tx WHERE is_laundering = 1
UNION ALL
SELECT receiver, tx_date, typology, 'in', sender_location <> receiver_location
FROM tx WHERE is_laundering = 1;

CREATE OR REPLACE TABLE laundering_accounts AS
SELECT account, LIST(DISTINCT typology ORDER BY typology) AS typologies
FROM laundering_events
GROUP BY account;

CREATE OR REPLACE VIEW tx AS
SELECT * FROM read_parquet('{parquet_path}');

CREATE OR REPLACE VIEW prof_overview AS
SELECT
    COUNT(*) AS transactions,
    MIN(tx_date) AS first_date,
    MAX(tx_date) AS last_date,
    COUNT(DISTINCT sender) AS sending_accounts,
    COUNT(DISTINCT receiver) AS receiving_accounts,
    SUM(is_laundering) AS laundering_transactions,
    ROUND(100.0 * AVG(is_laundering), 4) AS laundering_pct,
    ROUND(SUM(amount) / 1e9, 3) AS total_amount_bn
FROM tx;

-- Typologies: laundering and their 'Normal_*' look-alikes.
CREATE OR REPLACE VIEW prof_typology AS
SELECT
    is_laundering,
    typology,
    COUNT(*) AS transactions,
    COUNT(DISTINCT sender) AS sending_accounts,
    ROUND(MEDIAN(amount), 2) AS median_amount,
    ROUND(AVG(amount), 2) AS mean_amount
FROM tx
GROUP BY is_laundering, typology
ORDER BY is_laundering DESC, transactions DESC;

CREATE OR REPLACE VIEW prof_payment_type AS
SELECT
    payment_type,
    COUNT(*) AS transactions,
    SUM(is_laundering) AS laundering_transactions,
    ROUND(100.0 * AVG(is_laundering), 4) AS laundering_pct,
    ROUND(MEDIAN(amount), 2) AS median_amount
FROM tx
GROUP BY payment_type
ORDER BY transactions DESC;

CREATE OR REPLACE VIEW prof_monthly AS
SELECT
    date_trunc('month', tx_date) AS month,
    COUNT(*) AS transactions,
    SUM(is_laundering) AS laundering_transactions,
    ROUND(100.0 * AVG(is_laundering), 4) AS laundering_pct
FROM tx
GROUP BY month
ORDER BY month;

CREATE OR REPLACE VIEW prof_receiver_location AS
SELECT
    receiver_location,
    COUNT(*) AS transactions,
    SUM(is_laundering) AS laundering_transactions,
    ROUND(100.0 * AVG(is_laundering), 4) AS laundering_pct
FROM tx
GROUP BY receiver_location
ORDER BY transactions DESC;

CREATE OR REPLACE VIEW prof_amount_quantiles AS
SELECT
    is_laundering,
    ROUND(QUANTILE_CONT(amount, 0.01), 2) AS p01,
    ROUND(QUANTILE_CONT(amount, 0.25), 2) AS p25,
    ROUND(QUANTILE_CONT(amount, 0.50), 2) AS p50,
    ROUND(QUANTILE_CONT(amount, 0.75), 2) AS p75,
    ROUND(QUANTILE_CONT(amount, 0.99), 2) AS p99,
    ROUND(MAX(amount), 2) AS max
FROM tx
GROUP BY is_laundering;

-- Accounts involved in laundering, by the side of the transaction they appear on.
CREATE OR REPLACE VIEW prof_laundering_accounts AS
SELECT 'sender' AS side, COUNT(DISTINCT sender) AS accounts FROM tx WHERE is_laundering = 1
UNION ALL
SELECT 'receiver', COUNT(DISTINCT receiver) FROM tx WHERE is_laundering = 1
UNION ALL
SELECT 'either', COUNT(*) FROM (
    SELECT sender AS account FROM tx WHERE is_laundering = 1
    UNION
    SELECT receiver FROM tx WHERE is_laundering = 1
);

CREATE OR REPLACE VIEW dq_checks AS
SELECT
    SUM(CASE WHEN ts IS NULL OR amount IS NULL OR sender IS NULL OR receiver IS NULL THEN 1 ELSE 0 END) AS rows_with_nulls,
    SUM(CASE WHEN amount <= 0 THEN 1 ELSE 0 END) AS non_positive_amounts,
    SUM(CASE WHEN sender = receiver THEN 1 ELSE 0 END) AS self_transfers,
    SUM(CASE WHEN payment_type = 'Cross-border' AND sender_location = receiver_location THEN 1 ELSE 0 END) AS cross_border_same_location,
    SUM(CASE WHEN payment_type <> 'Cross-border' AND sender_location <> receiver_location THEN 1 ELSE 0 END) AS domestic_type_different_location,
    SUM(CASE WHEN payment_currency <> received_currency AND sender_location = receiver_location THEN 1 ELSE 0 END) AS currency_change_same_location
FROM tx;

CREATE OR REPLACE VIEW dq_duplicates AS
SELECT COUNT(*) AS duplicated_rows
FROM (
    SELECT ts, sender, receiver, amount, payment_type, COUNT(*) AS n
    FROM tx
    GROUP BY ALL
    HAVING COUNT(*) > 1
);

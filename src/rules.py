import duckdb
import pandas as pd

from src.db import run_sql

# Illustrative "current production" settings, deliberately generous (not real bank values).
BASELINE = {
    "r1_band_low": 1000,
    "r1_band_high": 10000,
    "r1_lookback_days": 91,
    "r1_min_senders": 10,
    "r1_min_cash_deposits": 8,
    "r2_min_inflow": 5000,
    "r2_min_outflow_share": 0.7,
    "r2_max_outflow_share": 1e9,  # no upper limit in the current rule (finding F-007)
    "r2_require_risk_leg": 0,
    "r2_large_inflow_without_leg": 1e12,
    "r3_min_amount": 10000,
    "r3_min_receivers": 2,
}

# Working assumptions from the requirements note.
MINUTES_PER_ALERT = 20
REVIEW_HOURS_PER_FTE_MONTH = 120
FULL_MONTHS = ("2022-11-01", "2023-07-31")  # finding F-001: first and last month are partial


def prepare(con: duckdb.DuckDBPyConnection) -> None:
    run_sql(con, "02_base.sql")


def run_rules(con: duckdb.DuckDBPyConnection, params: dict) -> None:
    run_sql(con, "03_rules.sql", **params)
    run_sql(con, "04_evaluate.sql", **params)


def summary(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Alerts, precision, workload and detection per rule and for all rules combined."""
    laundering_accounts = con.sql("SELECT COUNT(*) FROM laundering_accounts").fetchall()[0][0]
    per_rule = con.sql(f"""
        WITH full_months AS (
            SELECT rule, COUNT(*) AS alerts
            FROM alerts_eval
            WHERE wk BETWEEN DATE '{FULL_MONTHS[0]}' AND DATE '{FULL_MONTHS[1]}'
            GROUP BY rule
        ),
        months AS (
            SELECT COUNT(DISTINCT date_trunc('month', wk)) AS n
            FROM alerts_eval
            WHERE wk BETWEEN DATE '{FULL_MONTHS[0]}' AND DATE '{FULL_MONTHS[1]}'
        )
        SELECT
            a.rule,
            COUNT(*) AS alerts_total,
            ANY_VALUE(f.alerts) / ANY_VALUE(m.n) AS alerts_per_month,
            AVG(a.is_true::INT) AS precision,
            COUNT(DISTINCT a.account) AS alerted_accounts,
            (SELECT COUNT(*) FROM detections d WHERE d.rule = a.rule) AS detected_accounts
        FROM alerts_eval a
        JOIN full_months f USING (rule)
        CROSS JOIN months m
        GROUP BY a.rule
        ORDER BY a.rule
    """).df().set_index("rule")

    combined = con.sql(f"""
        SELECT
            COUNT(*) AS alerts_total,
            COUNT(*) FILTER (WHERE wk BETWEEN DATE '{FULL_MONTHS[0]}' AND DATE '{FULL_MONTHS[1]}')
                / COUNT(DISTINCT date_trunc('month', wk)) FILTER (WHERE wk BETWEEN DATE '{FULL_MONTHS[0]}' AND DATE '{FULL_MONTHS[1]}')
                AS alerts_per_month,
            AVG(is_true::INT) AS precision,
            COUNT(DISTINCT account) AS alerted_accounts,
            (SELECT COUNT(DISTINCT account) FROM detections) AS detected_accounts
        FROM alerts_eval
    """).df()
    combined.index = ["all rules"]

    out = pd.concat([per_rule, combined])
    out["detection_pct"] = 100 * out["detected_accounts"] / laundering_accounts
    out["review_hours_per_month"] = out["alerts_per_month"] * MINUTES_PER_ALERT / 60
    out["fte"] = out["review_hours_per_month"] / REVIEW_HOURS_PER_FTE_MONTH
    out["precision_pct"] = 100 * out.pop("precision")
    return out


def detection_by_typology(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Share of laundering accounts per typology caught by each rule and by any rule."""
    df = con.sql("""
        WITH acct_typ AS (
            SELECT account, UNNEST(typologies) AS typology FROM laundering_accounts
        ),
        hits AS (
            SELECT
                t.typology,
                t.account,
                MAX(CASE WHEN d.rule = 'R1' THEN 1 ELSE 0 END) AS r1,
                MAX(CASE WHEN d.rule = 'R2' THEN 1 ELSE 0 END) AS r2,
                MAX(CASE WHEN d.rule = 'R3' THEN 1 ELSE 0 END) AS r3,
                MAX(CASE WHEN d.rule IS NOT NULL THEN 1 ELSE 0 END) AS any_rule
            FROM acct_typ t
            LEFT JOIN detections d USING (account)
            GROUP BY ALL
        )
        SELECT
            typology,
            COUNT(*) AS accounts,
            100 * AVG(r1) AS r1_pct,
            100 * AVG(r2) AS r2_pct,
            100 * AVG(r3) AS r3_pct,
            100 * AVG(any_rule) AS any_rule_pct
        FROM hits
        GROUP BY typology
        ORDER BY any_rule_pct
    """).df()
    return df.set_index("typology")


def overlap(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """How many laundering accounts are caught by which combination of rules."""
    return con.sql("""
        SELECT combination, COUNT(*) AS laundering_accounts
        FROM (
            SELECT account, STRING_AGG(rule, ' + ' ORDER BY rule) AS combination
            FROM detections
            GROUP BY account
        )
        GROUP BY combination
        ORDER BY laundering_accounts DESC
    """).df()


def false_alerts_by_behaviour(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Which normal behaviour the account in a false alert mostly shows (finding F-005)."""
    return con.sql("""
        WITH acct_behaviour AS (
            SELECT account, MODE(typology) AS main_behaviour
            FROM (
                SELECT sender AS account, typology FROM tx
                UNION ALL
                SELECT receiver, typology FROM tx
            )
            GROUP BY account
        )
        SELECT a.rule, b.main_behaviour, COUNT(*) AS false_alerts
        FROM alerts_eval a
        JOIN acct_behaviour b USING (account)
        WHERE NOT a.is_true
        GROUP BY a.rule, b.main_behaviour
        QUALIFY ROW_NUMBER() OVER (PARTITION BY a.rule ORDER BY COUNT(*) DESC) <= 4
        ORDER BY a.rule, false_alerts DESC
    """).df()


def monthly(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.sql("""
        SELECT date_trunc('month', wk) AS month, rule, COUNT(*) AS alerts, 100 * AVG(is_true::INT) AS precision_pct
        FROM alerts_eval
        GROUP BY ALL
        ORDER BY month, rule
    """).df()

import duckdb
import pandas as pd

from src import rules

KEY_TYPOLOGIES = ["Deposit-Send", "Layered_Fan_In", "Layered_Fan_Out", "Structuring", "Smurfing"]
STEADY_STATE = ("2023-05-01", "2023-07-31")  # after the 182-day R1 lookback has full history

_RISK_LEG = {**rules.BASELINE, "r2_require_risk_leg": 1}

OPTIONS = {
    "A. Keep current rules": rules.BASELINE,
    "B. Raise R2 minimum inflow to 10k": {**rules.BASELINE, "r2_min_inflow": 10000},
    "C. R2 only with a cash or cross-border leg": _RISK_LEG,
    "D. C, but R2 also alerts on inflows of 30k+": {**_RISK_LEG, "r2_large_inflow_without_leg": 30000},
    "E. D + R1 lookback 182 days": {**_RISK_LEG, "r2_large_inflow_without_leg": 30000, "r1_lookback_days": 182},
}


def steady_state_alerts(con: duckdb.DuckDBPyConnection) -> pd.Series:
    """Alerts per month per rule over the steady-state months, for the last rule run."""
    df = con.sql(f"""
        SELECT rule, COUNT(*) / COUNT(DISTINCT date_trunc('month', wk)) AS per_month
        FROM alerts_eval
        WHERE wk BETWEEN DATE '{STEADY_STATE[0]}' AND DATE '{STEADY_STATE[1]}'
        GROUP BY rule
    """).df().set_index("rule")["per_month"]
    df["total"] = df.sum()
    return df


def detected_set(con: duckdb.DuckDBPyConnection) -> set:
    return {a for (a,) in con.sql("SELECT DISTINCT account FROM detections").fetchall()}


def evaluate(con: duckdb.DuckDBPyConnection, params: dict, label: str) -> tuple[dict, pd.Series]:
    """Run all rules with `params`; return headline metrics and detection per typology (any rule)."""
    rules.run_rules(con, params)
    s = rules.summary(con)
    typ = rules.detection_by_typology(con)["any_rule_pct"]
    unique_r2 = con.sql("""
        SELECT COUNT(*) FROM (
            SELECT account FROM detections GROUP BY account
            HAVING COUNT(*) = 1 AND ANY_VALUE(rule) = 'R2'
        )
    """).fetchall()[0][0]
    row = {
        "option": label,
        "r2_alerts_per_month": s.loc["R2", "alerts_per_month"],
        "r2_precision_pct": s.loc["R2", "precision_pct"],
        "r2_detected_accounts": s.loc["R2", "detected_accounts"],
        "r2_unique_detections": unique_r2,
        "total_alerts_per_month": s.loc["all rules", "alerts_per_month"],
        "total_fte": s.loc["all rules", "fte"],
        "total_precision_pct": s.loc["all rules", "precision_pct"],
        "detected_accounts": s.loc["all rules", "detected_accounts"],
        "detection_pct": s.loc["all rules", "detection_pct"],
        **{f"key: {t}": typ.get(t) for t in KEY_TYPOLOGIES},
    }
    return row, typ.rename(label)


def check_criteria(table: pd.DataFrame, baseline_label: str) -> pd.DataFrame:
    """Success criteria from the requirements note, relative to the baseline row."""
    base = table.loc[baseline_label]
    key_cols = [c for c in table.columns if c.startswith("key: ")]
    out = pd.DataFrame(index=table.index)
    out["r2_alert_change_pct"] = 100 * (table["r2_alerts_per_month"] / base["r2_alerts_per_month"] - 1)
    out["detection_change_pp"] = table["detection_pct"] - base["detection_pct"]
    out["worst_key_typology_change_pp"] = table[key_cols].sub(base[key_cols]).min(axis=1)
    out["meets_alert_target"] = out["r2_alert_change_pct"] <= -30
    out["meets_detection_target"] = out["detection_change_pp"] >= -2
    out["meets_key_typology_target"] = out["worst_key_typology_change_pp"] >= -5
    out["meets_all"] = out[["meets_alert_target", "meets_detection_target", "meets_key_typology_target"]].all(axis=1)
    # Not an agreed criterion: the request is about workload, but the criteria only measure R2 (finding F-011).
    out["total_alert_change_pct"] = 100 * (table["total_alerts_per_month"] / base["total_alerts_per_month"] - 1)
    return out

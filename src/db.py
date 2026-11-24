import zipfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
ZIP_PATH = RAW_DIR / "synthetic-transaction-monitoring-dataset-aml.zip"
CSV_PATH = RAW_DIR / "SAML-D.csv"
PARQUET_PATH = ROOT / "data" / "processed" / "transactions.parquet"
SQL_DIR = ROOT / "sql"
KAGGLE_DATASET = "berkanoztas/synthetic-transaction-monitoring-dataset-aml"


def run_sql(con: duckdb.DuckDBPyConnection, name: str, **params) -> None:
    con.execute((SQL_DIR / name).read_text().format(**params))


def build_parquet(force: bool = False) -> Path:
    if PARQUET_PATH.exists() and not force:
        return PARQUET_PATH
    if not CSV_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH) as zf:
            zf.extract("SAML-D.csv", RAW_DIR)
    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_sql(duckdb.connect(), "00_load.sql", csv_path=CSV_PATH.as_posix(), parquet_path=PARQUET_PATH.as_posix())
    return PARQUET_PATH


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    run_sql(con, "01_profile.sql", parquet_path=build_parquet().as_posix())
    return con

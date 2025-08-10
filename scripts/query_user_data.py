#!/usr/bin/env python3
"""
Query PostgreSQL database for all tables containing user_id=111.
Exports results to CSV/JSON in ./exports/ directory.

Usage:
    # Using environment variables from project root .env
    python3 scripts/query_user_data.py
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


def load_env() -> dict[str, str]:
    """Load environment variables from project root .env file."""
    load_dotenv(dotenv_path=Path("../.env"))
    env_vars = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": os.getenv("POSTGRES_DATABASE"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "target_user_id": os.getenv("TARGET_USER_ID", "111")
    }
    missing = [k for k, v in env_vars.items() if not v and k != "password"]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    return env_vars


def get_connection(config: dict[str, str]) -> psycopg2.extensions.connection:
    """Create a database connection."""
    return psycopg2.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"]
    )


def find_user_tables(conn: psycopg2.extensions.connection) -> list[dict[str, str]]:
    """Find all tables containing a user_id column."""
    sql = """
    SELECT table_schema, table_name
    FROM information_schema.columns
    WHERE column_name = 'user_id'
      AND table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return [{"schema": r[0], "table": r[1]} for r in cur.fetchall()]


def query_user_data(conn: psycopg2.extensions.connection, schema: str, table: str, user_id: str) -> list[dict[str, any]]:
    """Query a single table for user data."""
    sql = f"SELECT * FROM {schema}.{table} WHERE user_id = %s"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()


def export_data(data: list[dict], schema: str, table: str, user_id: str, export_dir: Path) -> None:
    """Export data to CSV and JSON."""
    if not data:
        return
    export_dir.mkdir(exist_ok=True)
    base_name = f"{schema}.{table}.user_{user_id}"
    csv_path = export_dir / f"{base_name}.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    json_path = export_dir / f"{base_name}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Exported {len(data)} rows to {csv_path} and {json_path}")


def main() -> int:
    try:
        config = load_env()
        user_id = config.pop("target_user_id")
        print(f"Connecting to {config['host']}:{config['port']}/{config['dbname']}...")
        print(f"Querying for user_id = {user_id}")
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True, parents=True)
        with get_connection(config) as conn:
            tables = find_user_tables(conn)
            if not tables:
                print("No tables with user_id column found.")
                return 0
            print(f"Found {len(tables)} tables with user_id column")
            for table_info in tables:
                try:
                    rows = query_user_data(conn, table_info["schema"], table_info["table"], user_id)
                    if rows:
                        export_data(rows, table_info["schema"], table_info["table"], user_id, export_dir)
                except Exception as e:
                    print(f"Error querying {table_info['schema']}.{table_info['table']}: {e}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    print("\nDone! Check the 'exports' directory for results.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

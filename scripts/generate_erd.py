"""Generate an ER diagram of the Postgres database using SQLAlchemy reflection
and pydot + Graphviz.

Usage:
    $ source venv/bin/activate  # ensure venv active
    $ python scripts/generate_erd.py

The script connects via environment variables set in the .env file (POSTGRES_* or DATABASE_URL)
and writes docs/prepsense_schema.png.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, MetaData
from dotenv import load_dotenv
import pydot  # type: ignore

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "prepsense_schema.png"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def build_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    db = os.getenv("POSTGRES_DATABASE", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

def main() -> None:
    # Load variables from .env in project root
    load_dotenv()
    db_url = build_db_url()
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    graph = pydot.Dot("prepsense_schema", graph_type="digraph", rankdir="LR")

    # Create nodes with HTML table labels
    for table_name, table in metadata.tables.items():
        header = f'<tr><td bgcolor="lightgrey"><b>{table_name}</b></td></tr>'
        rows = "".join(
            f'<tr><td align="left">{column.name}: {column.type}</td></tr>'
            for column in table.columns
        )
        label = f"""<
<table BORDER="0" CELLBORDER="1" CELLSPACING="0">
{header}
{rows}
</table>
>"""
        node = pydot.Node(table_name, shape="plaintext", label=label, fontname="Arial")
        graph.add_node(node)

    # Create edges for foreign keys
    inspector = inspect(engine)
    for table_name in metadata.tables:
        fks = inspector.get_foreign_keys(table_name)
        for fk in fks:
            ref_table = fk["referred_table"]
            if ref_table:
                edge = pydot.Edge(table_name, ref_table)
                graph.add_edge(edge)

    graph.write_png(str(OUTPUT_PATH))
    print(f"ER diagram written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

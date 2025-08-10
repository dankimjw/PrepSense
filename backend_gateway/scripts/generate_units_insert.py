#!/usr/bin/env python3
"""
Generate SQL INSERT statements for units data
This can be run by someone with table creation permissions
"""

from pathlib import Path


def generate_units_insert_sql():
    """Generate SQL file with just INSERT statements"""

    # Read the original SQL script
    script_path = Path(__file__).parent / "create_units_table.sql"
    with open(script_path) as f:
        sql_script = f.read()

    # More sophisticated parsing - look for complete statements
    lines = sql_script.split("\n")
    current_statement = ""
    create_statements = []
    insert_statements = []
    in_statement = False
    statement_type = None

    for line in lines:
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("--"):
            continue

        # Start of a new statement
        if not in_statement:
            if line.upper().startswith("CREATE TYPE"):
                in_statement = True
                statement_type = "CREATE_TYPE"
                current_statement = line
            elif line.upper().startswith("CREATE TABLE"):
                in_statement = True
                statement_type = "CREATE_TABLE"
                current_statement = line
            elif line.upper().startswith("CREATE INDEX"):
                in_statement = True
                statement_type = "CREATE_INDEX"
                current_statement = line
            elif line.upper().startswith("INSERT"):
                in_statement = True
                statement_type = "INSERT"
                current_statement = line
        else:
            # Continue building the current statement
            current_statement += "\n" + line

        # Check if statement is complete (ends with semicolon)
        if in_statement and line.endswith(";"):
            if statement_type in ["CREATE_TYPE", "CREATE_TABLE", "CREATE_INDEX"]:
                create_statements.append(current_statement)
            elif statement_type == "INSERT":
                insert_statements.append(current_statement)

            # Reset for next statement
            in_statement = False
            current_statement = ""
            statement_type = None

    # Generate the SQL file
    output_sql = """-- Units table creation and data for PrepSense
-- This script should be run with database administrator privileges

"""

    if create_statements:
        output_sql += "-- Create the unit_category enum type and tables\n"
        for stmt in create_statements:
            output_sql += stmt + "\n\n"

    if insert_statements:
        output_sql += "-- Insert units data\n"
        for stmt in insert_statements:
            output_sql += stmt + "\n\n"

    # Write to output file
    output_file = Path(__file__).parent / "units_table_complete.sql"
    with open(output_file, "w") as f:
        f.write(output_sql)

    print(f"✅ Generated complete SQL file: {output_file}")
    print(
        f"📝 This file contains {len(create_statements)} CREATE statements and {len(insert_statements)} INSERT statements"
    )
    print("\n📋 To deploy this:")
    print("1. Have a database administrator run this SQL file against the database")
    print("2. Or use the postgres superuser to run:")
    print(f"   psql -h [HOST] -U postgres -d prepsense < {output_file}")

    return output_file


if __name__ == "__main__":
    generate_units_insert_sql()

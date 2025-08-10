#!/usr/bin/env python3
"""
Grant permissions to IAM users for PostgreSQL access
"""

import os
import sys

import psycopg2


def grant_permissions(user_email):
    """Grant necessary permissions to an IAM user"""

    # Get password from environment or secrets file
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        print("Error: POSTGRES_PASSWORD environment variable is required")
        print("Please set it using: export POSTGRES_PASSWORD='your-password'")
        sys.exit(1)

    try:
        # Connect as postgres user
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DATABASE", "prepsense"),
            user="postgres",
            password=password,
            sslmode="require",
        )
        cursor = conn.cursor()

        # Grant permissions
        print(f"Granting permissions to {user_email}...")

        # Schema permissions
        cursor.execute(f'GRANT USAGE ON SCHEMA public TO "{user_email}";')

        # Table permissions
        cursor.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{user_email}";')

        # Sequence permissions (for auto-incrementing IDs)
        cursor.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{user_email}";')

        # Future tables
        cursor.execute(
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{user_email}";'
        )
        cursor.execute(
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{user_email}";'
        )

        conn.commit()
        print(f"✅ Permissions granted to {user_email}")

        # Verify permissions
        cursor.execute(
            """
            SELECT table_name, privilege_type
            FROM information_schema.table_privileges
            WHERE grantee = %s AND table_schema = 'public'
            LIMIT 5;
        """,
            (user_email,),
        )

        print(f"\nSample permissions for {user_email}:")
        for table, privilege in cursor.fetchall():
            print(f"  - {table}: {privilege}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default users
        users = [
            "danielk7@uchicago.edu",
            "bonnymathew@uchicago.edu",
            "asannidhanam@uchicago.edu",
            "prahalad@uchicago.edu",
        ]
        print("Granting permissions to all team members...")
        for user in users:
            grant_permissions(user)
    else:
        grant_permissions(sys.argv[1])

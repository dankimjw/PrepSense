#!/usr/bin/env python3
"""
Setup IAM authentication for Cloud SQL PostgreSQL
This allows team members to connect without passwords
"""

import os
import subprocess
import sys

PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'your-project-id')
INSTANCE_NAME = os.getenv('CLOUD_SQL_INSTANCE', 'your-instance-name')
DATABASE_NAME = os.getenv('POSTGRES_DATABASE', 'your-database-name')

def run_command(cmd, check=True):
    """Run command and return result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def setup_iam_auth():
    """Setup IAM authentication for Cloud SQL"""
    
    print("=== Setting up IAM Authentication for Cloud SQL ===\n")
    
    # 1. Grant database permissions to IAM user
    print("1. Granting database permissions to IAM users...")
    
    # Connect as postgres user to grant permissions
    grant_sql = """
-- Grant permissions to IAM users
DO $$
BEGIN
    -- Grant connect permission to cloudsqlsuperuser (IAM users)
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cloudsqlsuperuser') THEN
        CREATE ROLE cloudsqlsuperuser;
    END IF;
    
    -- Grant necessary permissions
    GRANT CONNECT ON DATABASE prepsense TO cloudsqlsuperuser;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cloudsqlsuperuser;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cloudsqlsuperuser;
    
    -- Grant permissions on future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cloudsqlsuperuser;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cloudsqlsuperuser;
END $$;

-- List current IAM users
SELECT usename, usesuper FROM pg_user WHERE usename LIKE '%@%';
"""
    
    # Save SQL to file
    with open('grant_iam_permissions.sql', 'w') as f:
        f.write(grant_sql)
    
    print("\n2. To complete IAM setup, run these commands:")
    print(f"   # Connect as postgres user and grant permissions")
    # Get password from environment variable
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    if not postgres_password:
        print("Error: POSTGRES_PASSWORD environment variable is required")
        print("Please set it using: export POSTGRES_PASSWORD='your-password'")
        return False
    
    # Get host from environment variable
    postgres_host = os.getenv('POSTGRES_HOST')
    if not postgres_host:
        print("Error: POSTGRES_HOST environment variable is required")
        print("Please set it using: export POSTGRES_HOST='your-cloud-sql-ip'")
        return False
    
    print(f"   PGPASSWORD=$POSTGRES_PASSWORD psql -h {postgres_host} -U postgres -d {DATABASE_NAME} < grant_iam_permissions.sql")
    
    print("\n3. Team members can now connect without passwords:")
    print(f"   # Using gcloud (recommended)")
    print(f"   gcloud sql connect {INSTANCE_NAME} --user=YOUR_EMAIL@uchicago.edu --database={DATABASE_NAME}")
    
    print("\n4. For programmatic access with IAM:")
    print("   - Use Cloud SQL Proxy with --enable-iam-login flag")
    print("   - Update backend to use IAM tokens instead of passwords")
    
    print("\n=== Python Connection Example ===")
    print("""
from google.auth import default
from google.auth.transport.requests import Request
import psycopg2

# Get credentials and access token
credentials, project = default()
credentials.refresh(Request())
access_token = credentials.token

# Connect using the access token as password
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),  # or 127.0.0.1 if using proxy
    database=os.getenv('POSTGRES_DATABASE', 'your-database'),
    user='your-email@example.com',  # Your IAM email
    password=access_token,  # Use token as password
    sslmode='require'
)
""")
    
    print("\n✓ IAM authentication guide created!")
    print("Note: The password in .env is only needed for the 'postgres' admin user.")
    print("Team members should use IAM authentication instead.")

if __name__ == "__main__":
    setup_iam_auth()
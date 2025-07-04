
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

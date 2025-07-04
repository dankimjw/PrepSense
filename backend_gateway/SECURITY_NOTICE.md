# Security Notice

## PostgreSQL Password Rotation Required

A database password was accidentally committed to the repository history. While it has been removed from the current codebase, the password should be rotated as a security precaution.

### Actions Taken
1. Removed all hardcoded passwords from scripts
2. Updated all scripts to require environment variables for passwords
3. Added validation to ensure passwords are not hardcoded

### Required Actions
1. **Rotate the PostgreSQL password** on the Cloud SQL instance
2. Update all team members with the new password
3. Set the password via environment variable:
   ```bash
   export POSTGRES_PASSWORD='new-secure-password'
   ```

### Best Practices Going Forward
- Never hardcode passwords in scripts
- Always use environment variables for sensitive data
- Review commits before pushing to ensure no secrets are included
- Use `.env` files locally (already in .gitignore)

### Affected Scripts Updated
- `backend_gateway/scripts/setup_cloud_sql_postgres.py`
- `backend_gateway/scripts/verify_postgres_performance.py`
- `backend_gateway/scripts/test_postgres_service.py`
- `backend_gateway/scripts/test_postgres_connection.py`
- `backend_gateway/scripts/migrate_pantry_items.py`
- `backend_gateway/scripts/setup_iam_auth.py`

All scripts now require passwords to be set via environment variables and will fail with clear error messages if not configured properly.
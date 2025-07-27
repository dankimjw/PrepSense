# Google Cloud Platform (GCP) Documentation

## 🚨 CRITICAL INSTRUCTIONS FOR ALL CLAUDE INSTANCES 🚨

**BEFORE making any GCP-related changes:**
1. **READ** this document to understand current GCP setup
2. **NEVER** commit credentials or connection strings
3. **TEST** database connections before documenting
4. **UPDATE** this document for any infrastructure changes
5. **VERIFY** environment variables match production needs

**This is LIVE DOCUMENTATION** - Keep it synchronized with actual GCP configuration!

---

## Overview

PrepSense uses Google Cloud Platform for:
- **Cloud SQL**: PostgreSQL database hosting
- **Application Default Credentials (ADC)**: Service authentication
- **Future**: Cloud Storage, Cloud Run deployment

---

## Cloud SQL PostgreSQL

### Instance Details
- **Instance Name**: `prepsense-db` (verify in GCP Console)
- **Region**: `us-central1`
- **PostgreSQL Version**: 14
- **IP Address**: `***REMOVED***` (from .env file)

### Database Configuration
- **Database Name**: `prepsense`
- **Port**: `5432`
- **SSL**: Required for production

### Connection Details
```python
# From backend_gateway/core/config.py
POSTGRES_HOST = "***REMOVED***"
POSTGRES_PORT = 5432
POSTGRES_DATABASE = "prepsense"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "<from .env file>"
```

### Database Schema
Key tables:
- `users` - User accounts
- `pantries` - User pantries
- `pantry_items` - Items in pantries
- `products` - Product catalog
- `user_recipes` - Saved recipes
- `user_preferences` - Dietary preferences
- `cooking_history` - Recipe completion history

---

## Environment Configuration

### Main .env File Location
```
/Users/danielkim/_Capstone/PrepSense/.env
```
**NOT** `backend_gateway/.env` - the root .env is the source of truth!

### Required Environment Variables
```bash
# Google Cloud SQL
POSTGRES_HOST=***REMOVED***
POSTGRES_PORT=5432
POSTGRES_DATABASE=prepsense
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>

# Google Application Credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# API Keys
OPENAI_API_KEY=<key>
SPOONACULAR_API_KEY=<key>
```

---

## Application Default Credentials (ADC)

### Service Account Setup
1. **File Location**: 
   ```
   /Users/danielkim/_Capstone/PrepSense/config/adsp-34002-on02-prep-sense-ef1111b0833b.json
   ```

2. **Permissions Required**:
   - Cloud SQL Client
   - Cloud SQL Editor (for migrations)

3. **Configuration**:
   ```python
   # Set in run_app.py
   os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
   ```

---

## Database Access

### Direct Connection (Development)
```bash
# Using psql
psql -h ***REMOVED*** -U postgres -d prepsense

# Connection string
postgresql://postgres:<password>@***REMOVED***:5432/prepsense
```

### From Application
```python
# Using asyncpg (preferred)
import asyncpg

pool = await asyncpg.create_pool(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    database=POSTGRES_DATABASE,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    min_size=1,
    max_size=10
)
```

### IAM Authentication (Future)
- Currently using password authentication
- IAM auth configured but not active
- See `MIGRATE_TO_ADC.md` for migration plan

---

## Common Database Operations

### Check Database Status
```python
# From backend
python scripts/test_postgres_connection.py
```

### Run Migrations
```sql
-- Example: Add environmental columns
\i backend_gateway/scripts/add_environmental_columns.sql
```

### Update Demo Data
```python
# Update ingredient expirations
python scripts/update_ingredient_expirations.py
```

---

## Monitoring & Debugging

### Check Connection from Backend
```bash
curl http://localhost:8001/api/v1/health
```

Response should show:
```json
{
  "environment": {
    "database_configured": true,
    "database_connected": true
  }
}
```

### Common Issues

1. **Connection Refused**
   - Check IP whitelist in Cloud SQL
   - Verify credentials in .env
   - Ensure Cloud SQL proxy isn't needed

2. **Authentication Failed**
   - Double-check password in .env
   - Verify user exists in PostgreSQL
   - Check pg_hba.conf settings

3. **SSL Required**
   - Add `sslmode=require` to connection string
   - Configure SSL certificates if needed

---

## Security Best Practices

### DO:
- ✅ Use environment variables for credentials
- ✅ Rotate passwords regularly
- ✅ Use service accounts for applications
- ✅ Enable Cloud SQL backups
- ✅ Use private IP when possible

### DON'T:
- ❌ Commit credentials to git
- ❌ Use root/postgres user in production
- ❌ Expose database publicly without IP restrictions
- ❌ Share service account keys
- ❌ Disable SSL in production

---

## Deployment Considerations

### Current State
- Development uses direct IP connection
- No Cloud SQL proxy required locally
- Single database instance

### Future Improvements
1. **Cloud SQL Proxy** for secure connections
2. **Private IP** with VPC peering
3. **Read replicas** for scaling
4. **Automated backups** configuration
5. **Cloud Run** deployment

---

## Cost Management

### Current Usage
- **Instance Type**: Check in GCP Console
- **Storage**: Monitor growth
- **Connections**: Pool size limits

### Optimization Tips
- Use connection pooling
- Close idle connections
- Monitor slow queries
- Regular maintenance

---

## Useful Commands

### GCP CLI
```bash
# List Cloud SQL instances
gcloud sql instances list

# Describe instance
gcloud sql instances describe prepsense-db

# Connect via cloud_sql_proxy
./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432
```

### Database Queries
```sql
-- Check active connections
SELECT pid, usename, application_name, client_addr 
FROM pg_stat_activity 
WHERE state = 'active';

-- Database size
SELECT pg_database_size('prepsense');

-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

---

**Last Updated**: 2025-07-27
**Next Review**: When modifying database schema or GCP resources
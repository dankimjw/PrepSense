# PrepSense Database Migration Guide

## Overview

This guide explains how to migrate PrepSense from BigQuery to PostgreSQL (Cloud SQL) to resolve timeout issues and improve performance for transactional operations.

## Why PostgreSQL?

### Current Issues with BigQuery
- **Timeout errors**: Updates taking 15-30+ seconds
- **Not designed for OLTP**: BigQuery is for analytics, not real-time transactions
- **Cost inefficient**: Paying per query for simple CRUD operations

### PostgreSQL Benefits
- **Sub-second updates**: Designed for transactional workloads
- **IAM authentication**: Team members can use Google accounts
- **Query insights**: Built-in performance monitoring
- **Lower cost**: Fixed monthly cost (~$7-15/month for db-f1-micro)

## Migration Steps

### 1. Check Cloud SQL Instance Status

```bash
gcloud sql instances describe prepsense-postgres \
  --project=adsp-34002-on02-prep-sense \
  --format="table(state,ipAddresses[0].ipAddress)"
```

Wait until state is `RUNNABLE`.

### 2. Import Database Schema

Once the instance is ready:

```bash
# Get the IP address
IP_ADDRESS=$(gcloud sql instances describe prepsense-postgres \
  --project=adsp-34002-on02-prep-sense \
  --format="value(ipAddresses[0].ipAddress)")

# Import schema
cd backend_gateway/scripts
PGPASSWORD=$POSTGRES_PASSWORD psql -h $IP_ADDRESS -U postgres -d prepsense < schema_postgres.sql
```

### 3. Run Data Migration

Migrate existing data from BigQuery to PostgreSQL:

```bash
python migrate_bigquery_to_postgres.py \
  --pg-host $IP_ADDRESS \
  --pg-password $POSTGRES_PASSWORD \
  --dry-run  # Test connection first

# If dry run succeeds, run actual migration
python migrate_bigquery_to_postgres.py \
  --pg-host $IP_ADDRESS \
  --pg-password $POSTGRES_PASSWORD
```

### 4. Configure Backend to Use PostgreSQL

Update your `.env` file:

```bash
# Run the configuration script
python configure_database.py
# Select option 1 for PostgreSQL

# Or manually add to .env:
DB_TYPE=postgres
POSTGRES_HOST=35.184.61.42  # Your Cloud SQL IP
POSTGRES_PORT=5432
POSTGRES_DATABASE=prepsense
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
CLOUD_SQL_CONNECTION_NAME=adsp-34002-on02-prep-sense:us-central1:prepsense-postgres
```

### 5. Test the Connection

```bash
# Test PostgreSQL service
python test_postgres_service.py

# Compare performance
python verify_postgres_performance.py
```

### 6. Restart Backend

```bash
# From backend_gateway directory
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

## Team Access Setup

### Add Team Members with IAM Authentication

```bash
# Add a team member
gcloud sql users create teammate@uchicago.edu \
  --instance=prepsense-postgres \
  --type=CLOUD_IAM_USER \
  --project=adsp-34002-on02-prep-sense

# Team member connects using:
gcloud sql connect prepsense-postgres \
  --user=teammate@uchicago.edu \
  --database=prepsense
```

## Production Considerations

### 1. Use Cloud SQL Proxy (More Secure)

```bash
# Download proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
chmod +x cloud_sql_proxy

# Run proxy
./cloud_sql_proxy -instances=$CLOUD_SQL_CONNECTION_NAME=tcp:5432 &

# Update .env to use localhost
POSTGRES_HOST=127.0.0.1
```

### 2. Backup Strategy

```bash
# Create on-demand backup
gcloud sql backups create \
  --instance=prepsense-postgres \
  --project=adsp-34002-on02-prep-sense

# List backups
gcloud sql backups list \
  --instance=prepsense-postgres \
  --project=adsp-34002-on02-prep-sense
```

### 3. Monitoring

- Enable Query Insights in Cloud Console
- Monitor slow queries
- Set up alerts for high CPU/memory usage

## Rollback Plan

If you need to switch back to BigQuery:

```bash
# Run configuration script
python configure_database.py
# Select option 2 for BigQuery

# Restart backend
uvicorn app:app --reload
```

## Performance Expectations

Based on our tests:
- **Read operations**: 50-100ms (vs 200-500ms on BigQuery)
- **Update operations**: 50-200ms (vs 15,000-30,000ms on BigQuery)
- **Batch inserts**: 200-500ms for 20 items
- **No more timeout errors!**

## Cost Breakdown

- **Cloud SQL db-f1-micro**: ~$7-15/month
- **Storage**: ~$0.17/GB/month
- **Network egress**: ~$0.12/GB (only when data leaves GCP)
- **Total estimated**: $10-20/month for typical usage

## Troubleshooting

### Connection Refused
- Check instance state is RUNNABLE
- Verify IP whitelist includes your IP (or use 0.0.0.0/0 for development)
- Ensure correct password

### Migration Errors
- Check BigQuery permissions
- Verify PostgreSQL connection
- Review migration logs for specific errors

### Performance Issues
- Check Query Insights
- Verify indexes are created
- Consider upgrading instance tier if needed

## Support

For issues:
1. Check instance logs: `gcloud sql operations list --instance=prepsense-postgres`
2. Review backend logs: Check FastAPI output
3. Contact team lead with specific error messages
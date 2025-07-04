# PostgreSQL Database Access Guide for PrepSense Team

## Overview
PrepSense uses PostgreSQL hosted on Google Cloud SQL. Since everyone has access to the GCP project, you'll use your Google account to connect securely.

## Primary Method: Google Account Authentication (Recommended)

### Step 1: Authenticate with Google Cloud
```bash
# If you haven't already, authenticate with Google
gcloud auth application-default login
```

### Step 2: Configure Your Environment
1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. In your `.env` file, set these values:
   ```
   POSTGRES_USE_IAM=true
   POSTGRES_IAM_USER=your-email@uchicago.edu
   ```

3. Ask the team lead for the `POSTGRES_SECRETS.md` file to get:
   - Database host/IP address
   - Database name
   - Other connection details (NOT the password)

### Step 3: Request Database Access
Ask the team lead to grant your Google account access to the database. They'll run:
```bash
gcloud sql users create your-email@uchicago.edu \
  --instance=prepsense-postgres \
  --type=CLOUD_IAM_USER
```

### Step 4: Test Your Connection
```bash
# Start the backend
python3 run_app.py --backend

# Check the health endpoint
# Open: http://localhost:8001/health
```

## Fallback Method: Password Authentication (Only if IAM fails)

If Google authentication doesn't work in your environment:

1. Get the password from the `POSTGRES_SECRETS.md` file
2. In your `.env` file, set:
   ```
   POSTGRES_USE_IAM=false
   ```
3. Update the PostgreSQL password field in your `.env`

**WARNING**: Password authentication is less secure. Always prefer Google IAM authentication.

## Security Best Practices

1. **Never share credentials in:**
   - Git commits
   - Slack/Discord messages
   - Documentation files
   - Screenshots

2. **Always use:**
   - Environment variables (`.env` file)
   - Secure file sharing for initial credential distribution
   - IAM authentication when possible

3. **Keep credentials secure:**
   - Don't copy `.env` files between machines
   - Regenerate credentials if compromised
   - Use different credentials for dev/prod

## Troubleshooting

**Connection refused:**
- Check if you're on the right network
- Verify your IP is whitelisted in Cloud SQL

**Authentication failed:**
- Double-check credentials in `.env`
- Ensure no extra spaces or quotes

**Need help?**
Contact the team lead for credential access or connection issues.
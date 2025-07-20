# Backend Setup Guide for PrepSense

This guide helps new team members set up the backend properly and avoid common configuration issues.

## Prerequisites

- Python 3.10+
- Virtual environment (venv)
- Access to team's shared credentials
- Access to Google Cloud Project (for database)

## Step-by-Step Setup

### 1. Clone and Navigate
```bash
git clone https://github.com/dankimjw/PrepSense.git
cd PrepSense
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the **project root** (not in backend_gateway/):
```bash
cp .env.template .env  # If template exists
# OR create new .env file
```

Add these required variables to `.env`:
```env
# Database Configuration (Get from team lead)
POSTGRES_HOST=<your-cloud-sql-ip>
POSTGRES_PORT=5432
POSTGRES_DATABASE=prepsense
POSTGRES_USER=<your-db-user>
POSTGRES_PASSWORD=<your-db-password>
CLOUD_SQL_CONNECTION_NAME=<your-project-id>:<region>:<instance-name>

# API Keys (Get from team lead or use your own)
OPENAI_API_KEY=sk-...your-key-here...
SPOONACULAR_API_KEY=your-spoonacular-key

# Demo User Configuration (Use unique ID to avoid conflicts)
DEMO_USER_ID=your-unique-id-number

# Optional: Google Cloud Credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### 5. Required API Keys Setup

Both API keys are **REQUIRED** for PrepSense to function:

**OpenAI API Key** - Without it:
- Chat features will not work
- Recipe recommendations will fail
- AI-powered features will be disabled

**Spoonacular API Key** - Without it:
- Recipe search will fail
- Nutritional data won't load
- Recipe details and images won't display

Set up OpenAI key using one of these methods:

**Option A: Environment Variable**
```bash
export OPENAI_API_KEY="sk-...your-key-here..."
```

**Option B: Config File**
```bash
mkdir -p config
echo "sk-...your-key-here..." > config/openai_key.txt
```

**Spoonacular API Key Setup**
The Spoonacular key must be set in the `.env` file:
```env
SPOONACULAR_API_KEY=your-actual-api-key-here
```

**Getting API Keys:**
- **OpenAI**: Sign up at https://platform.openai.com/api-keys
- **Spoonacular**: Sign up at https://spoonacular.com/food-api (free tier available)

### 6. Database Access Setup

The database is hosted on Google Cloud SQL. You may need:

1. **VPN Access** - Check with team lead if VPN is required
2. **Cloud SQL Proxy** (Alternative):
   ```bash
   # Download Cloud SQL Proxy
   curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
   chmod +x cloud_sql_proxy
   
   # Run proxy
   ./cloud_sql_proxy -instances=<your-connection-name>=tcp:5432
   ```

### 7. Run the Backend
```bash
cd backend_gateway
python main.py
```

## Common Issues and Solutions

### Issue 1: ModuleNotFoundError: No module named 'openai'
**Solution**: Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue 2: ValueError: OpenAI API key not found
**Solution**: Check that your API key is properly set:
- Verify `.env` file exists in project root (not backend_gateway/)
- Ensure OPENAI_API_KEY is set correctly
- Try alternative setup methods (environment variable or config file)

### Issue 3: Database Connection Error
**Symptoms**: 
- `psycopg2.OperationalError: could not connect to server`
- Connection timeout errors

**Solutions**:
1. Verify database credentials in `.env`
2. Check network connectivity (may need VPN)
3. Try using Cloud SQL Proxy
4. Contact team lead for database access

### Issue 4: Port Already in Use
**Solution**: The backend runs on port 8001. If occupied:
```bash
# Find process using port 8001
lsof -i :8001
# Kill the process
kill -9 <PID>
```

### Issue 5: Missing config/ directory
**Solution**: Create it manually:
```bash
mkdir -p backend_gateway/config
```

## Verification

After setup, verify everything works:

1. **Check Backend Health**:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "environment": {
       "openai_configured": true,
       "google_cloud_configured": true
     }
   }
   ```

2. **Run Health Check Script**:
   ```bash
   python scripts/check_app_health.py
   ```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| POSTGRES_HOST | Yes | Database host IP | <cloud-sql-ip> |
| POSTGRES_PORT | Yes | Database port | 5432 |
| POSTGRES_DATABASE | Yes | Database name | prepsense |
| POSTGRES_USER | Yes | Database user | <db-username> |
| POSTGRES_PASSWORD | Yes | Database password | (get from team) |
| OPENAI_API_KEY | **CRITICAL** | OpenAI API key - app won't function without it | sk-... |
| SPOONACULAR_API_KEY | **CRITICAL** | Spoonacular API key - recipe features won't work | (get your own) |
| DEMO_USER_ID | Yes | Your unique demo user ID | 1001 |
| GOOGLE_APPLICATION_CREDENTIALS | No | Path to GCP credentials | /path/to/creds.json |

## Getting Help

1. Check the error messages - the backend has detailed error reporting
2. Review this guide for common issues
3. Check `backend_gateway/main.py` for startup checks
4. Ask team lead for credentials or access issues
5. Post in team chat with specific error messages

## Security Notes

- Never commit `.env` file or API keys to Git
- Keep credentials secure and don't share publicly
- Use unique DEMO_USER_ID to avoid conflicts
- Rotate API keys periodically

Last updated: 2025-01-19
# Migration Guide: JSON Keys to Application Default Credentials (ADC)

## Quick Start for Team Members

### 1. Install Google Cloud SDK (if not already installed)
```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### 2. Authenticate with Google Cloud
```bash
# Login to your Google account
gcloud auth login

# Set up Application Default Credentials
gcloud auth application-default login

# Set the project
gcloud config set project adsp-34002-on02-prep-sense
```

### 3. Update Your Local Environment
```bash
# Edit your .env file
# Comment out or remove the GOOGLE_APPLICATION_CREDENTIALS line:
# GOOGLE_APPLICATION_CREDENTIALS=config/your-service-account-key.json
```

### 4. Test Your Setup
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Test Google Cloud Storage connection
python3 -c "from google.cloud import storage; client = storage.Client(); print('✅ ADC working for Google Cloud Storage!')"
```

### 5. Run the Application
```bash
python3 run_app.py
```

## Troubleshooting

### "Could not automatically determine credentials"
- Make sure you ran `gcloud auth application-default login`
- Check that you're in the correct project: `gcloud config get-value project`

### "Permission denied" errors
- Ensure your Google account has the necessary Google Cloud Storage permissions
- Contact the project admin to grant you access

### Need to use different Google accounts
```bash
# List all authenticated accounts
gcloud auth list

# Switch accounts
gcloud config set account your-email@gmail.com

# Re-run ADC login
gcloud auth application-default login
```

## Benefits of This Change

1. **Security**: No more JSON key files that could be accidentally committed
2. **Convenience**: No need to manage or share key files
3. **Accountability**: All actions are logged to individual Google accounts
4. **Best Practice**: Follows Google's security recommendations

## For CI/CD or Production

- Cloud Run/GKE: Use attached service accounts (no keys needed)
- GitHub Actions: Use Workload Identity Federation
- Other platforms: Create dedicated service accounts with minimal permissions

## Rolling Back (Not Recommended)

If you absolutely need to use a JSON key:
1. Uncomment `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
2. Ensure the path points to your key file
3. The Google Cloud client libraries will automatically use the key file if the environment variable is set
# IAM Authentication Setup Guide for PrepSense

## Overview

This guide explains how to set up IAM authentication so your team can connect to Cloud SQL without sharing passwords.

## Current Setup

- **Admin access**: Uses `postgres` user with password (for migrations, admin tasks)
- **Team access**: Uses Google accounts (IAM authentication) - no passwords needed!

## For Team Members

### 1. Initial Setup (One Time)

Your team lead needs to add you to Cloud SQL:

```bash
gcloud sql users create YOUR_EMAIL@uchicago.edu \
  --instance=prepsense-postgres \
  --type=CLOUD_IAM_USER \
  --project=adsp-34002-on02-prep-sense
```

### 2. Connect to Database

You can connect using your Google account:

```bash
# Using gcloud (easiest)
gcloud sql connect prepsense-postgres \
  --user=YOUR_EMAIL@uchicago.edu \
  --database=prepsense \
  --project=adsp-34002-on02-prep-sense
```

No password needed! It uses your Google authentication.

### 3. For Local Development

If you want to use IAM authentication in the backend:

```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Update .env file
POSTGRES_USE_IAM=true
POSTGRES_IAM_USER=YOUR_EMAIL@uchicago.edu  # Optional, auto-detected
```

## How It Works

1. **Password Authentication (Current)**
   - Simple setup
   - Uses shared password in .env
   - Good for development

2. **IAM Authentication (Recommended for Production)**
   - Uses Google accounts
   - No passwords to share or rotate
   - More secure
   - Automatic token refresh

## Backend Configuration

The backend automatically supports both authentication methods:

### Password Mode (Default)
```env
DB_TYPE=postgres
POSTGRES_USE_IAM=false
POSTGRES_PASSWORD=your-secure-password
```

### IAM Mode
```env
DB_TYPE=postgres
POSTGRES_USE_IAM=true
# Password not needed!
```

## Troubleshooting

### "Permission denied" error
- Make sure your email was added as a Cloud SQL user
- Check you're logged in: `gcloud auth list`

### "No default credentials" error
- Run: `gcloud auth application-default login`
- This creates credentials for applications to use

### Can't connect with gcloud
- Ensure you have the right project: `gcloud config set project adsp-34002-on02-prep-sense`
- Check your IP is whitelisted (happens automatically with gcloud)

## Benefits of IAM

1. **No Password Sharing**: Each person uses their own Google account
2. **Audit Trail**: Know who did what
3. **Easy Access Control**: Add/remove team members without changing passwords
4. **Automatic Token Management**: No manual token refresh needed

## Quick Test

Test your IAM connection:

```bash
# This should work without asking for a password
gcloud sql connect prepsense-postgres \
  --user=YOUR_EMAIL@uchicago.edu \
  --database=prepsense

# Once connected, try:
SELECT current_user;
```

## For Backend Development

When you need the backend to use IAM:

1. Set `POSTGRES_USE_IAM=true` in .env
2. Run `gcloud auth application-default login`
3. Restart the backend

The backend will automatically use your Google credentials!
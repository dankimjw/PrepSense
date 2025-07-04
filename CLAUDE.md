# Claude AI Assistant Guidelines for PrepSense

## Important: Decision Making and Best Practices

**You are encouraged to disagree and provide better alternatives when:**
- A feature request isn't effective or necessary
- A proposed solution goes against best practices
- There's a more efficient or elegant approach
- The implementation could cause technical debt or maintenance issues
- The user experience would be negatively impacted

Please explain your reasoning clearly when disagreeing and always suggest better alternatives.

## Important: Commit Message Policy

**DO NOT include any Claude/AI references in commit messages**

The following are explicitly forbidden in commit messages:
- ❌ "Claude" or "claude" 
- ❌ "🤖 Generated with [Claude Code]"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"
- ❌ Any AI/automated generation references

## Git Configuration

This repository has automated safeguards:
1. **Git Hook**: `.git/hooks/prepare-commit-msg` automatically removes Claude references
2. **Global Template**: `~/.gitmessage` provides clean commit template
3. **Config File**: `.claude-config` documents these requirements

## Commit Message Format

Use this format for all commits:
```
<type>: <description>

[optional body]

[optional footer]
```

Example:
```
feat: add ingredient availability checking to recipes

- Show green checkmarks for available ingredients
- Red X for missing ingredients
- Add shopping list integration
```

## Development Guidelines

1. Follow existing code conventions
2. Test changes before committing
3. Write clear, descriptive commit messages
4. Focus on what changed and why
5. Keep commits atomic and focused

## When Creating Commits

Simply use standard git commands:
```bash
git add .
git commit -m "type: clear description of changes"
git push
```

The git hook will automatically clean any accidental Claude references.

## Database Backup Strategy

### BigQuery Backup System
We maintain local backups of our BigQuery database to protect against accidental data loss.

**Important**: Database backups should NEVER be committed to the main repository.

### Creating Backups
```bash
cd /path/to/PrepSense
python3 backend_gateway/scripts/backup_bigquery_local.py
```

This creates:
- Timestamped backup folder in `bigquery_backups/` (gitignored)
- JSON exports of all tables
- Auto-generated restore script
- Backup metadata file

### Restoring from Backup
```bash
cd bigquery_backups/backup_YYYYMMDD_HHMMSS
python3 restore_tables.py
```

### Backup Storage Options
1. **Local Only**: Keep in `bigquery_backups/` directory
2. **Separate Repository**: Create a private git repo for backups
3. **Cloud Storage**: Upload to Google Drive, Dropbox, etc.

### Current Backup
- **Cloud Backup**: `Inventory_backup_2025_07_04` dataset in BigQuery
- **Local Backups**: Check `bigquery_backups/` directory

### Best Practices
- Create backups before major database changes
- Test restore process periodically
- Keep at least 3 recent backups
- Document any schema changes

### Files to Keep Local
- `backend_gateway/scripts/backup_bigquery_local.py`
- `backend_gateway/scripts/backup_bigquery_tables.py`
- `backend_gateway/scripts/BIGQUERY_BACKUP_RESTORE.md`
- All contents of `bigquery_backups/`

## Google Cloud Authentication Best Practices

### Use Application Default Credentials (ADC)
For team development, we use ADC instead of sharing JSON key files.

**Setup for each team member:**
```bash
# One-time authentication setup
gcloud auth login                          # For CLI access
gcloud auth application-default login       # For application access
gcloud config set project adsp-34002-on02-prep-sense
```

**Benefits:**
- No JSON key files to manage or accidentally commit
- OAuth tokens tied to individual Google accounts
- Better security and audit trails
- Follows Google's recommended best practices

**In code:**
```python
# The BigQueryService automatically uses ADC when no key file is specified
client = bigquery.Client()  # Uses ADC automatically
```

**Environment configuration:**
- Leave `GOOGLE_APPLICATION_CREDENTIALS` commented out in `.env`
- The service will automatically fall back to ADC

### Fallback: Service Account Keys
Only use JSON key files if:
1. ADC doesn't work in your environment
2. Deploying to a non-Google cloud platform
3. Running in Docker without Google metadata service

If you must use a key file:
- Store in `config/` directory (gitignored)
- Never commit to version control
- Rotate keys regularly
- Use least-privilege service accounts

#!/bin/bash

# Set the project and dataset
PROJECT_ID="adsp-34002-on02-prep-sense"
DATASET="Inventory"

# Get the last user ID and increment by 1
LAST_USER_ID=$(bq query --format=csv --use_legacy_sql=false --project_id=$PROJECT_ID \
    "SELECT MAX(user_id) as max_id FROM \`$PROJECT_ID.$DATASET.user\`" | \
    tail -n +2 | head -n 1 | tr -d ' ')
NEW_USER_ID=$((LAST_USER_ID + 1))

# User details
USERNAME="samantha_smith"
FIRST_NAME="Samantha"
LAST_NAME="Smith"
EMAIL="samantha.smith@example.com"
PASSWORD_HASH="$2b$12$KIXQJY0m2zLTe9Ju3lED0.wOr2FQ6MObVqpRwKiHz8cMZ6HRdiQFu"  # Default password: 'password'
API_KEY="${NEW_USER_ID}${RANDOM}${RANDOM}"  # Simple API key generation
API_KEY_B64=$(echo -n $API_KEY | base64)

# Insert into user table
echo "Inserting new user: $FIRST_NAME $LAST_NAME"
USER_QUERY=$(cat <<EOS
INSERT INTO \`$PROJECT_ID.$DATASET.user\` 
(user_id, user_name, first_name, last_name, email, password_hash, role, api_key_enc, created_at)
VALUES
($NEW_USER_ID, '$USERNAME', '$FIRST_NAME', '$LAST_NAME', '$EMAIL', 
'$PASSWORD_HASH', 'user', FROM_BASE64('$API_KEY_B64'), CURRENT_DATETIME())
EOS
)
echo "$USER_QUERY" | bq query --use_legacy_sql=false --project_id=$PROJECT_ID

# Insert into user_preference table
echo -e "\nAdding user preferences..."
PREF_QUERY=$(cat <<EOS
INSERT INTO \`$PROJECT_ID.$DATASET.user_preference\` 
(user_id, household_size, dietary_preference, allergens, cuisine_preference, created_at)
VALUES
($NEW_USER_ID, 2, ['vegetarian'], ['peanuts'], ['italian', 'mediterranean'], CURRENT_DATETIME())
EOS
)
echo "$PREF_QUERY" | bq query --use_legacy_sql=false --project_id=$PROJECT_ID

echo -e "\nUser created successfully!"
echo "User ID: $NEW_USER_ID"
echo "Username: $USERNAME"
echo "Email: $EMAIL"
echo "Password: password"  # Default password we hashed

# Verify the new user
echo -e "\nVerifying user creation..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
    "SELECT * FROM \`$PROJECT_ID.$DATASET.user\` WHERE user_id = $NEW_USER_ID"

echo -e "\nUser preferences:"
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
    "SELECT * FROM \`$PROJECT_ID.$DATASET.user_preference\` WHERE user_id = $NEW_USER_ID"

#!/bin/bash

set -e  # Exit on first error
set -o pipefail
set -u  # Treat unset variables as error

# === Configuration Parameters ===
STORAGE_ACCOUNT_NAME="$1"
CONTAINER_NAME="$2"
MANAGED_IDENTITY_CLIENT_ID="$3"
KEY_VAULT_NAME="$4"
SQL_SERVER_NAME="$5"
SQL_DB_NAME="$6"
RG_NAME="$7"
MI_BACKEND_APP="$8"
DISPLAY_NAME="$9"

# Extract the SQL server name without the domain
SQL_SERVER_NAME=$(echo "$SQL_SERVER_NAME" | cut -d'.' -f1)

# === Functions ===
log() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1" >&2
    exit 1
}

trap 'error "An unexpected error occurred. Please check the logs."' ERR

# basePath="C:/Users/$(whoami)/azscripts/azscriptinput"
# echo "${basePath}"

# === Step 1: Copy KB files ===
echo "Running copy_kb_files.sh"
bash infra/scripts/copy_kb_files.sh "$STORAGE_ACCOUNT_NAME" "$CONTAINER_NAME" "$MANAGED_IDENTITY_CLIENT_ID"
if [ $? -ne 0 ]; then
    echo "Error: copy_kb_files.sh failed."
    exit 1
fi
echo "copy_kb_files.sh completed successfully."

# === Step 2: Run create index scripts ===
log "Creating indexes..."
echo "Running run_create_index_scripts.sh"
bash infra/scripts/run_create_index_scripts.sh "$KEY_VAULT_NAME" "$MANAGED_IDENTITY_CLIENT_ID" "$SQL_SERVER_NAME" "$RG_NAME"
if [ $? -ne 0 ]; then
    echo "Error: run_create_index_scripts.sh failed."
    exit 1
fi
echo "run_create_index_scripts.sh completed successfully."


# curl -s -o create-sql-user-and-role.ps1 "${BASE_URL}infra/scripts/add_user_scripts/create-sql-user-and-role.ps1"
# chmod +x create-sql-user-and-role.ps1

# Note: You'll need to pass user info (client ID, display name, role) via environment vars or args.
# Here is a sample with hardcoded values for demo:

# === Step 3: SQL User & Role Setup ===
log "Setting up SQL users and roles..."

pwsh -File ./infra/scripts/add_user_scripts/create-sql-user-and-role.ps1 \
    -SqlServerName "$SQL_SERVER_NAME" \
    -SqlDatabaseName "$SQL_DB_NAME" \
    -ClientId "$MI_BACKEND_APP" \
    -DisplayName "$DISPLAY_NAME" \
    -ManagedIdentityClientId "$MI_BACKEND_APP" \
    -DatabaseRole "db_datareader, db_datawriter" \

log "Sample data processing completed successfully!"

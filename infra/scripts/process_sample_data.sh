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


# === Step 1: Copy KB files ===
echo "Running copy_kb_files.sh"
bash infra/scripts/copy_kb_files.sh "$STORAGE_ACCOUNT_NAME" "$CONTAINER_NAME" "$MANAGED_IDENTITY_CLIENT_ID" "$KEY_VAULT_NAME"
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

# === Step 3: SQL User & Role Setup ===
log "Setting up SQL users and roles..."

bash infra/scripts/add_user_scripts/create_sql_user_and_role.sh "$SQL_SERVER_NAME" "$SQL_DB_NAME" "$MI_BACKEND_APP" "$DISPLAY_NAME" "$MI_BACKEND_APP" "db_datareader, db_datawriter"

log "Sample data processing completed successfully!"

echo "All scripts executed successfully."
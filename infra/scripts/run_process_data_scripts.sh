#!/bin/bash

# === Configuration ===
RESOURCE_GROUP="$1"
BICEP_FILE="./../process_data_scripts.bicep"

# === Validate input ===
if [[ -z "$RESOURCE_GROUP" ]]; then
  echo "Usage: $0 <RESOURCE_GROUP>"
  echo "ERROR: RESOURCE_GROUP parameter is required."
  exit 1
fi

# === Ensure user is logged in to Azure CLI ===
az account show > /dev/null 2>&1 || az login

echo "Fetching Key Vault and Managed Identity from resource group: $RESOURCE_GROUP"

# === Retrieve the first Key Vault name from the specified resource group ===
keyVaultName=$(az keyvault list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)

# === Retrieve the ID of the first user-assigned identity with name starting with 'id-' ===
identityId=$(az identity list --resource-group "$RESOURCE_GROUP" --query "[?starts_with(name, 'id-')].id | [0]" -o tsv)

# === Normalize identityId (necessary for compatibility in Git Bash on Windows) ===
identityId=$(echo "$identityId" | sed -E 's|.*(/subscriptions/)|\1|')

# === Get the location of the first SQL Server in the resource group ===
sqlServerLocation=$(az sql server list --resource-group "$RESOURCE_GROUP" --query "[0].location" -o tsv)

# === Validate that all required resources were found ===
if [[ -z "$keyVaultName" || -z "$sqlServerLocation" || -z "$identityId" || ! "$identityId" =~ ^/subscriptions/ ]]; then
  echo "ERROR: Could not find required resources in resource group $RESOURCE_GROUP or identityId is invalid"
  exit 1
fi

echo "Using SQL Server Location: $sqlServerLocation"
echo "Using Key Vault: $keyVaultName"
echo "Using Managed Identity: $identityId"

# === Deploy resources using the specified Bicep template ===
echo "Deploying Bicep template..."

# MSYS_NO_PATHCONV disables path conversion in Git Bash for Windows
MSYS_NO_PATHCONV=1 az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$BICEP_FILE" \
  --parameters solutionLocation="$sqlServerLocation" keyVaultName="$keyVaultName" identity="$identityId"

echo "Deployment completed."

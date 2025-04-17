#!/bin/bash

# Variables
storageAccount="$1"
fileSystem="$2"
# baseUrl="$3"
managedIdentityClientId="$4"
keyVaultName="$5"  # ✅ NEW ARG REQUIRED

zipFileName1="call_transcripts.zip"
extractedFolder1="call_transcripts"
zipUrl1="infra/data/call_transcripts.zip"

zipFileName2="audio_data.zip"
extractedFolder2="audiodata"
zipUrl2="infra/data/audio_data.zip"

unzip infra/data/"$zipFileName1" -d infra/data/"$extractedFolder1"
unzip infra/data/"$zipFileName2" -d infra/data/"$extractedFolder2"

echo "Script Started"

# Authenticate with Azure
if az account show &> /dev/null; then
    echo "Already authenticated with Azure."
else
    if [ -n "$managedIdentityClientId" ]; then
        echo "Authenticating with Managed Identity..."
        az login --identity --client-id ${managedIdentityClientId}
    else
        echo "Authenticating with Azure CLI..."
        az login
    fi
    echo "Not authenticated with Azure. Attempting to authenticate..."
fi

echo "Getting signed in user id"
signed_user_id=$(az ad signed-in-user show --query id -o tsv)

echo "Getting storage account resource id"
storage_account_resource_id=$(az storage account show --name $storageAccount --query id --output tsv)

# ✅ Assign Storage Blob Data Contributor role (if not already assigned)
echo "Checking if user has the Storage Blob Data Contributor role"
storage_role_assignment=$(az role assignment list --assignee $signed_user_id --role "Storage Blob Data Contributor" --scope $storage_account_resource_id --query "[].roleDefinitionId" -o tsv)

if [ -z "$storage_role_assignment" ]; then
    echo "Assigning Storage Blob Data Contributor role..."
    az role assignment create --assignee $signed_user_id --role "Storage Blob Data Contributor" --scope $storage_account_resource_id --output none
    echo "Role assignment for Blob Storage completed."
else
    echo "User already has Storage Blob Data Contributor role."
fi

# ✅ Assign Key Vault Secrets User role (NEW BLOCK)
echo "Getting Key Vault resource ID"
key_vault_resource_id=$(az keyvault show --name $keyVaultName --query id --output tsv)

echo "Checking if user has Key Vault Secrets User role"
kv_role_assignment=$(az role assignment list --assignee $signed_user_id --role "Key Vault Secrets User" --scope $key_vault_resource_id --query "[].roleDefinitionId" -o tsv)

if [ -z "$kv_role_assignment" ]; then
    echo "Assigning Key Vault Secrets User role..."
    az role assignment create --assignee $signed_user_id --role "Key Vault Secrets User" --scope $key_vault_resource_id --output none
    echo "Role assignment for Key Vault completed."
else
    echo "User already has Key Vault Secrets User role."
fi

# Upload files to Azure Storage
echo "Uploading files to Azure Storage"
az storage blob upload-batch --account-name "$storageAccount" --destination "$fileSystem"/"$extractedFolder1" --source infra/data/"$extractedFolder1" --auth-mode login --pattern '*' --overwrite --output none
az storage blob upload-batch --account-name "$storageAccount" --destination "$fileSystem"/"$extractedFolder2" --source infra/data/"$extractedFolder2" --auth-mode login --pattern '*' --overwrite --output none
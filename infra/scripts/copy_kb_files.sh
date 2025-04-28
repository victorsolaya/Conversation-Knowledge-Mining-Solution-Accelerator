#!/bin/bash

# Variables
storageAccount="$1"
fileSystem="$2"
managedIdentityClientId="$3"
keyVaultName="$4"

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
        if ! az login --identity --client-id "$managedIdentityClientId" &> /dev/null; then
            echo "Failed to authenticate with Managed Identity. Falling back to Azure CLI login."
            az login
            if [ $? -ne 0 ]; then
                echo "Azure CLI login failed. Please authenticate manually and rerun the script."
                exit 1
            fi
        fi
    else
        echo "No Managed Identity Client ID provided. Attempting Azure CLI login..."
        az login
        if [ $? -ne 0 ]; then
            echo "Azure CLI login failed. Please authenticate manually and rerun the script."
            exit 1
        fi
    fi
fi

echo "Getting signed in user id"
signed_user_id=$(az ad signed-in-user show --query id -o tsv)

echo "Getting storage account resource id"
storage_account_resource_id=$(az storage account show --name $storageAccount --query id --output tsv)

#check if user has the Storage Blob Data Contributor role, add it if not
echo "Checking if user has the Storage Blob Data Contributor role"
role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list --assignee $signed_user_id --role "Storage Blob Data Contributor" --scope $storage_account_resource_id --query "[].roleDefinitionId" -o tsv)
if [ -z "$role_assignment" ]; then
    echo "User does not have the Storage Blob Data Contributor role. Assigning the role."
    MSYS_NO_PATHCONV=1 az role assignment create --assignee $signed_user_id --role "Storage Blob Data Contributor" --scope $storage_account_resource_id --output none
    if [ $? -eq 0 ]; then
        echo "Role assignment completed successfully."
    else
        echo "Error: Role assignment failed."
        exit 1
    fi
else
    echo "User already has the Storage Blob Data Contributor role."
fi

# Upload files to Azure Storage
echo "Uploading files to Azure Storage"
az storage blob upload-batch --account-name "$storageAccount" --destination "$fileSystem"/"$extractedFolder1" --source infra/data/"$extractedFolder1" --auth-mode login --pattern '*' --overwrite --output none
az storage blob upload-batch --account-name "$storageAccount" --destination "$fileSystem"/"$extractedFolder2" --source infra/data/"$extractedFolder2" --auth-mode login --pattern '*' --overwrite --output none
#!/bin/bash

# Variables
deployment_name="ai-model-deployment"
bicep_file="./infra/deploy_ai_model.bicep"

# Parameters
resource_group_name="$1"
solution_name="$2"
deployment_type="$3"
gpt_model_name="$4"
gpt_deployment_capacity="$5"
embedding_model="$6"
embedding_deployment_capacity="$7"
managedIdentityClientId="$8"

# # Check if Azure CLI is installed
# if ! command -v az &> /dev/null
# then
#     echo "Azure CLI not found. Installing Azure CLI..."
#     # Install Azure CLI for Debian-based systems
#     curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
#     if ! command -v az &> /dev/null
#     then
#         echo "Azure CLI installation failed. Please install it manually and rerun the script."
#         exit 1
#     fi
# fi

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

# Execute the Bicep deployment
az deployment group create \
  --resource-group $resource_group_name \
  --name $deployment_name \
  --template-file $bicep_file \
  --parameters solutionName=$solution_name \
               deploymentType=$deployment_type \
               gptModelName=$gpt_model_name \
               gptDeploymentCapacity=$gpt_deployment_capacity \
               embeddingModel=$embedding_model \
               embeddingDeploymentCapacity=$embedding_deployment_capacity
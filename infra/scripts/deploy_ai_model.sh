#!/bin/bash

set -e  # Exit on first error
set -o pipefail
set -u  # Treat unset variables as error

# Parameters
resource_group_name="$1"
solution_name="$2"
deployment_type="$3"
gpt_model_name="$4"
gpt_deployment_capacity="$5"
embedding_model="$6"
embedding_deployment_capacity="$7"
managedIdentityClientId="$8"

# Get parameters from azd env, if not provided
if [ -z "$resource_group_name" ]; then
    resource_group_name=$(azd env get-value RESOURCE_GROUP_NAME)
fi

if [ -z "$solution_name" ]; then
    solution_name=$(azd env get-value SOLUTION_NAME)
fi

if [ -z "$deployment_type" ]; then
    deployment_type=$(azd env get-value AZURE_OPEN_AI_MODEL_DEPLOYMENT_TYPE)
fi

if [ -z "$gpt_model_name" ]; then
    gpt_model_name=$(azd env get-value AZURE_OPEN_AI_DEPLOYMENT_MODEL)
fi

if [ -z "$gpt_deployment_capacity" ]; then
    gpt_deployment_capacity=$(azd env get-value AZURE_OPEN_AI_DEPLOYMENT_MODEL_CAPACITY)
fi

if [ -z "$embedding_model" ]; then
    embedding_model=$(azd env get-value AZURE_OPENAI_EMBEDDING_MODEL)
fi

if [ -z "$embedding_deployment_capacity" ]; then
    embedding_deployment_capacity=$(azd env get-value AZURE_OPENAI_EMBEDDING_MODEL_CAPACITY)
fi

if [ -z "$managedIdentityClientId" ]; then
    managedIdentityClientId=$(azd env get-value MANAGED_IDENTITY_CLIENT_ID)
fi

# Check if all required arguments are provided
if [ -z "$resource_group_name" ] || [ -z "$solution_name" ] || [ -z "$deployment_type" ] || [ -z "$gpt_model_name" ] || [ -z "$gpt_deployment_capacity" ] || [ -z "$embedding_model" ] || [ -z "$embedding_deployment_capacity" ] || [ -z "$managedIdentityClientId" ]; then
    echo "Usage: $0 <resource_group_name> <solution_name> <deployment_type> <gpt_model_name> <gpt_deployment_capacity> <embedding_model> <embedding_deployment_capacity> <managedIdentityClientId>"
    exit 1
fi

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

# === Execute the Bicep Deployment ===
deployment_name="ai-model-deployment"
bicep_file="./infra/deploy_ai_model.bicep"

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

echo "GPT and Embedding Model Deployment completed successfully."
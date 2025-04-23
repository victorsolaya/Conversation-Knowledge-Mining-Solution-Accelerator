#!/bin/bash

# Variables
DEPLOYMENT_NAME="ai-model-deployment"
BICEP_FILE="./infra/deploy_ai_model.bicep"

# Parameters
RESOURCE_GROUP_NAME="$1"
SOLUTION_NAME="$2"
DEPLOYMENT_TYPE="$3"
GPT_MODEL_NAME="$4"
GPT_DEPLOYMENT_CAPACITY="$5"
EMBEDDING_MODEL="$6"
EMBEDDING_DEPLOYMENT_CAPACITY="$7"

# Execute the Bicep deployment
az deployment group create \
  --resource-group $RESOURCE_GROUP_NAME \
  --name $DEPLOYMENT_NAME \
  --template-file $BICEP_FILE \
  --parameters solutionName=$SOLUTION_NAME \
               deploymentType=$DEPLOYMENT_TYPE \
               gptModelName=$GPT_MODEL_NAME \
               gptDeploymentCapacity=$GPT_DEPLOYMENT_CAPACITY \
               embeddingModel=$EMBEDDING_MODEL \
               embeddingDeploymentCapacity=$EMBEDDING_DEPLOYMENT_CAPACITY
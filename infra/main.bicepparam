using './main.bicep'

param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'env_name')
param contentUnderstandingLocation = 'West US'
param secondaryLocation = 'eastus2'
param deploymentType = 'GlobalStandard'
param gptModelName = 'gpt-4o-mini'
param gptDeploymentCapacity = 100
param embeddingModel = 'text-embedding-ada-002'
param embeddingDeploymentCapacity = 80


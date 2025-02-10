using './main.bicep'

param solutionPrefix = 'ckmazd'
param contentUnderstandingLocation = 'West US'
param secondaryLocation = 'eastus2'
param deploymentType = 'GlobalStandard'
param gptModelName = 'gpt-4o-mini'
param gptDeploymentCapacity = 100
param embeddingModel = 'text-embedding-ada-002'
param embeddingDeploymentCapacity = 80


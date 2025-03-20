param imageTag string
param applicationInsightsId string
param solutionName string
@secure()
param appSettings object = {}
param appServicePlanId string
@secure()
param azureOpenAIKey string
@secure()
param azureAiProjectConnString string
@secure()
param azureSearchAdminKey string
// param azureOpenAIKeyName string
// param keyVaultName string
param userassignedIdentityId string

var imageName = 'DOCKER|kmcontainerreg.azurecr.io/km-app:${imageTag}'
var name = '${solutionName}-backend-docker'

module appService 'deploy_app_service.bicep' = {
  name: '${name}-app-module'
  params: {
    solutionName: name
    appServicePlanId: appServicePlanId
    appImageName: imageName
    userassignedIdentityId:userassignedIdentityId
    appSettings: union(
      appSettings,
      {
        AZURE_OPENAI_API_KEY: azureOpenAIKey
        APPINSIGHTS_INSTRUMENTATIONKEY: reference(applicationInsightsId, '2015-05-01').InstrumentationKey
        AZURE_AI_SEARCH_API_KEY: azureSearchAdminKey
        AZURE_AI_PROJECT_CONN_STRING:azureAiProjectConnString
      }
    )
  }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2022-08-15' existing = {
  name: appSettings.AZURE_COSMOSDB_ACCOUNT
}

resource contributorRoleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-05-15' existing = {
  parent: cosmos
  name: '00000000-0000-0000-0000-000000000002'
}

resource role 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2022-05-15' = {
  parent: cosmos
  name: guid(contributorRoleDefinition.id, cosmos.id)
  properties: {
    principalId: appService.outputs.identityPrincipalId
    roleDefinitionId: contributorRoleDefinition.id
    scope: cosmos.id
  }
}

output appUrl string = appService.outputs.appUrl

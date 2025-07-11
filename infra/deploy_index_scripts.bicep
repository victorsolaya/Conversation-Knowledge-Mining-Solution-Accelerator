@description('Specifies the location for resources.')
param solutionLocation string 

param baseUrl string
param keyVaultName string
param managedIdentityObjectId string
param managedIdentityClientId string

resource create_index 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  kind:'AzureCLI'
  name: 'create_search_indexes'
  location: solutionLocation // Replace with your desired location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityObjectId}' : {}
    }
  }
  properties: {
    azCliVersion: '2.52.0'
    primaryScriptUri: '${baseUrl}infra/scripts/run_create_index_scripts.sh' 
    arguments: '${baseUrl} ${keyVaultName} ${managedIdentityClientId}'
    timeout: 'PT1H'
    retentionInterval: 'PT1H'
    cleanupPreference:'OnSuccess'
  }
}

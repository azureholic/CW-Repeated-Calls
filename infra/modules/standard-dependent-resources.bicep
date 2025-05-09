// Creates Azure dependent resources for Azure AI Agent Service standard agent setup

@description('Azure region of the deployment')
param location string = resourceGroup().location

@description('Tags to add to the resources')
param tags object = {}

@description('AI services name')
param aiServicesName string

@description('The name of the Key Vault')
param keyvaultName string

@description('Models to deploy.')
param deployments array = []

@description('The AI Service Account full ARM Resource ID. This is an optional field, and if not provided, the resource will be created.')
param aiServiceAccountResourceId string

param cosmosAccountName string = 'agentcosmosdb-${uniqueString(resourceGroup().id)}'
param cosmosDatabaseName string = 'agentdb'
param cosmosDocumentContainerName string = 'agentresults'
param cosmosHistoryContainerName string = 'agenthistory'
param cosmosThreadContainerLeaseName string = 'agentresultsleases'
param cosmosDocumentContainerLeaseName string = 'agenthistoryleases'

param sqlRoleName string = 'agent-sql-role'

param appInsightsName string = 'appinsights-${uniqueString(resourceGroup().id)}'

var aiServiceExists = aiServiceAccountResourceId != ''


module workspace 'br/public:avm/res/operational-insights/workspace:0.7.1' = {
  name: 'workspaceDeployment'
  params: {
    name: appInsightsName
    location: resourceGroup().location
  }
}
module appInsights 'br/public:avm/res/insights/component:0.4.1' = {
  name: 'appInsightsFunctionApp'
  params: {
    name: appInsightsName
    workspaceResourceId: workspace.outputs.resourceId
    location: resourceGroup().location
    kind: 'web'
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: keyvaultName
  location: location
  tags: tags
  properties: {
    createMode: 'default'
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableSoftDelete: true
    enableRbacAuthorization: true
    enablePurgeProtection: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
    sku: {
      family: 'A'
      name: 'standard'
    }
    softDeleteRetentionInDays: 7
    tenantId: subscription().tenantId
  }
}


var aiServiceParts = split(aiServiceAccountResourceId, '/')

resource existingAIServiceAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = if (aiServiceExists) {
  name: aiServiceParts[8]
  scope: resourceGroup(aiServiceParts[2], aiServiceParts[4])
}

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' = if(!aiServiceExists) {
  name: aiServicesName
  location: resourceGroup().location
  sku: {
    name: 'S0'
  }
  kind: 'AIServices' // or 'OpenAI'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: toLower('${(aiServicesName)}')
    publicNetworkAccess: 'Enabled'
  }
}



@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [for deployment in deployments: {
  parent: aiServices
  name: deployment.name
  properties: {
    model: deployment.model
  }
   sku: deployment.?sku ?? {
    name: 'DataZoneStandard'
    capacity: 20
  }  
}]

module cosmosDB 'br/public:avm/res/document-db/database-account:0.8.0' = {
  name: cosmosDatabaseName
  params: {
    name: cosmosAccountName
    location: 'francecentral'
    networkRestrictions: {
      publicNetworkAccess: 'Enabled'
      ipRules: []
      virtualNetworkRules: []
    }
    sqlDatabases: [
      {
        name: cosmosDatabaseName
        containers: [
          {
            indexingPolicy: {
              automatic: true
            }
            name: cosmosDocumentContainerName
            paths: [
              '/userId'
            ]
          }
          {
            indexingPolicy: {
              automatic: true
            }
            name: cosmosHistoryContainerName
            paths: [
              '/userId'
            ]
          }
          {
            indexingPolicy: {
              automatic: true
            }
            name: cosmosDocumentContainerLeaseName
            paths: [
              '/id'
            ]
          }
          {
            indexingPolicy: {
              automatic: true
            }
            name: cosmosThreadContainerLeaseName
            paths: [
              '/id'
            ]
          }
        ]
      }
    ]
    sqlRoleDefinitions: [
      {
        name: sqlRoleName
        dataAction: [
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/write'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/read'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/delete'
        ]
      }
    ]
  }
}

output aiServicesName string =  aiServiceExists ? existingAIServiceAccount.name : aiServicesName
output aiservicesID string = aiServiceExists ? existingAIServiceAccount.id : aiServices.id
output aiservicesTarget string = aiServiceExists ? existingAIServiceAccount.properties.endpoint : aiServices.properties.endpoint
output aiServiceAccountResourceGroupName string = aiServiceExists ? aiServiceParts[4] : resourceGroup().name
output aiServiceAccountSubscriptionId string = aiServiceExists ? aiServiceParts[2] : subscription().subscriptionId 


output appInsightsId string= appInsights.outputs.resourceId

output keyvaultId string = keyVault.id

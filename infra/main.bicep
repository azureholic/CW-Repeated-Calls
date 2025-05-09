// Parameters
@description('Name for the AI resource and used to derive name of dependent resources.')
param aiHubName string = 'hub-${uniqueString(resourceGroup().id)}'

@description('Friendly name for your Hub resource')
param aiHubFriendlyName string = 'Agents Hub resource'

@description('Description of your Azure AI resource displayed in AI studio')
param aiHubDescription string = 'This is an example AI resource for use in Azure AI Studio.'

@description('Name for the AI project resources.')
param aiProjectName string = 'project-${uniqueString(resourceGroup().id)}'

@description('Friendly name for your Azure AI resource')
param aiProjectFriendlyName string = 'Agents Project resource'

@description('Description of your Azure AI resource displayed in AI studio')
param aiProjectDescription string = 'This is an example AI Project resource for use in Azure AI Studio.'

@description('Azure region used for the deployment of all resources.')
param location string = resourceGroup().location

@description('Set of tags to apply to all resources.')
param tags object = {}

@description('Name for capabilityHost.')
param capabilityHostName string = 'caphost1-${uniqueString(resourceGroup().id)}'

@description('Name of the Azure AI Services account')
param aiServicesName string = 'ai-services-${uniqueString(resourceGroup().id)}'

@description('Model name for deployment')
param chatCompletionModelName string = 'gpt-4o'

@description('Model format for deployment')
param chatCompletionModelFormat string = 'OpenAI'

@description('Model version for deployment')
param chatCompletionModelVersion string = '2024-11-20'

@description('Model name for deployment')
param reasoningModelName string = 'o3-mini'

@description('Model format for deployment')
param reasoningModelFormat string = 'OpenAI'

@description('Model version for deployment')
param reasoningModelVersion string = '2025-01-31'

// @description('Model deployment location. If you want to deploy an Azure AI resource/model in different location than the rest of the resources created.')
// param modelLocation string = 'swedencentral'

@description('AI Service Account kind: either AzureOpenAI or AIServices')
param aiServiceKind string = 'AIServices'

@description('AI Service Account kind: either AzureOpenAI or AIServices')
param serviceBusName string = 'servicebus-${uniqueString(resourceGroup().id)}'

@description('The AI Service Account full ARM Resource ID. This is an optional field, and if not provided, the resource will be created.')
param aiServiceAccountResourceId string = ''

// Variables
var name = toLower('${aiHubName}')
var projectName = toLower('${aiProjectName}')

var aiServiceExists = aiServiceAccountResourceId != ''

var aiServiceParts = split(aiServiceAccountResourceId, '/')
var aiServiceAccountSubscriptionId = aiServiceExists ? aiServiceParts[2] : subscription().subscriptionId 
var aiServiceAccountResourceGroupName = aiServiceExists ? aiServiceParts[4] : resourceGroup().name


// Dependent resources for the Azure Machine Learning workspace
module aiDependencies 'modules/standard-dependent-resources.bicep' = {
  name: 'dependencies-${name}-deployment'
  params: {
    location: location
    keyvaultName: 'kv-${name}'
    aiServicesName: aiServicesName
    tags: tags    
    deployments: [
      {
        model: {
          format: chatCompletionModelFormat
          name: chatCompletionModelName
          version: chatCompletionModelVersion
        }
        name: chatCompletionModelName
        //sku: chatCompletionModelSkuName
      }
      {
        model: {
          format: reasoningModelFormat
          name: reasoningModelName
          version: reasoningModelVersion
        }
        name: reasoningModelName
        //sku:reasoningModelSkuName
      }
      
    ]
     aiServiceAccountResourceId: aiServiceAccountResourceId
    }
}

module aiHub 'modules/standard-ai-hub.bicep' = {
  name: '${name}-deployment'
  params: {
    // workspace organization
    aiHubName: name
    aiHubFriendlyName: aiHubFriendlyName
    aiHubDescription: aiHubDescription
    location: location
    tags: tags

    aiServicesName: aiDependencies.outputs.aiServicesName
    aiServiceKind: aiServiceKind
    aiServicesId: aiDependencies.outputs.aiservicesID
    aiServicesTarget: aiDependencies.outputs.aiservicesTarget
    aiServiceAccountResourceGroupName:aiDependencies.outputs.aiServiceAccountResourceGroupName
    aiServiceAccountSubscriptionId:aiDependencies.outputs.aiServiceAccountSubscriptionId
    
    keyVaultId: aiDependencies.outputs.keyvaultId
    appInsightsId: aiDependencies.outputs.appInsightsId
  }
}


module aiProject 'modules/standard-ai-project.bicep' = {
  name: '${projectName}-deployment'
  params: {
    // workspace organization
    aiProjectName: projectName
    aiProjectFriendlyName: aiProjectFriendlyName
    aiProjectDescription: aiProjectDescription
    location: location
    tags: tags
    aiHubId: aiHub.outputs.aiHubID
  }
}

module aiServiceRoleAssignments 'modules/ai-service-role-assignments.bicep' = {
  name: 'ai-service-role-assignments-${projectName}-deployment'
  scope: resourceGroup(aiServiceAccountSubscriptionId, aiServiceAccountResourceGroupName)
  params: {
    aiServicesName: aiDependencies.outputs.aiServicesName
    aiProjectPrincipalId: aiProject.outputs.aiProjectPrincipalId
    aiProjectId: aiProject.outputs.aiProjectResourceId
  }
}

module addCapabilityHost 'modules/add-capability-host.bicep' = {
  name: 'capabilityHost-configuration--${uniqueString(resourceGroup().id)}-deployment'
  params: {
    capabilityHostName: capabilityHostName
    aiHubName: aiHub.outputs.aiHubName
    aiProjectName: aiProject.outputs.aiProjectName
    aoaiConnectionName: aiHub.outputs.aoaiConnectionName
  }
}

module namespace 'br/public:avm/res/service-bus/namespace:0.14.1' = {
  name: 'servicebus-${uniqueString(resourceGroup().id)}-deployment'
  params: {
    // Required parameters
    name: serviceBusName
    // Non-required parameters
    skuObject: {
      capacity: 2
      name: 'Premium'
    }
  }
}

output PROJECT_CONNECTION_STRING string = aiProject.outputs.projectConnectionString

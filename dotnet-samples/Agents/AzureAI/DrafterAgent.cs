using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents.AzureAI
{
    internal class DrafterAgent
    {
        public async Task<AzureAIAgent> CreateAgent(Kernel kernel, string agentName, string systemPrompt)
        {
            Kernel agentKernel = kernel.Clone();
            var plugins = agentKernel.Plugins;

            var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
            string model = chatCompletion.Attributes["DeploymentName"].ToString();

            var client = agentKernel.GetRequiredService<PersistentAgentsClient>();
            var definition = await client.Administration.CreateAgentAsync(
               model: model,
               name: agentName,
               instructions: systemPrompt);

            AzureAIAgent drafterAgent = new(definition, client, plugins: agentKernel.Plugins)
            {

                Arguments = new KernelArguments(
                    new OpenAIPromptExecutionSettings()
                    {
                        Temperature = 0,
                        FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true }),
                    })
            };

            return drafterAgent;
        }
    }
}

using Azure.AI.Agents.Persistent;
using cw_repeated_calls_dotnet.PromptEngineering;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents.AzureAI
{
    internal class ReviewerAgent
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
               instructions: systemPrompt,
                responseFormat: BinaryData.FromString(JsonSerializer.Serialize(new
                {
                     type = "json_schema",
                     json_schema = new
                     {
                          name = "offerResult",
                          description = "Review the offer and provide feedback.",
                          schema = new
                          {
                            type = "object",
                            properties = new
                            {
                                productId = new { type = "integer", description = "The ID of the product causing the issue" },
                                customerId = new { type = "integer", description = "The ID of the customer" },
                                advice = new { type = "string", description = "Advice about the offer to compensate the customer" },
                            },
                            required = new[] { "productId", "customerId", "advice" }
                          }
                     }
                }))
               );

            AzureAIAgent reviewAgent = new(definition, client, plugins: agentKernel.Plugins)
            {
                Arguments = new KernelArguments(
                    new OpenAIPromptExecutionSettings()
                    {
                        Temperature = 0,
                        FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true }),
                    })
            };

            return reviewAgent;
        }
    }
}

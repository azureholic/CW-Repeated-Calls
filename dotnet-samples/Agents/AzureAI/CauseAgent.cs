using Azure.AI.Agents.Persistent;
using Azure.Identity;
using cw_repeated_calls_dotnet.Agents.SemanticKernel;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.PromptEngineering;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;
using ModelContextProtocol.Protocol;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents.AzureAI
{
    public class CauseAgent : IAgent<CauseResult>
    {
        public async Task<CauseResult> GetAgentResponseAsync(Kernel kernel, RepeatedCallState state)
        {
            Kernel agentKernel = kernel.Clone();
            var plugins = agentKernel.Plugins;

            var prompts = new CausePrompts(state);

            var client = agentKernel.GetRequiredService<PersistentAgentsClient>();
            var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
            string model = chatCompletion.Attributes["DeploymentName"].ToString();

            var definition = await client.Administration.CreateAgentAsync(
               model: model,
               name: "CauseAgent",
               instructions: prompts.SystemPrompt,
               responseFormat: BinaryData.FromString(JsonSerializer.Serialize(new
               {
                   type = "json_schema",
                   json_schema = new
                   {
                       name = "cause",
                       description = "Extract cause information.",
                       schema = new
                       {
                           type = "object",
                           properties = new
                           {
                               productId = new { type = "string", description = "The ID of the product causing the issue" },
                               customerId = new { type = "integer", description = "The ID of the customer" },
                               analysis = new { type = "string", description = "Analysis of the problem" },
                               conclusion = new { type = "string", description = "Conclusion of the analysis" },
                               isOperationsCause = new { type = "boolean", description = "Whether the issue is caused by operations" }
                           },
                           required = new[] { "productId", "customerId", "analysis", "conclusion", "isOperationsCause" }
                       }
                   }
               }))
               );

            AzureAIAgent causeAgent = new(definition, client, plugins:agentKernel.Plugins)
            {
                
                Arguments = new KernelArguments(
                    new OpenAIPromptExecutionSettings()
                    {
                        Temperature = 0,
                        FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true }),
                    })
            };

            AzureAIAgentThread thread = new AzureAIAgentThread(client, state.ThreadId);
            ChatMessageContent message = new(AuthorRole.User, prompts.UserPrompt);

            CauseResult causeResult = null;

            try
            {
                ChatMessageContent response = await causeAgent.InvokeAsync(message, thread: thread).FirstAsync();
                causeResult = JsonSerializer.Deserialize<CauseResult>(response!.ToString());
                
            }
            finally
            {
                await client.Administration.DeleteAgentAsync(causeAgent.Id);
            }
            
            if (causeResult == null)
            {
                throw new InvalidOperationException("Failed to deserialize the response from the Cause Agent.");
            }
            return causeResult;
        }
    }
}

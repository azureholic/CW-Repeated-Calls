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
using ModelContextProtocol.Protocol;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents.AzureAI
{
    public class RepeatedCallAgent: IAgent<RepeatedCallResult>
    {
        public async Task<RepeatedCallResult> GetAgentResponseAsync(Kernel kernel, RepeatedCallState state)
        {
            var prompts = new RepeatedCallPrompts(state);

            Kernel agentKernel = kernel.Clone();
            var plugins = agentKernel.Plugins;

            var client = agentKernel.GetRequiredService<PersistentAgentsClient>();
            var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
            string model = chatCompletion.Attributes["DeploymentName"].ToString();

            var definition = await client.Administration.CreateAgentAsync(
               model: model,
               name: "RepeatedCallAgent",
               instructions: prompts.SystemPrompt,
               responseFormat: BinaryData.FromString(JsonSerializer.Serialize(new
               {
                   type = "json_schema",
                   json_schema = new
                   {
                       name = "repeatedcall",
                       description = "Repeated call schema.",
                       schema = new
                       {
                           type = "object",
                           properties = new
                           {
                               customerId = new { type = "integer", description = "The ID of the customer" },
                               analysis = new { type = "string", description = "Analysis of the problem" },
                               conclusion = new { type = "string", description = "Conclusion of the analysis" },
                               isRepeatedCall = new { type = "boolean", description = "Whether this is a repeated call or not" },
                           },
                           required = new[] { "customerId", "analysis", "conclusion", "isRepeatedCall" }
                       }
                   }
               }))
               );

            AzureAIAgent repeatedCallAgent = new(definition, client, plugins: agentKernel.Plugins)
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

            RepeatedCallResult repeatedCallResult = null;
            try
            {
                ChatMessageContent response = await repeatedCallAgent.InvokeAsync(message, thread: thread).FirstAsync();
                repeatedCallResult = JsonSerializer.Deserialize<RepeatedCallResult>(response.Content!.ToString());
            }
            finally
            {
                await client.Administration.DeleteAgentAsync(repeatedCallAgent.Id);
            }

            return repeatedCallResult ?? throw new InvalidOperationException("Failed to deserialize the response from the Cause Agent.");

        }
    }
}

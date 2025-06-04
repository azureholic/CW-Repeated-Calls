using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.PromptEngineering;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents.SemanticKernel
{
    public class CauseAgent : IAgent<CauseResult>
    {
        public async Task<CauseResult> GetAgentResponseAsync(Kernel kernel, RepeatedCallState state)
        {
            var prompts = new CausePrompts(state);

            ChatCompletionAgent causeAgent = CreateAgent(kernel, "CauseAgent", prompts.SystemPrompt);
            ChatHistory history = new ChatHistory();
            ChatHistoryAgentThread agentThread = new(history);
            ChatMessageContent response = await causeAgent.InvokeAsync(prompts.UserPrompt).FirstAsync();
            var formattedResponse = JsonSerializer.Deserialize<CauseResult>(response.Content!.ToString());
            return formattedResponse ?? throw new InvalidOperationException("Failed to deserialize the response from the Cause Agent.");
        }

        private ChatCompletionAgent CreateAgent(Kernel kernel, string agentName, string instructions)
        {
            // Clone kernel instance to allow for agent specific plug-in definition
            Kernel agentKernel = kernel.Clone();

            // Define the instruction for the agent
            return
                new ChatCompletionAgent()
                {
                    Name = agentName,
                    Description = "Agent responsible for extracting requirements from documents.",
                    Instructions = instructions,
                    Kernel = agentKernel,
                    Arguments = new KernelArguments(
                        new OpenAIPromptExecutionSettings()
                        {
                            Temperature = 0,
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true }),
                            ResponseFormat = typeof(CauseResult),
                        })
                };

        }
    }
}

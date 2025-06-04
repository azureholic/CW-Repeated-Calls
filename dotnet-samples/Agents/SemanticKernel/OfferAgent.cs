using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.PromptEngineering;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
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
    internal class OfferAgent : IAgent<OfferResult>
    {
        public async Task<OfferResult> GetAgentResponseAsync(Kernel kernel, RepeatedCallState state)
        {
            var prompts = new RecommendationPrompts(state);

            ChatCompletionAgent drafterAgent = new DrafterAgent().CreateAgent(kernel, "DrafterAgent", prompts.DrafterSystemPrompt);
            ChatCompletionAgent reviewerAgent = new ReviewerAgent().CreateAgent(kernel, "ReviewerAgent", prompts.ReviewerSystemPrompt);
            KernelFunction terminationFunction = AgentGroupChat.CreatePromptFunctionForStrategy(prompts.TerminationPrompt);
            string terminationToken = prompts.TerminationToken;

            AgentGroupChat chat = new(drafterAgent, reviewerAgent)
            {
                ExecutionSettings = new AgentGroupChatSettings
                {
                    TerminationStrategy = new KernelFunctionTerminationStrategy(terminationFunction, kernel)
                    {
                        Agents = [reviewerAgent],
                        HistoryVariableName = "lastmessage",
                        MaximumIterations = 3,
                        ResultParser = (result) => result.GetValue<string>()?.Contains(terminationToken, StringComparison.OrdinalIgnoreCase) ?? false,
                        Arguments = new KernelArguments(
                        new OpenAIPromptExecutionSettings()
                        {
                            Temperature = 0,
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true }),
                        })
                    }
                }
            };

            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, content: prompts.UserPrompt));
            IAsyncEnumerable<ChatMessageContent> messages = null;

            await foreach (ChatMessageContent response in chat.InvokeAsync())
            {
            }
            messages = chat.GetChatMessagesAsync(reviewerAgent);

            var lastMessage = await messages.FirstOrDefaultAsync();

            var offerResult = JsonSerializer.Deserialize<OfferResult>(lastMessage.Content!.ToString());
            return offerResult;
        }
       
    }
}

using cw_repeated_calls_dotnet.Agents;
using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using Microsoft.Extensions.Logging;
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

namespace cw_repeated_calls_dotnet
{
    public class DetermineRepeatedCallerStep : KernelProcessStep
    {
        public string AgentServiceKey { get; set; } = "CustomerDataExtractor";

        [KernelFunction("determine_repeated_caller")]
        public async Task RepeatedCallAsync(KernelProcessStepContext context, Kernel kernel, IncomingMessage incomingMessage)
        {
            int customerId = incomingMessage.CustomerId;

            // Get the chat history
            // IChatHistoryProvider historyProvider = kernel.GetHistory();todo, this doesn't work in current version (kernel.GetHistory)
            ChatHistory history = new ChatHistory();
            ChatHistoryAgentThread agentThread = new(history);

            ChatCompletionAgent customerDataAgent = new CustomerDataAgent().CreateAgent(kernel, AgentServiceKey, customerId);

            string userInput = $"""
                ## Customer ID: {customerId}
                
                """;

            // Obtain the agent response todo, this doesn't work in current version (kernel.GetAgent)
            // ChatCompletionAgent agent = kernel.GetAgent<ChatCompletionAgent>(AgentServiceKey);
            List<ChatMessageContent> messages = new();
            await foreach (ChatMessageContent message in customerDataAgent.InvokeAsync(new ChatMessageContent(AuthorRole.User, userInput), agentThread))
            {
                // Both the input message and response message will automatically be added to the thread, which will update the internal chat history.
                messages.Add(message);
                // Emit event for each agent response
                // await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponse, Data = message });
                Console.WriteLine(message.ToString());

            }

            var repeatedCallResult = await IsRepeatedCall(kernel, history);
            
            if (repeatedCallResult.IsRepeatedCall)
            {
                await context.EmitEventAsync("IsRepeatedCall", data: repeatedCallResult);
            }
            else
            {
                await context.EmitEventAsync("IsNotRepeatedCall");
            }

        }

        private static async Task<RepeatedCallResult> IsRepeatedCall(Kernel kernel, ChatHistory history)
        {
            string userInput = $"""
                Based on the information provided, is the current call a repeated call about the same issue? 
                Please analyze the timing between calls, similarity of issues discussed, and provide your reasoning.
                """;

            ChatHistory localHistory =
            [
                new ChatMessageContent(AuthorRole.System, userInput),
            .. history.TakeLast(1)
            ];
           

            IChatCompletionService service = kernel.GetRequiredService<IChatCompletionService>();

            ChatMessageContent response = await service.GetChatMessageContentAsync(localHistory, new OpenAIPromptExecutionSettings { ResponseFormat = typeof(RepeatedCallResult) });
            RepeatedCallResult intent = JsonSerializer.Deserialize<RepeatedCallResult>(response.ToString())!;

            return intent;
        }

    }

}
using Azure;
using cw_repeated_calls_dotnet.Agents;
using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.Helpers;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;


public class DetermineCauseStep : KernelProcessStep
{
    private string AgentServiceKey { get; set; } = "OperationsDataExtractor";

    private string subscriptionCsvPath = "Data\\subscription.csv";
    private string softwareUpdateCsvPath = "Data\\software_update.csv";
    private string productCsvPath = "Data\\product.csv";

    [KernelFunction]
    public async Task DetermineCause(KernelProcessStepContext context, Kernel kernel, RepeatedCallResult result)
    {

        int customerId = result.CustomerId;

        // Get the chat history
        // IChatHistoryProvider historyProvider = kernel.GetHistory();todo, this doesn't work in current version (kernel.GetHistory)
        ChatHistory history = new ChatHistory();
        ChatHistoryAgentThread agentThread = new(history);

        ChatCompletionAgent customerDataAgent = new OperationsAgent().CreateAgent(kernel, AgentServiceKey, customerId);

        var userPrompt = JsonSerializer.Serialize(result);

        // Obtain the agent response todo, this doesn't work in current version (kernel.GetAgent)
        // ChatCompletionAgent agent = kernel.GetAgent<ChatCompletionAgent>(AgentServiceKey);
        List<ChatMessageContent> messages = new();
        await foreach (ChatMessageContent message in customerDataAgent.InvokeAsync(
            new ChatMessageContent(AuthorRole.User, userPrompt), agentThread))
        {
            // Both the input message and response message will automatically be added to the thread, which will update the internal chat history.
            messages.Add(message);
            // Emit event for each agent response
            // await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponse, Data = message });
            Console.WriteLine(message.ToString());

        }
        
        var repeatedCallResult = await IsCausedDeterminedAsync(kernel, history);

        if (repeatedCallResult!.IsOperationsCause)
        {
            await context.EmitEventAsync("CauseDetermined", data: repeatedCallResult);
        }
        else
        {
            await context.EmitEventAsync("NotCauseDetermined");
        }

        Console.WriteLine(repeatedCallResult.ToString());
    }

    private static async Task<CauseResult> IsCausedDeterminedAsync(Kernel kernel, ChatHistory history)
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

        ChatMessageContent response = await service.GetChatMessageContentAsync(localHistory, new OpenAIPromptExecutionSettings { ResponseFormat = typeof(CauseResult) });
        CauseResult intent = JsonSerializer.Deserialize<CauseResult>(response.ToString())!;

        Console.WriteLine($"Response: {response}");
        return intent;
    }
}


using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using System.Text.Json;
using cw_repeated_calls_dotnet.Helpers;
using cw_repeated_calls_dotnet.Entities.Database;
using System.Runtime.CompilerServices;


public class DetermineCauseStep : KernelProcessStep
{
    private string systemPrompt =
        """
        Your job is to determine the cause of a product issue. 
        You will be provided with a list of software updates and products, 
        and you must identify the associated software updates and products for the given issue.
        """;

    private string subscriptionCsvPath = "Data\\subscription.csv";
    private string softwareUpdateCsvPath = "Data\\software_update.csv";
    private string productCsvPath = "Data\\product.csv";

    [KernelFunction]
    public async Task DetermineCause(KernelProcessStepContext context, Kernel kernel, RepeatedCallResult result)
    {
        var softwareUpdates = RetrieveData.LoadFromCsv<SoftwareUpdate>(softwareUpdateCsvPath);
        var products = RetrieveData.LoadFromCsv<Product>(productCsvPath);
        var subscriptions = RetrieveData.LoadFromCsv<Subscription>(subscriptionCsvPath);

        var customerProducts = subscriptions
            .Where(s => s.CustomerId == result.CustomerId)
            .ToList();

        List<SoftwareUpdate> customerRelevantUpdates = new List<SoftwareUpdate>();
        foreach (var customerProduct in customerProducts)
        {
            // check for software updates for the used products
            var productSoftwareUpdates = softwareUpdates
                .Where(s => s.ProductId == customerProduct!.ProductId)
                .ToList();

            customerRelevantUpdates.AddRange(productSoftwareUpdates);
        }

        // Add the new product info to the chat history
        ChatHistory chatHistory = new ChatHistory(systemPrompt);

        // Build the user message with detailed context
        StringBuilder userMessage = new StringBuilder();

        userMessage.AppendLine($"## Customer ID: {result.CustomerId}");

        // Add current call information
        if (result.Conclusion != null)
        {
            userMessage.AppendLine("## Conclusion");
            userMessage.AppendLine(result.Conclusion);
        }

        // Add call history in reverse chronological order (most recent first)
        if (customerRelevantUpdates != null && customerProducts != null)
        {
            userMessage.AppendLine("## Software updates relevant for issue");
            
            foreach (var update in customerRelevantUpdates)
            {
                userMessage.AppendLine($"Product ID: {update.ProductId}");
                userMessage.AppendLine($"Update ID: {update.Id}");
                userMessage.AppendLine($"Update Type: {update.Type}");
                userMessage.AppendLine($"Update Timestamp: {update.RolloutDate:yyyy-MM-dd HH:mm:ss}");
                userMessage.AppendLine();
            }
        }

        // Add specific question for the model
        userMessage.AppendLine("Based on this information, is the current call a repeated call about the same issue and is it due because of software updates?");

        chatHistory.AddUserMessage(userMessage.ToString());


        OpenAIPromptExecutionSettings settings = new OpenAIPromptExecutionSettings();
        settings.ResponseFormat = typeof(CauseResult);

        // Get a response from the LLM
        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var contextResponse = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings:settings);
        var formattedResponse = JsonSerializer.Deserialize<CauseResult>(contextResponse.Content!.ToString());

        if (formattedResponse!.IsOperationsCause)
        {
            await context.EmitEventAsync("CauseDetermined", data: formattedResponse);
        }
        else
        {
            await context.EmitEventAsync("NotCauseDetermined");
        }

        Console.WriteLine(contextResponse.Content!.ToString());
    }
}


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


public class DetermineRepeatedCallerStep : KernelProcessStep
{
    private string systemPrompt = "Your job is to provide the context for a customer. " +
        "You will be provided with a customer ID and you must return the customer object, " +
        "the call event object, and the historic call event object." +
        "Determine if the current events are considered a repeateable event.";

    [KernelFunction]
    public async Task RepeatedCallAsync(KernelProcessStepContext context, Kernel kernel, RepeatedCallState callstate)
    {
        // Add the new product info to the chat history
        ChatHistory chatHistory = new ChatHistory(systemPrompt);

        // Build the user message with detailed context
        StringBuilder userMessage = new StringBuilder();

        // Add customer information
        if (callstate.Customer != null)
        {
            userMessage.AppendLine("## Customer Information");
            userMessage.AppendLine($"ID: {callstate.Customer.Id}");
            userMessage.AppendLine($"Name: {callstate.Customer.Name}");
            userMessage.AppendLine($"Customer Lifetime Value: {callstate.Customer.Clv}");
            userMessage.AppendLine($"Customer Since: {callstate.Customer.RelationStartDate:yyyy-MM-dd}");
            userMessage.AppendLine();
        }

        // Add current call information
        if (callstate.CallEvent != null)
        {
            userMessage.AppendLine("## Current Call Details");
            userMessage.AppendLine($"Call ID: {callstate.CallEvent.Id}");
            userMessage.AppendLine($"Call Description: {callstate.CallEvent.Sdc}");
            userMessage.AppendLine($"Timestamp: {callstate.CallEvent.TimeStamp:yyyy-MM-dd HH:mm:ss}");
            userMessage.AppendLine();
        }

        // Add call history in reverse chronological order (most recent first)
        if (callstate.CallHistory != null && callstate.CallHistory.Count > 0)
        {
            userMessage.AppendLine("## Previous Call History");

            var sortedHistory = callstate.CallHistory
                .OrderByDescending(h => h.StartTime)
                .ToList();

            foreach (var call in sortedHistory)
            {
                TimeSpan duration = call.EndTime - call.StartTime;

                userMessage.AppendLine($"### Call on {call.StartTime:yyyy-MM-dd HH:mm:ss}");
                userMessage.AppendLine($"Description: {call.Sdc}");
                userMessage.AppendLine($"Summary: {call.CallSummary}");
                userMessage.AppendLine($"Duration: {duration.TotalMinutes:F1} minutes");
                userMessage.AppendLine($"Start: {call.StartTime:yyyy-MM-dd HH:mm:ss}");
                userMessage.AppendLine($"End: {call.EndTime:yyyy-MM-dd HH:mm:ss}");

                // If there's a current call, calculate time between this historic call and the current one
                if (callstate.CallEvent != null)
                {
                    TimeSpan timeSinceCall = callstate.CallEvent.TimeStamp - call.EndTime;
                    userMessage.AppendLine($"Time since this call: {timeSinceCall.TotalHours:F1} hours");
                }
                userMessage.AppendLine();
            }
        }

        // Add specific question for the model
        userMessage.AppendLine("Based on this information, is the current call a repeated call about the same issue? Please analyze the timing between calls, similarity of issues discussed, and provide your reasoning.");

        chatHistory.AddUserMessage(userMessage.ToString());

        // Use structured output to ensure the response format is easily parsable
        OpenAIPromptExecutionSettings settings = new OpenAIPromptExecutionSettings();
        settings.ResponseFormat = typeof(RepeatedCallResult);

        // Get a response from the LLM
        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var repeatedCallResponse = await chatCompletionService.GetChatMessageContentAsync(chatHistory,executionSettings: settings);
        var formattedResponse = JsonSerializer.Deserialize<RepeatedCallResult>(repeatedCallResponse.Content!.ToString());
        
        Console.WriteLine(repeatedCallResponse.Content!.ToString());
        if (formattedResponse!.IsRepeatedCall)
        {
            await context.EmitEventAsync("IsRepeatedCall", data: formattedResponse);
        }
        else
        {
            await context.EmitEventAsync("IsNotRepeatedCall");
        }
    }
}


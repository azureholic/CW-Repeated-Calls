using cw_repeated_calls_dotnet.Agents;
using cw_repeated_calls_dotnet.Agents.AzureAI;
using cw_repeated_calls_dotnet.Agents.SemanticKernel;
using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.PromptEngineering;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;


public class DetermineRepeatedCallerStep : KernelProcessStep
{
    private readonly IAgent<RepeatedCallResult> _repeatedCallAgent;
   
    public DetermineRepeatedCallerStep(IAgent<RepeatedCallResult> repeatedCallAgent)
    {
        _repeatedCallAgent = repeatedCallAgent ?? throw new ArgumentNullException(nameof(repeatedCallAgent));
    }

    [KernelFunction]
    public async Task DetermineRepeatedCallAsync(KernelProcessStepContext context, Kernel kernel, RepeatedCallState state)
    {
        // Create the RepeatedCallAgent using the Azure AI
        RepeatedCallResult repeatedCallResult = await _repeatedCallAgent.GetAgentResponseAsync(
            kernel,
           state);

        Console.WriteLine(repeatedCallResult);

        if (repeatedCallResult != null)
        {
            if (repeatedCallResult.IsRepeatedCall)
            {
                state.RepeatedCallResult = repeatedCallResult;
                await context.EmitEventAsync("IsRepeatedCall", data:state);
            }
            else
            {
                await context.EmitEventAsync("IsNotRepeatedCall", data: state);
            }
        }
    }
}


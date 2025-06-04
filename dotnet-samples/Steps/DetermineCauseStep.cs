using Azure.AI.Agents.Persistent;
using cw_repeated_calls_dotnet.Agents;
using cw_repeated_calls_dotnet.Agents.AzureAI;
using cw_repeated_calls_dotnet.Agents.SemanticKernel;
using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.Helpers;
using cw_repeated_calls_dotnet.PromptEngineering;
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
    private readonly IAgent<CauseResult> _causeAgent;
    public DetermineCauseStep(IAgent<CauseResult> causeAgent)
    {
        _causeAgent = causeAgent;
    }

    [KernelFunction]
    public async Task DetermineCauseAsync(KernelProcessStepContext context, Kernel kernel, RepeatedCallState state)
    {
        CauseResult causeResult = await _causeAgent.GetAgentResponseAsync(
            kernel,
            state
            );

        Console.WriteLine(causeResult);

        bool isOperationsCause = causeResult.IsOperationsCause;

        state.CauseResult = causeResult;

        if (isOperationsCause)
        {
            await context.EmitEventAsync("CauseDetermined", data:state);
        }
        else
        {
            await context.EmitEventAsync("NotCauseDetermined");
        }

       
    }
}


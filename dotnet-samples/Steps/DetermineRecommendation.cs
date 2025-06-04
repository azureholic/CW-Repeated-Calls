using cw_repeated_calls_dotnet.Agents;
using cw_repeated_calls_dotnet.Agents.SemanticKernel;
using cw_repeated_calls_dotnet.Entities.Database;
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
using System.Numerics;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Steps
{
    internal class DetermineRecommendation : KernelProcessStep
    {
        private readonly IAgent<OfferResult> _offerAgent;

        public DetermineRecommendation(IAgent<OfferResult> offerAgent)
        {
            _offerAgent = offerAgent ?? throw new ArgumentNullException(nameof(offerAgent));
        }

        [KernelFunction]
        public async Task RecommendAsync(KernelProcessStepContext context, Kernel kernel, RepeatedCallState state)
        {
            // Setup the prompts for the DetermineRecommendation
            var prompts = new RecommendationPrompts(state);

            OfferResult offerResult = await _offerAgent.GetAgentResponseAsync(kernel, state);

            state.OfferResult = offerResult;

            Console.WriteLine(offerResult);

            await context.EmitEventAsync("RecommendationMade", data: state);

        }
    }
}

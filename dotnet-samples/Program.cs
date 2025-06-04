using Azure.AI.Agents.Persistent;
using Azure.Identity;
using cw_repeated_calls_dotnet.Agents;
using cw_repeated_calls_dotnet.Agents.AzureAI;
using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.Plugins;
using cw_repeated_calls_dotnet.Steps;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;

namespace cw_repeated_calls_dotnet
{
    internal class Program
    {
        private readonly static bool useAzureAIAgent = false; // This could come from configuration

        static async Task Main(string[] args)
        {
            var builder = Host.CreateApplicationBuilder(args);

            // Configuration
            builder.Configuration
                .SetBasePath(Directory.GetCurrentDirectory())
                .AddJsonFile("appsettings.development.json", optional: true, reloadOnChange: true)
                .AddEnvironmentVariables()
                .AddCommandLine(args);

            builder.Services.AddSingleton<IConfiguration>(builder.Configuration);

            var reasoningModel = builder.Configuration["AzureOpenAI:ReasoningModel"];
            var completionModel = builder.Configuration["AzureOpenAI:CompletionModel"];
            var endpoint = builder.Configuration["AzureOpenAI:Endpoint"];
            var projectEndpoint = builder.Configuration["AzureOpenAI:ProjectEndpoint"];


            builder.Services.AddSingleton<Customers>();
            builder.Services.AddSingleton<Operation>();


            // Configure the kernel with your LLM connection details
            var kernelBuilder = Kernel.CreateBuilder();
           
            if (useAzureAIAgent)
            {
                // Register the agents client for Azure AI Agents
                var client = AzureAIAgent.CreateAgentsClient(projectEndpoint!, new DefaultAzureCredential());
                kernelBuilder.Services.AddSingleton(client);
                kernelBuilder.Services.AddSingleton<IAgent<RepeatedCallResult>, RepeatedCallAgent>();
                kernelBuilder.Services.AddSingleton<IAgent<CauseResult>, CauseAgent>();
                kernelBuilder.Services.AddSingleton<IAgent<OfferResult>, OfferAgent>();
            }
            else
            {
                kernelBuilder.Services.AddSingleton<IAgent<RepeatedCallResult>, cw_repeated_calls_dotnet.Agents.SemanticKernel.RepeatedCallAgent>();
                kernelBuilder.Services.AddSingleton<IAgent<CauseResult>, cw_repeated_calls_dotnet.Agents.SemanticKernel.CauseAgent>();
                kernelBuilder.Services.AddSingleton<IAgent<OfferResult>, cw_repeated_calls_dotnet.Agents.SemanticKernel.OfferAgent>();
            }

            kernelBuilder.AddAzureOpenAIChatCompletion(deploymentName: completionModel!, endpoint: endpoint!, new DefaultAzureCredential());
            kernelBuilder.Plugins.AddFromType<Customers>();
            kernelBuilder.Plugins.AddFromType<Operation>();
            var kernel = kernelBuilder.Build();

            builder.Services
                .AddMcpServer()
                .WithTools<Customers>()
                .WithTools<Operation>();


            builder.Services.AddSingleton(kernel);

            var app = builder.Build();

            await RunSequenceAsync(kernel);

        }

        static async Task RunSequenceAsync(Kernel kernel)
        {
            // This is the incoming message that will be processed (simulating a customer call)
            // Next step is that this message comes from the servicebus
            IncomingMessage incomingMessage = new()
            {
                CustomerId = 7,
                Message = "My self-driving mower isn’t working since this morning",
                TimeStamp = DateTime.Parse("2024-01-10 10:05:22")

            };

            string threadId = string.Empty;
            if (useAzureAIAgent)
            {
                AzureAIAgentThread azureAIAgentThread = new(kernel.GetRequiredService<PersistentAgentsClient>());
                await azureAIAgentThread.CreateAsync();
                threadId = azureAIAgentThread.Id;
            }   
            else
            {
                // For Semantic Kernel, we can use a simple string as thread ID
                threadId = Guid.NewGuid().ToString();
            }


            RepeatedCallState state = new()
            {
                CallEvent = new CallEvent
                {
                    CustomerId = incomingMessage.CustomerId,
                    Sdc = incomingMessage.Message,
                    Id = 1,
                    TimeStamp = incomingMessage.TimeStamp
                },
                ThreadId = threadId,
            };

            // Create the process builder
            ProcessBuilder processBuilder = new("RepeatedCalls");
            
            // Add the steps
            var determineRepeatedCallerStep = processBuilder.AddStepFromType<DetermineRepeatedCallerStep>();
            var determineCauseStep = processBuilder.AddStepFromType<DetermineCauseStep>();
            var determineRecommendationStep = processBuilder.AddStepFromType<DetermineRecommendation>();
            var exitStep = processBuilder.AddStepFromType<ExitStep>();
            
            // Orchestrate the events
            processBuilder
                .OnInputEvent("Start")
                .SendEventTo(new(determineRepeatedCallerStep));

            determineRepeatedCallerStep
                .OnEvent("IsRepeatedCall")
                .SendEventTo(new(determineCauseStep));

            determineRepeatedCallerStep
                .OnEvent("IsNotRepeatedCall")
                .SendEventTo(new(exitStep));

            determineCauseStep
                .OnEvent("NotCauseDetermined")
                .SendEventTo(new(exitStep));

            determineCauseStep
                .OnEvent("CauseDetermined")
                .SendEventTo(new(determineRecommendationStep));

            determineRecommendationStep
                .OnEvent("RecommendationMade")
                .SendEventTo(new(exitStep));

            // Build and run the process
            var process = processBuilder.Build();
            await process.StartAsync(kernel, new KernelProcessEvent { Id = "Start", Data = state });

        }
    }
}

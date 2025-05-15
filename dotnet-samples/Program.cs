using Azure.Identity;
using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Steps;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Process;
using OpenAI.Assistants;
using System.Net;

namespace cw_repeated_calls_dotnet
{
    internal class Program
    {

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

            // Configure the kernel with your LLM connection details
            Kernel kernel = Kernel.CreateBuilder()
                .AddAzureOpenAIChatCompletion(deploymentName: completionModel!, endpoint: endpoint!, new DefaultAzureCredential())
                .Build();

            builder.Services.AddSingleton(kernel);

            var app = builder.Build();

            await RunSequenceAsync(kernel);

        }

        static async Task RunSequenceAsync(Kernel kernel)
        {
            // Initialize services
           


            // This is the incoming message that will be processed (simulating a customer call)
            // Next step is that this message comes from the servicebus
            IncomingMessage incomingMessage = new()
            {
                CustomerId = 7,
                Message = "My self-driving mower isn’t working since this morning",
                TimeStamp = DateTime.Parse("2024-01-10 10:05:22")

            };

            // Create the process builder
            ProcessBuilder processBuilder = new("RepeatedCalls");

            // Add the steps
            var determineRepeatedCallerStep = processBuilder.AddStepFromType<DetermineRepeatedCallerStep>();
            var determineCauseStep = processBuilder.AddStepFromType<DetermineCauseStep>();
            var exitStep = processBuilder.AddStepFromType<ExitStep>();

            // Orchestrate the events
            processBuilder
                .OnInputEvent("Start")
                .SendEventTo(new(determineRepeatedCallerStep));

            //getCustomerContextStep
            //    .OnEvent("FetchingContextDone")
            //    .SendEventTo(new(determineRepeatedCallerStep));

            determineRepeatedCallerStep
                .OnEvent("IsRepeatedCall")
                .SendEventTo(new(determineCauseStep));

            determineRepeatedCallerStep
                .OnEvent("IsNotRepeatedCall")
                .SendEventTo(new(exitStep));

            determineCauseStep
                .OnEvent("NotCauseDetermined")
                .SendEventTo(new(exitStep));

            // todo:
            determineCauseStep
                .OnEvent("CauseDetermined")
                .SendEventTo(new(exitStep));



            // Build and run the process
            var process = processBuilder.Build();
            await process.StartAsync(kernel, new KernelProcessEvent { Id = "Start", Data = incomingMessage });

        }
    }
}

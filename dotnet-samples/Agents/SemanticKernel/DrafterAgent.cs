using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents.SemanticKernel
{
    public class DrafterAgent
    {


        public ChatCompletionAgent CreateAgent(Kernel kernel, string agentName, string instructions)
        {
            // Clone kernel instance to allow for agent specific plug-in definition
            Kernel agentKernel = kernel.Clone();

            // Define the instruction for the agent
            return
                new ChatCompletionAgent()
                {
                    Name = agentName,
                    Description = "Agent responsible for extracting requirements from documents.",
                    Instructions = instructions,
                    Kernel = agentKernel,
                    Arguments = new KernelArguments(
                        new OpenAIPromptExecutionSettings()
                        {
                            Temperature = 0,
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true }),
                        })
                };

        }
    }
}

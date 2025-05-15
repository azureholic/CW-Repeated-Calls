using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using cw_repeated_calls_dotnet.Plugins.CustomerDomain;
using cw_repeated_calls_dotnet.Plugins.OperationsDomain;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents
{
    public class OperationsAgent
    {
        public ChatCompletionAgent CreateAgent(Kernel kernel, string agentName, int customerId)
        {
            // Clone kernel instance to allow for agent specific plug-in definition
            Kernel agentKernel = kernel.Clone();

            // Import plug-in from type
            agentKernel.ImportPluginFromType<CustomerTool>();
            agentKernel.ImportPluginFromType<ProductsTool>();
            agentKernel.ImportPluginFromType<OperationsTool>();

            return
                new ChatCompletionAgent()
                {
                    Name = agentName,
                    Instructions = $""""
                        For a given customer {customerId} which has repeated calls about a product issue.
                        Get the current subscription and the products used by the customer.
                        Check if any software updates which are related to the product issue are available.
                        Determine if any of products used by the customer are associated with the issue.

                        Give a detailed explanation of the cause of the issue in the analysis.
                        """",
                    Kernel = agentKernel,
                    Arguments = new KernelArguments(
                        new OpenAIPromptExecutionSettings()
                        {
                            ResponseFormat = typeof(OperationsCallState),
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Required(),
                            Temperature = 0,
                        })
                };
        }
    }
}

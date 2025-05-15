using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Plugins.CustomerDomain;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.OpenAI;


namespace cw_repeated_calls_dotnet.Agents
{
    public class CustomerDataAgent
    {
        public ChatCompletionAgent CreateAgent(Kernel kernel, string agentName, int customerId)
        {
            // Clone kernel instance to allow for agent specific plug-in definition
            Kernel agentKernel = kernel.Clone();

            // Import plug-in from type
            agentKernel.ImportPluginFromType<CustomerTool>();
            return
                new ChatCompletionAgent()
                {
                    Name = agentName,
                    Instructions = $"""
                    Your job is to provide the context for a given customer. 
                    You will be provided with a customer ID and you must return the 
                    - customer object
                    - the call event object
                    - historic call event object

                    ## Customer ID: {customerId}
                """,
                    Kernel = agentKernel,
                    Arguments = new KernelArguments(
                        new OpenAIPromptExecutionSettings()
                        {
                            ResponseFormat = typeof(RepeatedCallState),
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Required(),
                            Temperature = 0,
                        })
                };
        }
    }
}

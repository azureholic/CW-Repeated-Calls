using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using Microsoft.SemanticKernel;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Agents
{
    /// <summary>
    /// Generic interface for all AI agents that return structured results
    /// </summary>
    /// <typeparam name="T">The type of structured result returned by the agent</typeparam>
    public interface IAgent<T>
    {
        /// <summary>
        /// Gets a response from the agent based on the provided instructions and input
        /// </summary>
        /// <param name="kernel">The semantic kernel instance</param>
        /// <param name="instructions">System instructions for the agent</param>
        /// <param name="input">User input for the agent</param>
        /// <param name="threadId">Unique identifier for the conversation thread</param>
        /// <returns>A structured result of type T</returns>
        Task<T> GetAgentResponseAsync(Kernel kernel, RepeatedCallState state);
    }
}
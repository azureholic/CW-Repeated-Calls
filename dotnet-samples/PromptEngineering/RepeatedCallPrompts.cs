using cw_repeated_calls_dotnet.Entities.States;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.PromptEngineering
{
    internal class RepeatedCallPrompts
    {
        public RepeatedCallPrompts(RepeatedCallState initialState)
        {
            _state = initialState;
        }
        private RepeatedCallState _state;

        public string SystemPrompt =>
        """
            Your job is to provide the context for a customer.
            "You will be provided with a customer ID and you must return the customer object,
            "the call event object, and the historic call event object." 
            "Determine if the current events are considered a repeateable event.
        """;

        public string UserPrompt =>
        $"Determine if the current call is a repeated call based on the provided customer data and call event. " +
            $"See {_state.CallEvent} for the details.";

      
    }
}

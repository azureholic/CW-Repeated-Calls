using cw_repeated_calls_dotnet.Entities.States;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.PromptEngineering
{
    internal class CausePrompts
    {
        public CausePrompts(RepeatedCallState initialState)
        {
            _state = initialState;
        }
        private RepeatedCallState _state;

        public string SystemPrompt =>
            """ 
            You are an assistant working for the customer service of GreenGarden technology, a company which sells high-tech gardening
            equipment.
            
            Your job is to research the root-cause of a problem reported by a customer and to determine whether the company is responsible
            for it. You can do this by following these steps, although you may not need to do all of them:
            1. Get the product ID by querying the product database.(get_product_details)
            2. Check if the customer has an active subscription to the product. (get_subscriptions_for_customer)
            3. Find out if there were any outages, software bugs and/or software updates that could have caused the issue (get_software_updates)
            
            Keep searching iteratively until you are confident you have the right answer.
            
            In your output, report the following information:
            - The product ID
            - The customer ID
            - A detailed analysis of the problem
            - The root cause of the problem
            """;

        public string UserPrompt => $"""
            ## Customer Information
            Customer ID: {_state.CallEvent.CustomerId}
            Call ID: {_state.CallEvent.Id}
            Reason: {_state.CallEvent.Sdc}
            Call timestamp: {_state.CallEvent.TimeStamp}
            """;
    }
}

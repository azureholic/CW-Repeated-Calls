using cw_repeated_calls_dotnet.Entities.States;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.PromptEngineering
{
    internal class RecommendationPrompts
    {
        public RecommendationPrompts(RepeatedCallState initialState)
        {
            _state = initialState;
        }
        private RepeatedCallState _state;

        public string DrafterSystemPrompt => $"""
            Your job is to draft an offer for a customer experiencing a product issue. There are various discounts to offer, but
            it is your job to determine one which is relevant and for which the customer is eligible based on their Customer Lifetime Value (CLV).

            Reason whether the customer should receive the discount and include the following in the advice to a customer service agent:
            - Whether the customer should receive a discount
            - The discount to offer
            - The reasoning behind the discount
            - The issue the customer is experiencing and the request to confirm this with the customer
            - The customer ID and relevant product ID
            """;

        public string ReviewerSystemPrompt => $"""
            Your job is to review the offer drafted by the drafter agent.

            Check the offer based on the following criteria:
            - Is the offer relevant to the customer?
            - Is the offer eligible for the customer based on their Customer Lifetime Value (CLV)?
            - Is the reasoning behind the offer clear and logical?
            - Is the issue the customer is experiencing and the request to confirm this with the customer clear?
            - Is the customer ID and relevant product ID included?

            If the offer is not relevant or eligible, provide feedback to the drafter agent on how to improve the offer.
            If the offer is relevant and eligible, include a sentence with the word 'APPROVED'.
            
            """;

        public string UserPrompt => $"""
            ## Recommendation Information
            # CUSTOMER
            Customer ID: { _state.CallEvent.CustomerId }
            Call reason: { _state.CallEvent.Sdc}

            # ANALYSIS
            Product ID: { _state.CauseResult.ProductId}
            Issue description: { _state.CauseResult.Analysis}
            
            """;

        public string TerminationToken => "APPROVED";
        public string TerminationPrompt =>
        $""""
        Examine the RESPONSE and determine whether the content has been deemed satisfactory.
        If content is satisfactory, respond with a single word without explanation: {TerminationToken}.
        If specific suggestions are being provided, it is not satisfactory.
        If no correction is suggested, it is satisfactory.
        """";
    }
}

using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Helpers;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Steps
{
    internal class GetCustomerDataStep : KernelProcessStep<RepeatedCallState>
    {
        private RepeatedCallState _state = new();

        private string customerCsvPath = "Data\\customer.csv";
        private string historicCallEventCsvPath = "Data\\historic_call_event.csv";
        private string callEventCsvPath = "Data\\call_event.csv";
       

        [KernelFunction]
        public async Task GetCallEventAsync(IncomingMessage incomingMessage, KernelProcessStepContext context)
        {
            int customerId = incomingMessage.CustomerId;

            // To load a list of Customer objects
            var callEvents = RetrieveData.LoadFromCsv<CallEvent>(callEventCsvPath);
            if (callEvents == null || callEvents.Count == 0)
            {
                Console.WriteLine($"Warning: No call events found at {callEventCsvPath}");
            }

            var customerCallEvent = callEvents.FirstOrDefault(x => x.CustomerId == customerId);
            if (customerCallEvent == null)
            {
                Console.WriteLine($"Warning: No call event found for customer ID {customerId}");
            }

            var historicCallEvents = RetrieveData.LoadFromCsv<HistoricCallEvent>(historicCallEventCsvPath);
            if (historicCallEvents == null || historicCallEvents.Count == 0)
            {
                Console.WriteLine($"Warning: No historic call events found at {historicCallEventCsvPath}");
            }

            var customerHistoricCallEvent = historicCallEvents.Where(x => x.CustomerId == customerId);
            if (customerHistoricCallEvent == null)
            {
                Console.WriteLine($"Warning: No historic call event found for customer ID {customerId}");
            }

            var customers = RetrieveData.LoadFromCsv<Customer>(customerCsvPath);
            var customer = customers.FirstOrDefault(x => x.Id == customerId);

            RepeatedCallState repeatedCallState = new RepeatedCallState
            {
                Customer = customer,
                CallEvent = customerCallEvent,
                CallHistory = customerHistoricCallEvent.ToList()
            };

            await context.EmitEventAsync("FetchingContextDone", data:repeatedCallState);

        }

       
    }
}
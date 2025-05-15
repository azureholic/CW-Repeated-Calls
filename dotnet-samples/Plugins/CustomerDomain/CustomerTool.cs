using cw_repeated_calls_dotnet.Entities;
using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Entities.States;
using cw_repeated_calls_dotnet.Helpers;
using cw_repeated_calls_dotnet.Steps;
using Microsoft.SemanticKernel;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Plugins.CustomerDomain
{
    public class CustomerTool        
    {
        private string customerCsvPath = "Data\\customer.csv";
        private string historicCallEventCsvPath = "Data\\historic_call_event.csv";
        private string callEventCsvPath = "Data\\call_event.csv";


        [KernelFunction("get_customer_details")]
        [Description("Retrieves the data of the customer")]
        public Customer GetCustomerData(int customerId)
        {
            var customers = RetrieveData.LoadFromCsv<Customer>(customerCsvPath);
            var customer = customers.FirstOrDefault(x => x.Id == customerId);

            return customer;
        }

        [KernelFunction("get_current_call_event")]
        [Description("Retrieves the call event for the current customer")]
        public CallEvent GetCallEvent(int customerId)
        {
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
            return customerCallEvent;
        }

        [KernelFunction("get_historic_call_events")]
        [Description("Retrieves the historic call events for the current customer")]
        public List<HistoricCallEvent> GetHistoricCallEvents(int customerId)
        {
            var historicCallEvents = RetrieveData.LoadFromCsv<HistoricCallEvent>(historicCallEventCsvPath);
            if (historicCallEvents == null || historicCallEvents.Count == 0)
            {
                Console.WriteLine($"Warning: No historic call events found at {historicCallEventCsvPath}");
            }
            var customerHistoricCallEvent = historicCallEvents.Where(x => x.CustomerId == customerId).ToList();
            if (customerHistoricCallEvent == null)
            {
                Console.WriteLine($"Warning: No historic call event found for customer ID {customerId}");
            }
            return customerHistoricCallEvent;
        }
    }
}

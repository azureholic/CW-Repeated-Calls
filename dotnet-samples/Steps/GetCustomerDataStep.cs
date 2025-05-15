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
       

        //[KernelFunction]
        //public async Task GetCallEventAsync(IncomingMessage incomingMessage, KernelProcessStepContext context)
        //{
            

        //    await context.EmitEventAsync("FetchingContextDone", data:repeatedCallState);

        //}

       
    }
}
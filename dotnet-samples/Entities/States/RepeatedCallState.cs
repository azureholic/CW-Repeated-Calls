using Azure.AI.Agents.Persistent;
using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Entities.StructuredOutput;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.States
{
    public class RepeatedCallState
    {
        public CallEvent? CallEvent { get; set; }
        public Customer? Customer { get; set; }
        public List<HistoricCallEvent>? CallHistory { get; set; }
        public RepeatedCallResult? RepeatedCallResult { get; set; } = new();
        public CauseResult? CauseResult { get; set; } = new();
        public OfferResult? OfferResult { get; set; } = new();
        public string? ThreadId { get; set; } = string.Empty;
    }
}

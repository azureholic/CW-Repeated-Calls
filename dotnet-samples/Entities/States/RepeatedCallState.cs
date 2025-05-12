using cw_repeated_calls_dotnet.Entities.Database;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.States
{
    public class RepeatedCallState
    {
        public Customer? Customer { get; set; }
        public CallEvent? CallEvent { get; set; }
        public List<HistoricCallEvent>? CallHistory { get; set; }
        public bool IsRepeatedCall { get; set; } = false;
    }
}

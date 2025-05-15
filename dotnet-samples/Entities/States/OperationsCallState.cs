using cw_repeated_calls_dotnet.Entities.Database;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.States
{
    public class OperationsCallState
    {
        public Customer? Customer { get; set; }
        public Subscription? Subscription { get; set; }
        public List<Product>? Products { get; set; }
        public List<SoftwareUpdate>? SoftwareUpdates { get; set; }
        public string Analysis { get; set; } = string.Empty;

    }
}

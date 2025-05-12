using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities
{
    internal class IncomingMessage
    {
        public int CustomerId { get; set; }
        public required string Message { get; set; }
        public DateTime TimeStamp { get; set; } = DateTime.UtcNow;
    }
}

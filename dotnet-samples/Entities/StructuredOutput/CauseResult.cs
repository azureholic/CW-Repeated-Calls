using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.StructuredOutput
{
    public class CauseResult
    {
        public int CustomerId { get; set; }
        public string Analysis { get; set; }
        public string Conclusion { get; set; }
        public bool IsOperationsCause { get; set; }

    }
}

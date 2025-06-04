using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.StructuredOutput
{
    public record RepeatedCallResult
    {
        [JsonPropertyName("customerId")]
        public int CustomerId { get; set; }

        [JsonPropertyName("analysis")]
        public string Analysis { get; set; }

        [JsonPropertyName("conclusion")]
        public string Conclusion { get; set; }

        [JsonPropertyName("isRepeatedCall")]
        public bool IsRepeatedCall { get; set; }
    }
}

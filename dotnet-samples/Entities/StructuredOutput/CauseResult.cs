using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.StructuredOutput
{
    public record CauseResult
    {
        [JsonPropertyName("productId")]
        public string ProductId { get; set; }
        [JsonPropertyName("customerId")]
        public int CustomerId { get; set; }
        [JsonPropertyName("analysis")]
        public string Analysis { get; set; }
        [JsonPropertyName("conclusion")]
        public string Conclusion { get; set; }
        [JsonPropertyName("isOperationsCause")]
        public bool IsOperationsCause { get; set; }

    }
}

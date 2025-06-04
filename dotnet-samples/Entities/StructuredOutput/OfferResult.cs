using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.StructuredOutput
{
    public record OfferResult
    {
        [JsonPropertyName("customerId")]
        public int CustomerId { get; set; } // Foreign key as string for Cosmos DB   
        [JsonPropertyName("productId")]
        public int ProductId { get; set; } // Foreign key as int for SQL DB
        [JsonPropertyName("advice")]
        public string Advice { get; set; } // Advice for the customer, e.g., "Consider upgrading to a higher plan for better support."
    }
}

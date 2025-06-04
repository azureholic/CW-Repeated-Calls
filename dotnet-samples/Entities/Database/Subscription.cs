using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.Database
{
    public record Subscription
    {
       // [JsonProperty("id")]
        public int Id { get; set; }

      //  [JsonProperty("customer_id")]
        public int CustomerId { get; set; } // Foreign key as string for Cosmos DB

      //  [JsonProperty("product_Id")]
        public int ProductId { get; set; }

      //  [JsonProperty("contract_duration_months")]
        public int ContractDurationMonths { get; set; }

      //  [JsonProperty("price_per_month")]
        public double PricePerMonth { get; set; }

      //  [JsonProperty("start_date")]
        public DateTime StartDate { get; set; }

      //  [JsonProperty("end_date")]
        public DateTime EndDate { get; set; }
    }
}

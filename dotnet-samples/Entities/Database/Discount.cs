using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.Database
{
    // JsonProperties not needed when reading from csv files

    public class Discount
    {
      //  [JsonProperty("id")]
        public string Id { get; set; }

     //   [JsonProperty("productId")]
        public string ProductId { get; set; }

    //    [JsonProperty("minimumClv")]
        public string MinimumClv { get; set; }

   //     [JsonProperty("percentage")]
        public int Percentage { get; set; }

    //    [JsonProperty("durationMonths")]
        public int DurationMonths { get; set; }
    }
}

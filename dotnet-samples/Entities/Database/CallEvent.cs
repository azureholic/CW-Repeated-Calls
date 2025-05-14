using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.Database
{
    // JsonProperties not needed when reading from csv files

    public class CallEvent
    {
     //   [JsonProperty("id")]
        public int Id { get; set; }

     //   [JsonProperty("customer_id")]
        public int CustomerId { get; set; }

      //  [JsonProperty("sdc")]
        public string Sdc { get; set; }

     //   [JsonProperty("timestamp")]
        public DateTime TimeStamp { get; set; }
    }
}

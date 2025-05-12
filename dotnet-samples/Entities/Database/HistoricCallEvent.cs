using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.Database
{
    public class HistoricCallEvent
    {
       // [JsonProperty("id")]
        public int Id { get; set; }

       // [JsonProperty("customer_id")]
        public int CustomerId { get; set; }

        //[JsonProperty("sdc")]
        public string Sdc { get; set; }

       // [JsonProperty("call_summary")]
        public string CallSummary { get; set; }

       // [JsonProperty("start_time")]
        public DateTime StartTime { get; set; }

      //  [JsonProperty("end_time")]
        public DateTime EndTime { get; set; }
    }
}

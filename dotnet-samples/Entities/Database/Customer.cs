using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.Database
{
    // JsonProperties not needed when reading from csv files

    public record Customer
    {
       // [JsonProperty("id")]
        public int Id { get; set; } 

      //  [JsonProperty("name")]
        public string Name { get; set; }

     //   [JsonProperty("clv")]
        public string Clv { get; set; }

      //  [JsonProperty("relation_start_date")]
        public DateTime RelationStartDate { get; set; }
    }
}

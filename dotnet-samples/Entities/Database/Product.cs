using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.Database
{
    // JsonProperties not needed when reading from csv files

    public class Product
    {
      //  [JsonProperty("id")]
        public int Id { get; set; }

      //  [JsonProperty("name")]
        public string Name { get; set; }

      //  [JsonProperty("type")]
        public string Type { get; set; }

       // [JsonProperty("listingPrice")]
        public double ListingPrice { get; set; }
    }
}

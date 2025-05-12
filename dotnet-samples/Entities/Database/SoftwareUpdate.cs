using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Entities.Database
{
    public class SoftwareUpdate
    {
      //  [JsonProperty("id")]
        public int Id { get; set; }

      //  [JsonProperty("productId")]
        public int ProductId { get; set; }

      //  [JsonProperty("rolloutDate")]
        public DateTime RolloutDate { get; set; }

      //  [JsonProperty("type")]
        public string Type { get; set; }
    }
}

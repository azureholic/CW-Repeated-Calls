using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Helpers;
using Microsoft.SemanticKernel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Plugins.OperationsDomain
{
    public class OperationsTool
    {
        private string subscriptionCsvPath = "Data\\subscription.csv";
        private string softwareUpdateCsvPath = "Data\\software_update.csv";
        private string productCsvPath = "Data\\product.csv";

        [KernelFunction("get_software_updates_by_product_id")]
        public SoftwareUpdate GetSoftwareUpdate(int productId)
        {
            // To load a list of SoftwareUpdate objects
            var softwareUpdates = RetrieveData.LoadFromCsv<SoftwareUpdate>(softwareUpdateCsvPath);
            if (softwareUpdates == null || softwareUpdates.Count == 0)
            {
                Console.WriteLine($"Warning: No software updates found at {softwareUpdateCsvPath}");
            }
            var softwareUpdate = softwareUpdates.FirstOrDefault(x => x.ProductId == productId);
            if (softwareUpdate == null)
            {
                Console.WriteLine($"Warning: No software update found for productId {productId}");
            }
            return softwareUpdate;
        }


    }
}

using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Helpers;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Server;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Plugins
{
    [McpServerToolType]
    public class Operation
    {
        [KernelFunction("get_software_updates")]
        [McpServerTool]
        [Description("List software updates, optionally filtered by product")]
        public List<SoftwareUpdate> GetSoftwareUpdates(int productId)
        {
            var softwareUpdates = RetrieveData.LoadFromCsv<SoftwareUpdate>();
            if (softwareUpdates == null || softwareUpdates.Count == 0)
            {
                Console.WriteLine($"Warning: No software updates found. ");
            }

            var productSoftwareUpdate = softwareUpdates.Where(x => x.ProductId == productId);
            if (productSoftwareUpdate == null)
            {
                Console.WriteLine($"Warning: No software updates found. ");
            }

            return productSoftwareUpdate.ToList();
        }
    }
    
}

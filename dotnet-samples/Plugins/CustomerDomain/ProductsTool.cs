using cw_repeated_calls_dotnet.Entities.Database;
using cw_repeated_calls_dotnet.Helpers;
using Microsoft.SemanticKernel;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Plugins.CustomerDomain
{
    public class ProductsTool
    {
        private string productCsvPath = "Data\\product.csv";
        private string subscriptionCsvPath = "Data\\subscription.csv";

        [KernelFunction("get_products_used_by_customer")]
        [Description("Retrieves the products for the given customer")]
        public List<Product> GetProductByCustomerId(int customerId)
        {
            var customerSubscriptions = GetSubscriptions(customerId);
            var products = RetrieveData.LoadFromCsv<Product>(productCsvPath);
            var customerProducts = products
                .Where(p => customerSubscriptions.Any(s => s.ProductId == p.Id))
                .ToList();

            return customerProducts;
        }

        [KernelFunction("get_subscriptions_used_by_customer")]
        [Description("Retrieves the subscriptions for the given customer")]
        public List<Subscription> GetSubscriptions(int customerId)
        {
            var subscriptions = RetrieveData.LoadFromCsv<Subscription>(subscriptionCsvPath);
            if (subscriptions == null || subscriptions.Count == 0)
            {
                Console.WriteLine($"Warning: No subscriptions found at {subscriptionCsvPath}");
            }

            var customerSubscriptions = subscriptions
               .Where(s => s.CustomerId == customerId)
               .ToList();
            
            return customerSubscriptions;
        }


    }
}

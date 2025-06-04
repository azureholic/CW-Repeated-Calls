using CsvHelper.Delegates;
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
    public class Customers
    {
        [KernelFunction("get_call_event")]
        [McpServerTool]
        [Description("Retrieves a call event for the specified customer")]
        public CallEvent GetCallEvent(int customerId)
        {
            var callEvents = RetrieveData.LoadFromCsv<CallEvent>();
            if (callEvents == null || callEvents.Count == 0)
            {
                Console.WriteLine($"Warning: No call events found for customer ID {customerId}");
            }

            var customerCallEvent = callEvents.FirstOrDefault(x => x.CustomerId == customerId);
            if (customerCallEvent == null)
            {
                Console.WriteLine($"Warning: No call event found for customer ID {customerId}");
            }
            return customerCallEvent;
        }

        [KernelFunction("get_customer_details")]
        [McpServerTool]
        [Description("Retrieves details for the specified customer")]
        public Customer GetCustomer(int customerId)
        {
            // Simulate fetching customer data from a database or service
            var customers = RetrieveData.LoadFromCsv<Customer>();
            var customer = customers.FirstOrDefault(x => x.Id == customerId);
            return customer;
        }

        [KernelFunction("get_call_history")]
        [McpServerTool]
        [Description("Retrieves historic calls for the current user")]
        public List<HistoricCallEvent> GetCallHistory(int customerId)
        {
            var historicCallEvents = RetrieveData.LoadFromCsv<HistoricCallEvent>();
            if (historicCallEvents == null || historicCallEvents.Count == 0)
            {
                Console.WriteLine($"Warning: No historic call events found.");
            }

            var customerHistoricCallEvent = historicCallEvents.Where(x => x.CustomerId == customerId).ToList();
            if (customerHistoricCallEvent == null || customerHistoricCallEvent.Count == 0)
            {
                Console.WriteLine($"Warning: No historic call event found for customer ID {customerId}");
            }
            return customerHistoricCallEvent;
        }

        [KernelFunction("get_subscriptions_for_customer")]
        [McpServerTool]
        [Description("Retrieves the subscriptions the customer has")]
        public List<Subscription> GetSubscriptions(int customerId)
        {
            // Simulate fetching subscriptions for the customer
            var subscriptions = RetrieveData.LoadFromCsv<Subscription>();
            if (subscriptions == null || subscriptions.Count == 0)
            {
                Console.WriteLine($"Warning: No subscriptions found for customer ID {customerId}");
                return new List<Subscription>();
            }
            var customerSubscriptions = subscriptions.Where(x => x.CustomerId == customerId).ToList();
            if (customerSubscriptions == null || customerSubscriptions.Count == 0)
            {
                Console.WriteLine($"Warning: No subscriptions found for customer ID {customerId}");
            }
            return customerSubscriptions;
        }

        [KernelFunction("get_product_details")]
        [McpServerTool]
        [Description("Retrieves the subscriptions the customer has")]
        public Product GetProduct(int productId)
        {
            // Simulate fetching product details
           var products = RetrieveData.LoadFromCsv<Product>();
            if (products == null || products.Count == 0)
            {
                Console.WriteLine($"Warning: No products found.");
            }
            var product = products.FirstOrDefault(x => x.Id == productId);
            if (product == null)
            {
                Console.WriteLine($"Warning: No product found for product ID {productId}");
            }
            return product; 
        }

        [KernelFunction("get_discounts")]
        [McpServerTool]
        [Description("Retrieves the discounts a product can have")]
        public List<Discount> GetDiscounts(int productId)
        {
            // Simulate fetching discount information for the product
           var discounts = RetrieveData.LoadFromCsv<Discount>();
            if (discounts == null || discounts.Count == 0)
            {
                Console.WriteLine($"Warning: No discounts found for product ID {productId}");
                return new List<Discount>();
            }
            var productDiscounts = discounts.Where(x => x.ProductId == productId.ToString()).ToList();
            if (productDiscounts == null || productDiscounts.Count == 0)
            {
                Console.WriteLine($"Warning: No discounts found for product ID {productId}");
            }
            return productDiscounts;
        }
    }
}

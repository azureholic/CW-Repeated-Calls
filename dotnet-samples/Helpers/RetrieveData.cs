using CsvHelper;
using CsvHelper.Configuration;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Formats.Asn1;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace cw_repeated_calls_dotnet.Helpers
{
    internal static class RetrieveData
    {
        public static List<T> LoadFromCsv<T>(string filePath) where T : class
        {
            if (!File.Exists(filePath))
            {
                Console.WriteLine($"Warning: CSV file not found at {filePath}");
                return new List<T>();
            }

            try
            {
                // Create a mapping dictionary from JsonProperty attributes
                var jsonPropertyMap = CreateJsonPropertyMap<T>();

                using var reader = new StreamReader(filePath);
                using var csv = new CsvReader(reader, new CsvConfiguration(CultureInfo.InvariantCulture)
                {
                    Delimiter = ",",
                    HasHeaderRecord = true,
                    HeaderValidated = null, // Don't validate headers
                    MissingFieldFound = null, // Don't throw on missing fields
                    // Use our custom mapping logic that respects JsonProperty attributes
                    PrepareHeaderForMatch = args => MapHeaderToProperty(args.Header, jsonPropertyMap)
                });

                return csv.GetRecords<T>().ToList();
            }
            catch (Exception ex)
            {
                string typeName = typeof(T).Name;
                Console.WriteLine($"Error loading {typeName} data: {ex.Message}");
                return new List<T>();
            }
        }

        /// <summary>
        /// Creates a mapping dictionary from JSON property names to C# property names
        /// </summary>
        private static Dictionary<string, string> CreateJsonPropertyMap<T>() where T : class
        {
            var map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

            foreach (var prop in typeof(T).GetProperties())
            {
                // Check if the property has a JsonProperty attribute
                var jsonAttr = prop.GetCustomAttribute<JsonPropertyAttribute>();
                if (jsonAttr != null && !string.IsNullOrEmpty(jsonAttr.PropertyName))
                {
                    // Add mapping from JSON property name to actual property name
                    map[jsonAttr.PropertyName] = prop.Name;
                }
                else
                {
                    // Also add direct mapping (property name to itself) for properties without attribute
                    map[prop.Name.ToLowerInvariant()] = prop.Name;
                }
            }

            return map;
        }

        /// <summary>
        /// Maps CSV header to C# property name using JsonProperty attributes when available
        /// </summary>
        private static string MapHeaderToProperty(string header, Dictionary<string, string> jsonPropertyMap)
        {
            if (string.IsNullOrEmpty(header))
                return header;

            // Check if we have a direct match in our mapping dictionary
            if (jsonPropertyMap.TryGetValue(header, out var propertyName))
                return propertyName;

            // Fall back to our PascalCase conversion for headers not matched by JsonProperty
            return ConvertToPascalCase(header);
        }

        /// <summary>
        /// Converts underscore_case strings to PascalCase
        /// </summary>
        private static string ConvertToPascalCase(string input)
        {
            if (string.IsNullOrEmpty(input))
                return input;

            // First lowercase everything for consistency
            input = input.ToLowerInvariant();

            // Handle snake_case conversion
            if (input.Contains('_'))
            {
                StringBuilder pascalCase = new StringBuilder();
                bool makeUpper = true;

                foreach (char c in input)
                {
                    if (c == '_')
                    {
                        makeUpper = true;
                    }
                    else if (makeUpper)
                    {
                        pascalCase.Append(char.ToUpper(c));
                        makeUpper = false;
                    }
                    else
                    {
                        pascalCase.Append(c);
                    }
                }

                return pascalCase.ToString();
            }
            else
            {
                // For single word, just capitalize first letter
                return char.ToUpper(input[0]) + input.Substring(1);
            }
        }
    }
    //internal static class RetrieveData
    //{
    //    public static List<T> LoadFromCsv<T>(string folderPath) where T : class
    //    {
    //        // Get the type name without namespace to use as the CSV file name
    //        string typeName = typeof(T).Name.ToLowerInvariant();
    //        string csvFilePath = Path.Combine(folderPath);

    //        if (!File.Exists(csvFilePath))
    //        {
    //            Console.WriteLine($"Warning: CSV file not found at {csvFilePath}");
    //            return new List<T>();
    //        }

    //        try
    //        {
    //            using var reader = new StreamReader(csvFilePath);
    //            using var csv = new CsvReader(reader, new CsvConfiguration(CultureInfo.InvariantCulture)
    //            {
    //                Delimiter = ",",
    //                HasHeaderRecord = true,
    //                HeaderValidated = null, // Don't validate headers
    //                MissingFieldFound = null, // Don't throw on missing fields
    //                PrepareHeaderForMatch = args => ConvertToPascalCase(args.Header)
    //            });

    //            return csv.GetRecords<T>().ToList();
    //        }
    //        catch (Exception ex)
    //        {
    //            Console.WriteLine($"Error loading {typeName} data: {ex.Message}");
    //            return new List<T>();
    //        }
    //    }

    //    /// <summary>
    //    /// Converts underscore_case strings to camelCase
    //    /// </summary>
    //    /// <param name="input">The underscore_case string</param>
    //    /// <returns>The camelCase string</returns>
    //    private static string ConvertToPascalCase(string input)
    //    {
    //        if (string.IsNullOrEmpty(input))
    //            return input;

    //        // First lowercase everything for consistency
    //        input = input.ToLowerInvariant();

    //        // Handle snake_case conversion
    //        if (input.Contains('_'))
    //        {
    //            StringBuilder pascalCase = new StringBuilder();
    //            bool makeUpper = true;

    //            foreach (char c in input)
    //            {
    //                if (c == '_')
    //                {
    //                    makeUpper = true;
    //                }
    //                else if (makeUpper)
    //                {
    //                    pascalCase.Append(char.ToUpper(c));
    //                    makeUpper = false;
    //                }
    //                else
    //                {
    //                    pascalCase.Append(c);
    //                }
    //            }

    //            return pascalCase.ToString();
    //        }
    //        else
    //        {
    //            // For single word, just capitalize first letter
    //            return char.ToUpper(input[0]) + input.Substring(1);
    //        }
    //    }
    //}
}

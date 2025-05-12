import pandas as pd
from semantic_kernel.functions import kernel_function

class OperationalDataEnricher:
    """
    A plugin to retrieve operational data, such as software updates, for a specific product from a CSV file.
    """

    def __init__(self, logger, csv_file_path):
        self.logger = logger
        self.csv_file_path = csv_file_path

    @kernel_function(name="retrieve_operational_data", description="Retrieve operational data for a product.")
    def retrieve_operational_data(self, product_id: int):
        try:
            self.logger.info(f"Retrieving operational data for product_id={product_id} from CSV")

            df = pd.read_csv(self.csv_file_path)
            product_data = df[df['product_id'] == product_id]

            if product_data.empty:
                self.logger.warning(f"No operational data found for product_id={product_id}")
                return []
            
            update_descriptions = product_data['update_description'].tolist()

            self.logger.info(f"Successfully retrieved {len(update_descriptions)} updates for product_id={product_id}")
            return update_descriptions
        except Exception as e:
            self.logger.error(f"Error retrieving operational data for product_id={product_id}: {e}")
            return []

import pandas as pd
from semantic_kernel.functions import kernel_function

class CustomerDataEnricher:
    """
    A plugin to retrieve customer data from a CSV file.
    """

    def __init__(self, logger, csv_file_path):
        self.logger = logger
        self.csv_file_path = csv_file_path

    @kernel_function(name="retrieve_customer_data", description="Retrieve customer data from a CSV file.")
    def retrieve_customer_data(self, customer_id: int):
        try:
            self.logger.info(f"Retrieving data for customer_id={customer_id} from CSV")
            df = pd.read_csv(self.csv_file_path)
            customer_data = df[df['customer_id'] == customer_id]

            if customer_data.empty:
                self.logger.warning(f"No customer found with ID {customer_id}")
                return {"customer": None, "discount": None}
            
            customer = customer_data.iloc[0].to_dict()
            self.logger.info(f"Successfully retrieved data for customer_id={customer_id}")
            return {"customer": customer, "discount": None}
        except Exception as e:
            self.logger.error(f"Error retrieving customer data for customer_id={customer_id}: {e}")
            return {"customer": None, "discount": None}

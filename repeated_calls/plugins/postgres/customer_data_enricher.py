from semantic_kernel.functions import kernel_function
from sqlalchemy.orm import Session
from repeated_calls.database.tables import Customer, Discount

class CustomerDataEnricher:
    """
    A plugin to retrieve customer commercial information, such as customer details and applicable discounts.
    """

    def __init__(self, logger):
        self.logger = logger

    @kernel_function(name="retrieve_customer_data", description="Retrieve customer commercial information.")
    def retrieve_customer_data(self, session: Session, customer_id: int):
        try:
            self.logger.info(f"Retrieving data for customer_id={customer_id}")
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                self.logger.warning(f"No customer found with ID {customer_id}")
                return {"customer": None, "discount": None}
            discount = session.query(Discount).filter(Discount.minimum_clv <= customer.clv).order_by(Discount.minimum_clv.desc()).first()            
            self.logger.info(f"Successfully retrieved data for customer_id={customer_id}")
            return {"customer": customer, "discount": discount}
        except Exception as e:
            self.logger.error(f"Error retrieving customer data for customer_id={customer_id}: {e}")
            return {"customer": None, "discount": None}

"""Entity classes for representing database models."""
import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, List, Optional, Type, TypeVar

# Base directory for data files
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

T = TypeVar("T")


def parse_datetime(value: str) -> datetime:
    """
    Parse a datetime string in various formats.

    Args:
        value: Datetime string

    Returns:
        Parsed datetime object
    """
    if not value:
        raise ValueError("Empty value provided for datetime parsing.")

    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Value '{value}' does not match any expected datetime format.")


def process_csv_value(value: str, field_type: Type) -> any:
    """Convert a CSV string value to the appropriate type."""
    if field_type == int:
        return int(value) if value else 0
    elif field_type == float:
        return float(value) if value else 0.0
    elif field_type == datetime:
        return parse_datetime(value)
    elif field_type == bool:
        return value.lower() in ("true", "yes", "1")
    elif field_type == Optional[datetime]:
        return parse_datetime(value) if value else None
    else:
        return value


@dataclass
class Customer:
    """Customer entity class."""

    # Input attributes
    id: int
    name: str
    clv: str
    relation_start_date: datetime

    # Computed attributes
    relation_start_date_str: str = field(init=False)

    # Static storage for all customer instances
    _all_customers: ClassVar[List["Customer"]] = []
    _loaded: ClassVar[bool] = False

    def __post_init__(self):
        """Post-initialisation."""
        self.relation_start_date_str = self.relation_start_date.strftime("%Y-%m-%d")

    @classmethod
    def get_all(cls) -> List["Customer"]:
        """Get all customer instances, loading from CSV if not already loaded."""
        if not cls._loaded:
            cls.load_from_csv()
        return cls._all_customers

    @classmethod
    def load_from_csv(cls, csv_path: str = None) -> None:
        """Load customer data from CSV file."""
        if csv_path is None:
            csv_path = os.path.join(DATA_DIR, "customer.csv")

        cls._all_customers = []  # Clear existing data

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found at {csv_path}")
            return

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                customer = cls(
                    id=process_csv_value(row["id"], int),
                    name=process_csv_value(row["name"], str),
                    clv=process_csv_value(row["clv"], str),
                    relation_start_date=process_csv_value(row["relation_start_date"], datetime),
                )
                cls._all_customers.append(customer)

        cls._loaded = True

    @classmethod
    def find_by_id(cls, customer_id: int) -> Optional["Customer"]:
        """Find a customer by ID."""
        for customer in cls.get_all():
            if customer.id == customer_id:
                return customer
        return None


@dataclass
class CallEvent:
    """Call event entity class."""

    # Input attributes
    id: int
    customer_id: int
    sdc: str  # self-described callreason
    timestamp: datetime

    # Computed attributes
    timestamp_str: str = field(init=False)

    # Static storage for all call event instances
    _all_call_events: ClassVar[List["CallEvent"]] = []
    _loaded: ClassVar[bool] = False

    def __post_init__(self):
        """Post-initialisation."""
        self.timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def get_all(cls) -> List["CallEvent"]:
        """Get all call event instances, loading from CSV if not already loaded."""
        if not cls._loaded:
            cls.load_from_csv()
        return cls._all_call_events

    @classmethod
    def load_from_csv(cls, csv_path: str = None) -> None:
        """Load call event data from CSV file."""
        if csv_path is None:
            csv_path = os.path.join(DATA_DIR, "call_event.csv")

        cls._all_call_events = []  # Clear existing data

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found at {csv_path}")
            return

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                call_event = cls(
                    id=process_csv_value(row["id"], int),
                    customer_id=process_csv_value(row["customer_id"], int),
                    sdc=process_csv_value(row["sdc"], str),
                    timestamp=process_csv_value(row["timestamp"], datetime),
                )
                cls._all_call_events.append(call_event)

        cls._loaded = True

    @classmethod
    def find_by_customer_id(cls, customer_id: int) -> List["CallEvent"]:
        """Find call events for a specific customer."""
        return [event for event in cls.get_all() if event.customer_id == customer_id]


@dataclass
class HistoricCallEvent:
    """Historic call event entity class."""

    # Input attributes
    id: int
    customer_id: int
    sdc: str  # self-described callreason
    call_summary: str
    start_time: datetime
    end_time: datetime

    # Computed attributes
    start_time_str: str = field(init=False)
    end_time_str: str = field(init=False)
    duration_minutes: float = field(init=False)
    days_since: float | None = field(init=False, default=None)
    remaining_hours_since: float | None = field(init=False, default=None)

    # Static storage for all historic call event instances
    _all_historic_call_events: ClassVar[List["HistoricCallEvent"]] = []
    _loaded: ClassVar[bool] = False

    def __post_init__(self):
        """Post-initialisation."""
        datetime_format = "%Y-%m-%d %H:%M:%S"
        self.start_time_str = self.start_time.strftime(datetime_format)
        self.end_time_str = self.end_time.strftime(datetime_format)
        self.duration_minutes = round((self.end_time - self.start_time).total_seconds() / 60, 1)

    def compute_time_since(self, timestamp: datetime) -> None:
        """Compute time since the call event."""
        # print("FLAGGGG TESTTTT")
        total_hours_since = (timestamp - self.end_time).total_seconds() / 3600
        self.days_since = round(int(total_hours_since // 24), 1)
        self.remaining_hours_since = round(total_hours_since % 24, 1)

    @classmethod
    def get_all(cls) -> List["HistoricCallEvent"]:
        """Get all historic call event instances, loading from CSV if not already loaded."""
        if not cls._loaded:
            cls.load_from_csv()
        return cls._all_historic_call_events

    @classmethod
    def load_from_csv(cls, csv_path: str = None) -> None:
        """Load historic call event data from CSV file."""
        if csv_path is None:
            csv_path = os.path.join(DATA_DIR, "historic_call_event.csv")

        cls._all_historic_call_events = []  # Clear existing data

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found at {csv_path}")
            return

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                historic_call_event = cls(
                    id=process_csv_value(row["id"], int),
                    customer_id=process_csv_value(row["customer_id"], int),
                    sdc=process_csv_value(row["sdc"], str),
                    call_summary=process_csv_value(row["call_summary"], str),
                    start_time=process_csv_value(row["start_time"], datetime),
                    end_time=process_csv_value(row["end_time"], datetime),
                )
                cls._all_historic_call_events.append(historic_call_event)

        cls._loaded = True

    @classmethod
    def find_by_customer_id(cls, customer_id: int) -> List["HistoricCallEvent"]:
        """Find historic call events for a specific customer."""
        return [event for event in cls.get_all() if event.customer_id == customer_id]


@dataclass
class Product:
    """Product entity class."""

    id: int
    name: str
    description: str

    # Static storage for all product instances
    _all_products: ClassVar[List["Product"]] = []
    _loaded: ClassVar[bool] = False

    @classmethod
    def get_all(cls) -> List["Product"]:
        """Get all product instances, loading from CSV if not already loaded."""
        if not cls._loaded:
            cls.load_from_csv()
        return cls._all_products

    @classmethod
    def load_from_csv(cls, csv_path: str = None) -> None:
        """Load product data from CSV file."""
        if csv_path is None:
            csv_path = os.path.join(DATA_DIR, "product.csv")

        cls._all_products = []  # Clear existing data

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found at {csv_path}")
            return

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Handle difference in CSV schema vs class definition
                description = row.get("type", "")  # Using the 'type' field as description

                product = cls(
                    id=process_csv_value(row["id"], int),
                    name=process_csv_value(row["name"], str),
                    description=process_csv_value(description, str),
                )
                cls._all_products.append(product)

        cls._loaded = True

    @classmethod
    def find_by_id(cls, product_id: int) -> Optional["Product"]:
        """Find a product by ID."""
        for product in cls.get_all():
            if product.id == product_id:
                return product
        return None


@dataclass
class SoftwareUpdate:
    """Software update entity class."""

    id: int
    product_id: int
    type: str
    rollout_date: datetime

    # Static storage for all software update instances
    _all_software_updates: ClassVar[List["SoftwareUpdate"]] = []
    _loaded: ClassVar[bool] = False

    @classmethod
    def get_all(cls) -> List["SoftwareUpdate"]:
        """Get all software update instances, loading from CSV if not already loaded."""
        if not cls._loaded:
            cls.load_from_csv()
        return cls._all_software_updates

    @classmethod
    def load_from_csv(cls, csv_path: str = None) -> None:
        """Load software update data from CSV file."""
        if csv_path is None:
            csv_path = os.path.join(DATA_DIR, "software_update.csv")

        cls._all_software_updates = []  # Clear existing data

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found at {csv_path}")
            return

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                software_update = cls(
                    id=process_csv_value(row["id"], int),
                    product_id=process_csv_value(row["product_id"], int),
                    type=process_csv_value(row["type"], str),
                    rollout_date=process_csv_value(row["rollout_date"], datetime),
                )
                cls._all_software_updates.append(software_update)

        cls._loaded = True

    @classmethod
    def find_by_product_id(cls, product_id: int) -> List["SoftwareUpdate"]:
        """Find software updates for a specific product."""
        return [update for update in cls.get_all() if update.product_id == product_id]


@dataclass
class Subscription:
    """Subscription entity class."""

    id: int
    customer_id: int
    product_id: int
    start_date: datetime
    end_date: Optional[datetime] = None

    # Static storage for all subscription instances
    _all_subscriptions: ClassVar[List["Subscription"]] = []
    _loaded: ClassVar[bool] = False

    @classmethod
    def get_all(cls) -> List["Subscription"]:
        """Get all subscription instances, loading from CSV if not already loaded."""
        if not cls._loaded:
            cls.load_from_csv()
        return cls._all_subscriptions

    @classmethod
    def load_from_csv(cls, csv_path: str = None) -> None:
        """Load subscription data from CSV file."""
        if csv_path is None:
            csv_path = os.path.join(DATA_DIR, "subscription.csv")

        cls._all_subscriptions = []  # Clear existing data

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found at {csv_path}")
            return

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                subscription = cls(
                    id=process_csv_value(row["id"], int),
                    customer_id=process_csv_value(row["customer_id"], int),
                    product_id=process_csv_value(row["product_id"], int),
                    start_date=process_csv_value(row["start_date"], datetime),
                    end_date=process_csv_value(row["end_date"], Optional[datetime]) if "end_date" in row else None,
                )
                cls._all_subscriptions.append(subscription)

        cls._loaded = True

    @classmethod
    def find_by_customer_id(cls, customer_id: int) -> List["Subscription"]:
        """Find subscriptions for a specific customer."""
        return [sub for sub in cls.get_all() if sub.customer_id == customer_id]

    @classmethod
    def find_by_product_id(cls, product_id: int) -> List["Subscription"]:
        """Find subscriptions for a specific product."""
        return [sub for sub in cls.get_all() if sub.product_id == product_id]


@dataclass
class Discount:
    """Discount entity class."""

    id: int
    product_id: int
    minimum_clv: str
    percentage: float
    duration_months: int

    # Static storage for all discount instances
    _all_discounts: ClassVar[List["Discount"]] = []
    _loaded: ClassVar[bool] = False

    @classmethod
    def get_all(cls) -> List["Discount"]:
        """Get all discount instances, loading from CSV if not already loaded."""
        if not cls._loaded:
            cls.load_from_csv()
        return cls._all_discounts

    @classmethod
    def load_from_csv(cls, csv_path: str = None) -> None:
        """Load discount data from CSV file."""
        if csv_path is None:
            csv_path = os.path.join(DATA_DIR, "discount.csv")

        cls._all_discounts = []  # Clear existing data

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found at {csv_path}")
            return

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                discount = cls(
                    id=process_csv_value(row["id"], int),
                    product_id=process_csv_value(row["product_id"], int),
                    minimum_clv=process_csv_value(row["minimum_clv"], str),
                    percentage=process_csv_value(row["percentage"], float),
                    duration_months=process_csv_value(row["duration_months"], int),
                )
                cls._all_discounts.append(discount)
        cls._loaded = True

    @classmethod
    def find_by_minimum_clv(cls, clv_value: str) -> List["Discount"]:
        """Find discounts for a specific CLV level."""
        return [discount for discount in cls.get_all() if discount.minimum_clv == clv_value]

    @classmethod
    def find_by_product_id(cls, product_id: int) -> List["Discount"]:
        """Find discounts for a specific product."""
        return [discount for discount in cls.get_all() if discount.product_id == product_id]

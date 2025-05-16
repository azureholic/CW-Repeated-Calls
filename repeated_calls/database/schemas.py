"""Pydantic models used for data validation and serialization."""

import csv
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Customer(BaseModel):
    """A customer profile."""

    id: int = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer name")
    clv: str = Field(..., description="Customer lifetime value")
    relation_start_date: date = Field(..., description="Customer relation start date")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.strftime("%Y-%m-%d")})

    @staticmethod
    def from_csv(file_path: str) -> list["Customer"]:
        """Load a collection of items from a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [Customer(**row) for row in reader]


class Subscription(BaseModel):
    """A subscription that is offered."""

    id: int = Field(..., description="Subscription ID")
    customer_id: int = Field(..., description="Customer ID")
    product_id: int = Field(..., description="Product ID")
    contract_duration_months: int = Field(..., description="Contract duration in months")
    price_per_month: float = Field(..., description="Subscription price per month")
    start_date: date = Field(..., description="Subscription start date")
    end_date: date = Field(..., description="Subscription end date")

    @staticmethod
    def from_csv(file_path: str) -> list["Subscription"]:
        """Load a collection of items from a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [Subscription(**row) for row in reader]


class CallEvent(BaseModel):
    """An (incoming) call event."""

    id: int = Field(..., description="Call event ID")
    customer_id: int = Field(..., description="Customer ID")
    sdc: str = Field(..., description="Self-described call reason (SDC) by the customer")
    timestamp: datetime = Field(..., description="Call event timestamp")

    @staticmethod
    def from_csv(file_path: str) -> list["CallEvent"]:
        """Load a collection of items from a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [CallEvent(**row) for row in reader]


class HistoricCallEvent(BaseModel):
    """A historic call event."""

    id: int = Field(..., description="Historic call event ID")
    customer_id: int = Field(..., description="Customer ID")
    sdc: str = Field(..., description="Self-described call reason (SDC) by the customer")
    call_summary: str = Field(..., description="Call summary")
    start_time: datetime = Field(..., description="Call start time")
    end_time: datetime = Field(..., description="Call end time")
    days_since: float | None = Field(None, description="Days since the call event")
    remaining_hours_since: float | None = Field(None, description="Remaining hours")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")})

    @computed_field
    @property
    def duration_minutes(self) -> float:
        """Calculate the duration of the call in minutes."""
        return round((self.end_time - self.start_time).total_seconds() / 60, 1)

    @staticmethod
    def from_csv(file_path: str) -> list["HistoricCallEvent"]:
        """Load a collection of items from a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [HistoricCallEvent(**row) for row in reader]

    def compute_time_since(self, timestamp: datetime) -> None:
        """Compute the time since the call event.

        Args:
            timestamp (datetime): The timestamp to compare against.
        """
        total_hours_since = (timestamp - self.end_time).total_seconds() / 3600
        self.days_since = round(int(total_hours_since // 24), 1)
        self.remaining_hours_since = round(total_hours_since % 24, 1)


class Product(BaseModel):
    """A product."""

    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    type: str = Field(..., description="Product description")
    listing_price: float = Field(..., description="Listed price of the product")

    @staticmethod
    def from_csv(file_path: str) -> list["Product"]:
        """Load a collection of items from a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [Product(**row) for row in reader]


class Discount(BaseModel):
    """A discount for a product."""

    id: int = Field(..., description="Discount ID")
    product_id: int = Field(..., description="Product ID")
    minimum_clv: str = Field(..., description="Minimum CLV to qualify for the discount")
    percentage: int = Field(..., description="Discount percentage")
    duration_months: int = Field(..., description="Duration of the discount in months")

    @staticmethod
    def from_csv(file_path: str) -> list["Discount"]:
        """Load a collection of items from a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [Discount(**row) for row in reader]


class SoftwareUpdate(BaseModel):
    """A software update."""

    id: int = Field(..., description="Software update ID")
    product_id: int = Field(..., description="Product ID")
    rollout_date: date = Field(..., description="Software update rollout date")
    type: str = Field(..., description="Type of software update")

    @staticmethod
    def from_csv(file_path: str) -> list["SoftwareUpdate"]:
        """Load a collection of items from a CSV file.

        Args:
            file_path (str): Path to the CSV file.
        """
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [SoftwareUpdate(**row) for row in reader]

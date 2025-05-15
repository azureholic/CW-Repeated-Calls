"""Pydantic models used for data validation and serialization."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class Customer(BaseModel):
    """A customer profile."""

    id: int = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer name")
    clv: str = Field(..., description="Customer lifetime value")
    relation_start_date: date = Field(..., description="Customer relation start date")


class Subscription(BaseModel):
    """A subscription that is offered."""

    id: int = Field(..., description="Subscription ID")
    customer_id: int = Field(..., description="Customer ID")
    product_id: int = Field(..., description="Product ID")
    contract_duration_months: int = Field(..., description="Contract duration in months")
    price_per_month: float = Field(..., description="Subscription price per month")
    start_date: date = Field(..., description="Subscription start date")
    end_date: date = Field(..., description="Subscription end date")


class CallEvent(BaseModel):
    """An (incoming) call event."""

    id: int = Field(..., description="Call event ID")
    customer_id: int = Field(..., description="Customer ID")
    sdc: str = Field(..., description="Self-described call reason (SDC) by the customer")
    timestamp: datetime = Field(..., description="Call event timestamp")


class HistoricCallEvent(BaseModel):
    """A historic call event."""

    id: int = Field(..., description="Historic call event ID")
    customer_id: int = Field(..., description="Customer ID")
    sdc: str = Field(..., description="Self-described call reason (SDC) by the customer")
    call_summary: str = Field(..., description="Call summary")
    start_time: datetime = Field(..., description="Call start time")
    end_time: datetime = Field(..., description="Call end time")


class Product(BaseModel):
    """A product."""

    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    type: str = Field(..., description="Product description")
    listing_price: float = Field(..., description="Listed price of the product")


class Discount(BaseModel):
    """A discount for a product."""

    id: int = Field(..., description="Discount ID")
    product_id: int = Field(..., description="Product ID")
    minimum_clv: str = Field(..., description="Minimum CLV to qualify for the discount")
    percentage: int = Field(..., description="Discount percentage")
    duration_months: int = Field(..., description="Duration of the discount in months")


class SoftwareUpdate(BaseModel):
    """A software update."""

    id: int = Field(..., description="Software update ID")
    product_id: int = Field(..., description="Product ID")
    rollout_date: date = Field(..., description="Software update rollout date")
    type: str = Field(..., description="Type of software update")

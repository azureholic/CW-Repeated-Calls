"""Pydantic models for customer-related data and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HistoricCallEvent(BaseModel):
    """Represents a historic call event."""

    id: int
    customer_id: int
    sdc: str = Field(description="Self-described call reason")
    call_summary: str
    start_time: datetime
    end_time: Optional[datetime] = None


class HistoricCallEventResponse(BaseModel):
    """Response model for historic call events."""

    events: List[HistoricCallEvent]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Customer(BaseModel):
    """Represents a customer."""

    id: int
    name: str
    clv: str
    relation_start_date: datetime


class CustomerResponse(BaseModel):
    """Response model for customer data."""

    customer: Optional[Customer] = None
    query_time_ms: float
    error: Optional[str] = None


class CallEvent(BaseModel):
    """Represents a call event."""

    id: int
    customer_id: int
    sdc: str
    timestamp: datetime


class CallEventResponse(BaseModel):
    """Response model for call events."""

    events: List[CallEvent]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Subscription(BaseModel):
    """Represents a subscription."""

    id: int
    customer_id: int
    product_id: int
    contract_duration_months: int
    price_per_month: float
    start_date: datetime
    end_date: datetime


class SubscriptionResponse(BaseModel):
    """Response model for subscriptions."""

    subscriptions: List[Subscription]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Product(BaseModel):
    """Represents a product."""

    id: int
    name: str
    type: str
    listing_price: float


class ProductResponse(BaseModel):
    """Response model for products."""

    products: List[Product]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class SoftwareUpdate(BaseModel):
    """Represents a software update."""

    id: int
    product_id: int
    rollout_date: datetime
    type: str


class SoftwareUpdateResponse(BaseModel):
    """Response model for software updates."""

    updates: List[SoftwareUpdate]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Discount(BaseModel):
    """Represents a discount."""

    id: int
    product_id: int
    minimum_clv: str
    percentage: float
    duration_months: int


class DiscountResponse(BaseModel):
    """Response model for discounts."""

    discounts: List[Discount]
    count: int
    query_time_ms: float
    error: Optional[str] = None

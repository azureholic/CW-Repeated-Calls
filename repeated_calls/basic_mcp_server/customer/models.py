from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class HistoricCallEvent(BaseModel):
    id: int
    customer_id: int
    sdc: str = Field(description="Self-described call reason")
    call_summary: str
    start_time: datetime
    end_time: Optional[datetime] = None


class HistoricCallEventResponse(BaseModel):
    events: List[HistoricCallEvent]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Customer(BaseModel):
    id: int
    name: str
    clv: str
    relation_start_date: datetime


class CustomerResponse(BaseModel):
    customer: Optional[Customer] = None
    query_time_ms: float
    error: Optional[str] = None


class CallEvent(BaseModel):
    id: int
    customer_id: int
    sdc: str
    timestamp: datetime


class CallEventResponse(BaseModel):
    events: List[CallEvent]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Subscription(BaseModel):
    id: int
    customer_id: int
    product_id: int
    contract_duration_months: int
    price_per_month: float
    start_date: datetime
    end_date: datetime


class SubscriptionResponse(BaseModel):
    subscriptions: List[Subscription]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Product(BaseModel):
    id: int
    name: str
    type: str
    listing_price: float


class ProductResponse(BaseModel):
    products: List[Product]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class SoftwareUpdate(BaseModel):
    id: int
    product_id: int
    rollout_date: datetime
    type: str


class SoftwareUpdateResponse(BaseModel):
    updates: List[SoftwareUpdate]
    count: int
    query_time_ms: float
    error: Optional[str] = None


class Discount(BaseModel):
    id: int
    product_id: int
    minimum_clv: str
    percentage: float
    duration_months: int


class DiscountResponse(BaseModel):
    discounts: List[Discount]
    count: int
    query_time_ms: float
    error: Optional[str] = None
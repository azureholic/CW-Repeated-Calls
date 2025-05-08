from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String())
    clv: Mapped[str] = mapped_column(String())
    relation_start_date: Mapped[date] = mapped_column(Date())


class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer(), ForeignKey("customer.id"))
    product_id: Mapped[int] = mapped_column(Integer(), ForeignKey("product.id"))
    contract_duration_months: Mapped[int] = mapped_column(Integer())
    price_per_month: Mapped[float] = mapped_column(Float())
    start_date: Mapped[date] = mapped_column(Date())
    end_date: Mapped[date] = mapped_column(Date())


class CallEvent(Base):
    __tablename__ = "call_event"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer(), ForeignKey("customer.id"))
    sdc: Mapped[str] = mapped_column(String())
    time_stamp: Mapped[datetime] = mapped_column(DateTime())


class HistoricCallEvent(Base):
    __tablename__ = "historic_call_event"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer(), ForeignKey("customer.id"))
    sdc: Mapped[str] = mapped_column(String())
    call_summary: Mapped[str] = mapped_column(String())
    start_time: Mapped[datetime] = mapped_column(DateTime())
    end_time: Mapped[datetime] = mapped_column(DateTime())


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String())
    type: Mapped[str] = mapped_column(String())
    listing_price: Mapped[float] = mapped_column(Float())


class Discount(Base):
    __tablename__ = "discount"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer(), ForeignKey("product.id"))
    clv: Mapped[str] = mapped_column(String())
    percentage: Mapped[int] = mapped_column(Integer())
    duration_months: Mapped[int] = mapped_column(Integer())


class SoftwareUpdate(Base):
    __tablename__ = "software_update"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer(), ForeignKey("product.id"))
    rollout_date: Mapped[date] = mapped_column(Date())
    type: Mapped[str] = mapped_column(String())

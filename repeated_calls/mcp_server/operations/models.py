"""Models for operations-related MCP data."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SoftwareUpdate(BaseModel):
    """Represents a software update record."""

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

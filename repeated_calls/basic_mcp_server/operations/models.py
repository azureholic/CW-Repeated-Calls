from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


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
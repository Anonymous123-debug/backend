from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FixedSlotCreate(BaseModel):
    title: str
    google_start_datetime: datetime
    google_end_datetime: datetime

class FixedSlotUpdate(BaseModel):
    title: Optional[str] = None
    google_start_datetime: Optional[datetime] = None
    google_end_datetime: Optional[datetime] = None

class FixedSlotResponse(BaseModel):
    id: int
    user_id: int
    title: str
    google_start_datetime: datetime
    google_end_datetime: datetime
    is_google_event: bool
    google_event_id: Optional[str]
    last_updated_source: Optional[str]
    is_deleted: bool
    
    class Config:
        from_attributes = True
from sqlalchemy.orm import Session
from persistence.models import FixedSlot
from typing import Optional, List
from datetime import datetime

class FixedSlotRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, slot_id: int) -> Optional[FixedSlot]:
        return self.db.query(FixedSlot).filter(FixedSlot.id == slot_id).first()
    
    def get_by_google_event_id(self, google_event_id: str) -> Optional[FixedSlot]:
        return self.db.query(FixedSlot).filter(
            FixedSlot.google_event_id == google_event_id
        ).first()
    
    def get_by_user_id(self, user_id: int) -> List[FixedSlot]:
        return self.db.query(FixedSlot).filter(
            FixedSlot.user_id == user_id,
            FixedSlot.is_deleted == False
        ).all()
    
    def create(self, user_id: int, **kwargs) -> FixedSlot:
        slot = FixedSlot(user_id=user_id, **kwargs)
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot
    
    def update(self, slot_id: int, data: dict) -> Optional[FixedSlot]:
        slot = self.get_by_id(slot_id)
        if slot:
            for key, value in data.items():
                setattr(slot, key, value)
            self.db.commit()
            self.db.refresh(slot)
        return slot
    
    def update_with_lock(self, slot_id: int, data: dict) -> Optional[FixedSlot]:
        """Update with row-level lock to prevent race conditions"""
        slot = self.db.query(FixedSlot).filter(
            FixedSlot.id == slot_id
        ).with_for_update().first()
        
        if slot:
            for key, value in data.items():
                setattr(slot, key, value)
            self.db.commit()
            self.db.refresh(slot)
        return slot
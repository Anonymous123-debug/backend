from sqlalchemy.orm import Session
from persistence.models import CalendarSyncState
from typing import Optional
from datetime import datetime

class SyncStateRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_id(self, user_id: int) -> Optional[CalendarSyncState]:
        return self.db.query(CalendarSyncState).filter(
            CalendarSyncState.user_id == user_id
        ).first()
    
    def create_or_update(self, user_id: int, **kwargs) -> CalendarSyncState:
        state = self.get_by_user_id(user_id)
        if state:
            for key, value in kwargs.items():
                setattr(state, key, value)
        else:
            state = CalendarSyncState(user_id=user_id, **kwargs)
            self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state
    
    def update_sync_token(self, user_id: int, sync_token: Optional[str], last_synced_at: datetime = None):
        state = self.get_by_user_id(user_id)
        if not state:
            state = CalendarSyncState(user_id=user_id)
            self.db.add(state)
        
        state.sync_token = sync_token
        if last_synced_at:
            state.last_synced_at = last_synced_at
        self.db.commit()
    
    def update_webhook_info(self, user_id: int, webhook_channel_id: str, 
                           webhook_resource_id: str, webhook_expires_at: datetime):
        state = self.get_by_user_id(user_id)
        if not state:
            state = CalendarSyncState(user_id=user_id)
            self.db.add(state)
        
        state.webhook_channel_id = webhook_channel_id
        state.webhook_resource_id = webhook_resource_id
        state.webhook_expires_at = webhook_expires_at
        self.db.commit()
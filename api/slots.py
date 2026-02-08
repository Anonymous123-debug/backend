from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from schemas.slot_schemas import FixedSlotCreate, FixedSlotUpdate, FixedSlotResponse
from persistence.database import get_db
from persistence.repositories.user_repository import UserRepository
from persistence.repositories.fixed_slot_repository import FixedSlotRepository
from persistence.repositories.sync_state_repository import SyncStateRepository
from services.google_oauth import GoogleOAuthService
from services.calendar_service import CalendarService
from services.sync_engine import SyncEngine

router = APIRouter(prefix="/slots")

def get_sync_engine(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    slot_repo = FixedSlotRepository(db)
    sync_state_repo = SyncStateRepository(db)
    oauth_service = GoogleOAuthService(user_repo)
    calendar_service = CalendarService(oauth_service, slot_repo, sync_state_repo)
    return SyncEngine(oauth_service, calendar_service, slot_repo, sync_state_repo)

@router.post("/", response_model=FixedSlotResponse)
def create_slot(
    slot_data: FixedSlotCreate,
    x_user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
    sync_engine: SyncEngine = Depends(get_sync_engine)
):
    """Create a new slot and sync to Google"""
    slot_repo = FixedSlotRepository(db)
    
    # Create in database
    slot = slot_repo.create(
        user_id=x_user_id,
        title=slot_data.title,
        google_start_datetime=slot_data.google_start_datetime,
        google_end_datetime=slot_data.google_end_datetime,
        last_updated_source='APP',
        last_updated_at=datetime.utcnow(),
        is_google_event=False
    )
    
    # Push to Google
    try:
        sync_engine.push_to_google(x_user_id, slot.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync to Google: {str(e)}")
    
    # Refresh to get updated google_event_id
    db.refresh(slot)
    return slot

@router.get("/", response_model=list[FixedSlotResponse])
def list_slots(
    x_user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """List all slots for a user"""
    slot_repo = FixedSlotRepository(db)
    return slot_repo.get_by_user_id(x_user_id)

@router.put("/{slot_id}", response_model=FixedSlotResponse)
def update_slot(
    slot_id: int,
    slot_data: FixedSlotUpdate,
    x_user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
    sync_engine: SyncEngine = Depends(get_sync_engine)
):
    """Update a slot and sync to Google"""
    slot_repo = FixedSlotRepository(db)
    
    update_data = slot_data.model_dump(exclude_unset=True)
    update_data['last_updated_source'] = 'APP'
    update_data['last_updated_at'] = datetime.utcnow()
    
    slot = slot_repo.update(slot_id, update_data)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # Push to Google
    try:
        sync_engine.push_to_google(x_user_id, slot_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync to Google: {str(e)}")
    
    db.refresh(slot)
    return slot

@router.delete("/{slot_id}")
def delete_slot(
    slot_id: int,
    x_user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
    sync_engine: SyncEngine = Depends(get_sync_engine)
):
    """Delete a slot (soft delete) and sync to Google"""
    slot_repo = FixedSlotRepository(db)
    
    slot = slot_repo.update(
        slot_id,
        {
            'is_deleted': True,
            'last_updated_source': 'APP',
            'last_updated_at': datetime.utcnow()
        }
    )
    
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # Delete from Google
    try:
        sync_engine.push_to_google(x_user_id, slot_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync to Google: {str(e)}")
    
    return {"status": "deleted", "slot_id": slot_id}
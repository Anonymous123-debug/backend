from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from persistence.database import get_db
from persistence.repositories.user_repository import UserRepository
from persistence.repositories.fixed_slot_repository import FixedSlotRepository
from persistence.repositories.sync_state_repository import SyncStateRepository
from services.google_oauth import GoogleOAuthService
from services.calendar_service import CalendarService
from services.sync_engine import SyncEngine
import os

router = APIRouter(prefix="/webhooks")

def get_sync_engine(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    slot_repo = FixedSlotRepository(db)
    sync_state_repo = SyncStateRepository(db)
    oauth_service = GoogleOAuthService(user_repo)
    calendar_service = CalendarService(oauth_service, slot_repo, sync_state_repo)
    return SyncEngine(oauth_service, calendar_service, slot_repo, sync_state_repo)

@router.post("/google-calendar")
async def google_calendar_webhook(
    request: Request,
    x_goog_channel_id: str = Header(None, alias="X-Goog-Channel-ID"),
    x_goog_resource_state: str = Header(None, alias="X-Goog-Resource-State"),
    sync_engine: SyncEngine = Depends(get_sync_engine)
):
    """Receive push notifications from Google Calendar"""
    
    # Handle sync confirmation
    if x_goog_resource_state == 'sync':
        return {"status": "webhook confirmed"}
    
    # Extract user_id from channel_id
    if not x_goog_channel_id:
        return {"status": "no channel id"}
    
    try:
        # Parse user_id from channel-{user_id}-{uuid}
        parts = x_goog_channel_id.split('-')
        if len(parts) >= 2:
            user_id = int(parts[1])
        else:
            return {"status": "invalid channel id format"}
    except (ValueError, IndexError):
        return {"status": "could not parse user_id"}
    
    # Trigger sync
    try:
        sync_engine.sync_from_google(user_id)
        return {"status": "sync completed", "user_id": user_id}
    except Exception as e:
        print(f"Error during webhook sync: {e}")
        return {"status": "sync failed", "error": str(e)}

@router.post("/setup/{user_id}")
def setup_webhook(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Setup webhook channel for a user"""
    user_repo = UserRepository(db)
    slot_repo = FixedSlotRepository(db)
    sync_state_repo = SyncStateRepository(db)
    oauth_service = GoogleOAuthService(user_repo)
    calendar_service = CalendarService(oauth_service, slot_repo, sync_state_repo)
    
    webhook_url = f"{os.getenv('WEBHOOK_BASE_URL')}/webhooks/google-calendar"
    
    try:
        response = calendar_service.setup_webhook_channel(user_id, webhook_url)
        return {
            "status": "webhook configured",
            "channel_id": response['id'],
            "webhook_url": webhook_url,
            "expires_at": response.get('expiration')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
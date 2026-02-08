from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from dateutil import parser as date_parser

class SyncEngine:
    def __init__(self, oauth_service, calendar_service, slot_repository, sync_state_repository):
        self.oauth_service = oauth_service
        self.calendar_service = calendar_service
        self.slot_repo = slot_repository
        self.sync_state_repo = sync_state_repository
    
    def push_to_google(self, user_id: int, slot_id: int):
        """Push app changes to Google Calendar with loop prevention"""
        slot = self.slot_repo.get_by_id(slot_id)
        if not slot:
            return
        
        # CRITICAL: Prevent loop
        if slot.last_updated_source != 'APP':
            return
        
        # Check circuit breaker
        if slot.last_updated_at:
            seconds_since_update = (datetime.utcnow() - slot.last_updated_at).total_seconds()
            if seconds_since_update < 2:
                return  # Too soon, possible loop
        
        try:
            if not slot.is_google_event:
                # Create new event
                google_event_id = self.calendar_service.create_event_in_google(
                    user_id,
                    {
                        'title': slot.title,
                        'google_start_datetime': slot.google_start_datetime,
                        'google_end_datetime': slot.google_end_datetime
                    }
                )
                
                self.slot_repo.update(
                    slot_id,
                    {
                        'google_event_id': google_event_id,
                        'is_google_event': True,
                        'last_updated_source': 'APP',
                        'last_updated_at': datetime.utcnow()
                    }
                )
            else:
                # Update or delete existing event
                if slot.is_deleted:
                    self.calendar_service.delete_event_in_google(user_id, slot.google_event_id)
                else:
                    self.calendar_service.update_event_in_google(
                        user_id,
                        slot.google_event_id,
                        {
                            'title': slot.title,
                            'google_start_datetime': slot.google_start_datetime,
                            'google_end_datetime': slot.google_end_datetime
                        }
                    )
        except Exception as e:
            print(f"Error pushing to Google: {e}")
            raise
    
    def sync_from_google(self, user_id: int):
        """Fetch changes from Google Calendar (incremental sync)"""
        creds = self.oauth_service.get_valid_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        
        sync_state = self.sync_state_repo.get_by_user_id(user_id)
        calendar_id = sync_state.google_calendar_id if sync_state else 'primary'
        
        try:
            if sync_state and sync_state.sync_token:
                # Incremental sync
                events_result = service.events().list(
                    calendarId=calendar_id,
                    syncToken=sync_state.sync_token
                ).execute()
            else:
                # Initial sync
                events_result = service.events().list(
                    calendarId=calendar_id,
                    singleEvents=True,
                    timeMin=datetime.utcnow().isoformat() + 'Z'
                ).execute()
            
            # Process events
            for event in events_result.get('items', []):
                self._process_google_event(user_id, event)
            
            # Save new sync token
            new_sync_token = events_result.get('nextSyncToken')
            if new_sync_token:
                self.sync_state_repo.update_sync_token(
                    user_id,
                    sync_token=new_sync_token,
                    last_synced_at=datetime.utcnow()
                )
        
        except HttpError as e:
            if e.resp.status == 410:
                # Sync token expired - full resync
                self._full_resync(user_id)
            else:
                print(f"Error syncing from Google: {e}")
                raise
    
    def _process_google_event(self, user_id: int, event: dict):
        """Process individual event from Google"""
        google_event_id = event['id']
        existing_slot = self.slot_repo.get_by_google_event_id(google_event_id)
        
        # Handle deleted events
        if event.get('status') == 'cancelled':
            if existing_slot:
                if existing_slot.last_updated_source == 'APP':
                    return  # Skip echo
                
                self.slot_repo.update(
                    existing_slot.id,
                    {
                        'is_deleted': True,
                        'last_updated_source': 'GOOGLE',
                        'last_updated_at': datetime.utcnow()
                    }
                )
            return
        
        # Parse event data
        event_data = {
            'title': event.get('summary', 'Untitled'),
            'google_start_datetime': self._parse_datetime(event['start']),
            'google_end_datetime': self._parse_datetime(event['end']),
            'google_event_id': google_event_id,
            'is_google_event': True,
            'last_updated_source': 'GOOGLE',
            'last_updated_at': datetime.utcnow()
        }
        
        if existing_slot:
            # Check for echo
            if existing_slot.last_updated_source == 'APP':
                if self._events_match(existing_slot, event_data):
                    return  # Skip echo
            
            self.slot_repo.update(existing_slot.id, event_data)
        else:
            self.slot_repo.create(user_id=user_id, **event_data)
    
    def _events_match(self, slot, event_data: dict) -> bool:
        """Check if event matches (for echo detection)"""
        time_tolerance = timedelta(seconds=5)
        
        start_match = abs(slot.google_start_datetime.replace(tzinfo=None) - 
                         event_data['google_start_datetime'].replace(tzinfo=None)) < time_tolerance
        end_match = abs(slot.google_end_datetime.replace(tzinfo=None) - 
                       event_data['google_end_datetime'].replace(tzinfo=None)) < time_tolerance
        title_match = slot.title == event_data['title']
        
        return start_match and end_match and title_match
    
    def _parse_datetime(self, dt_dict: dict) -> datetime:
        """Parse Google Calendar datetime"""
        if 'dateTime' in dt_dict:
            return date_parser.parse(dt_dict['dateTime'])
        elif 'date' in dt_dict:
            return datetime.fromisoformat(dt_dict['date'])
        return datetime.utcnow()
    
    def _full_resync(self, user_id: int):
        """Perform full resync when sync token is invalid"""
        self.sync_state_repo.update_sync_token(user_id, sync_token=None)
        self.sync_from_google(user_id)
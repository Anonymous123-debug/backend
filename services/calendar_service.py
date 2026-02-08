from googleapiclient.discovery import build
from datetime import datetime, timedelta
import uuid
import os

class CalendarService:
    def __init__(self, oauth_service, slot_repository, sync_state_repository):
        self.oauth_service = oauth_service
        self.slot_repo = slot_repository
        self.sync_state_repo = sync_state_repository
    
    def create_event_in_google(self, user_id: int, slot_data: dict) -> str:
        creds = self.oauth_service.get_valid_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        
        sync_state = self.sync_state_repo.get_by_user_id(user_id)
        calendar_id = sync_state.google_calendar_id if sync_state else 'primary'
        
        event_body = {
            'summary': slot_data['title'],
            'start': {
                'dateTime': slot_data['google_start_datetime'].isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': slot_data['google_end_datetime'].isoformat(),
                'timeZone': 'UTC',
            }
        }
        
        event = service.events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()
        
        return event['id']
    
    def update_event_in_google(self, user_id: int, google_event_id: str, slot_data: dict):
        creds = self.oauth_service.get_valid_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        
        sync_state = self.sync_state_repo.get_by_user_id(user_id)
        calendar_id = sync_state.google_calendar_id if sync_state else 'primary'
        
        event_body = {
            'summary': slot_data['title'],
            'start': {
                'dateTime': slot_data['google_start_datetime'].isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': slot_data['google_end_datetime'].isoformat(),
                'timeZone': 'UTC',
            }
        }
        
        service.events().update(
            calendarId=calendar_id,
            eventId=google_event_id,
            body=event_body
        ).execute()
    
    def delete_event_in_google(self, user_id: int, google_event_id: str):
        creds = self.oauth_service.get_valid_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        
        sync_state = self.sync_state_repo.get_by_user_id(user_id)
        calendar_id = sync_state.google_calendar_id if sync_state else 'primary'
        
        service.events().delete(
            calendarId=calendar_id,
            eventId=google_event_id
        ).execute()
    
    def setup_webhook_channel(self, user_id: int, webhook_url: str):
        creds = self.oauth_service.get_valid_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        
        sync_state = self.sync_state_repo.get_by_user_id(user_id)
        calendar_id = sync_state.google_calendar_id if sync_state else 'primary'
        
        channel_body = {
            'id': f"channel-{user_id}-{uuid.uuid4()}",
            'type': 'web_hook',
            'address': webhook_url,
            'expiration': int((datetime.utcnow() + timedelta(days=7)).timestamp() * 1000)
        }
        
        response = service.events().watch(
            calendarId=calendar_id,
            body=channel_body
        ).execute()
        
        self.sync_state_repo.update_webhook_info(
            user_id,
            webhook_channel_id=response['id'],
            webhook_resource_id=response['resourceId'],
            webhook_expires_at=datetime.fromtimestamp(response['expiration'] / 1000)
        )
        
        return response
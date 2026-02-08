from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleOAuthService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, user_repository):
        self.user_repo = user_repository
        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("OAUTH_REDIRECT_URI")]
            }
        }
    
    def get_authorization_url(self, state: str = "random_state") -> str:
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=self.client_config["web"]["redirect_uris"][0]
        )
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            state=state
        )
        return auth_url
    
    def exchange_code_for_tokens(self, code: str) -> dict:
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=self.client_config["web"]["redirect_uris"][0]
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user email from Google
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=credentials)
        calendar = service.calendars().get(calendarId='primary').execute()
        email = calendar.get('id', 'unknown@example.com')
        
        return {
            "refresh_token": credentials.refresh_token,
            "access_token": credentials.token,
            "email": email
        }
    
    def get_valid_credentials(self, user_id: int) -> Credentials:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        creds = Credentials(
            token=None,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_config["web"]["client_id"],
            client_secret=self.client_config["web"]["client_secret"],
            scopes=self.SCOPES
        )
        
        if not creds.valid:
            creds.refresh(Request())
        
        return creds
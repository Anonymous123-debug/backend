from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from services.google_oauth import GoogleOAuthService
from persistence.repositories.user_repository import UserRepository
from persistence.database import get_db
from pydantic import BaseModel, EmailStr
import secrets

router = APIRouter(prefix="/auth")

class UserCreate(BaseModel):
    email: EmailStr

@router.post("/users")
def create_user_manual(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Manually create a user (for testing)
    User must still complete OAuth to get a valid Google refresh token
    """
    user_repo = UserRepository(db)
    
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        return {
            "message": "User already exists",
            "user_id": existing_user.id,
            "email": existing_user.email,
            "has_valid_token": "PLACEHOLDER" not in existing_user.google_refresh_token
        }
    
    # Create user with placeholder token
    user = user_repo.create_or_update(
        email=user_data.email,
        google_refresh_token="PLACEHOLDER_TOKEN_COMPLETE_OAUTH"
    )
    
    return {
        "message": "User created successfully",
        "user_id": user.id,
        "email": user.email,
        "next_step": "Complete OAuth by visiting /auth/google/authorize"
    }

@router.get("/google/authorize")
def authorize(
    user_email: str = Query(None, description="Optional: pre-fill with specific user email"),
    db: Session = Depends(get_db)
):
    """
    Get Google OAuth authorization URL
    Optional: pass user_email to ensure OAuth completes for specific user
    """
    user_repo = UserRepository(db)
    oauth_service = GoogleOAuthService(user_repo)
    
    state = secrets.token_urlsafe(32)
    
    # Optionally encode user_email in state for tracking
    if user_email:
        state = f"{state}:{user_email}"
    
    auth_url = oauth_service.get_authorization_url(state)
    
    return {
        "authorization_url": auth_url,
        "instructions": "Open this URL in your browser to authorize with Google"
    }

@router.get("/google/callback")
def oauth_callback(
    code: str, 
    state: str, 
    db: Session = Depends(get_db)
):
    """Handle OAuth callback and store refresh token"""
    user_repo = UserRepository(db)
    oauth_service = GoogleOAuthService(user_repo)
    
    try:
        # Exchange code for tokens
        tokens = oauth_service.exchange_code_for_tokens(code)
        
        # Create or update user with real refresh token
        user = user_repo.create_or_update(
            email=tokens["email"],
            google_refresh_token=tokens["refresh_token"]
        )
        
        return {
            "status": "success",
            "message": "Authorization successful! You can now close this window.",
            "user_id": user.id,
            "email": user.email
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"OAuth failed: {str(e)}"
        )

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """List all users (for testing/debugging)"""
    from persistence.models import User
    users = db.query(User).all()
    
    return {
        "count": len(users),
        "users": [
            {
                "user_id": u.id,
                "email": u.email,
                "has_valid_token": "PLACEHOLDER" not in u.google_refresh_token,
                "created_at": u.created_at
            }
            for u in users
        ]
    }

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user details"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user.id,
        "email": user.email,
        "has_valid_token": "PLACEHOLDER" not in user.google_refresh_token,
        "created_at": user.created_at
    }
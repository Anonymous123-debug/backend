from sqlalchemy.orm import Session
from persistence.models import User
from typing import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def create_or_update(self, email: str, google_refresh_token: str) -> User:
        user = self.get_by_email(email)
        if user:
            user.google_refresh_token = google_refresh_token
        else:
            user = User(email=email, google_refresh_token=google_refresh_token)
            self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
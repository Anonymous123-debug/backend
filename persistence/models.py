from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    google_refresh_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    fixed_slots = relationship("FixedSlot", back_populates="user", cascade="all, delete-orphan")
    sync_state = relationship("CalendarSyncState", back_populates="user", uselist=False, cascade="all, delete-orphan")

class FixedSlot(Base):
    __tablename__ = 'fixed_slots'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    title = Column(String, nullable=False)
    
    google_start_datetime = Column(DateTime(timezone=True), nullable=False)
    google_end_datetime = Column(DateTime(timezone=True), nullable=False)
    
    day_of_week = Column(String(10))
    start_time = Column(Time)
    end_time = Column(Time)
    
    is_google_event = Column(Boolean, default=False)
    google_event_id = Column(String, unique=True)
    
    last_updated_source = Column(String(10))
    last_updated_at = Column(DateTime)
    
    is_deleted = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="fixed_slots")
    
    __table_args__ = (
        CheckConstraint("last_updated_source IN ('APP', 'GOOGLE')"),
    )

class CalendarSyncState(Base):
    __tablename__ = 'calendar_sync_state'
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    google_calendar_id = Column(String, default='primary')
    
    sync_token = Column(String)
    last_synced_at = Column(DateTime)
    
    webhook_channel_id = Column(String)
    webhook_resource_id = Column(String)
    webhook_expires_at = Column(DateTime)
    
    user = relationship("User", back_populates="sync_state")
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from pymongo import MongoClient
from config import settings
import logging

# MySQL Database Setup
MYSQL_URL = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"

engine = create_engine(MYSQL_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB Setup
mongo_client = MongoClient(settings.MONGODB_URL)
mongo_db = mongo_client[settings.MONGODB_DATABASE]
messages_collection = mongo_db.messages

# Association table for many-to-many relationship between users and chats
chat_participants = Table(
    'chat_participants',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('chat_id', Integer, ForeignKey('chats.id'), primary_key=True),
    Column('joined_at', DateTime, default=func.now()),
    Column('is_admin', Boolean, default=False)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    
    # Relationships
    chats = relationship("Chat", secondary=chat_participants, back_populates="participants")
    sent_messages = relationship("MessageMetadata", back_populates="sender")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))  # For group chats
    chat_type = Column(String(20), nullable=False)  # 'direct' or 'group'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    participants = relationship("User", secondary=chat_participants, back_populates="chats")
    messages = relationship("MessageMetadata", back_populates="chat")

class MessageMetadata(Base):
    __tablename__ = "message_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(String(100), unique=True, nullable=False)  # MongoDB document ID
    timestamp = Column(DateTime, default=func.now())
    message_type = Column(String(20), default="text")
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mongo_db():
    return mongo_db

def create_tables():
    """Create all tables in the database"""
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise

def init_mongodb_indexes():
    """Initialize MongoDB indexes for better performance"""
    try:
        # Create indexes for better query performance
        messages_collection.create_index("message_id")
        messages_collection.create_index("timestamp")
        messages_collection.create_index("chat_id")
        logging.info("MongoDB indexes created successfully")
    except Exception as e:
        logging.error(f"Error creating MongoDB indexes: {e}")
        raise

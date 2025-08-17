from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager

from config import settings
from database import create_tables, init_mongodb_indexes
from routes import users, chats, messages, websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Chat Service...")
    
    try:
        # Initialize databases
        create_tables()
        init_mongodb_indexes()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Chat Service...")

# Create FastAPI app
app = FastAPI(
    title="Chat Service API",
    description="A real-time chat service supporting 1:1 and group chats",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(chats.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Chat Service API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connections
        from database import SessionLocal, mongo_db
        
        # Test MySQL connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # Test MongoDB connection
        mongo_db.command("ping")
        
        return {
            "status": "healthy",
            "mysql": "connected",
            "mongodb": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/v1/info")
async def get_api_info():
    """Get API information"""
    return {
        "name": "Chat Service API",
        "version": "1.0.0",
        "features": {
            "direct_chat": True,
            "group_chat": True,
            "real_time_messaging": True,
            "message_history": True,
            "typing_indicators": True,
            "online_status": True
        },
        "limits": {
            "max_group_members": settings.MAX_GROUP_MEMBERS,
            "max_message_length": settings.MAX_MESSAGE_LENGTH
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )

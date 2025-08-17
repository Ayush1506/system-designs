import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "chat_user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "chat_password")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "chat_service")
    
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "chat_messages")
    
    # JWT Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Chat Configuration
    MAX_GROUP_MEMBERS = 100
    MAX_MESSAGE_LENGTH = 10000

settings = Settings()

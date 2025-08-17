#!/usr/bin/env python3
"""
Local development runner for Chat Service
This script helps you run the chat service locally with minimal setup
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version: {sys.version}")
    return True

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    if not venv_path.exists():
        logger.info("Creating virtual environment...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            logger.info("Virtual environment created successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
    else:
        logger.info("Virtual environment already exists")
    return True

def get_venv_python():
    """Get the path to the virtual environment Python executable"""
    if sys.platform == "win32":
        return Path("venv/Scripts/python.exe")
    else:
        return Path("venv/bin/python")

def install_dependencies():
    """Install required Python packages in virtual environment"""
    logger.info("Installing dependencies in virtual environment...")
    
    # Create virtual environment first
    if not create_virtual_environment():
        return False
    
    venv_python = get_venv_python()
    
    try:
        # Upgrade pip first
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
        
        # Try simple requirements first (latest versions)
        logger.info("Trying to install latest versions of packages...")
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", "requirements-simple.txt"])
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install latest versions: {e}")
        logger.info("Trying with specific versions...")
        try:
            # Try specific versions
            subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"])
            logger.info("Dependencies installed successfully with specific versions")
            return True
        except subprocess.CalledProcessError as e2:
            logger.error(f"Failed to install specific versions: {e2}")
            logger.info("Trying with --break-system-packages flag...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-simple.txt", "--break-system-packages"])
                logger.info("Dependencies installed successfully with --break-system-packages")
                return True
            except subprocess.CalledProcessError as e3:
                logger.error(f"Failed to install dependencies even with --break-system-packages: {e3}")
                return False

def setup_env_file():
    """Set up environment file with default values for local development"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            logger.info("Creating .env file from .env.example...")
            # Copy example file and modify for local development
            with open(env_example, 'r') as f:
                content = f.read()
            
            # Replace with local development values
            content = content.replace("your-secret-key-here", "local-dev-secret-key-change-in-production")
            content = content.replace("chat_password", "password")
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            logger.info(".env file created with local development settings")
        else:
            logger.error(".env.example file not found")
            return False
    else:
        logger.info(".env file already exists")
    
    return True

def check_databases():
    """Check if databases are accessible and provide setup instructions"""
    logger.info("Checking database requirements...")
    
    print("\n" + "="*60)
    print("DATABASE SETUP REQUIRED")
    print("="*60)
    
    print("\n1. MySQL Setup:")
    print("   - Install MySQL server")
    print("   - Create database and user:")
    print("     CREATE DATABASE chat_service;")
    print("     CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'password';")
    print("     GRANT ALL PRIVILEGES ON chat_service.* TO 'chat_user'@'localhost';")
    print("     FLUSH PRIVILEGES;")
    
    print("\n2. MongoDB Setup:")
    print("   - Install MongoDB")
    print("   - Start MongoDB service:")
    print("     - On macOS: brew services start mongodb-community")
    print("     - On Ubuntu: sudo systemctl start mongod")
    print("     - On Windows: Start MongoDB service from Services")
    print("   - MongoDB will run on default port 27017")
    
    print("\n3. After setting up databases, run:")
    print("   python init_db.py")
    
    print("\n" + "="*60)
    
    return True

def run_server():
    """Run the FastAPI server"""
    logger.info("Starting Chat Service server...")
    
    venv_python = get_venv_python()
    
    # Check if we should use virtual environment
    if venv_python.exists():
        logger.info("Using virtual environment to run server...")
        try:
            # Run server using virtual environment python
            subprocess.check_call([
                str(venv_python), "main.py"
            ])
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start server with virtual environment: {e}")
            return False
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            return True
    else:
        # Fallback to system python
        try:
            # Import here to avoid import errors if dependencies aren't installed
            import uvicorn
            from main import app
            
            logger.info("Server starting on http://localhost:8000")
            logger.info("API Documentation: http://localhost:8000/docs")
            logger.info("Press Ctrl+C to stop the server")
            
            uvicorn.run(
                "main:app",
                host="0.0.0.0",
                port=8000,
                reload=True,
                log_level="info"
            )
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            logger.error("Make sure all dependencies are installed")
            return False
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    return True

def main():
    """Main function to set up and run the chat service locally"""
    print("Chat Service Local Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Set up environment file
    if not setup_env_file():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Check database requirements
    check_databases()
    
    # Ask user if they want to continue
    response = input("\nHave you set up the databases? (y/n): ").lower().strip()
    if response != 'y':
        print("Please set up the databases first, then run this script again.")
        return 0
    
    # Initialize databases
    try:
        logger.info("Initializing databases...")
        venv_python = get_venv_python()
        if venv_python.exists():
            subprocess.check_call([str(venv_python), "init_db.py"])
        else:
            from init_db import main as init_db_main
            init_db_main()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error("Please check your database connections and try again")
        return 1
    
    # Run the server
    run_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

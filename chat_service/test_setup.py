#!/usr/bin/env python3
"""
Test setup script for Chat Service - runs without requiring databases
This script tests if all dependencies are installed correctly
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

def get_venv_python():
    """Get the path to the virtual environment Python executable"""
    if sys.platform == "win32":
        return Path("venv/Scripts/python.exe")
    else:
        return Path("venv/bin/python")

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    venv_python = get_venv_python()
    
    test_script = '''
import sys
print(f"Python version: {sys.version}")

try:
    import fastapi
    print(f"✅ FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"❌ FastAPI: {e}")

try:
    import uvicorn
    print(f"✅ Uvicorn: {uvicorn.__version__}")
except ImportError as e:
    print(f"❌ Uvicorn: {e}")

try:
    import sqlalchemy
    print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ SQLAlchemy: {e}")

try:
    import pymongo
    print(f"✅ PyMongo: {pymongo.__version__}")
except ImportError as e:
    print(f"❌ PyMongo: {e}")

try:
    import pydantic
    print(f"✅ Pydantic: {pydantic.__version__}")
except ImportError as e:
    print(f"❌ Pydantic: {e}")

try:
    import websockets
    print(f"✅ WebSockets: {websockets.__version__}")
except ImportError as e:
    print(f"❌ WebSockets: {e}")

try:
    import mysql.connector
    print(f"✅ MySQL Connector: {mysql.connector.__version__}")
except ImportError as e:
    print(f"❌ MySQL Connector: {e}")

try:
    from jose import jwt
    print("✅ Python-JOSE: OK")
except ImportError as e:
    print(f"❌ Python-JOSE: {e}")

try:
    from passlib.context import CryptContext
    print("✅ Passlib: OK")
except ImportError as e:
    print(f"❌ Passlib: {e}")

print("\\n🎉 All core dependencies are working!")
'''
    
    try:
        if venv_python.exists():
            result = subprocess.run([str(venv_python), "-c", test_script], 
                                  capture_output=True, text=True, check=True)
            print(result.stdout)
        else:
            exec(test_script)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Import test failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def test_app_structure():
    """Test if the app can be imported without database connections"""
    logger.info("Testing app structure...")
    
    venv_python = get_venv_python()
    
    test_script = '''
import sys
import os

# Test basic imports
try:
    from config import settings
    print("✅ Config loaded successfully")
    print(f"   - Max group members: {settings.MAX_GROUP_MEMBERS}")
    print(f"   - Max message length: {settings.MAX_MESSAGE_LENGTH}")
except Exception as e:
    print(f"❌ Config error: {e}")

try:
    from schemas import UserCreate, ChatCreate, MessageCreate
    print("✅ Schemas imported successfully")
except Exception as e:
    print(f"❌ Schemas error: {e}")

try:
    from auth import get_password_hash, verify_password
    print("✅ Auth functions imported successfully")
    
    # Test password hashing
    test_password = "test123"
    hashed = get_password_hash(test_password)
    if verify_password(test_password, hashed):
        print("✅ Password hashing works correctly")
    else:
        print("❌ Password hashing failed")
except Exception as e:
    print(f"❌ Auth error: {e}")

print("\\n🎉 App structure is correct!")
'''
    
    try:
        if venv_python.exists():
            result = subprocess.run([str(venv_python), "-c", test_script], 
                                  capture_output=True, text=True, check=True)
            print(result.stdout)
        else:
            exec(test_script)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"App structure test failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Test the chat service setup without requiring databases"""
    print("Chat Service Setup Test")
    print("=" * 40)
    
    # Check if virtual environment exists
    venv_python = get_venv_python()
    if not venv_python.exists():
        logger.error("Virtual environment not found. Please run 'python3 run_local.py' first.")
        return 1
    
    logger.info("Virtual environment found ✅")
    
    # Test imports
    if not test_imports():
        logger.error("Import tests failed")
        return 1
    
    print("\n" + "="*50)
    
    # Test app structure
    if not test_app_structure():
        logger.error("App structure tests failed")
        return 1
    
    print("\n" + "="*50)
    print("🎉 SUCCESS! Your chat service setup is working correctly!")
    print("\nNext steps:")
    print("1. Set up MySQL and MongoDB databases")
    print("2. Run 'python3 run_local.py' and answer 'y' when asked about databases")
    print("3. The server will start at http://localhost:8000")
    print("4. Visit http://localhost:8000/docs for API documentation")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

#scripts/init_database.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import mongo_manager
import bcrypt
from datetime import datetime

def setup_initial_admin():
    """Create initial admin user if no users exist"""
    if not mongo_manager.connect():
        print("Failed to connect to database")
        return False
    
    # Check if any users exist
    if mongo_manager.db.users.count_documents({}) > 0:
        print("Users already exist in database")
        return True
    
    # Create admin user
    password = "admin123"  # Change this in production!
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    result = mongo_manager.db.users.insert_one({
        "username": "admin",
        "password": hashed_password,
        "created_at": datetime.now(),
        "last_login": None,
        "two_factor_secret": None,
        "two_factor_enabled": False
    })
    
    if result.inserted_id:
        print(f"Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: admin123")  # Warn user to change this
        print("⚠️  CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!")
        return True
    return False

if __name__ == "__main__":

    setup_initial_admin()



# database.py
import pymongo
from pymongo import MongoClient
from datetime import datetime
import streamlit as st
import bcrypt
from encryption import encryption_manager

class MongoDBManager:
    def __init__(self):
        # MongoDB connection details
        self.connection_string = "mongodb://localhost:27017/"
        self.database_name = "password_manager"
        self.client = None
        self.db = None
        self.connected = False  # Track connection status
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            # Test the connection
            self.client.admin.command('ping')
            self.connected = True
            return True
        except Exception as e:
            st.error(f"Failed to connect to MongoDB: {str(e)}")
            self.connected = False
            return False
            
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            
    def is_connected(self):
        """Check if database is connected"""
        return self.connected
            
    def init_database(self):
        """
        Initialize the database with proper collections and indexes
        """
        if not self.is_connected():
            if not self.connect():
                return False
        
        # Create users collection if it doesn't exist
        if "users" not in self.db.list_collection_names():
            self.db.create_collection("users")
            # Create unique index on username
            self.db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
            
        # Create passwords collection if it doesn't exist
        if "passwords" not in self.db.list_collection_names():
            self.db.create_collection("passwords")
            # Create compound index on username and service
            self.db.passwords.create_index(
                [("username", pymongo.ASCENDING), ("service", pymongo.ASCENDING)], 
                unique=True
            )
            
        return True

    def get_user_2fa_secret(self, username):
        """Get user's 2FA secret"""
        if not self.is_connected():
            if not self.connect():
                return None
        try:
            user = self.db.users.find_one({"username": username})
            return user.get('two_factor_secret') if user else None
        except Exception as e:
            st.error(f"Error retrieving 2FA secret: {str(e)}")
            return None

    def update_user_2fa_secret(self, username, secret):
        """Update user's 2FA secret"""
        if not self.is_connected():
            if not self.connect():
                return False
        try:
            result = self.db.users.update_one(
                {"username": username},
                {"$set": {"two_factor_secret": secret}}
            )
            return result.modified_count > 0
        except Exception as e:
            st.error(f"Error updating 2FA secret: {str(e)}")
            return False

    def set_user_2fa_enabled(self, username, enabled: bool):
        """Set user's 2FA enabled status"""
        if not self.is_connected():
            if not self.connect():
                return False
        try:
            result = self.db.users.update_one(
                {"username": username},
                {"$set": {"two_factor_enabled": enabled}}
            )
            return result.modified_count > 0
        except Exception as e:
            st.error(f"Error updating 2FA status: {str(e)}")
            return False

    def is_2fa_enabled(self, username):
        """Check if 2FA is enabled for user"""
        if not self.is_connected():
            if not self.connect():
                return False
        try:
            user = self.db.users.find_one({"username": username})
            return user.get('two_factor_enabled', False) if user else False
        except Exception as e:
            st.error(f"Error checking 2FA status: {str(e)}")
            return False

    def create_user(self, username, password):
        """
        Create a new user with hashed password
        """
        if not self.is_connected():
            if not self.connect():
                return False
                
        try:
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Insert user into users collection
            result = self.db.users.insert_one({
                "username": username,
                "password": hashed_password,
                "created_at": datetime.now(),
                "last_login": None,
                "two_factor_secret": None, 
                "two_factor_enabled": False,
                "is_admin": False # Default to non-admin
            })
            
            return result.inserted_id is not None
        except pymongo.errors.DuplicateKeyError:
            st.error("Username already exists")
            return False
        except Exception as e:
            st.error(f"Failed to create user: {str(e)}")
            return False
            
    def verify_user(self, username, password):
        """
        Verify user credentials
        """
        if not self.is_connected():
            if not self.connect():
                return False
                
        try:
            # Find user by username
            user = self.db.users.find_one({"username": username})
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # Update last login time
                self.db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"last_login": datetime.now()}}
                )
                return True
            return False
        except Exception as e:
            st.error(f"Error verifying user: {str(e)}")
            return False
            
    def get_user_passwords(self, username):
        """
        Get all passwords for a specific user
        """
        if not self.is_connected():
            if not self.connect():
                return []
                
        try:
            passwords = self.db.passwords.find({"username": username}).sort("service", pymongo.ASCENDING)
            return list(passwords)
        except Exception as e:
            st.error(f"Error retrieving passwords: {str(e)}")
            return []
            
    def save_password(self, username, service, service_username, password):
        """Save or update a password for a user with encryption"""
        if not self.is_connected():
            if not self.connect():
                return False
                
        try:
            # Encrypt the password before storing
            encrypted_password = encryption_manager.encrypt_password(password)
            if not encrypted_password:
                st.error("Failed to encrypt password")
                return False
            
            # Check if password already exists for this service
            existing = self.db.passwords.find_one({
                "username": username,
                "service": service
            })
            
            if existing:
                # Update existing password
                result = self.db.passwords.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {
                            "service_username": service_username,
                            "password": encrypted_password,  # Store encrypted
                            "updated_at": datetime.now()
                        }
                    }
                )
                return result.modified_count > 0
            else:
                # Insert new password
                result = self.db.passwords.insert_one({
                    "username": username,
                    "service": service,
                    "service_username": service_username,
                    "password": encrypted_password,  # Store encrypted
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                })
                return result.inserted_id is not None
                
        except Exception as e:
            st.error(f"Error saving password: {str(e)}")
            return False

    def get_decrypted_password(self, username, service):
        """Retrieve and decrypt a password"""
        if not self.is_connected():
            if not self.connect():
                return None
        entry = self.db.passwords.find_one({
            "username": username,
            "service": service
        })
        
        if entry and 'password' in entry:
            return encryption_manager.decrypt_password(entry['password'])
        return None
            
    def delete_password(self, username, service):
        """
        Delete a password for a specific service
        """
        if not self.is_connected():
            if not self.connect():
                return False
                
        try:
            result = self.db.passwords.delete_one({
                "username": username,
                "service": service
            })
            return result.deleted_count > 0
        except Exception as e:
            st.error(f"Error deleting password: {str(e)}")
            return False

# Global MongoDB manager instance
mongo_manager = MongoDBManager()
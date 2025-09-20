# crud_operations.py
from database import mongo_manager
from datetime import datetime
import streamlit as st
import time
import re
from encryption import encryption_manager

# Validation pattern
SERVICE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\- ]+$')

def is_valid_service_name(service):
    return bool(SERVICE_NAME_PATTERN.match(service)) and len(service.strip()) > 0

def _ensure_db_connection():
    """Helper to ensure database connection before operation."""
    if not mongo_manager.is_connected():
        if not mongo_manager.init_database():
            st.error("Failed to connect to database.")
            return False
    return True

def register_user(username, password):
    """
    Register a new user with hashed password
    """
    if not username or not password:
        st.error("Username and password are required")
        return False
        
    if not _ensure_db_connection():
        return False
        
    # Create user
    return mongo_manager.create_user(username, password)

def verify_user_credentials(username, password):
    """
    Verify user credentials
    """
    if not username or not password:
        return False
        
    if not _ensure_db_connection():
        return False
        
    return mongo_manager.verify_user(username, password)

def service_exists(username, service):
    """
    Check if a service already exists for the given user
    """
    try:
        if not _ensure_db_connection():
            return False
                
        # Check if service exists
        existing_entry = mongo_manager.db.passwords.find_one({
            "username": username,
            "service": service
        })
        
        return existing_entry is not None
    except Exception as e:
        st.error(f"Error checking service existence: {str(e)}")
        return False

def save_password(service, service_username, password):
    """
    Save a password to MongoDB for the current user
    """
    if not is_valid_service_name(service):
        st.error("Error: Service name can only contain letters, numbers, spaces, hyphens, and underscores")
        return False
    
    if not password.strip():
        st.error("Error: Password cannot be blank")
        return False
        
    # Get the current user from session state
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("Error: No user logged in")
        return False
        
    # Check if service already exists
    if service_exists(current_user, service):
        st.error(f"Error: Service '{service}' already exists. Use update instead.")
        return False
        
    if not _ensure_db_connection():
        return False
        
    # Save the password
    return mongo_manager.save_password(current_user, service, service_username, password)

def get_password(service):
    """
    Retrieve a password for a specific service (decrypted)
    """
    if not is_valid_service_name(service):
        st.error("Error: Invalid service name format")
        return None
        
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("Error: No user logged in")
        return None
        
    try:
        if not _ensure_db_connection():
            return None
                
        # Use the new decryption method
        decrypted_password = mongo_manager.get_decrypted_password(current_user, service)
        
        if decrypted_password:
            # Get the full entry for timestamp info
            entry = mongo_manager.db.passwords.find_one({
                "username": current_user,
                "service": service
            })
            
            return {
                'service': service,
                'username': entry.get('service_username'),
                'password': decrypted_password,  # Decrypted password
                'timestamp': entry.get('updated_at', entry.get('created_at')).strftime("%Y-%m-%d %H:%M:%S")
            }
        return None
    except Exception as e:
        st.error(f"Error retrieving password: {str(e)}")
        return None

def complete_login(username):
    """
    Complete the login process after successful authentication
    This function should be called after both password and 2FA verification
    """
    # Update last login time in database
    if mongo_manager.is_connected():
        try:
            mongo_manager.db.users.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.now()}}
            )
        except Exception as e:
            st.error(f"Error updating login time: {str(e)}")
    
    # Set session state variables
    st.session_state.authenticated = True
    st.session_state.current_user = username
    st.session_state.last_activity = time.time()
    st.session_state.login_attempts = 0
    st.session_state.account_locked = False
    st.session_state.lock_time = None
    st.session_state.current_page_num = 1
    st.session_state.login_step = None
    
    # Clear temporary credentials
    st.session_state.temp_username = None
    st.session_state.temp_password = None
    st.session_state.otp_attempts = 0
    st.session_state.otp_lock_time = None
    
    # Reset password cache
    if 'passwords_loaded' in st.session_state:
        st.session_state.passwords_loaded = False
    if 'passwords' in st.session_state:
        st.session_state.passwords = []
    
    st.success("Login successful! Redirecting...")
    time.sleep(1)
    st.rerun()

def get_all_passwords():
    """
    Retrieve all passwords for the current user
    """
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("Error: No user logged in")
        return []
        
    try:
        if not _ensure_db_connection():
            return []
                
        entries = mongo_manager.get_user_passwords(current_user)
        passwords = []
        for entry in entries:
            # Passwords stored in DB are encrypted, decrypt them here for display
            decrypted_pwd = encryption_manager.decrypt_password(entry.get('password'))
            passwords.append({
                'service': entry.get('service'),
                'username': entry.get('service_username'),
                'password': decrypted_pwd,  # Decrypted password
                'timestamp': entry.get('updated_at', entry.get('created_at')).strftime("%Y-%m-%d %H:%M:%S")
            })
        return passwords
    except Exception as e:
        st.error(f"Error retrieving passwords: {str(e)}")
        return []

def update_password(service, new_password):
    """
    Update a password for a specific service
    """
    if not is_valid_service_name(service):
        st.error("Error: Invalid service name format")
        return False
        
    if not new_password.strip():
        st.error("Error: Password cannot be blank")
        return False
        
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("Error: No user logged in")
        return False
        
    if not _ensure_db_connection():
        return False
        
    # Get the current service username to preserve it
    current_data = get_password(service) # Use this to get service_username
    if not current_data:
        st.error(f"No password found for service '{service}'")
        return False
        
    # Update the password while preserving the service username
    return mongo_manager.save_password(current_user, service, current_data['username'], new_password)

def delete_password(service):
    """
    Delete a password for a specific service
    """
    if not is_valid_service_name(service):
        st.error("Error: Invalid service name format")
        return False
        
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("Error: No user logged in")
        return False
        
    if not _ensure_db_connection():
        return False
            
    return mongo_manager.delete_password(current_user, service)

def get_user_2fa_secret(username):
    """Retrieves the 2FA secret for a given user."""
    if not _ensure_db_connection():
        return None
    
    return mongo_manager.get_user_2fa_secret(username)

def update_user_2fa_secret(username, secret):
    """Updates the 2FA secret for a given user."""
    if not _ensure_db_connection():
        return False
    
    return mongo_manager.update_user_2fa_secret(username, secret)

def set_user_2fa_enabled(username, enabled: bool):
    """Sets the 2FA enabled status for a given user."""
    if not _ensure_db_connection():
        return False
    
    return mongo_manager.set_user_2fa_enabled(username, enabled)

def is_2fa_enabled(username):
    """Checks if 2FA is enabled for a given user."""
    if not _ensure_db_connection():
        return False
    
    return mongo_manager.is_2fa_enabled(username)
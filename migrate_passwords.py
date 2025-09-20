# migrate_passwords.py
from database import mongo_manager
from encryption import encryption_manager
#from crud_operations import is_valid_service_name
import streamlit as st

def has_migration_been_run():
    """Check if migration has already been performed"""
    # Check if any passwords are already encrypted
    collection = mongo_manager.db.passwords
    encrypted_passwords = collection.count_documents({
        "password": {"$regex": r"^gAAAA[A-Za-z0-9+/]+={0,2}$"}  # Fernet pattern
    })
    return encrypted_passwords > 0

def migrate_existing_passwords():
    """Migrate existing plaintext passwords to encrypted format"""
    if has_migration_been_run():
        st.warning("⚠️ Password migration has already been completed!")
        return False
    
    try:
        # Get all password entries
        passwords_collection = mongo_manager.db.passwords
        all_entries = list(passwords_collection.find({}))
        
        migrated_count = 0
        failed_count = 0
        
        for entry in all_entries:
            current_password = entry.get('password', '')
            
            # Skip if already encrypted or empty
            if not current_password or len(current_password) > 100:
                continue
                
            # Encrypt the password
            encrypted_password = encryption_manager.encrypt_password(current_password)
            if encrypted_password:
                # Update the document with encrypted password
                result = passwords_collection.update_one(
                    {"_id": entry["_id"]},
                    {"$set": {"password": encrypted_password}}
                )
                if result.modified_count > 0:
                    migrated_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        
        st.success(f"Password migration complete: {migrated_count} migrated, {failed_count} failed")
        return True
        
    except Exception as e:
        st.error(f"Migration error: {str(e)}")
        return False

# Add this to your main app for one-time execution
if __name__ == "__main__":
    if st.button("Migrate Existing Passwords to Encryption"):
        migrate_existing_passwords()
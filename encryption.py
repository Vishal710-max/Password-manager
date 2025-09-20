# encryption.py
from cryptography.fernet import Fernet
import os
import streamlit as st
import base64

class EncryptionManager:
    def __init__(self):
        self.key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.key)
    
    def _get_encryption_key(self):
        """Get encryption key from environment variable with fallback"""
        # Try to get key from environment variable
        key_env = os.environ.get('PASSWORD_MANAGER_ENCRYPTION_KEY')
        
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env)
            except:
                st.error("Invalid encryption key in environment variable")
                return None
        
        # Try to get key from Streamlit secrets
        try:
            if hasattr(st, 'secrets') and 'encryption_key' in st.secrets:
                return base64.urlsafe_b64decode(st.secrets['encryption_key'])
        except:
            pass
        
        # Use a default key for development (not recommended for production)
        st.warning("Using default encryption key for development. Not secure for production!")
        default_key = base64.urlsafe_b64decode("RFUyV2NHaV8yYnpGb2s3MFhwaGRzcXd5cjJfTUNJYlNqLU5mX1dmNVpzWT0=")
        return default_key
    
    def encrypt_password(self, password):
        """Encrypt a password"""
        if not password or self.key is None:
            return None
        try:
            return self.cipher_suite.encrypt(password.encode()).decode()
        except Exception as e:
            st.error(f"Encryption error: {str(e)}")
            return None
    
    def decrypt_password(self, encrypted_password):
        """Decrypt a password"""
        if not encrypted_password or self.key is None:
            return None
        try:
            return self.cipher_suite.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            st.error(f"Decryption error: {str(e)}")
            return None

# Global encryption manager instance
encryption_manager = EncryptionManager()
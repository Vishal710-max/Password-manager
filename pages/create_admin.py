# pages/Create_Admin.py
import streamlit as st
from database import mongo_manager
import bcrypt
from datetime import datetime

def create_admin_user():
    """Create admin user if it doesn't exist and show results in Streamlit"""
    
    # Initialize database connection
    if not mongo_manager.connect():
        st.error("❌ Failed to connect to database")
        return False
    
    # Check if admin already exists
    if mongo_manager.db.users.find_one({"username": "admin"}):
        st.success("✅ Admin user already exists")
        return True
    
    # Create admin user with password "admin123"
    password = "admin123"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    result = mongo_manager.db.users.insert_one({
        "username": "admin",
        "password": hashed_password,
        "created_at": datetime.now(),
        "last_login": None,
        "two_factor_secret": None,
        "two_factor_enabled": False,
        "is_admin": True
    })
    
    if result.inserted_id:
        st.success("✅ Admin user created successfully!")
        
        # Display credentials in a nice box
        st.info("""
        **📋 Login Credentials:**
        - **Username:** `admin`
        - **Password:** `admin123`
        
        ⚠️ **IMPORTANT:** Change this password after first login!
        """)
        
        # Warning box for security
        st.warning("""
        🔒 **SECURITY NOTICE:** 
        - The default password is insecure
        - Change it immediately after login
        - Enable 2FA for better security
        """)
        
        return True
    else:
        st.error("❌ Failed to create admin user")
        return False

def update_admin_password():
    """Update admin password - only accessible to admin users"""
    
    # Check if current user is admin
    if not st.session_state.get('authenticated', False):
        st.error("⛔ You must be logged in to update admin password")
        return False
        
    if st.session_state.get('current_user') != 'admin':
        st.error("⛔ Administrator privileges required to update admin password")
        return False
    
    # Initialize database connection
    if not mongo_manager.connect():
        st.error("❌ Failed to connect to database")
        return False
    
    # Check if admin exists
    admin_user = mongo_manager.db.users.find_one({"username": "admin"})
    if not admin_user:
        st.error("❌ Admin user does not exist. Please create it first.")
        return False
    
    st.subheader("🔐 Update Admin Password")
    
    with st.form("update_admin_password_form"):
        current_password = st.text_input("Current Password", type="password", 
                                        placeholder="Enter current admin password")
        new_password = st.text_input("New Password", type="password", 
                                    placeholder="Enter new password")
        confirm_password = st.text_input("Confirm New Password", type="password", 
                                        placeholder="Re-enter new password")
        
        if st.form_submit_button("Update Admin Password", use_container_width=True):
            if not current_password or not new_password or not confirm_password:
                st.error("Please fill in all fields.")
                return False
                
            if new_password != confirm_password:
                st.error("New passwords do not match.")
                return False
                
            if len(new_password) < 8:
                st.error("New password must be at least 8 characters long.")
                return False
                
            # Verify current password
            if not bcrypt.checkpw(current_password.encode('utf-8'), admin_user['password']):
                st.error("Current password is incorrect.")
                return False
                
            # Hash new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Update password in database
            result = mongo_manager.db.users.update_one(
                {"username": "admin"},
                {"$set": {"password": hashed_password}}
            )
            
            if result.modified_count > 0:
                st.success("✅ Admin password updated successfully!")
                return True
            else:
                st.error("❌ Failed to update admin password")
                return False
    
    return False

def main():
    st.set_page_config(
        page_title="Create Admin - Password Manager",
        page_icon="👨‍💼",
        layout="centered"
    )
    
    st.title("👨‍💼 Administrator Account Management")
    st.markdown("---")
    
    # Check if user is already logged in as admin
    is_admin_logged_in = (st.session_state.get('authenticated', False) and 
                         st.session_state.get('current_user') == 'admin')
    
    # Create tabs for different functionalities
    if is_admin_logged_in:
        admin_tabs = st.tabs(["📋 Create Admin", "🔐 Update Admin Password", "📊 Admin Status"])
    else:
        admin_tabs = st.tabs(["📋 Create Admin", "📊 Admin Status"])
    
    with admin_tabs[0]:  # Create Admin tab
        st.subheader("Create Administrator Account")
        
        st.markdown("""
        ### Welcome to Admin Setup
        
        This section helps you create the initial administrator account for your password manager.
        
        **What will be created:**
        - 👤 Username: `admin`
        - 🔑 Password: `admin123` (change this immediately!)
        - ⚠️ Admin privileges: **Enabled**
        """)
        
        # Create columns for better layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            **ℹ️ Important Notes:**
            - This only needs to be done once
            - Admin account has special privileges
            - Change the default password immediately
            """)
        
        with col2:
            st.warning("""
            **⚠️ Security Alert:**
            Default password is weak!
            Change it after login.
            """)
        
        st.markdown("---")
        
        # Create admin button
        if st.button("🛠️ Create Admin Account", type="primary", use_container_width=True):
            with st.spinner("Creating admin account..."):
                success = create_admin_user()
                
                if success:
                    st.balloons()
                    st.markdown("---")
                    
                    # Next steps
                    st.subheader("🎉 Next Steps:")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🔐 Login Now", use_container_width=True):
                            st.session_state.current_page = "login"
                            st.switch_page("demo.py")
                    
                    with col2:
                        if st.button("🔄 Check Status", use_container_width=True):
                            st.rerun()
                    
                    with col3:
                        if st.button("🏠 Go Home", use_container_width=True):
                            st.switch_page("demo.py")
    
    # Add Update Admin Password tab if user is logged in as admin
    if is_admin_logged_in and len(admin_tabs) > 1:
        with admin_tabs[1]:  # Update Admin Password tab
            update_admin_password()
    
    # Status check section (always available)
    status_tab_index = 2 if is_admin_logged_in else 1
    with admin_tabs[status_tab_index]:
        st.subheader("🔍 Current Status Check")
        
        if st.button("🔄 Check if Admin Exists", use_container_width=True):
            if mongo_manager.connect():
                admin_exists = mongo_manager.db.users.find_one({"username": "admin"})
                if admin_exists:
                    st.success("✅ Admin account exists in database")
                    
                    # Show admin account details
                    st.json({
                        "Username": admin_exists.get('username'),
                        "Is Admin": admin_exists.get('is_admin', False),
                        "2FA Enabled": admin_exists.get('two_factor_enabled', False),
                        "Created At": admin_exists.get('created_at', 'N/A').strftime("%Y-%m-%d %H:%M:%S") if admin_exists.get('created_at') else 'N/A',
                        "Last Login": admin_exists.get('last_login', 'N/A').strftime("%Y-%m-%d %H:%M:%S") if admin_exists.get('last_login') else 'Never'
                    })
                else:
                    st.warning("❌ No admin account found")
            else:
                st.error("❌ Cannot connect to database")

# Add to sidebar menu in demo.py
if __name__ == "__main__":
    main()
# pages/Admin.py
import streamlit as st
from database import mongo_manager
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

def get_database_statistics():
    """Get comprehensive database statistics"""
    stats = {}
    
    try:
        # User statistics
        stats['total_users'] = mongo_manager.db.users.count_documents({})
        stats['admin_users'] = mongo_manager.db.users.count_documents({"is_admin": True})
        stats['regular_users'] = stats['total_users'] - stats['admin_users']
        
        # Password statistics
        stats['total_passwords'] = mongo_manager.db.passwords.count_documents({})
        
        # Storage statistics
        users_size = mongo_manager.db.command("collstats", "users")['size']
        passwords_size = mongo_manager.db.command("collstats", "passwords")['size']
        stats['total_storage_kb'] = (users_size + passwords_size) / 1024
        
        # Activity statistics (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        stats['recent_logins'] = mongo_manager.db.users.count_documents({
            "last_login": {"$gte": week_ago}
        })
        
        # Password strength analysis (placeholder - would require actual analysis)
        stats['weak_passwords'] = 0  # This would require password strength checking
        
        return stats
        
    except Exception as e:
        st.error(f"Error fetching statistics: {str(e)}")
        return None

def show_user_management():
    """User management functionality"""
    st.subheader("👥 User Management")
    
    # Get all users
    try:
        users = list(mongo_manager.db.users.find({}, {
            "username": 1, 
            "created_at": 1, 
            "last_login": 1, 
            "is_admin": 1,
            "two_factor_enabled": 1
        }).sort("created_at", -1))
        
        if users:
            # Convert to DataFrame for better display
            user_data = []
            for user in users:
                user_data.append({
                    "Username": user.get('username', 'N/A'),
                    "Admin": "✅" if user.get('is_admin') else "❌",
                    "2FA Enabled": "✅" if user.get('two_factor_enabled') else "❌",
                    "Created": user.get('created_at', 'N/A').strftime("%Y-%m-%d") if user.get('created_at') else 'N/A',
                    "Last Login": user.get('last_login', 'N/A').strftime("%Y-%m-%d %H:%M") if user.get('last_login') else 'Never',
                    "Status": "Active" if user.get('last_login') else "Inactive"
                })
            
            df = pd.DataFrame(user_data)
            
            # Display user table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Username": st.column_config.TextColumn("Username", width="medium"),
                    "Admin": st.column_config.TextColumn("Admin", width="small"),
                    "2FA Enabled": st.column_config.TextColumn("2FA", width="small"),
                    "Created": st.column_config.TextColumn("Created", width="small"),
                    "Last Login": st.column_config.TextColumn("Last Login", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small")
                }
            )
            
            # User actions
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Refresh User List", use_container_width=True):
                    st.rerun()
            
            with col2:
                if st.button("📊 Export User Data (JSON)", use_container_width=True):
                    json_data = df.to_json(orient="records", force_ascii=False, indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name="users_export.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            with col3:
                if st.button("🧹 Find Inactive Users", use_container_width=True):
                    inactive_threshold = datetime.now() - timedelta(days=30)
                    inactive_users = mongo_manager.db.users.count_documents({
                        "last_login": {"$lt": inactive_threshold}
                    })
                    st.info(f"🔍 {inactive_users} users inactive for 30+ days")
        
        else:
            st.info("No users found in the database.")
            
    except Exception as e:
        st.error(f"Error accessing user data: {str(e)}")

def show_database_statistics():
    """Display comprehensive database statistics"""
    st.subheader("📊 Database Statistics")
    
    stats = get_database_statistics()
    if not stats:
        return
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", stats['total_users'])
    with col2:
        st.metric("Admin Users", stats['admin_users'])
    with col3:
        st.metric("Total Passwords", stats['total_passwords'])
    with col4:
        st.metric("Storage Used", f"{stats['total_storage_kb']:.1f} KB")
    
    # Visualization
    st.markdown("---")
    
    # User type pie chart
    user_types = {
        'Admin Users': stats['admin_users'],
        'Regular Users': stats['regular_users']
    }
    
    if stats['total_users'] > 0:
        fig = px.pie(
            values=list(user_types.values()),
            names=list(user_types.keys()),
            title="User Distribution",
            color=list(user_types.keys()),
            color_discrete_map={'Admin Users':'red', 'Regular Users':'green'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.info(f"🎯 {stats['recent_logins']} users logged in during last 7 days")
    
    # Database health check
    st.markdown("---")
    st.subheader("🔧 Database Health")
    
    health_col1, health_col2 = st.columns(2)
    
    with health_col1:
        if st.button("🩺 Run Health Check", use_container_width=True):
            try:
                # Simple health check
                users_ok = mongo_manager.db.users.find_one() is not None
                passwords_ok = mongo_manager.db.passwords.find_one() is not None
                
                if users_ok and passwords_ok:
                    st.success("✅ Database connection healthy")
                else:
                    st.warning("⚠️ Database collections may be empty")
                    
            except Exception as e:
                st.error(f"❌ Health check failed: {str(e)}")
    
    with health_col2:
        if st.button("📈 Performance Stats", use_container_width=True):
            try:
                # Collection stats
                users_stats = mongo_manager.db.command("collstats", "users")
                passwords_stats = mongo_manager.db.command("collstats", "passwords")
                
                st.info(f"📁 Users collection: {users_stats['count']} documents")
                st.info(f"🔑 Passwords collection: {passwords_stats['count']} documents")
                
            except Exception as e:
                st.error(f"Error getting performance stats: {str(e)}")

def main():
    st.set_page_config(
        page_title="Admin Panel - Password Manager",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ Administrator Panel")
    st.markdown("---")
    
    # Security check
    if not st.session_state.get('authenticated', False):
        st.error("⛔ Please log in to access this page")
        st.stop()
    
    if st.session_state.get('current_user') != 'admin':
        st.error("⛔ Administrator Previllages Required to Access This Page")
        st.stop()
    
    # Admin navigation
    admin_tabs = st.tabs(["📊 Database Statistics", "👥 User Management", "⚙️ System Settings"])
    
    with admin_tabs[0]:
        show_database_statistics()
    
    with admin_tabs[1]:
        show_user_management()
    
    with admin_tabs[2]:
        st.subheader("⚙️ System Configuration")
        st.info("System settings panel coming soon...")
        
        # Quick actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Clear Cache", use_container_width=True):
                if 'passwords' in st.session_state:
                    del st.session_state.passwords
                st.success("✅ Cache cleared")
        
        with col2:
            if st.button("📋 View System Info", use_container_width=True):
                st.json({
                    "Current User": st.session_state.current_user,
                    "Session Active": st.session_state.authenticated,
                    "Python Version": "3.x",  # You can add actual version check
                    "Streamlit Version": st.__version__,
                    "Database Status": "Connected" if mongo_manager.is_connected() else "Disconnected"
                })
    
    # Quick stats footer
    st.markdown("---")
    stats = get_database_statistics()
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Total Users", stats['total_users'])
        col2.metric("🔑 Total Passwords", stats['total_passwords'])
        col3.metric("💾 Storage", f"{stats['total_storage_kb']:.1f} KB")
        col4.metric("📈 7d Logins", stats['recent_logins'])

if __name__ == "__main__":
    main()
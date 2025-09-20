import streamlit as st
import time
import random
import re
import os
import base64
import pyotp
import qrcode
import io
from datetime import datetime, timedelta
from pathlib import Path
from streamlit_option_menu import option_menu  # pip install streamlit-option-menu
from migrate_passwords import migrate_existing_passwords
from clipboard_manager import clipboard_manager

# Import MongoDB functionality
from crud_operations import (
    register_user, verify_user_credentials, save_password, 
    get_password, get_all_passwords, update_password, delete_password,
    is_valid_service_name, get_user_2fa_secret, update_user_2fa_secret,
    set_user_2fa_enabled, is_2fa_enabled, complete_login  # Add complete_login here
)

# Configuration
MAX_ATTEMPTS = 2
SESSION_TIMEOUT = 600  # 10 minutes in seconds
ITEMS_PER_PAGE = 5  # Number of services to show per page

# Character sets for password generation
chars = {
    'lower': "abcdefghijklmnopqrstuvwxyz",
    'upper': "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    'numbers': "1234567890",
    'symbols': "=-!@#$%^&*"
}

# --- Asset Paths ---
LOGO_PATH = "assets/images/logo.png"
LOGO_PATH1 = "assets/images/logo.png"
BACKGROUND_IMAGE_PATH = "assets/images/password.png"

# Cache management functions
def initialize_passwords():
    """Initialize passwords in session state if not already present"""
    if 'passwords' not in st.session_state:
        st.session_state.passwords = []
    if 'passwords_loaded' not in st.session_state:
        st.session_state.passwords_loaded = False

def refresh_passwords():
    """Force refresh passwords from database"""
    if st.session_state.authenticated and st.session_state.current_user:
        st.session_state.passwords = get_all_passwords()
        st.session_state.passwords_loaded = True

def get_passwords_cached():
    """Get passwords from cache or database if not loaded"""
    initialize_passwords()
    
    if not st.session_state.passwords_loaded or not st.session_state.passwords:
        refresh_passwords()
    
    return st.session_state.passwords

def invalidate_passwords_cache():
    """Mark passwords cache as invalid (to be refreshed on next access)"""
    st.session_state.passwords_loaded = False

# Function to convert image to base64
def img_to_base64(img_path):
    if not Path(img_path).exists():
        st.error(f"Error: Image not found at {img_path}. Please check the path.")
        return None
    try:
        img_bytes = Path(img_path).read_bytes()
        encoded = base64.b64encode(img_bytes).decode()
        return encoded
    except Exception as e:
        st.error(f"Error encoding image {img_path}: {e}")
        return None

# Function to generate QR code
def generate_qr_code(uri):
    """Generate QR code from URI"""
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

# Custom CSS for styling
def inject_custom_css():
    # Load background image
    bg_b64 = img_to_base64(BACKGROUND_IMAGE_PATH)
    bg_image_style = f"url('data:image/jpeg;base64,{bg_b64}')" if bg_b64 else "linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)"
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Montserrat:wght@400;600;700&display=swap');

    /* General App Styling */
    .stApp {{
        background-image: {bg_image_style};
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        font-family: 'Montserrat', sans-serif;
        color: #E0E0E0;
    }}
    
    .verification-input {{
        text-align: center;
        font-size: 1.5rem;
        letter-spacing: 0.5rem;
    }}

    /* Overlay for better readability over background */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(10, 10, 20, 0.85);
        z-index: -1;
    }}

    /* Global text color for better consistency */
    h1, h2, h3, h4, h5, h6, label, p, .stMarkdown, .stText, .stTextInput, .stButton, .stCheckbox {{
        color: #E0E0E0 !important;
        font-family: 'Montserrat', sans-serif;
    }}

    /* Animated Border Glow */
    .login-container::before {{
        content: '';
        position: absolute;
        top: -5px; bottom: -5px;
        left: -5px; right: -5px;
        background: linear-gradient(45deg, #00BFFF, #8A2BE2, #00BFFF);
        background-size: 400% 400%;
        border-radius: 18px;
        z-index: -1;
        animation: glow 10s ease infinite;
        opacity: 0.6;
        filter: blur(8px);
    }}
    
    @keyframes glow {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    /* Header styling with Orbitron font */
    .login-header {{
    text-align: center;
    margin-bottom: 0;
    }}
    .login-header h1 {{
        font-family: 'Orbitron', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #00BFFF;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 10px rgba(0, 191, 255, 0.7);
    }}
    .login-header p {{
        font-family: 'Montserrat', sans-serif;
        font-size: 1.1rem;
        color: #90A4AE;
    }}
    
    /* App Logo */
    .app-logo {{
        display: block;
        margin: 0 auto 1rem;
        width: 140px;
        height: auto;
        filter: drop-shadow(0 0 8px rgba(0, 191, 255, 0.8));
    }}
    .app-logo-fallback {{
        font-family: 'Orbitron', sans-serif;
        font-size: 3rem;
        color: #00BFFF;
        text-align: center;
        margin-bottom: 1rem;
    }}

    /* Input field styling */
    .stTextInput > label {{
        font-size: 1rem;
        font-weight: 600;
        color: #E0E0E0;
        margin-bottom: 0.5rem;
    }}
    .stTextInput > div > div > input {{
        background-color: #1A1A2E;
        color: #E0E0E0;
        border: 2px solid #0F3460;
        border-radius: 8px;
        padding: 14px;
        font-size: 16px;
        transition: all 0.3s ease;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #00BFFF;
        box-shadow: 0 0 0 3px rgba(0, 191, 255, 0.4);
        outline: none;
    }}
    .stTextInput > div > div > input[disabled] {{
        background-color: #0F1626;
        cursor: not-allowed;
        opacity: 0.7;
    }}

    /* Button styling */
    .stButton > button {{
        background: linear-gradient(90deg, #00BFFF 0%, #8A2BE2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 14px 28px;
        font-weight: 700;
        font-size: 16px;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1.5rem;
        letter-spacing: 1px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.4);
    }}
    .stButton > button:hover {{
        background: linear-gradient(90deg, #8A2BE2 0%, #00BFFF 100%);
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
    }}
    .stButton > button:disabled {{
        background: #3A4750;
        cursor: not-allowed;
        opacity: 0.6;
        transform: none;
        box-shadow: none;
    }}
    
    /* Navigation link button (Register/Login) */
    .register-link-btn > button {{
        background: none !important;
        color: #00BFFF !important;
        border: 1px solid #00BFFF !important;
        margin-top: 1rem;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 600;
        box-shadow: none;
    }}
    .register-link-btn > button:hover {{
        background: rgba(0, 191, 255, 0.1) !important;
        color: #E0E0E0 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 191, 255, 0.2);
    }}
    .register-link-btn > button:disabled {{
        border-color: #3A4750 !important;
        color: #90A4AE !important;
        background: none !important;
    }}

    /* Messages (success, error, warning) */
    .stSuccess > div {{
        background-color: #28a74530;
        color: #28a745;
        border-left: 5px solid #28a745;
        border-radius: 8px;
        padding: 10px;
    }}
    .stError > div {{
        background-color: #dc354530;
        color: #dc3545;
        border-left: 5px solid #dc3545;
        border-radius: 8px;
        padding: 10px;
    }}
    .stWarning > div {{
        background-color: #ffc10730;
        color: #ffc107;
        border-left: 5px solid #ffc107;
        border-radius: 8px;
        padding: 10px;
    }}

    /* Custom locked screen styling */
    .locked-overlay {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.95);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        backdrop-filter: blur(5px);
    }}
    .locked-card {{
        background: rgba(23, 27, 42, 0.98);
        border: 2px solid #FF4500;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 0 30px rgba(255, 69, 0, 0.7);
        max-width: 550px;
    }}
    .locked-card h4 {{
        color: #FF4500;
        font-size: 28px;
        font-family: 'Orbitron', sans-serif;
        margin-bottom: 20px;
    }}
    .locked-card p {{
        color: #E0E0E0;
        font-size: 18px;
        margin-bottom: 30px;
    }}
    .locked-card .timer {{
        font-family: 'Orbitron', monospace;
        font-size: 60px;
        color: #00BFFF;
        background: #1A1A2E;
        padding: 15px 30px;
        border-radius: 10px;
        border: 1px solid #0F3460;
        margin: 20px auto;
        display: inline-block;
        text-shadow: 0 0 15px rgba(0, 191, 255, 0.5);
    }}

    /* Main app content styling */
    .main {{
        padding: 2rem;
    }}
    .st-emotion-cache-z5fcl4 {{
        width: 100% !important;
    }}
    
    /* Service card styling */
    .service-card {{
        background-color: #1A1A2E;
        border: 2px solid #0F3460;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}
    .service-card:hover {{
        border-color: #00BFFF;
        box-shadow: 0 0 15px rgba(0, 191, 255, 0.3);
        transform: translateY(-2px);
    }}
    .service-card h3 {{
        color: #00BFFF !important;
        margin-bottom: 0.5rem;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.4rem;
    }}
    .service-card p {{
        margin-bottom: 0.3rem;
        font-size: 1rem;
    }}
    .service-card .timestamp {{
        color: #90A4AE;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }}
    
    /* Pagination styling */
    .pagination-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 1.5rem;
        gap: 1rem;
    }}
    .pagination-btn {{
        background: linear-gradient(90deg, #00BFFF 0%, #8A2BE2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    .pagination-btn:disabled {{
        background: #3A4750;
        cursor: not-allowed;
        opacity: 0.6;
    }}
    .pagination-btn:not(:disabled):hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }}
    .page-info {{
        font-weight: 600;
        color: #E0E0E0;
    }}

    /* Modern Dashboard Styling */
    .hero-text {{
        text-align: center;
        margin-bottom: 2.5rem;
    }}
    .hero-headline {{
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: #00BFFF;
        margin-bottom: 1rem;
        text-shadow: 0 0 15px rgba(0, 191, 255, 0.7);
        background: linear-gradient(90deg, #00BFFF, #8A2BE2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .hero-subheadline {{
        font-size: 1.3rem;
        color: #90A4AE;
        margin-bottom: 2rem;
    }}

    /* Stats Cards */
    .stats-card {{
        background: rgba(27, 38, 59, 0.7);
        border: 1px solid rgba(0, 191, 255, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
        height: 100%;
    }}
    .stats-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 191, 255, 0.2);
        border-color: rgba(0, 191, 255, 0.6);
    }}
    .stats-card h3 {{
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        color: #00BFFF;
    }}
    .stats-card p {{
        margin: 0;
        font-size: 0.9rem;
        color: #E0E0E0;
    }}

    /* Quick Actions Section */
    .quick-actions {{
        margin-top: 2rem;
    }}
    .section-title {{
        font-family: 'Orbitron', sans-serif;
        font-size: 1.5rem;
        color: #00BFFF;
        margin-bottom: 1rem;
        border-bottom: 2px solid rgba(0, 191, 255, 0.3);
        padding-bottom: 0.5rem;
    }}
    .action-btn {{
        background: linear-gradient(90deg, rgba(0, 191, 255, 0.2), rgba(138, 43, 226, 0.2));
        border: 1px solid rgba(0, 191, 255, 0.3);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        height: 100%;
    }}
    .action-btn:hover {{
        background: linear-gradient(90deg, rgba(0, 191, 255, 0.3), rgba(138, 43, 226, 0.3));
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0, 191, 255, 0.2);
    }}
    .action-btn h4 {{
        color: #00BFFF;
        margin-bottom: 0.5rem;
    }}
    .action-btn p {{
        color: #90A4AE;
        font-size: 0.9rem;
        margin: 0;
    }}

    /* Password Strength Meter */
    .password-meter {{
        background: rgba(27, 38, 59, 0.7);
        border: 1px solid rgba(0, 191, 255, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
    }}
    .meter-title {{
        font-family: 'Orbitron', sans-serif;
        color: #00BFFF;
        margin-bottom: 1rem;
    }}
    .strength-bar {{
        height: 10px;
        background: #1A1A2E;
        border-radius: 5px;
        overflow: hidden;
        margin-bottom: 1rem;
    }}
    .strength-fill {{
        height: 100%;
        background: linear-gradient(90deg, #00BFFF, #8A2BE2);
        border-radius: 5px;
        width: 85%;
    }}
    .strength-text {{
        text-align: center;
        font-weight: 600;
        color: #00BFFF;
    }}

    /* 2FA Specific Styling */
    .verification-input {{
        text-align: center;
        font-size: 1.5rem;
        letter-spacing: 0.5rem;
    }}
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    """Initializes necessary session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    if 'account_locked' not in st.session_state:
        st.session_state.account_locked = False
    if 'lock_time' not in st.session_state:
        st.session_state.lock_time = None
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = time.time()
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_page_num' not in st.session_state:
        st.session_state.current_page_num = 1
    if 'menu_selected' not in st.session_state:
        st.session_state.menu_selected = "Dashboard"
    if 'login_step' not in st.session_state:
        st.session_state.login_step = None
    if 'temp_username' not in st.session_state:
        st.session_state.temp_username = None
    if 'temp_password' not in st.session_state:
        st.session_state.temp_password = None
    if 'registered_users' not in st.session_state:
        st.session_state.registered_users = {"testuser": "testpass"}
    
    # Initialize cache variables
    if 'passwords' not in st.session_state:
        st.session_state.passwords = []
    if 'passwords_loaded' not in st.session_state:
        st.session_state.passwords_loaded = False
    if 'otp_attempts' not in st.session_state:
        st.session_state.otp_attempts = 0
    if 'otp_locked' not in st.session_state:
        st.session_state.otp_locked = False
    if 'otp_lock_time' not in st.session_state:
        st.session_state.otp_lock_time = None

def check_session_timeout():
    if 'last_activity' in st.session_state and st.session_state.authenticated:
        elapsed = time.time() - st.session_state.last_activity
        if elapsed > SESSION_TIMEOUT:
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.current_page = "login"
            st.warning("Session timed out due to inactivity. Please log in again.")
            st.rerun()
            return False
    st.session_state.last_activity = time.time()
    return True


def logout_user():
    # Clear all sensitive session data
    sensitive_keys = ['temp_username', 'temp_password', 'passwords', 'generated_password']
    for key in sensitive_keys:
        if key in st.session_state:
            del st.session_state[key]
    # Then reset authentication state
    st.session_state.authenticated = False
    st.session_state.current_user = None

def generate_password(length=12, use_lower=True, use_upper=True, use_numbers=True, use_symbols=True):
    character_set = ""
    
    if use_lower: character_set += chars['lower']
    if use_upper: character_set += chars['upper']
    if use_numbers: character_set += chars['numbers']
    if use_symbols: character_set += chars['symbols']
    
    if not character_set:
        st.error("Error: At least one character type must be selected")
        return None
    
    # Ensure at least one character from each selected set is included
    password = []
    if use_lower: password.append(random.choice(chars['lower']))
    if use_upper: password.append(random.choice(chars['upper']))
    if use_numbers: password.append(random.choice(chars['numbers']))
    if use_symbols: password.append(random.choice(chars['symbols']))
    
    # Fill the rest with random characters
    remaining_length = length - len(password)
    password.extend(random.choice(character_set) for _ in range(remaining_length))
    
    # Shuffle the password
    random.shuffle(password)
    return ''.join(password)

def save_password_to_db(service, service_username, password):
    """Wrapper function to save password using MongoDB"""
    result = save_password(service, service_username, password)
    if result:
        invalidate_passwords_cache()  # Invalidate cache after saving
    return result

def get_password_data(service):
    """Wrapper function to get password using MongoDB"""
    return get_password(service)

def list_services():
    try:
        passwords = get_passwords_cached()  # Use cached passwords
        
        if passwords:
            st.subheader("Your Saved Services")
            
            # Initialize pagination if not already set
            if 'current_page_num' not in st.session_state:
                st.session_state.current_page_num = 1
                
            # Calculate total pages
            total_pages = max(1, (len(passwords) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            
            # Ensure current page is within valid range
            if st.session_state.current_page_num > total_pages:
                st.session_state.current_page_num = total_pages
                
            # Calculate start and end indices for current page
            start_idx = (st.session_state.current_page_num - 1) * ITEMS_PER_PAGE
            end_idx = min(start_idx + ITEMS_PER_PAGE, len(passwords))
            
            # Display services for current page
            for i in range(start_idx, end_idx):
                password_data = passwords[i]
                st.markdown(f"""
                <div class="service-card">
                    <h3>{password_data['service']}</h3>
                    <p><strong>Username:</strong> {password_data['username']}</p>
                    <p><strong>Password:</strong> ••••••••</p>
                    <p class="timestamp"><strong>Last Updated:</strong> {password_data['timestamp']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add a reveal password button for each service
                with st.expander("Show Password"):
                    st.code(password_data['password'])
                    
            # Display pagination controls
            if total_pages > 1:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏮️ First", disabled=st.session_state.current_page_num == 1, 
                                use_container_width=True, key="first_page"):
                        st.session_state.current_page_num = 1
                        st.rerun()
                
                with col2:
                    if st.button("◀️ Prev", disabled=st.session_state.current_page_num == 1, 
                                use_container_width=True, key="prev_page"):
                        st.session_state.current_page_num -= 1
                        st.rerun()
                
                with col3:
                    st.markdown(f"<div class='page-info'>Page {st.session_state.current_page_num} of {total_pages}</div>", 
                               unsafe_allow_html=True)
                
                with col4:
                    if st.button("Next ▶️", disabled=st.session_state.current_page_num == total_pages, 
                                use_container_width=True, key="next_page"):
                        st.session_state.current_page_num += 1
                        st.rerun()
                
                with col5:
                    if st.button("Last ⏭️", disabled=st.session_state.current_page_num == total_pages, 
                                use_container_width=True, key="last_page"):
                        st.session_state.current_page_num = total_pages
                        st.rerun()
        else:
            st.info("You haven't saved any passwords yet.")
    except Exception as e:
        st.error(f"Error loading services: {str(e)}")

def register_page():
    is_locked = st.session_state.get('account_locked', False)
    logo_html = img_to_base64(LOGO_PATH1)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="login-header">
            {f"<img src='data:image/png;base64,{logo_html}' class='app-logo'>" if logo_html else "<h1 class='app-logo-fallback'>SentinelKey</h1>"}
            <h1>Join SentinelKey</h1>
            <p>Secure your digital life. Start now!</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("register_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Choose a unique username", disabled=is_locked, key="reg_username")
        password = st.text_input("Password", type="password", placeholder="Create a strong password", disabled=is_locked, key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", disabled=is_locked, key="reg_confirm_password")
        
        if st.form_submit_button("Register Account", use_container_width=True, disabled=is_locked):
            if not username or not password or not confirm_password:
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                success = register_user(username, password)
                if success:
                    st.success("Registration successful! Please login.")
                    time.sleep(1)
                    st.session_state.current_page = "login"
                    st.rerun()
                else:
                    st.error("Registration failed. Username may already exist...")
    st.markdown('</div>', unsafe_allow_html=True)

def show_2fa_verification():
    """Show 2FA verification page with rate limiting"""
    
    # Check if OTP is rate limited
    if check_otp_rate_limit():
        remaining_time = int((st.session_state.otp_lock_time - datetime.now()).total_seconds())
        st.error(f"Too many failed OTP attempts! Please try again in {remaining_time} seconds.")
        
        # Show countdown timer
        countdown_placeholder = st.empty()
        for i in range(remaining_time, 0, -1):
            countdown_placeholder.info(f"⏳ Try again in {i} seconds...")
            time.sleep(1)
        countdown_placeholder.empty()
        
        # Reset after countdown
        st.session_state.otp_locked = False
        st.session_state.otp_attempts = 0
        st.session_state.otp_lock_time = None
        st.rerun()
        return
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="login-header">
            <h1>Two-Factor Verification</h1>
            <p>Enter the code from your authenticator app</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Show remaining attempts warning
    remaining_attempts = 3 - st.session_state.otp_attempts
    if remaining_attempts < 3:
        st.warning(f"⚠️ {remaining_attempts} attempt(s) remaining before lockout")
    
    verification_code = st.text_input("6-digit verification code", placeholder="000000", key="2fa_code")
    
    if st.button("Verify", use_container_width=True):
        if verification_code and len(verification_code) == 6:
            username = st.session_state.temp_username
            password = st.session_state.temp_password
            secret = get_user_2fa_secret(username)
            
            if secret:
                totp = pyotp.TOTP(secret)
                if totp.verify(verification_code):
                    # Reset OTP attempts on success
                    st.session_state.otp_attempts = 0
                    
                    # Re-verify credentials before completing login
                    if verify_user_credentials(username, password):
                        complete_login(username)
                    else:
                        st.error("Credentials verification failed during 2FA process.")
                else:
                    # Increment failed attempt counter
                    st.session_state.otp_attempts += 1
                    
                    if st.session_state.otp_attempts >= 3:
                        # Lock OTP verification for 1 minute
                        st.session_state.otp_locked = True
                        st.session_state.otp_lock_time = datetime.now() + timedelta(minutes=1)
                        st.error("Too many failed OTP attempts! Account temporarily locked.")
                        time.sleep(1)
                        # Redirect to account locked page
                        st.switch_page("pages/Account_Locked.py")
                    else:
                        st.error("Invalid verification code. Please try again.")
            else:
                st.error("2FA is not properly configured for your account.")
        else:
            st.error("Please enter a valid 6-digit code.")
    
    if st.button("Back to Login", use_container_width=True):
        # Clear temporary credentials and reset OTP attempts
        st.session_state.temp_username = None
        st.session_state.temp_password = None
        st.session_state.login_step = None
        st.session_state.otp_attempts = 0
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def check_otp_rate_limit():
    """
    Check if OTP verification is rate limited
    Returns True if limited, False otherwise
    """
    if st.session_state.get('otp_locked', False):
        # Check if lock time has expired (1 minute lock)
        if st.session_state.otp_lock_time and datetime.now() < st.session_state.otp_lock_time:
            return True
        else:
            # Lock expired, reset
            st.session_state.otp_locked = False
            st.session_state.otp_attempts = 0
            st.session_state.otp_lock_time = None
            return False
    return False

def login_page():
    is_locked = st.session_state.get('account_locked', False)
    logo_html = img_to_base64(LOGO_PATH)
    
    # If account is locked, redirect to locked page
    if is_locked and st.session_state.lock_time and st.session_state.lock_time > datetime.now():
        st.switch_page("Account_Locked.py")
        return
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="login-header">
            {f"<img src='data:image/png;base64,{logo_html}' class='app-logo'>" if logo_html else "<h1 class='app-logo-fallback'>SentinelKey</h1>"}
            <h1>Welcome Back!</h1>
            <p style="color: green;">Access your secure password vault.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.login_attempts > 0 and not is_locked:
        remaining_attempts = MAX_ATTEMPTS - st.session_state.login_attempts
        st.warning(f"⚠️ Access denied. {remaining_attempts} Attempt(s) Remaining before account lock.")
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Your username", disabled=is_locked, key="login_username_input")
        password = st.text_input("Password", type="password", placeholder="Your password", disabled=is_locked, key="login_password_input")
        
        if st.form_submit_button("Log In", use_container_width=True, disabled=is_locked):
            if not username or not password:
                st.error("Please enter both username and password.")
            elif verify_user_credentials(username, password):
                # Check if 2FA is enabled for this user
                if is_2fa_enabled(username):
                    # Store credentials temporarily for 2FA verification
                    st.session_state.temp_username = username
                    st.session_state.temp_password = password
                    st.session_state.login_step = '2fa_verification'
                    # Redirect to 2FA verification page
                    st.switch_page("pages/2fa_verification.py")
                else:
                    # Proceed with normal login
                    complete_login(username)
            else:
                # Failed login - increment attempt counter
                st.session_state.login_attempts += 1
                # Check if account should be locked
                if st.session_state.login_attempts > MAX_ATTEMPTS:
                    st.session_state.account_locked = True
                    st.session_state.lock_time = datetime.now() + timedelta(minutes=1)
                    st.error(f"Too many failed attempts! Account locked for 1 minute.")
                    time.sleep(1)
                    # Redirect to locked page
                    st.switch_page("pages/Account_Locked.py")
                else:
                    st.error("Invalid username or password.")
    st.markdown('</div>', unsafe_allow_html=True)

def password_generator_section():
    st.header("🔑 Password Generator")
    
    col1, col2 = st.columns(2)
    with col1:
        length = st.slider("Password Length", 8, 64, 16, key="gen_length_slider")
    with col2:
        st.write("Character Types:")
        use_lower = st.checkbox("Lowercase (a-z)", True, key="gen_lower_checkbox")
        use_upper = st.checkbox("Uppercase (A-Z)", True, key="gen_upper_checkbox")
        use_numbers = st.checkbox("Numbers (0-9)", True, key="gen_numbers_checkbox")
        use_symbols = st.checkbox("Symbols (!@#$)", True, key="gen_symbols_checkbox")
    
    if 'generated_password' not in st.session_state:
        st.session_state.generated_password = ''
    
    if st.button("Generate Password", use_container_width=True, key="generate_btn"):
        if not (use_lower or use_upper or use_numbers or use_symbols):
            st.error("Please select at least one character type.")
        else:
            password = generate_password(
                length=length,
                use_lower=use_lower,
                use_upper=use_upper,
                use_numbers=use_numbers,
                use_symbols=use_symbols
            )
            if password:
                st.session_state.generated_password = password
    
    if st.session_state.generated_password:
        st.code(st.session_state.generated_password)
        with st.expander("💾 Save this password", expanded=True):
            service = st.text_input("Service Name (e.g., Google)", key="gen_service")
            service_username = st.text_input("Service Username (e.g., your_email@domain.com)", key="gen_service_username", value=st.session_state.current_user if st.session_state.current_user else "")
            
            if st.button("Save Generated Password", key="save_gen_password", use_container_width=True):
                if not service:
                    st.error("Please enter a service name.")
                elif not service_username:
                    st.error("Please enter a service username.")
                else:
                    if save_password_to_db(service, service_username, st.session_state.generated_password):
                        st.success(f"Password for '{service}' saved successfully!")
                        st.session_state.generated_password = ''
                        st.session_state.gen_service_username = ''
                        st.rerun()
                    else:
                        st.error("Failed to save password. Service name might already exist for this user.")

def save_password_section():
    st.header("💾 Save New Password Manually")
    
    with st.form("save_password_form", clear_on_submit=True):
        service = st.text_input("Service Name (e.g., Facebook)", key="save_service_name_input")
        service_username = st.text_input("Service Username (e.g., your_fb_id)", key="save_service_username_input", value=st.session_state.current_user if st.session_state.current_user else "")
        
        password = st.text_input("Password", type="password", 
                                  value=st.session_state.get('generated_password', ""),
                                  key="save_password_field_input")
        
        if st.form_submit_button("Save Password", use_container_width=True):
            if not service or not service_username or not password:
                st.error("Please fill in all fields.")
            else:
                if save_password_to_db(service, service_username, password):
                    st.success(f"Password for '{service}' saved successfully!")
                    st.session_state.generated_password = ''
                    st.rerun()
                else:
                    st.error("Failed to save password. Service name might already exist for this user.")

def update_password_section():
    st.header("🔄 Update Existing Password")
    
    with st.form("update_password_form", clear_on_submit=True):
        service = st.text_input("Service Name to Update", placeholder="e.g., Google", key="update_service_name_input")
        new_password = st.text_input("New Password", type="password", placeholder="Enter new password", key="update_new_password_input")
        
        if st.form_submit_button("Update Password", use_container_width=True):
            if not service or not new_password:
                st.error("Please enter both the service name and the new password.")
            else:
                if update_password(service, new_password):
                    st.success(f"Password for '{service}' updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update password for '{service}'. Check if the service exists for your account.")

# Modify the retrieve_password_section function
def retrieve_password_section():
    st.header("🔍 Retrieve Stored Password")
    
    # Add clipboard timeout setting
    with st.expander("⚙️ Clipboard Settings", expanded=False):
        clipboard_timeout = st.slider(
            "Auto-clear clipboard after (seconds)",
            min_value=10,
            max_value=120,
            value=30,
            help="Password will be automatically cleared from clipboard after this time"
        )
    
    # Initialize session state for password data
    if 'retrieved_password_data' not in st.session_state:
        st.session_state.retrieved_password_data = None
    if 'retrieved_service' not in st.session_state:
        st.session_state.retrieved_service = None
    
    # Form for service input
    with st.form("retrieve_password_form", clear_on_submit=False):
        service = st.text_input("Enter Service Name", placeholder="e.g., Netflix", key="retrieve_service_name_input")
        
        if st.form_submit_button("Retrieve Password", use_container_width=True):
            if not service:
                st.error("Please enter a service name.")
            else:
                password_data = get_password_data(service)
                if password_data:
                    st.session_state.retrieved_password_data = password_data
                    st.session_state.retrieved_service = service
                    st.success("Credentials found!")
                else:
                    st.error(f"No matching credentials found for '{service}' under your account.")
                    st.session_state.retrieved_password_data = None
                    st.session_state.retrieved_service = None
    
    # Display results and buttons OUTSIDE the form
    if st.session_state.retrieved_password_data:
        password_data = st.session_state.retrieved_password_data
        service = st.session_state.retrieved_service
        
        st.subheader("🔓 Retrieved Credentials")
        
        # Display credentials (masked by default)
        st.json({
            "Service": service,
            "Username": password_data['username'],
            "Password": "••••••••",  # Masked password
            "Last Saved": password_data['timestamp']
        })
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy Password", key="copy_password_btn", use_container_width=True):
                if clipboard_manager.copy_to_clipboard(
                    password_data['password'], 
                    clear_after=clipboard_timeout,
                    key=f"pwd_{service}"
                ):
                    # Show success message
                    st.success(f"✅ Password copied! Will clear in {clipboard_timeout} seconds")
                    
                    # Show countdown timer (optional)
                    countdown_placeholder = st.empty()
                    for i in range(clipboard_timeout, 0, -1):
                        countdown_placeholder.info(f"🕒 Clipboard will clear in {i} seconds...")
                        time.sleep(1)
                    countdown_placeholder.empty()
        
        with col2:
            if st.button("👁️ Reveal Password", key="show_password_btn", use_container_width=True):
                # Toggle password visibility
                if 'show_password' not in st.session_state:
                    st.session_state.show_password = False
                st.session_state.show_password = not st.session_state.show_password
                
                if st.session_state.show_password:
                    st.code(f"Password: {password_data['password']}")
                else:
                    st.info("Password hidden")
        
        with col3:
            if st.button("🧹 Clear Clipboard", key="clear_clipboard_btn", use_container_width=True):
                clipboard_manager.clear_clipboard(f"pwd_{service}")
                st.info("📋 Clipboard cleared!")
        
        # Show actual password if revealed
        if st.session_state.get('show_password', False):
            st.code(f"🔓 Password: {password_data['password']}")
        
        # Additional security info
        st.info("""
        🔒 **Security Tip:** 
        - Clipboard auto-clears after {} seconds
        - Always clear clipboard after use
        - Never leave passwords in clipboard
        """.format(clipboard_timeout))
        
def delete_password_section():
    st.header("🗑️ Delete Stored Password")
    
    with st.form("delete_password_form", clear_on_submit=True):
        service = st.text_input("Enter Service Name to Delete", placeholder="e.g., Old Forum Account", key="delete_service_name_input")
        
        if st.form_submit_button("Delete Password", use_container_width=True):
            if not service:
                st.error("Please enter a service name.")
            else:
                if delete_password(service):
                    st.success(f"Password for '{service}' deleted successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to delete password for '{service}'. Service may not exist for your account.")

def show_2fa_management():
    st.header("🔐 Two-Factor Authentication")
    
    if 'current_user' not in st.session_state:
        st.error("You must be logged in to manage 2FA")
        return
        
    username = st.session_state.current_user
    is_enabled = is_2fa_enabled(username)
    
    if is_enabled:
        st.success("Two-factor authentication is **enabled** for your account.")
        
        if st.button("Disable 2FA", type="secondary"):
            if set_user_2fa_enabled(username, False):
                st.success("Two-factor authentication has been disabled.")
                st.rerun()
            else:
                st.error("Failed to disable 2FA.")
    else:
        st.warning("Two-factor authentication is **not enabled** for your account.")
        
        # Generate new secret if not exists
        secret = get_user_2fa_secret(username)
        if not secret:
            secret = pyotp.random_base32()
            update_user_2fa_secret(username, secret)
        
        # Generate provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name="SentinelKey Password Manager"
        )
        
        # Display QR code
        st.subheader("Setup Instructions")
        st.write("1. Scan the QR code below with your authenticator app (Google Authenticator, Authy, etc.)")
        
        qr_code_base64 = generate_qr_code(provisioning_uri)
        st.image(f"data:image/png;base64,{qr_code_base64}", width=200)
        
        st.write("2. Or enter this secret key manually:")
        st.code(secret)
        
        st.write("3. Verify the setup by entering a code from your authenticator app:")
        
        verification_code = st.text_input("Enter verification code", placeholder="6-digit code")
        
        if st.button("Verify and Enable 2FA"):
            if verification_code:
                if totp.verify(verification_code):
                    if set_user_2fa_enabled(username, True):
                        st.success("Two-factor authentication has been successfully enabled!")
                        st.rerun()
                    else:
                        st.error("Failed to enable 2FA.")
                else:
                    st.error("Invalid verification code. Please try again.")
            else:
                st.error("Please enter a verification code.")

def main_app():
    with st.sidebar:
        st.markdown(f"# 🔒 Welcome, {st.session_state.current_user}")
        st.markdown("---")
        
        # ✅ MODIFIED OPTION_MENU WITH ADMIN CHECK
        # Create base menu options
        menu_options = ["Dashboard", "Generate Password", "Save Password", "Update Password", 
                       "Retrieve Password", "View Services", "Delete Password", "2FA Settings"]
        menu_icons = ["house", "key", "save", "pencil", "search", "list", "trash", "shield"]
        
        # # Add Admin option if user is admin
        # if st.session_state.authenticated and st.session_state.current_user == "admin":
        #     menu_options.append("Admin")
        #     menu_icons.append("gear")
        
        selected = option_menu(
            menu_title="Main Menu",
            options=menu_options,
            icons=menu_icons,
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#1B263B"},
                "icon": {"color": "#E0E1DD", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#415A77"},
                "nav-link-selected": {"background-color": "#778DA9"}
            },
            key="menu_selected_sidebar"
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.generated_password = ''
            st.session_state.current_page_num = 1
            st.rerun()
    
    if not check_session_timeout():
        return
    
    if selected == "Dashboard":
        st.markdown("""
        <div class="hero-text">
            <div class="hero-headline">Stop Password Stress. Start Simple Security.</div>
            <div class="hero-subheadline">Welcome to your password management dashboard</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.success(f"Welcome back, {st.session_state.current_user}! Your digital vault is secure. 🔒")
        
        # Stats cards
        st.markdown("### 📊 Your Security Stats")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class='stats-card'>
                <h3>12</h3>
                <p><strong>Saved Passwords</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='stats-card'>
                <h3>85%</h3>
                <p><strong>Password Strength</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class='stats-card'>
                <h3>30d</h3>
                <p><strong>Last Audit</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick actions
        st.markdown("""
        <style>
        .quick-action-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #1B263B;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.5rem;
            color: #E0E0E0;
            cursor: pointer;
            transition: box-shadow 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        .quick-action-card:hover {
            box-shadow: 0 4px 16px #00BFFF;
            background: #16213E;
        }
        .quick-action-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .quick-action-desc {
            font-size: 1rem;
            color: #90A4AE;
        }
        </style>
        <div class='quick-actions'>
            <div class='section-title'>Quick Actions</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                """
                <div class='quick-action-card' onclick=\"window.location.search='?quick=gen'\">
                    <div class='quick-action-title'>🔑 Generate Password</div>
                    <div class='quick-action-desc'>Create a strong, secure password</div>
                </div>
                """, unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                """
                <div class='quick-action-card' onclick=\"window.location.search='?quick=save'\">
                    <div class='quick-action-title'>💾 Save Password</div>
                    <div class='quick-action-desc'>Store a new credential</div>
                </div>
                """, unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                """
                <div class='quick-action-card' onclick=\"window.location.search='?quick=retrieve'\">
                    <div class='quick-action-title'>� Retrieve Password</div>
                    <div class='quick-action-desc'>Access stored credentials</div>
                </div>
                """, unsafe_allow_html=True
            )

        # Handle quick action navigation
        query_params = st.query_params
        if "quick" in query_params:
            quick_action = query_params["quick"]
            if quick_action == "gen":
                st.session_state.menu_selected = "Generate Password"
                st.experimental_set_query_params()
                st.rerun()
            elif quick_action == "save":
                st.session_state.menu_selected = "Save Password"
                st.experimental_set_query_params()
                st.rerun()
            elif quick_action == "retrieve":
                st.session_state.menu_selected = "Retrieve Password"
                st.experimental_set_query_params()
                st.rerun()
        
        # Password strength meter
        st.markdown("""
        <div class='password-meter'>
            <div class='meter-title'>Your Password Health</div>
            <div class='strength-bar'>
                <div class='strength-fill'></div>
            </div>
            <div class='strength-text'>Strong - 85%</div>
            <p style='text-align: center; color: #90A4AE; margin-top: 1rem;'>
                Keep up the good work! Your passwords are well protected.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recent activity
        st.markdown("""
        <div class='quick-actions'>
            <div class='section-title'>Recent Activity</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: rgba(27, 38, 59, 0.7); border-radius: 12px; padding: 1rem;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                <span>🔒 Facebook password updated</span>
                <span style='color: #90A4AE; font-size: 0.9rem;'>2 hours ago</span>
            </div>
            <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                <span>🔑 Generated new password</span>
                <span style='color: #90A4AE; font-size: 0.9rem;'>Yesterday</span>
            </div>
            <div style='display: flex; justify-content: space-between;'>
                <span>📊 Security audit completed</span>
                <span style='color: #90A4AE; font-size: 0.9rem;'>3 days ago</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    elif selected == "Generate Password":
        password_generator_section()
    elif selected == "Save Password":
        save_password_section()
    elif selected == "Update Password":
        update_password_section()
    elif selected == "Retrieve Password":
        retrieve_password_section()
    elif selected == "View Services":
        st.header("📋 Your Saved Services")
        list_services()
    elif selected == "Delete Password":
        delete_password_section()
    elif selected == "2FA Settings":
        show_2fa_management()

        st.markdown("""
        <div class='quick-actions'>
            <div class='section-title'>Quick Actions</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔑 Generate Password", use_container_width=True, key="quick_gen"):
                st.session_state.menu_selected = "Generate Password"
                st.rerun()

        with col2:
            if st.button("💾 Save Password", use_container_width=True, key="quick_save"):
                st.session_state.menu_selected = "Save Password"
                st.rerun()

        with col3:
            if st.button("🔍 Retrieve Password", use_container_width=True, key="quick_retrieve"):
                st.session_state.menu_selected = "Retrieve Password"
                st.rerun()
    
    # In your main() function, add cleanup
    if st.session_state.get('login_step') == '2fa_verification':
        # If user navigates away from 2FA page, clear temp credentials
        if not st.session_state.get('showing_2fa', False):
            st.session_state.temp_username = None
            st.session_state.temp_password = None
            st.session_state.login_step = None
    
    # Check if account is locked and redirect to locked page
    if st.session_state.get('account_locked', False):
        if st.session_state.lock_time is None:
            st.session_state.account_locked = False
            st.session_state.login_attempts = 0
            st.session_state.lock_time = None
        else:
            remaining_time = st.session_state.lock_time - datetime.now()
            if remaining_time.total_seconds() > 0:
                  # Redirect to locked page instead of showing lock screen
                st.switch_page("pages/Account_Locked.py")
            else:
                # Lock period has ended - reset everything
                st.session_state.account_locked = False
                st.session_state.login_attempts = 0
                st.session_state.lock_time = None
    
    # Only render login/register if not authenticated
    if not st.session_state.authenticated:
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "login"

        # Check if we're in 2FA verification step
        if st.session_state.get('login_step') == '2fa_verification':
            show_2fa_verification()
        else:
            # Show normal login/register page
            if st.session_state.current_page == "login":
                login_page()
                st.markdown('<div class="register-link">', unsafe_allow_html=True)
                if st.button("Don't have an account? Register here", use_container_width=True, key="go_to_register"):
                    st.session_state.current_page = "register"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else: # current_page == "register"
                register_page()
                st.markdown('<div class="register-link">', unsafe_allow_html=True)
                if st.button("Already have an account? Login here", use_container_width=True, key="go_to_login"):
                    st.session_state.current_page = "login"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    # Do not recursively call main_app() to avoid duplicate Streamlit element keys

def main():
    inject_custom_css()

    init_session_state()
    # Only render login/register if not authenticated
    if not st.session_state.authenticated:
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "login"

        # Check if we're in 2FA verification step
        if st.session_state.get('login_step') == '2fa_verification':
            show_2fa_verification()
        else:
            # Show normal login/register page
            if st.session_state.current_page == "login":
                login_page()
                st.markdown('<div class="register-link">', unsafe_allow_html=True)
                if st.button("Don't have an account? Register here", use_container_width=True, key="go_to_register"):
                    st.session_state.current_page = "register"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else: # current_page == "register"
                register_page()
                st.markdown('<div class="register-link">', unsafe_allow_html=True)
                if st.button("Already have an account? Login here", use_container_width=True, key="go_to_login"):
                    st.session_state.current_page = "login"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        main_app()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Password Manager Pro", 
        page_icon="🔒", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
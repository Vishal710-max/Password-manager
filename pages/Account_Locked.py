import streamlit as st
import time
from datetime import datetime
import base64
from pathlib import Path

def inject_locked_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Montserrat:wght@400;600;700&display=swap');
    
    /* Lock screen styling */
    .lock-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: rgba(0, 0, 0, 0.95);
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 10000;
        backdrop-filter: blur(5px);
    }}
    .lock-content {{
        background: rgba(23, 27, 42, 0.98);
        border: 2px solid #FF4500;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 0 30px rgba(255, 69, 0, 0.7);
        max-width: 550px;
        width: 90%;
    }}
    .lock-title {{
        color: #FF4500;
        font-size: 28px;
        font-family: 'Orbitron', sans-serif;
        margin-bottom: 20px;
    }}
    .lock-message {{
        color: #E0E0E0;
        font-size: 18px;
        margin-bottom: 15px;
    }}
    .lock-timer {{
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
    </style>
    """, unsafe_allow_html=True)

def main():
    inject_locked_css()
    
    # Check if we have lock time in session state
    if 'lock_time' not in st.session_state or st.session_state.lock_time is None:
        st.error("Invalid access to locked page. Redirecting to login.")
        time.sleep(2)
        st.switch_page("demo.py")
        return
    remaining_time = st.session_state.lock_time - datetime.now()
    
    # If lock time has expired, redirect back to main app
    if remaining_time.total_seconds() <= 0:
        st.session_state.account_locked = False
        st.session_state.login_attempts = 0
        st.session_state.lock_time = None
        st.switch_page("demo.py")
        return
    
    minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
    
    # Display the lock screen
    st.markdown("""
    <div class="lock-container">
        <div class="lock-content">
            <div class="lock-title">🔒 Account Temporarily Locked</div>
            <div class="lock-message">Too many failed login attempts. Please try again after:</div>
            <div class="lock-timer">{:02d}:{:02d}</div>
            <div class="lock-message">This is a security measure to protect your account.</div>
        </div>
    </div>
    """.format(minutes, seconds), unsafe_allow_html=True)
    
    # Automatically update the page every second
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Account Locked - Password Manager",
        page_icon="🔒",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    main()
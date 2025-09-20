# pages/2fa_verification.py
import streamlit as st
import pyotp
import time
from datetime import datetime, timedelta
from crud_operations import get_user_2fa_secret, verify_user_credentials, complete_login

# Custom CSS for 2FA page
st.markdown("""
<style>
.verification-container {
    max-width: 400px;
    margin: 0 auto;
    padding: 2rem;
    background: rgba(27, 38, 59, 0.8);
    border-radius: 12px;
    border: 1px solid rgba(0, 191, 255, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.verification-header {
    text-align: center;
    margin-bottom: 2rem;
}

.verification-header h1 {
    color: #00BFFF;
    font-family: 'Orbitron', sans-serif;
    margin-bottom: 0.5rem;
}

.verification-input {
    text-align: center;
    font-size: 1.5rem;
    letter-spacing: 0.5rem;
}

.timer-text {
    text-align: center;
    color: #90A4AE;
    font-size: 0.9rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

def check_otp_rate_limit():
    """Check if OTP verification is rate limited"""
    if 'otp_attempts' not in st.session_state:
        st.session_state.otp_attempts = 0
    if 'otp_lock_time' not in st.session_state:
        st.session_state.otp_lock_time = None
    
    if st.session_state.otp_lock_time and datetime.now() < st.session_state.otp_lock_time:
        remaining_time = int((st.session_state.otp_lock_time - datetime.now()).total_seconds())
        st.error(f"Too many failed attempts! Please try again in {remaining_time} seconds.")
        return True
    return False

def verify_2fa_code():
    """Verify the 2FA code entered by the user"""
    if check_otp_rate_limit():
        return False
    
    # Get the 2FA secret for the user
    username = st.session_state.temp_username
    password = st.session_state.temp_password
    secret = get_user_2fa_secret(username)
    
    if not secret:
        st.error("2FA is not properly configured for your account.")
        return False
    
    # Verify the code
    totp = pyotp.TOTP(secret)
    verification_code = st.session_state.get('verification_code', '')
    
    if verification_code and len(verification_code) == 6:
        if totp.verify(verification_code):
            # Reset OTP attempts on success
            st.session_state.otp_attempts = 0
            
            # Re-verify credentials before completing login
            if verify_user_credentials(username, password):
                # COMPLETE LOGIN FUNCTION WILL SET st.session_state.authenticated = True
                # AND st.session_state.current_user = username
                complete_login(username)
                
                # Show success message. Using st.success and then immediately switching
                # might make the message flash briefly or not appear at all
                # A more robust approach would be to set a success message in session state
                # and display it on the target page (demo.py)
                st.success("Verification successful! Redirecting to dashboard...")
                
                # Clear temporary credentials used for 2FA
                st.session_state.temp_username = None
                st.session_state.temp_password = None
                st.session_state.login_step = None
                
                # Switch page immediately. No time.sleep()
                st.switch_page("demo.py")
                return True
            else:
                st.error("Credentials verification failed during 2FA process. Please re-login.")
                # Clear temporary credentials if re-verification fails
                st.session_state.temp_username = None
                st.session_state.temp_password = None
                st.session_state.login_step = None
                st.rerun() # Rerun to go back to initial state or login
                return False
        else:
            # Increment failed attempt counter
            st.session_state.otp_attempts += 1
            
            if st.session_state.otp_attempts >= 3:
                    # Lock OTP verification for 1 minute and redirect to account locked page
                    st.session_state.lock_time = datetime.now() + timedelta(minutes=1)
                    st.session_state.account_locked = True
                    st.switch_page("pages/Account_Locked.py")
                    st.stop() # Stop execution to ensure redirection
            else:
                st.error(f"Invalid verification code. {3 - st.session_state.otp_attempts} attempt(s) remaining.")
                return False
    else:
        st.error("Please enter a valid 6-digit code.")
        return False

def show_2fa_verification_page():
    """Display the 2FA verification page"""
    st.markdown('<div class="verification-container">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="verification-header">
        <h1>Two-Factor Verification</h1>
        <p>Enter the code from your authenticator app</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show remaining attempts warning
    remaining_attempts = 3 - st.session_state.get('otp_attempts', 0)
    if remaining_attempts < 3:
        st.warning(f"⚠️ {remaining_attempts} attempt(s) remaining")
    
    # Verification code input
    verification_code = st.text_input(
        "6-digit verification code", 
        placeholder="000000", 
        key="verification_code",
        max_chars=6,
        help="Enter the 6-digit code from your authenticator app"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Verify", use_container_width=True):
            verify_2fa_code() # This will handle the page switch
    
    with col2:
        if st.button("Back to Login", use_container_width=True):
            # Clear temporary credentials
            st.session_state.temp_username = None
            st.session_state.temp_password = None
            st.session_state.login_step = None
            st.session_state.otp_attempts = 0
            st.switch_page("demo.py") # Go back to the main login page
    
    # Show timer for code validity
    # Ensure this doesn't interfere with the redirection logic
    # If the user clicks 'Verify' while the timer is updating,
    # the verify_2fa_code function should take precedence.
    if 'last_totp_time' not in st.session_state:
        st.session_state.last_totp_time = time.time()
    
    current_time = time.time()
    time_remaining = 30 - (current_time - st.session_state.last_totp_time) % 30
    
    if time_remaining < 5:
        st.warning(f"⏰ Code expires in {int(time_remaining)} seconds!")
    else:
        st.info(f"⏱️ Code valid for {int(time_remaining)} more seconds")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main execution
if 'temp_username' not in st.session_state or 'temp_password' not in st.session_state:
    st.error("No pending verification found. Please login first.")
    if st.button("Go to Login"):
        st.switch_page("demo.py")
else:
    show_2fa_verification_page()
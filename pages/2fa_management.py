import streamlit as st
import pyotp
import qrcode
import io
import base64
from crud_operations import get_user_2fa_secret, update_user_2fa_secret, set_user_2fa_enabled, is_2fa_enabled
from two_factor_auth import verify_2fa_code

def generate_qr_code(uri):
    """Generate QR code from URI"""
    try:
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        st.error(f"Error generating QR code: {e}")
        return None

def show_2fa_management():
    st.title("🔐 Two-Factor Authentication")
    
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
            if not update_user_2fa_secret(username, secret):
                st.error("Failed to generate 2FA secret. Please try again.")
                return
        
        # Validate secret format
        try:
            # Test if secret is valid by creating a TOTP object
            test_totp = pyotp.TOTP(secret)
            test_totp.now()  # This will raise an exception if secret is invalid
        except Exception as e:
            st.error(f"Invalid 2FA secret format. Generating new one...")
            secret = pyotp.random_base32()
            if not update_user_2fa_secret(username, secret):
                st.error("Failed to generate new 2FA secret. Please try again.")
                return
        
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
        if qr_code_base64:
            st.image(f"data:image/png;base64,{qr_code_base64}", width=200)
        else:
            st.error("Failed to generate QR code. Please use manual setup.")
        
        st.write("2. Or enter this secret key manually:")
        st.code(secret)
        
        st.write("3. Verify the setup by entering a code from your authenticator app:")
        
        verification_code = st.text_input(
            "Enter verification code", 
            placeholder="6-digit code",
            max_chars=6,
            help="Enter the 6-digit code from your authenticator app"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify and Enable 2FA", type="primary"):
                if verification_code and len(verification_code.strip()) == 6:
                    # Use the improved verification with time window
                    if verify_2fa_code(secret, verification_code.strip(), window=1):
                        if set_user_2fa_enabled(username, True):
                            st.success("Two-factor authentication has been successfully enabled!")
                            st.rerun()
                        else:
                            st.error("Failed to enable 2FA in database.")
                    else:
                        st.error("Invalid verification code. Please check your authenticator app and try again.")
                else:
                    st.error("Please enter a valid 6-digit verification code.")
        
        with col2:
            if st.button("Generate New Secret", type="secondary"):
                new_secret = pyotp.random_base32()
                if update_user_2fa_secret(username, new_secret):
                    st.success("New secret generated! Please scan the QR code again.")
                    st.rerun()
                else:
                    st.error("Failed to generate new secret.")

        # Debug information (remove in production)
        if st.checkbox("Show debug info"):
            st.write("**Debug Information:**")
            st.write(f"Username: {username}")
            st.write(f"Secret length: {len(secret)}")
            st.write(f"Current TOTP: {totp.now()}")
            st.write(f"2FA enabled in DB: {is_enabled}")

# Run the 2FA management page
if __name__ == "__main__":
    show_2fa_management()
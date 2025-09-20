import pyotp
import qrcode
import base64
from io import BytesIO

def generate_2fa_secret():
    """Generates a new TOTP secret key."""
    return pyotp.random_base32()

def get_provisioning_uri(username, secret, issuer_name="SentinelKey Password Manager"):
    """Generates the provisioning URI for TOTP."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer_name)

def generate_qr_code_base64(provisioning_uri):
    """Generates a QR code from a provisioning URI and returns it as a base64 string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def verify_2fa_code(secret, code, window=1):
    """
    Verifies a 2FA code against the secret with time window tolerance.
    window=1 allows codes from 1 period before and after current time.
    """
    if not secret or not code:
        return False
    
    try:
        totp = pyotp.TOTP(secret)
        # Use valid_window to allow for clock drift - checks current + previous + next time windows
        return totp.verify(code, valid_window=window)
    except Exception as e:
        print(f"2FA verification error: {e}")
        return False

def setup_2fa_for_user(username):
    """
    Generates a new 2FA secret and its corresponding QR code for a user.
    Returns the secret and the base64 encoded QR code image.
    """
    secret = generate_2fa_secret()
    provisioning_uri = get_provisioning_uri(username, secret)
    qr_code_b64 = generate_qr_code_base64(provisioning_uri)
    
    return secret, qr_code_b64
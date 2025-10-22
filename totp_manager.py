import pyotp
import qrcode
import io
import base64
from PIL import Image
from typing import Optional, Dict, Tuple
import secrets
import string

class TOTPManager:
    def __init__(self, issuer_name: str = "Discord Auth Bot"):
        self.issuer_name = issuer_name
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, secret: str, account_name: str) -> io.BytesIO:
        """Generate QR code for authenticator app setup"""
        # Create TOTP URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=self.issuer_name
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            # Allow for some time drift (±1 window = ±30 seconds)
            return totp.verify(token, valid_window=1)
        except:
            return False
    
    def get_current_token(self, secret: str) -> str:
        """Get current TOTP token (for testing/debugging)"""
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def get_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes for emergency access"""
        backup_codes = []
        for _ in range(count):
            # Generate 8-character backup code
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            backup_codes.append(code)
        return backup_codes
    
    def format_secret_for_manual_entry(self, secret: str) -> str:
        """Format secret key for manual entry in authenticator apps"""
        # Add spaces every 4 characters for readability
        formatted = ' '.join([secret[i:i+4] for i in range(0, len(secret), 4)])
        return formatted
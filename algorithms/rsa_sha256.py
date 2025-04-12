from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import re

class RSA2048Signer:
    def __init__(self, selector="rsa-default", domain="example.com"):
        self.selector = selector
        self.domain = domain
        self.private_key = None
        self.public_key = None

    def generate_keys(self):
        """Generate 2048-bit RSA key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        return self.private_key, self.public_key
    
    def sign(self, message: bytes) -> bytes:
        """Sign message using RSA-PSS with SHA-256"""
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature)
    
    def generate_dkim_signature(self, email_headers: dict, body: str) -> str:
        """Generate DKIM signature for email"""
        headers_to_sign = ["From", "To", "Subject", "Date"]
        header_string = "\r\n".join(
            f"{h}: {email_headers[h]}" for h in headers_to_sign if h in email_headers
        )

        body_hash = hashlib.sha256(body.encode()).digest()
        body_hash_b64 = base64.b64encode(body_hash).decode()

        dkim_header = (
            f"v=1; a=rsa-sha256; c=relaxed/relaxed; "
            f"d={self.domain}; s={self.selector}; "
            f"h={' '.join(headers_to_sign)}; "
            f"bh={body_hash_b64}; "
            f"b="
        )

        signature = self.private_key.sign(
            header_string.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode()
        folded_signature = "\r\n ".join(re.findall('.{1,75}', signature_b64))

        return f"{dkim_header}{folded_signature}"
    
    def dkim_record(self) -> str:
        """Generate DKIM DNS TXT record"""
        pub_key_bytes = self.public_key.public_bytes(
            Encoding.PEM,
            PublicFormat.SubjectPublicKeyInfo
        )
        
        pub_key_str = b"".join(pub_key_bytes.split(b"\n")[1:-2]).decode()
        
        return f"{self.selector}._domainkey.{self.domain}", f"v=DKIM1; k=rsa; p={pub_key_str}"

class RSA2048Verifier:
    def __init__(self, dkim_record: str):
        self.public_key = self._extract_public_key(dkim_record)
    
    def _extract_public_key(self, dkim_record: str):
        """Extract and reconstruct public key from DKIM record"""
        clean_record = dkim_record.strip()
        match = re.search(r'p=([A-Za-z0-9+/=]+)', clean_record)
        if not match:
            raise ValueError("Invalid DKIM record - missing public key")
        
        pub_key_b64 = match.group(1)
        
        try:
            der_bytes = base64.b64decode(pub_key_b64)
            
            public_key = serialization.load_der_public_key(
                der_bytes,
                backend=default_backend()
            )
            
            if public_key.key_size != 2048:
                raise ValueError("Key size mismatch - expected 2048 bits")
                
            return public_key
            
        except Exception as e:
            raise ValueError(f"Failed to load public key: {str(e)}")
    
    def verify(self, message: bytes, signature_b64: str) -> bool:
        """Verify RSA signature"""
        try:
            signature = base64.b64decode(signature_b64)
            self.public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
        
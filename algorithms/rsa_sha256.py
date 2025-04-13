from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
import hashlib
import base64
import re

def canonicalize_body(body: str, method: str = "simple") -> str:
    """Canonicalize email body according to DKIM spec"""
    if method == "simple":
        return body.replace("\r\n", "\n").replace("\n", "\r\n")
    elif method == "relaxed":
        lines = body.replace("\r\n", "\n").split("\n")
        canonical_lines = []

        for line in lines:
            line = re.sub(r"[ \t]+", " ", line.strip())
            canonical_lines.append(line)

        while canonical_lines and canonical_lines[-1] == "":
            canonical_lines.pop()

        return "\r\n".join(canonical_lines) + "\r\n"
    
    else:
        raise ValueError(f"Unknown canonicalization method: {method}")

def canonicalize_headers(headers: str, signed_headers: list, method: str = "simple") -> str:
    """Canonicalize email headers according to DKIM spec"""
    header_lines = headers.split("\r\n")
    selected_headers = []
    
    for header_name in signed_headers:
        for line in header_lines:
            if line.lower().startswith(header_name + ":"):
                selected_headers.append(line)
                break
    
    if method == "simple":
        return "\r\n".join(selected_headers)
    
    elif method == "relaxed":
        canonical_lines = []
        for line in selected_headers:
            name, value = line.split(":", 1)
            value = re.sub(r"[ \t]+", " ", value.strip())
            canonical_lines.append(f"{name.lower()}:{value}")
        return "\r\n".join(canonical_lines)
    
    else:
        raise ValueError(f"Unknown canonicalization method: {method}")

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
                salt_length=32
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature)
    
    def generate_dkim_signature(self, email_headers: dict, body: str) -> str:
        """Generate DKIM signature for email"""
        canonical_body = canonicalize_body(body, "relaxed")
        body_hash = hashlib.sha256(canonical_body.encode()).digest()
        body_hash_b64 = base64.b64encode(body_hash).decode()

        headers_to_sign = ["From", "To", "Subject", "Date"]
        header_lines = [f"{h}: {email_headers[h]}" for h in headers_to_sign]
        
        canonical_headers = canonicalize_headers("\r\n".join(header_lines), 
                                            headers_to_sign, 
                                            "relaxed")

        dkim_header = (
            f"v=1; a=rsa-sha256; c=relaxed/relaxed; "
            f"d={self.domain}; s={self.selector}; "
            f"h={' '.join(headers_to_sign)}; "
            f"bh={body_hash_b64}; "
            f"b="
        )

        signature = self.private_key.sign(
            canonical_headers.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode()
        return f"{dkim_header}{signature_b64}"
    
    def dkim_record(self) -> str:
        """Generate DKIM DNS TXT record"""
        pub_key_der = self.public_key.public_bytes(
            Encoding.DER,
            PublicFormat.SubjectPublicKeyInfo
        )
        pub_key_b64 = base64.b64encode(pub_key_der).decode()
        return f"{self.selector}._domainkey.{self.domain}", f"v=DKIM1; k=rsa; p={pub_key_b64}"

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
                    salt_length=32
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
        
    def verify_dkim_signature(self, dkim_signature: str, email_headers: str, email_body: str) -> bool:
        """
        Verify a DKIM signature using RSA-SHA256
        
        Args:
            dkim_signature: The DKIM-Signature header value
            email_headers: Only the From, To, Subject, Date email headers as a string
            email_body: Only the body of the email as a string
        
        Returns:
            bool: True if both body hash (bh) and signature (b) verify, False otherwise
        """
        params = {}
        for param in dkim_signature.split(";"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key.strip()] = value.strip()
        
        if params.get("a", "").lower() != "rsa-sha256":
            raise ValueError("Unsupported algorithm, expected rsa-sha256")
        
        bh = base64.b64decode(params.get("bh", ""))
        b = base64.b64decode(params.get("b", ""))
        
        canonical_body = canonicalize_body(email_body, "relaxed")
        computed_bh = hashlib.sha256(canonical_body.encode()).digest()
        
        if computed_bh != bh:
            print("Body hash verification failed")
            return False

        headers_to_sign = ["From", "To", "Subject", "Date"]
        canonical_headers = canonicalize_headers(email_headers, 
                                            headers_to_sign, 
                                            "relaxed")

        self.public_key.verify(
            b,
            canonical_headers.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        
        return True
            
        
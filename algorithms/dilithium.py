from .dilithium_helpers.mldsa import ML_DSA

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

class DilithiumSigner:
    _ML_DSA_44_PARAMS = {
        "d": 13,
        "tau": 39,
        "gamma_1": 131072,
        "gamma_2": 95232,
        "k": 4,
        "l": 4,
        "eta": 2,
        "omega": 80,
        "c_tilde_bytes": 32,
    }

    _ML_DSA_65_PARAMS = {
        "d": 13,
        "tau": 49,
        "gamma_1": 524288,
        "gamma_2": 261888,
        "k": 6,
        "l": 5,
        "eta": 4,
        "omega": 55,
        "c_tilde_bytes": 48,
    }

    _ML_DSA_87_PARAMS = {
        "d": 13,
        "tau": 60,
        "gamma_1": 524288,
        "gamma_2": 261888,
        "k": 8,
        "l": 7,
        "eta": 2,
        "omega": 75,
        "c_tilde_bytes": 64,
    }

    def __init__(self, security_level: str, selector="default", domain="example.com") -> None:
        if security_level == "44":
            self.params = self._ML_DSA_44_PARAMS
        elif security_level == "65":
            self.params = self._ML_DSA_65_PARAMS
        elif security_level == "87":
            self.params = self._ML_DSA_87_PARAMS
        else:
            raise ValueError("Invalid security level. Choose '44', '65', or '87'.")

        self.dilithium_model: ML_DSA = ML_DSA(self.params)

        self.selector = selector
        self.domain = domain
        self.private_key = None
        self.public_key = None

    def generate_keys(self) -> tuple:
        """Generate Dilithium key pair"""
        self.public_key, self.private_key = self.dilithium_model.keygen()
        return self.private_key, self.public_key
    
    def sign(self, message: bytes) -> bytes:
        """Sign message using dilithium"""
        signature = self.dilithium_model.sign(self.private_key, message)
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
            f"v=1; a=dilithium; c=relaxed/relaxed; "
            f"d={self.domain}; s={self.selector}; "
            f"h={' '.join(headers_to_sign)}; "
            f"bh={body_hash_b64}; "
            f"b="
        )

        signature = self.dilithium_model.sign(self.private_key, canonical_headers.encode())
        signature_b64 = base64.b64encode(signature).decode()
        return f"{dkim_header}{signature_b64}"
    
    def dkim_record(self) -> str:
        """Generate DKIM DNS TXT record"""

        pub_key_b64 = base64.b64encode(self.public_key).decode()
        return f"{self.selector}._domainkey.{self.domain}", f"v=DKIM1; k=dilithium; p={pub_key_b64}"

class DilithiumVerifier:
    _ML_DSA_44_PARAMS = {
        "d": 13,
        "tau": 39,
        "gamma_1": 131072,
        "gamma_2": 95232,
        "k": 4,
        "l": 4,
        "eta": 2,
        "omega": 80,
        "c_tilde_bytes": 32,
    }

    _ML_DSA_65_PARAMS = {
        "d": 13,
        "tau": 49,
        "gamma_1": 524288,
        "gamma_2": 261888,
        "k": 6,
        "l": 5,
        "eta": 4,
        "omega": 55,
        "c_tilde_bytes": 48,
    }

    _ML_DSA_87_PARAMS = {
        "d": 13,
        "tau": 60,
        "gamma_1": 524288,
        "gamma_2": 261888,
        "k": 8,
        "l": 7,
        "eta": 2,
        "omega": 75,
        "c_tilde_bytes": 64,
    }

    def __init__(self, security_level: str, dkim_record: str):
        if security_level == "44":
            self.params = self._ML_DSA_44_PARAMS
        elif security_level == "65":
            self.params = self._ML_DSA_65_PARAMS
        elif security_level == "87":
            self.params = self._ML_DSA_87_PARAMS
        else:
            raise ValueError("Invalid security level. Choose '44', '65', or '87'.")

        self.dilithium_model: ML_DSA = ML_DSA(self.params)        
        self.public_key = self._extract_public_key(dkim_record)

    def _extract_public_key(self, dkim_record: str) -> bytes:
        clean_record = dkim_record.strip()
        match = re.search(r'p=([A-Za-z0-9+/=]+)', clean_record)
        if not match:
            raise ValueError("Invalid DKIM record - missing public key")
        
        pub_key_b64 = match.group(1)
        public_key = base64.b64decode(pub_key_b64)

        return public_key

    def verify(self, message: bytes, signature_b64: str) -> bool: 
        try:
            signature = base64.b64decode(signature_b64)

            verification_result = self.dilithium_model.verify(self.public_key, message, signature)
            return verification_result
        
        except Exception:
            return False    
        
    def verify_dkim_signature(self, dkim_signature: str, email_headers: str, email_body: str) -> bool:
        """
        Verify a DKIM signature using Dilithium
        
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

        if params.get("a", "").lower() != "dilithium":
            raise ValueError("Unsupported algorithm, expected dilithium")
        
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
        
        verification_result = self.dilithium_model.verify(self.public_key, canonical_headers.encode(), b)
        return verification_result
    

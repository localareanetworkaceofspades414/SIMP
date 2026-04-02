from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
import hashlib
import json

class SimpCrypto:
    """Cryptographic utilities for SIMP"""

    @staticmethod
    def generate_keypair():
        """Generate a new Ed25519 keypair"""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def private_key_to_pem(private_key) -> bytes:
        """Convert private key to PEM format"""
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    @staticmethod
    def public_key_to_pem(public_key) -> bytes:
        """Convert public key to PEM format"""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @staticmethod
    def load_private_key(pem_data: bytes):
        """Load private key from PEM"""
        return serialization.load_pem_private_key(pem_data, password=None)

    @staticmethod
    def load_public_key(pem_data: bytes):
        """Load public key from PEM"""
        return serialization.load_pem_public_key(pem_data)

    @staticmethod
    def sign_intent(intent_dict: dict, private_key) -> str:
        """Sign an intent"""
        # Make a copy without signature
        intent_copy = intent_dict.copy()
        intent_copy.pop("signature", None)

        # Hash it
        intent_json = json.dumps(intent_copy, sort_keys=True)
        intent_bytes = intent_json.encode()
        intent_hash = hashlib.sha256(intent_bytes).digest()

        # Sign
        signature = private_key.sign(intent_hash)
        return signature.hex()

    @staticmethod
    def verify_signature(intent_dict: dict, public_key) -> bool:
        """Verify an intent's signature"""
        try:
            intent_copy = intent_dict.copy()
            signature_hex = intent_copy.pop("signature", "")

            intent_json = json.dumps(intent_copy, sort_keys=True)
            intent_bytes = intent_json.encode()
            intent_hash = hashlib.sha256(intent_bytes).digest()

            signature_bytes = bytes.fromhex(signature_hex)
            public_key.verify(signature_bytes, intent_hash)
            return True
        except Exception:
            return False

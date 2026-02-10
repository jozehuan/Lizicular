from __future__ import annotations
import os
from cryptography.fernet import Fernet

# It is recommended to generate a key and set it as an environment variable.
# from cryptography.fernet import Fernet
# key = Fernet.generate_key()
# print(key.decode())
FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable not set.")

fernet = Fernet(FERNET_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypts a string."""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a string."""
    return fernet.decrypt(encrypted_data.encode()).decode()

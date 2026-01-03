"""
Security module for password hashing and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
from jose import JWTError, jwt
from .config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a random salt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string in format: salt$hash
    """
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Hash password with salt
    pwd_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    # Return salt and hash separated by $
    return f"{salt}${pwd_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database (format: salt$hash)
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Split salt and hash
        salt, stored_hash = hashed_password.split('$')
        # Hash the provided password with the stored salt
        pwd_hash = hashlib.sha256((salt + plain_password).encode('utf-8')).hexdigest()
        # Compare hashes
        return pwd_hash == stored_hash
    except (ValueError, AttributeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claims to encode in the token (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

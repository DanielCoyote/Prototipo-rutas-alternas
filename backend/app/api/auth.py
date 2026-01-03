"""
Authentication API endpoints for user registration and login.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
import logging

from ..core.config import supabase, JWT_EXPIRATION_HOURS
from ..core.security import hash_password, verify_password, create_access_token, verify_token

logger = logging.getLogger("backend.auth")

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    email: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None


# Helper function to get current user from JWT token
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency to extract and verify JWT token from Authorization header.
    
    Args:
        authorization: Authorization header with format "Bearer <token>"
        
    Returns:
        Dictionary with user information from token
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1]
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {"user_id": user_id}


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """
    Register a new user with email and password.
    
    Args:
        req: Registration request with email, password, and optional name
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If email already exists or database error
    """
    try:
        # Check if user already exists
        existing_user = supabase.table("users").select("id").eq("email", req.email).execute()
        
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        hashed_pw = hash_password(req.password)
        
        # Insert new user into database
        user_data = {
            "email": req.email,
            "password_hash": hashed_pw,
            "name": req.name
        }
        
        result = supabase.table("users").insert(user_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        user = result.data[0]
        user_id = str(user["id"])
        
        # Create JWT token
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=JWT_EXPIRATION_HOURS)
        )
        
        logger.info(f"User registered successfully: {req.email}")
        
        return AuthResponse(
            token=token,
            user_id=user_id,
            email=user["email"],
            name=user.get("name")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """
    Authenticate user with email and password.
    
    Args:
        req: Login request with email and password
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Fetch user from database
        result = supabase.table("users").select("*").eq("email", req.email).execute()
        
        if not result.data:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = result.data[0]
        
        # Verify password
        if not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_id = str(user["id"])
        
        # Create JWT token
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=JWT_EXPIRATION_HOURS)
        )
        
        logger.info(f"User logged in: {req.email}")
        
        return AuthResponse(
            token=token,
            user_id=user_id,
            email=user["email"],
            name=user.get("name")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: User info from JWT token (injected by dependency)
        
    Returns:
        User information from database
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_id = current_user["user_id"]
        
        # Fetch full user info from database
        result = supabase.table("users").select("id, email, name").eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = result.data[0]
        
        return UserResponse(
            user_id=str(user["id"]),
            email=user["email"],
            name=user.get("name")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")

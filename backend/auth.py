"""
Optional Authentication Middleware
JWT-based authentication for securing API endpoints.

To enable:
1. Set JWT_SECRET_KEY in .env
2. Uncomment @router.post("/auth/login") in main.py
3. Add Depends(verify_token) to protected endpoints

For public/demo deployment, authentication is optional.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel


# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")  # Set in .env for production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer(auto_error=False)  # auto_error=False makes it optional


class TokenData(BaseModel):
    username: Optional[str] = None
    expires: Optional[datetime] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token (e.g., {"username": "user@example.com"})
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token string
    """
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY not configured")
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token from Authorization header.
    
    Usage:
        @app.get("/protected")
        def protected_endpoint(token_data: dict = Depends(verify_token)):
            return {"user": token_data}
    
    Raises:
        HTTPException: If token is invalid or missing
        
    Returns:
        Decoded token data
    """
    # If no JWT secret configured, skip authentication
    if not JWT_SECRET_KEY:
        return {"username": "demo_user", "auth_disabled": True}
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return {"username": username, **payload}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Example: Simple user authentication (for demo purposes)
# In production, use a proper user database with hashed passwords
DEMO_USERS = {
    "demo@example.com": {
        "username": "demo@example.com",
        "password": "demo123",  # In production: use hashed passwords!
        "email": "demo@example.com"
    }
}


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate user credentials.
    
    In production:
    - Store users in database
    - Hash passwords with bcrypt
    - Implement proper user management
    
    Args:
        username: User's username/email
        password: User's password
        
    Returns:
        User object if authenticated, None otherwise
    """
    user = DEMO_USERS.get(username)
    
    if not user:
        return None
    
    # In production: use password_hash.verify(password, user["password_hash"])
    if user["password"] != password:
        return None
    
    return User(**user)


# Example login request model
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRATION_HOURS * 3600


# To enable authentication in main.py:
"""
from backend.auth import verify_token, authenticate_user, create_access_token, LoginRequest, LoginResponse

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(hours=24)
    )
    
    return LoginResponse(access_token=access_token)


# Then protect endpoints:
@app.post("/text", response_model=InfrastructureResponse)
def generate_infrastructure(
    request: TextRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)  # <-- Add this
):
    # endpoint code...
"""

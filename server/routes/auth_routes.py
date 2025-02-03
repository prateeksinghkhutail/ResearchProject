# routes/auth_routes.py
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Cookie  # Add Depends and Cookiefrom fastapi.responses import JSONResponse
import logging
from fastapi.responses import JSONResponse
from sqlalchemy import select
from db import user_table, engine
from auth import create_access_token, get_password_hash, verify_password,SECRET_KEY, ALGORITHM
import jwt
router = APIRouter()
logger = logging.getLogger(__name__)


async def validate_token(token: str = Cookie(None)):
    """Validate JWT token on every request."""
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register")
async def register_user(request: Request, response: Response):
    """
    Register a new user.
    
    Expects JSON body with:
    - name
    - email
    - contact
    - campus
    - password
    - confirmPassword
    """
    try:
        data = await request.json()
        name = data.get("name")
        email = data.get("email")
        contact = data.get("contact")
        campus = data.get("campus")
        password = data.get("password")
        confirm_password = data.get("confirmPassword")
        
        # Validate all required fields
        required_fields = [name, email, contact, campus, password, confirm_password]
        if not all(required_fields):
            raise HTTPException(status_code=400, detail="All fields are required.")
        
        if password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")
            
        if campus not in ["Pilani", "Goa", "Hyderabad"]:
            raise HTTPException(status_code=400, detail="Invalid campus selection.")

        with engine.connect() as connection:
            # Check if email already exists
            existing_user = connection.execute(
                select(user_table).where(user_table.c.email == email)
            ).fetchone()
            if existing_user:
                raise HTTPException(status_code=400, detail="User already exists.")

        hashed_password = get_password_hash(password)
        
        with engine.begin() as connection:
            # Insert new user with all fields
            connection.execute(
                user_table.insert().values(
                    name=name,
                    email=email,
                    contact=contact,
                    campus=campus,
                    hashed_password=hashed_password
                )
            )

        access_token = create_access_token({"sub": email})
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=False,
            path="/",
            samesite="lax"
        )
        return {"token": access_token, "message": "User registered successfully."}
        
    except Exception as e:
        logger.exception("Error during registration for email: %s", data.get("email", ""))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login_user(request: Request, response: Response):
    """
    Log in an existing user.
    
    Expects JSON body with:
    - email
    - password
    """
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        logger.info("Attempting login for email: %s", email)
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required.")
        
        with engine.connect() as connection:
            user = connection.execute(
                select(user_table).where(user_table.c.email == email)
            ).mappings().fetchone()
            
            if not user:
                logger.info("User not found for email: %s", email)
                raise HTTPException(status_code=400, detail="Invalid email or password.")
            
            hashed_password = user["hashed_password"]
            if not verify_password(password, hashed_password):
                logger.info("Password verification failed for email: %s", email)
                raise HTTPException(status_code=400, detail="Invalid email or password.")
        
        # Create a JWT access token
        access_token = create_access_token({"sub": email})
        
        # Set the token as an HttpOnly cookie with explicit parameters
        response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=False,
        path="/",
        samesite="lax"
        )
        
        logger.info("Login successful for email: %s", email)
        return {"token": access_token, "message": "Login successful."}
    except HTTPException as he:
        logger.error("HTTPException during login: %s", he.detail)
        raise he
    except Exception as e:
        logger.exception("Unhandled error during login for email: %s", email)
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/validate-token")
async def validate_token(payload: dict = Depends(validate_token)):
    """Endpoint to check token validity."""
    return {"valid": True}

@router.post("/logout")
async def logout_user(response: Response):
    """Clear the JWT cookie."""
    response.delete_cookie(key="token")
    return {"message": "Logged out"}
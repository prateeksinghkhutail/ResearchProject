from fastapi import FastAPI, UploadFile, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, and_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import sessionmaker
from fastapi.encoders import jsonable_encoder
import pandas as pd
import io
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI instance
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://172.17.48.18:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection (update with your MySQL credentials)
DATABASE_URL = "mysql+pymysql://root:userpassword@localhost:3306/rp"  # Update with your DB details
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define the MASTER_TABLE
master_table = Table(
    "MASTER_TABLE",
    metadata,
    Column("app_no", String(20), primary_key=True),
    Column("name", String(20), nullable=False),
)

# Define the ITERATION_OFFER table with a composite primary key (app_no, itr_no)
iteration_offer_table = Table(
    "ITERATION_OFFER",
    metadata,
    Column("app_no", String(20), primary_key=True, nullable=False),
    Column("itr_no", Integer, primary_key=True, nullable=False),
    Column("offer", String(20), nullable=False),
    Column("scholarship", Integer),
    Column("uploaded_by", String(20), nullable=False),
    Column("upload_datetime", DateTime),
    Column("status", String(20)),  # Initially, status can be null (or "nill")
)

# Define the FEES_PAID table
fees_paid_table = Table(
    "FEES_PAID",
    metadata,
    Column("app_no", String(20), primary_key=True),
    Column("admission_fees_amount", Integer),
    Column("admission_fees_status", Integer),
    Column("admission_fees_paid_date", DateTime, nullable=False),
    Column("admission_fees_uploaded_by", String(20), nullable=False),
    Column("admission_fees_upload_date_time", DateTime),
    Column("tution_fees_amount", Integer),
    Column("tution_fees_status", Integer),
    Column("tution_fees_paid_date", DateTime, nullable=False),
    Column("tution_fees_uploaded_by", String(20), nullable=False),
    Column("tution_fees_upload_date_time", DateTime),
)

# Define the ITERATION_DATE table
iteration_date_table = Table(
    "ITERATION_DATE",
    metadata,
    Column("iteration", Integer, primary_key=True),
    Column("date", DateTime, nullable=False),
)

# Define the WITHDRAWS table
withdraws_table = Table(
    "WITHDRAWS",
    metadata,
    Column("app_no", String(20), primary_key=True),
    Column("date", DateTime, nullable=False),
    Column("uploaded_by", String(20), nullable=False),
    Column("upload_date_time", DateTime),
)

# Define the LOGS_T table
logs_table = Table(
    "LOGS_T",
    metadata,
    Column("upload_date", DateTime, nullable=False),
    Column("uploaded_by", String(20), nullable=False),
    Column("category", String(20), nullable=False),
    Column("remark", String(20), nullable=False),
    Column("ip_addr", String(50), nullable=False),
)

# Define the USERS table for login/registration
user_table = Table(
    "USERS",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("hashed_password", String(255), nullable=False),
)

# Create tables if they don't exist
metadata.create_all(engine)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Security: Password hashing configuration using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = "your_secret_key_here"  # Replace with your secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # Token valid for 24 hours

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    """Verifies a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generates a hash for the given password."""
    return pwd_context.hash(password)

@app.get("/")
async def root():
    """Root endpoint to indicate the API is working."""
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/data/{table_name}")
async def read_data(table_name: str):
    """Fetch all data from the specified database table."""
    try:
        table = metadata.tables.get(table_name)
        if table is None:
            raise HTTPException(status_code=400, detail=f"Table {table_name} does not exist.")
        
        with engine.connect() as connection:
            result = connection.execute(table.select())
            data = [jsonable_encoder(dict(row._mapping)) for row in result]
        return JSONResponse(content={"data": data}, status_code=200)
    except Exception as e:
        logger.exception("Error reading data from table %s", table_name)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update/{table_name}")
async def update_data(table_name: str, file: UploadFile):
    """
    Update the specified database table with data from a CSV file.
    
    Flow Details:
    1. MASTER_TABLE: Insert/update student records.
    2. ITERATION_OFFER: Insert/update offer details for a given iteration.
       - After processing, update the ITERATION_DATE table with the current system datetime
         and iteration number (itr_no) from the CSV.
    3. FEES_PAID: Insert/update fee payment details.
       - After processing, determine the latest iteration from ITERATION_DATE,
         then for each fee record, update the corresponding record in ITERATION_OFFER (using app_no and latest iteration)
         with a status calculated as:
            - "accept"   : admission_fees_status AND tution_fees_status are true.
            - "upgrade"  : admission_fees_status is true but tution_fees_status is false.
            - "withdrawls": neither fee is paid.
    4. For WITHDRAWS and LOGS_T, no additional logic is applied.
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        table = metadata.tables.get(table_name)
        if table is None:
            raise HTTPException(status_code=400, detail=f"Table {table_name} does not exist.")
        table_columns = set(table.columns.keys())
        if not table_columns.issubset(set(df.columns)):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {table_columns}")

        with engine.begin() as connection:
            for _, row in df.iterrows():
                primary_keys = [col.name for col in table.primary_key]
                stmt = insert(table).values(row.to_dict())
                stmt = stmt.on_duplicate_key_update(
                    {key: row[key] for key in row.keys() if key not in primary_keys}
                )
                connection.execute(stmt)
            
            upper_table = table_name.upper()
            if upper_table == "ITERATION_OFFER":
                if not df.empty:
                    iteration_value = df.iloc[0]["itr_no"]
                    current_time = datetime.now()
                    stmt = insert(iteration_date_table).values(iteration=iteration_value, date=current_time)
                    stmt = stmt.on_duplicate_key_update(date=current_time)
                    connection.execute(stmt)
            elif upper_table == "FEES_PAID":
                result = connection.execute(
                    iteration_date_table.select().order_by(iteration_date_table.c.date.desc()).limit(1)
                )
                latest_iteration_record = result.fetchone()
                if latest_iteration_record is not None:
                    latest_iteration = latest_iteration_record["iteration"]
                    for _, row in df.iterrows():
                        app_no = row["app_no"]
                        admission_paid = bool(row["admission_fees_status"])
                        tuition_paid = bool(row["tution_fees_status"])
                        if admission_paid and tuition_paid:
                            new_status = "accept"
                        elif admission_paid and not tuition_paid:
                            new_status = "upgrade"
                        elif not admission_paid and not tuition_paid:
                            new_status = "withdrawls"
                        else:
                            new_status = "withdrawls"
                        update_stmt = iteration_offer_table.update().where(
                            and_(
                                iteration_offer_table.c.app_no == app_no,
                                iteration_offer_table.c.itr_no == latest_iteration
                            )
                        ).values(status=new_status)
                        connection.execute(update_stmt)
            
        return JSONResponse(content={"message": f"Data updated successfully in {table_name}!"}, status_code=200)
    except Exception as e:
        logger.exception("Error updating data for table %s", table_name)
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------
# New Endpoints for Login and Register
# -------------------------------

@app.post("/api/register")
async def register_user(request: Request, response: Response):
    """
    Register a new user.
    
    Expects JSON body with:
    - email
    - password
    - confirmPassword
    """
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        confirm_password = data.get("confirmPassword")
        
        if not email or not password or not confirm_password:
            raise HTTPException(status_code=400, detail="Email and password required.")
        
        if password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")
        
        # Check if user already exists
        with engine.connect() as connection:
            existing_user = connection.execute(
                user_table.select().where(user_table.c.email == email)
            ).fetchone()
            if existing_user:
                raise HTTPException(status_code=400, detail="User already exists.")
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Insert new user into the USERS table
        with engine.begin() as connection:
            connection.execute(
                user_table.insert().values(email=email, hashed_password=hashed_password)
            )
        
        # Create a JWT access token
        access_token = create_access_token({"sub": email})
        
        # Set the token as an HttpOnly cookie in the response
        response.set_cookie(key="token", value=access_token, httponly=True)
        
        return JSONResponse(
            content={"token": access_token, "message": "User registered successfully."},
            status_code=200
        )
    except Exception as e:
        logger.exception("Error during registration for email: %s", data.get("email", ""))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/login")
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
                user_table.select().where(user_table.c.email == email)
            ).fetchone()
            
            if not user:
                logger.info("User not found for email: %s", email)
                raise HTTPException(status_code=400, detail="Invalid email or password.")
            
            hashed_password = user["hashed_password"]
            if not verify_password(password, hashed_password):
                logger.info("Password verification failed for email: %s", email)
                raise HTTPException(status_code=400, detail="Invalid email or password.")
        
        # Create a JWT access token
        access_token = create_access_token({"sub": email})
        
        # Set the token as an HttpOnly cookie in the response
        response.set_cookie(key="token", value=access_token, httponly=True)
        
        logger.info("Login successful for email: %s", email)
        return JSONResponse(
            content={"token": access_token, "message": "Login successful."},
            status_code=200
        )
    except HTTPException as he:
        logger.error("HTTPException during login: %s", he.detail)
        raise he
    except Exception as e:
        logger.exception("Unhandled error during login for email: %s", email)
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

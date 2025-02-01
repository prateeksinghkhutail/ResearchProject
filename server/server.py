from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, and_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import sessionmaker
from fastapi.encoders import jsonable_encoder
import pandas as pd
import io
from datetime import datetime

# FastAPI instance
app = FastAPI()

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

# Create tables if they don't exist
metadata.create_all(engine)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
            # Use jsonable_encoder to serialize datetime objects
            data = [jsonable_encoder(dict(row._mapping)) for row in result]
        return JSONResponse(content={"data": data}, status_code=200)
    except Exception as e:
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
        # Read the uploaded file into a DataFrame
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Check if the table exists
        table = metadata.tables.get(table_name)
        if table is None:
            raise HTTPException(status_code=400, detail=f"Table {table_name} does not exist.")
        
        # Validate if DataFrame columns match the table columns (CSV column names must match exactly)
        table_columns = set(table.columns.keys())
        if not table_columns.issubset(set(df.columns)):
            raise HTTPException(
                status_code=400, detail=f"CSV must contain columns: {table_columns}"
            )

        # Begin a transaction
        with engine.begin() as connection:
            # Process each row in the CSV file for insert/upsert
            for _, row in df.iterrows():
                # Exclude primary key columns from being updated on duplicate key.
                primary_keys = [col.name for col in table.primary_key]
                stmt = insert(table).values(row.to_dict())
                stmt = stmt.on_duplicate_key_update(
                    {key: row[key] for key in row.keys() if key not in primary_keys}
                )
                connection.execute(stmt)
            
            # Additional logic based on the table being updated
            upper_table = table_name.upper()
            
            # If updating ITERATION_OFFER, update the ITERATION_DATE table with the current upload datetime.
            if upper_table == "ITERATION_OFFER":
                if not df.empty:
                    # Assumption: all rows in the iteration offer CSV have the same iteration number (itr_no)
                    iteration_value = df.iloc[0]["itr_no"]
                    current_time = datetime.now()
                    stmt = insert(iteration_date_table).values(iteration=iteration_value, date=current_time)
                    stmt = stmt.on_duplicate_key_update(date=current_time)
                    connection.execute(stmt)
            
            # If updating FEES_PAID, update the corresponding ITERATION_OFFER records with fee status.
            elif upper_table == "FEES_PAID":
                # Determine the latest iteration from ITERATION_DATE table (most recent date)
                result = connection.execute(
                    iteration_date_table.select().order_by(iteration_date_table.c.date.desc()).limit(1)
                )
                latest_iteration_record = result.fetchone()
                if latest_iteration_record is not None:
                    latest_iteration = latest_iteration_record["iteration"]
                    # For each record in the FEES_PAID CSV, update the matching ITERATION_OFFER record.
                    for _, row in df.iterrows():
                        app_no = row["app_no"]
                        # Calculate fee payment status.
                        admission_paid = bool(row["admission_fees_status"])
                        tuition_paid = bool(row["tution_fees_status"])
                        if admission_paid and tuition_paid:
                            new_status = "accept"
                        elif admission_paid and not tuition_paid:
                            new_status = "upgrade"
                        elif not admission_paid and not tuition_paid:
                            new_status = "withdrawls"
                        else:
                            # If tuition fee is paid but admission fee is not, default to "withdrawls"
                            new_status = "withdrawls"
                        
                        # Update the ITERATION_OFFER record matching the application number and latest iteration.
                        update_stmt = iteration_offer_table.update().where(
                            and_(
                                iteration_offer_table.c.app_no == app_no,
                                iteration_offer_table.c.itr_no == latest_iteration
                            )
                        ).values(status=new_status)
                        connection.execute(update_stmt)
                # If no iteration record exists, the status update is skipped.
            
            # For other tables (MASTER_TABLE, WITHDRAWS, LOGS_T), no additional logic is applied.
            
        return JSONResponse(
            content={"message": f"Data updated successfully in {table_name}!"}, status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

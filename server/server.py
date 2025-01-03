from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import sessionmaker
import pandas as pd
import io

# FastAPI instance
app = FastAPI()

# Database connection (update with your MySQL credentials)
DATABASE_URL = "mysql+pymysql://root:userpassword@localhost:3306/rp"  # Update with your DB details
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define the MySQL table
table_name = "masterTable"
sample_table = Table(
    table_name,
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String(255), nullable=False),
    Column("value", Integer, nullable=False),
)

# Create table if it doesn't exist
metadata.create_all(engine)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.get("/data")
async def read_data():
    """Fetch all data from the database table."""
    try:
        with engine.connect() as connection:
            result = connection.execute(sample_table.select())
            data = [dict(row._mapping) for row in result]  # Use ._mapping
        return JSONResponse(content={"data": data}, status_code=200)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@app.post("/update")
async def update_data(file: UploadFile):
    """Update the database table with data from a CSV file."""
    try:
        # Read the uploaded file into a DataFrame
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # Validate the CSV file
        required_columns = {"id", "name", "value"}
        if not required_columns.issubset(df.columns):
            return HTTPException(
                status_code=400, detail=f"CSV must contain columns: {required_columns}"
            )

        # Insert/Update data in the table
        with engine.begin() as connection:
            for _, row in df.iterrows():
                # Use MySQL-specific insert with ON DUPLICATE KEY UPDATE
                print(f"Inserting/Updating: {row.to_dict()}")

                stmt = insert(sample_table).values(
                    id=row["id"], name=row["name"], value=row["value"]
                )
                stmt = stmt.on_duplicate_key_update(
                    name=row["name"], value=row["value"]
                )
                connection.execute(stmt)

        return JSONResponse(
            content={"message": "Data updated successfully!"}, status_code=200
        )
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
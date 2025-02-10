# routes/data_routes.py
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import pandas as pd
import io
from datetime import datetime
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import and_
import logging
import numpy as np
from db import (
    master_table,
    iteration_offer_table,
    fees_paid_table,
    iteration_date_table,
    withdraws_table,
    logs_table,
    engine,
    metadata
)

router = APIRouter()
logger = logging.getLogger(__name__)

def clean_nan_values(row: dict):
    """Replaces NaN values with None (so they can be stored as NULL in MySQL)."""
    return {key: (None if pd.isna(value) else value) for key, value in row.items()}

@router.get("/data/{table_name}")
async def read_data(table_name: str):
    try:
        table_obj = metadata.tables.get(table_name)
        if table_obj is None:
            raise HTTPException(status_code=400, detail=f"Table {table_name} does not exist.")
        with engine.connect() as connection:
            result = connection.execute(table_obj.select())
            data = [jsonable_encoder(dict(row._mapping)) for row in result]
            
        return JSONResponse(content={"data": data}, status_code=200)
    except Exception as e:
        logger.exception("Error reading data from table %s", table_name)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update/{table_name}")
async def update_data(table_name: str, file: UploadFile):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        #df.replace({np.nan: None}, inplace=True)
        table_obj = metadata.tables.get(table_name)
        if table_obj is None:
            raise HTTPException(status_code=400, detail=f"Table {table_name} does not exist.")
        table_columns = set(table_obj.columns.keys())
        if not table_columns.issubset(set(df.columns)):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {table_columns}")
        
        with engine.begin() as connection:
            for _, row in df.iterrows():
                row = clean_nan_values(dict(row))
                primary_keys = [col.name for col in table_obj.primary_key]
                stmt = insert(table_obj).values(row)
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
                    latest_iteration = latest_iteration_record[0]
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

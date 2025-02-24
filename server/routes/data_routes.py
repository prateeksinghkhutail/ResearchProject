# routes/data_routes.py
from fastapi import APIRouter, HTTPException, UploadFile ,Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import pandas as pd
import io
import requests
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

                result = connection.execute(
                    iteration_date_table.select().order_by(iteration_date_table.c.date.desc()).limit(1)
                )
                latest_iteration_record = result.fetchone()
                if latest_iteration_record is not None:
                    latest_iteration = latest_iteration_record[0]
    
                    fees_records = connection.execute(
                        fees_paid_table.select()
                        )  .mappings().all()
    
                    for row in fees_records:
                        app_no = row["app_no"]
                        admission_paid = bool(row["admission_fees_status"])
                        tuition_paid = bool(row["tution_fees_status"])

                        new_status = None

                        if admission_paid and tuition_paid:
                            iteration_result = connection.execute(
                                iteration_offer_table.select()
                                .where(iteration_offer_table.c.app_no == app_no)
                                .order_by(iteration_offer_table.c.itr_no.desc())
                                .limit(2)
                                ).mappings().all()  # This ensures you get dictionaries instead of tuples

                            iterations = iteration_result
                            
                            if len(iterations) == 2 and iterations[0]["offer"] != iterations[1]["offer"] and "accept" in iterations[1]["status"]:
                                new_status = "accept & upgraded"
                                #print("AU->  ",app_no , admission_paid, tuition_paid)
                                #print(iteration_result)
                            
                        if new_status!= None:
                            update_stmt = iteration_offer_table.update().where(
                                and_(
                                    iteration_offer_table.c.app_no == app_no,
                                    iteration_offer_table.c.itr_no == latest_iteration
                                )
                            ).values(status=new_status)
                            connection.execute(update_stmt)



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
                            #print(app_no , admission_paid, tuition_paid)
                            iteration_result = connection.execute(
                                iteration_offer_table.select()
                                .where(iteration_offer_table.c.app_no == app_no)
                                .order_by(iteration_offer_table.c.itr_no.desc())
                                .limit(2)
                            ).mappings().all() 
                            iterations = iteration_result   
                            if len(iterations) == 2 and iterations[0]["offer"] != iterations[1]["offer"] and "accept" in iterations[1]["status"]:
                                new_status = "accept & upgraded"
                                #print("AU->  ",app_no , admission_paid, tuition_paid)
                                #print(iteration_result)
                            else:
                                #print(app_no , admission_paid, tuition_paid)
                                new_status = "accept"
                        elif not admission_paid and not tuition_paid:
                            new_status = "withdraw"
                        elif admission_paid and not tuition_paid:
                            latest_offer_result = connection.execute(
                                iteration_offer_table.select()
                                .where(
                                    and_(
                                        iteration_offer_table.c.app_no == app_no,
                                        iteration_offer_table.c.itr_no == latest_iteration
                                    )
                                )
                            ).fetchone()
                            latest_offer = latest_offer_result[2] if latest_offer_result else None
                            
                            if latest_offer == "WL":
                                new_status = "upgrade"
                            else :
                                new_status = "withdraw"
                        else:
                            #print("w "  , app_no , admission_paid, tuition_paid)
                          # both not paid 
                          # waitlist -> both not paid 
                            new_status = "withdraw"
                        
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




@router.post("/update_LOGS_TABLE")
async def update_log_table(request: Request):
    try:
        data = await request.json()  # Get JSON data from request
        user_ip = request.client.host  # Get client IP address
        upload_date = datetime.now()  # Get current timestaRp

        # Extract required fields from request data
        file_name = data.get("file_name")
        category = data.get("category")
        uploaded_by = data.get("uploaded_by")
        remark = data.get("remark")

        # Validate if all required fields are present
        if not all([file_name, category, uploaded_by, remark]):
            raise HTTPException(status_code=400, detail="Missing required fields.")

        # Insert data into LOGS_TABLE
        stmt = insert(logs_table).values(
            file_name=file_name,
            category=category,
            upload_date=upload_date,
            uploaded_by=uploaded_by,
            remark=remark,
            ip_address=user_ip
        )

        with engine.begin() as connection:
            connection.execute(stmt)

        return JSONResponse(content={"message": "Log entry added successfully!"}, status_code=201)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



"""

        print("now updating logtable")
        session = requests.Session()
        user_url = "http://localhost:8000/api/user"
        user_response = session.get(user_url)
        print("now updating logtable")
        if user_response.status_code == 200:
            user_name = user_response.json().get("name", "Unknown User")  # Default to 'Unknown User' if not found
        else:
            user_name = "Unknown User"
            print(f"Error fetching user: {user_response.text}")
        print("now updating logtable")
        url = "http://localhost:8000/update_LOGS_TABLE"  # Replace with your actual API URL
        data = {
                "file_name": file.filename,
                "category": upper_table,
                "uploaded_by": user_name,
                "remark": "Initial upload"
            }
        print("now updating logtable")
        response = requests.post(url, json=data)
        print(response)

"""
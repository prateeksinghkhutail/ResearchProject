from fastapi import APIRouter, HTTPException ,Query
from sqlalchemy import select, func
from db import SessionLocal, master_table, iteration_offer_table, iteration_date_table,fees_paid_table
from datetime import datetime
from fastapi.encoders import jsonable_encoder


router = APIRouter()

@router.get("/stats")
def get_stats():
    """
    Returns statistics including:
      - totalApplications: Total number of applications from MASTER_TABLE.
      - acceptedStudents: Count of offers with status 'accept' from ITERATION_OFFER.
      - latestIterationNumber and latestIterationDate: The latest iteration details from ITERATION_DATE.
        Defaults: 0 for iteration number and today's date if no record exists.
    """
    session = SessionLocal()
    try:
        # Total applications from MASTER_TABLE.
        stmt_total = select(func.count()).select_from(master_table)
        total_applications = session.execute(stmt_total).scalar() or 0

        # Count accepted students from ITERATION_OFFER where status is 'accept'.
        stmt_accepted = (
            select(func.count())
            .select_from(iteration_offer_table)
            .where(iteration_offer_table.c.status == "accept")
        )
        accepted_students = session.execute(stmt_accepted).scalar() or 0

        # Retrieve the latest iteration record (ordered by date descending).
        stmt_latest = (
            select(iteration_date_table)
            .order_by(iteration_date_table.c.date.desc())
            .limit(1)
        )
        latest_record = session.execute(stmt_latest).fetchone()

        if latest_record:
            latest_iteration = latest_record.iteration
            latest_iteration_date = latest_record.date
        else:
            # Defaults: 0 for iteration number and today's date.
            latest_iteration = 0
            latest_iteration_date = datetime.now()

        return {
            "totalApplications": total_applications,
            "acceptedStudents": accepted_students,
            "latestIterationNumber": latest_iteration,
            "latestIterationDate": latest_iteration_date,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()



@router.get("/fees")
def get_fees(query: str):
    """
    Returns the fees record for a given application number provided via the query parameter.
    
    Example:
      GET http://localhost:8000/api/fees?query=APP001
     
    The endpoint queries the FEES_PAID table (with the following schema):
      - app_no (primary key)
      - admission_fees_amount
      - admission_fees_status
      - admission_fees_paid_date
      - admission_fees_uploaded_by
      - admission_fees_upload_date_time
      - tution_fees_amount
      - tution_fees_status
      - tution_fees_paid_date
      - tution_fees_uploaded_by
      - tution_fees_upload_date_time
     
    and returns all these column values.
    """
    session = SessionLocal()
    try:
        stmt = select(fees_paid_table).where(fees_paid_table.c.app_no == query)
        # Use .mappings() to get a dictionary-like result.
        fees_record = session.execute(stmt).mappings().fetchone()
        if not fees_record:
            return {"message": f"No fees record found for application number: {query}"}
        return jsonable_encoder(fees_record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


##############        

def num_there(s):
    return any(i.isdigit() for i in s)



@router.get("/students")
def get_student(query: str):
    """
    Returns the student record along with iteration offer details for a given application number or student name 
    provided via the query parameter.

    Example:
      GET http://localhost:8000/api/students?query=APP001
      GET http://localhost:8000/api/students?query=John%20Doe

    The endpoint queries the master_table and iteration_offer_table:
      - master_table (app_no, name)
      - iteration_offer_table (app_no, itr_no, offer, scholarship, status)
      
    and returns the corresponding student data.
    """
    session = SessionLocal()
    try:
        # Check if query is numeric (for app_no) or string (for name)
        if num_there(query):
            # If query is a number, search by app_no
            stmt = (
                select(
                    master_table.c.app_no,
                    master_table.c.name,
                    iteration_offer_table.c.itr_no,
                    iteration_offer_table.c.offer,
                    iteration_offer_table.c.scholarship,
                    iteration_offer_table.c.status,
                )
                .select_from(master_table)
                .join(iteration_offer_table, master_table.c.app_no == iteration_offer_table.c.app_no)
                .where(master_table.c.app_no.ilike(f"%{query}%"))
            )
        else:
            # Otherwise, search by name
            stmt = (
                select(
                    master_table.c.app_no,
                    master_table.c.name,
                    iteration_offer_table.c.itr_no,
                    iteration_offer_table.c.offer,
                    iteration_offer_table.c.scholarship,
                    iteration_offer_table.c.status,
                )
                .select_from(master_table)
                .join(iteration_offer_table, master_table.c.app_no == iteration_offer_table.c.app_no)
                .where(master_table.c.name.ilike(f"%{query}%"))
            )

        # Fetch all matching records
        student_records = session.execute(stmt).mappings().all()

        if not student_records:
            return {"message": f"No student record found for query: {query}"}

        return jsonable_encoder(student_records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()



@router.get("/iterations")
def get_iteration_details(iteration: int = Query(None, description="Iteration number")):
    """
    Fetches iteration details for a given iteration number.
    
    Returns:
    - Application Number (app_no)
    - Iteration Number (itr_no)
    - Offer (offer)
    - Status (status)
    """
    session = SessionLocal()
    try:
        if iteration is None:
            raise HTTPException(status_code=400, detail="Iteration number is required.")

        # Fetch iteration details from ITERATION_OFFER table
        stmt = select(
            iteration_offer_table.c.app_no,
            iteration_offer_table.c.itr_no,
            iteration_offer_table.c.offer,
            iteration_offer_table.c.status
        ).where(iteration_offer_table.c.itr_no == iteration)

        result = session.execute(stmt).mappings().all()

        if not result:
            return {"message": f"No data found for iteration {iteration}"}

        return jsonable_encoder(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
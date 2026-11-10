from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from auth import get_caller, require_owner_or_admin
from models import EmployeeIn
from services import employee_service

router = APIRouter(tags=["employees"])


@router.post("/employees", status_code=201)
def create_employee(payload: EmployeeIn):
    return employee_service.create(payload.model_dump(mode="json"))


@router.get("/employees")
def list_employees(hiredFrom: date | None = None, hiredTo: date | None = None):
    if hiredFrom or hiredTo:
        return {
            "employees": employee_service.list_by_hire_date(
                hiredFrom.isoformat() if hiredFrom else None,
                hiredTo.isoformat() if hiredTo else None,
            )
        }

    return {"employees": employee_service.list_all()}


@router.get("/employees/{employee_id}")
def get_employee(employee_id: str):
    employee = employee_service.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee


@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: str, caller: dict = Depends(get_caller)):
    employee = employee_service.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    require_owner_or_admin(caller, employee)

    employee_service.delete(employee_id)
    return {"deleted": employee_id}
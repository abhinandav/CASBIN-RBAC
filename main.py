from fastapi import FastAPI, Depends, HTTPException, Request
import casbin
from casbin_sqlalchemy_adapter import Adapter
from sqlalchemy.orm import Session
from database import *
from schema import *
from middleware import *
from sqlalchemy import delete

app = FastAPI()

def initialize_enforcer():
    try:
        adapter = Adapter('postgresql://postgres:1234@localhost/casbin')
        enforcer = casbin.Enforcer("data.conf",adapter)
        return enforcer
    except Exception as ex:
        print(f"Error initializing Casbin Enforcer: {ex}")
        raise


enforcer = initialize_enforcer()
app.add_middleware(AuthorizationMiddleware, enforcer=enforcer)


@app.get('/')
async def hello():
    return {'message': "hello"}



@app.post('/add_policy')
async def add_policy(sub: str, obj: str, act: str, field: str):
    enforcer.add_policy(sub, obj, act, field)

    permissions = enforcer.get_permissions_for_user(sub)

    return {
        "message": f"Policy ({sub}, {obj}, {act}, {field}) added",
        "current_permissions": permissions
    }




@app.post('/assign_role')
async def add_role_to_user(user: str, role: str):
    if role in enforcer.get_roles_for_user(user):
        return f"{role} role already assigned to user"
    enforcer.add_role_for_user(user, role)
    return enforcer.get_roles_for_user(user)






@app.post("/employees/")
def create_employee(employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    new_employee = Employee(**employee_data.model_dump())
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)  
    return new_employee 



@app.get("/employees/{employee_id}",response_model=EmployeeCreate) 
async def read_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee








@app.post("/items/", response_model=Item)
def create_item(item_data: ItemCreate, db: Session = Depends(get_db)):
    new_item = Items(**item_data.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item



@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Items).filter(Items.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item






@app.put("/update_item/{item_id}", response_model=Item)
def update_item(item_id: int, item_data: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(Items).filter(Items.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_data.name is not None:
        item.name = item_data.name
    if item_data.price is not None:
        item.price = item_data.price
    if item_data.tax is not None:
        item.tax = item_data.tax
    if item_data.created is not None:
        item.created = item_data.created
    if item_data.updated is not None:
        item.updated = item_data.updated

    db.commit()
    db.refresh(item)
    return item



@app.delete("/delete_item/{item_id}", response_model=dict)
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Items).filter(Items.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.execute(delete(Items).where(Items.id == item_id))
    db.commit() 

    return {"message": f"Item with ID {item_id} has been deleted."}




















# @app.post("/employees/")
# def create_employee(employee_data: EmployeeCreate, user_role: str, db: Session = Depends(get_db)):
#     new_employee_data = {}

#     employee_dict = employee_data.dict()  

#     for field, value in employee_dict.items():
#         if e.enforce(user_role, "employee", "write", field):
#             new_employee_data[field] = value
#         else:
#             print(f"Access denied for role '{user_role}' on column '{field}'")
#             raise HTTPException(status_code=403, detail=f"No access to insert data into column '{field}'")

#     if not new_employee_data:
#         raise HTTPException(status_code=403, detail=f"No permissions to insert any employee data for role {user_role}")

#     new_employee = Employee(**new_employee_data)
#     db.add(new_employee)
#     db.commit()
#     db.refresh(new_employee)

#     return new_employee




# @app.get("/employees/{employee_id}")
# def read_employee(employee_id: int, user_role: str, db: Session = Depends(get_db)):
#     employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
#     if not employee:
#         raise HTTPException(status_code=404, detail="Employee not found")

#     allowed_employee_data = {}

#     employee_fields = employee.__dict__.keys()  
#     for field in employee_fields:
#         if e.enforce(user_role, "employee", "read", field):
#             allowed_employee_data[field] = getattr(employee, field)

#     if not allowed_employee_data:
#         raise HTTPException(status_code=403, detail=f"No permissions to read any employee data for role {user_role}")

#     return allowed_employee_data






# @app.get('/permission')
# def has_permission(user_role: str, object_name: str, action: str, field: str) -> dict:
#     try:
#         permission_granted = e.enforce(user_role, object_name, action, field)
#         return {"permission_granted": permission_granted}
#     except Exception as ex:
#         print(f"Error occurred while checking permission: {ex}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
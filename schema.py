from pydantic import BaseModel
from datetime import datetime


class EmployeeCreate(BaseModel):
    name: str|None=None
    position: str|None=None
    status: str|None=None




class ItemCreate(BaseModel):
    name: str
    price:  int|None=None
    tax:  int|None=None

class Item(BaseModel):
    id: int
    name: str
    price:  int|None=None
    tax:  int|None=None
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True


class ItemUpdate(BaseModel):
    name: str|None=None
    price:int|None=None
    tax: int|None=None
    created: datetime|None=None
    updated: datetime|None=None
from pydantic import BaseModel
import enum
from fastapi import Query

class Role(str, enum.Enum):
    admin: str = "admin"
    personel: str = "personel"


class User(BaseModel):
    name: str
    password: str
    mail: str = Query(..., regex="^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$")
    role: Role

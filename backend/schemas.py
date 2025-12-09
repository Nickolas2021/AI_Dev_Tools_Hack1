from pydantic import BaseModel

class EmployeeSchema(BaseModel):
    name : str
    email : str
    position : int
    department : str
    preference : int
    username : str
    api_key : str
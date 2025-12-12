from pydantic import BaseModel

class EmployeeSchema(BaseModel):
    name : str
    email : str
    position : int
    department : str
    preference : str
    username : str
    api_key : str
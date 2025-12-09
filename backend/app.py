from contextlib import asynccontextmanager
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select


from backend.database import Base, engine, SessionLocal
from shared_models import Employee

with open("secret.json", "r", encoding="utf-8") as f:
    cal_com_api_keys = json.load(f)



@asynccontextmanager
async def lifespan(app : FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Создана база данных")

    async with SessionLocal() as session:
        result = await session.execute(
            select(Employee)
        )
        employees = result.scalars().all()
        if len(employees) == 0:
            employee1 = Employee(
                name="Николай Пащенко",
                email="1210492n@gmail.com",
                position=3,
                department="AI",
                preference="Встречи не позже 15:00",
                cal_com_username="nickolay-pashenko-ddeuc4",
                cal_com_api_key=cal_com_api_keys["nickolay-pashenko-ddeuc4"]
            )
            employee2 = Employee(
                name="John Geery",
                position=2,
                email="johngeery4@gmail.com",
                department="Sales",
                preference="Встречи после обеда",
                cal_com_username="john-geery-7jnfvx",
                cal_com_api_key=cal_com_api_keys["john-geery-7jnfvx"]
            )
            session.add_all([employee1, employee2])
            await session.commit()
            print("Созданы сотрудники")
        else:
            print("В БД уже есть сотрудники")
    yield
    print("Сеанс завершен")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("app/departments/{department}")
async def get_employees_from_department(department : str):
    """_summary_

    Args:
        department (str): _description_
    """  
    with SessionLocal() as session:
        employees = session.query(Employee).filter(
            Employee.department == department
        ).all()

        return {"employees" : employees}
    
@app.get("app/departments/{department}")
async def get_departments(department : str):
    """_summary_

    Args:
        department (str): _description_
    """  
    with SessionLocal() as session:
        employees = session.query(Employee).filter(
            Employee.department == department
        ).all()

        return {"employees" : employees}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8002, reload=False)



from fastmcp.client.transports import StreamableHttpTransport
from fastmcp import Client
from sqlalchemy import select

from shared_models import Employee
from backend.schemas import EmployeeSchema
from backend.database import SessionLocal


transport = StreamableHttpTransport(
    url="http://127.0.0.1:8007/mcp/"
)




async def test():
    async with SessionLocal() as session:
        result = await session.execute(
            select(Employee).where(Employee.name == "Николай Пащенко")
        )
        employee = result.scalar_one_or_none()
        employee_res = EmployeeSchema(
            name=employee.name,
            email=employee.email,
            position=employee.position,
            department=employee.department,
            preference=employee.preference,
            username=employee.cal_com_username,
            api_key=employee.cal_com_api_key
        ) 
    async with Client(transport=transport) as client:
        # Получение MCP session
        session = client.session
        # вызов функции для назначения встречи
        res = await session.call_tool(
            name="create_meeting",
            arguments={
                "organizer_name": "Николай Пащенко",
                "attendee_name": "John Geery",
                "start_time": "2025-12-18T10:00:00Z",
                "duration_minutes": 30,
                "title": "Project Discussion"
            }
        )

        # res = await session.call_tool(
        #     name="get_available_slots",
        #     arguments={
        #         "employee": employee_res,
        #         "date_from": "2025-12-10",
        #         "date_to": "2025-12-10",
        #         "duration_minutes": 60
        #     }
        # )
        print(res)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
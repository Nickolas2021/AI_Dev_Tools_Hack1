from fastmcp import FastMCP
from sqlalchemy import select
import logging
import os
from dotenv import load_dotenv
import requests

from backend.database import SessionLocal
from shared_models import Employee
from backend.schemas import EmployeeSchema

load_dotenv()

USER_AGENT = "Office manager"

CAL_COM_URL = os.getenv("CALCOM_HOST")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Office manager")

async def create_custom_event_type(
    api_key: str,
    title: str,
    duration_minutes: int,
    slug: str = None
) -> dict:
    """_summary_

    Args:
        title (str): _description_
        duration_minutes (int): _description_
        slug (str, optional): _description_. Defaults to None.

    Returns:
        dict: _description_
    """    
    if not slug:
        slug = f"meeting-{duration_minutes}min"
    
    response = requests.post(
        f"{CAL_COM_URL}/v1/event-types",
        params={"apiKey": api_key},
        json={
            "title": title,
            "slug": slug,
            "length": duration_minutes,  # Длительность в минутах
            "hidden": False
        }
    )
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        return {"error": response.text}
    
async def find_event_type_by_duration(
        api_key: str,
        duration_minutes: int) -> int | None:
    """_summary_

    Args:
        duration_minutes (int): _description_

    Returns:
        int | None: _description_
    """    
    # Получить все event types пользователя
    response = requests.get(
        f"{CAL_COM_URL}/v1/event-types",
        params={"apiKey": api_key}
    )
    
    if response.status_code == 200:
        event_types = response.json().get("event_types", [])
        
        # Ищем подходящий по длительности
        for et in event_types:
            if et["length"] == duration_minutes:
                return et["id"]
    
    return None

@mcp.tool()
async def get_all_departments() -> list[str]:
    """
    Получает список всех отделов компании
    """  
    async with SessionLocal() as session:  
        logger.info("Tool вызван: get_all_departments()")
        result = await session.execute(
            select(Employee.department).distinct()
        )
        departments = result.scalars().all()

        return departments
    
@mcp.tool()
async def get_all_employees_from_department(department: str) -> list[str]:
    """
    Получает список всех сотрудников отдела
    """  
    async with SessionLocal() as session:  
        logger.info(f"Tool вызван: get_all_employees_from_department(department: {department})")
        result = await session.execute(
            select(Employee.name).where(Employee.department == department)
        )
        employees = result.scalars().all()

        return employees

@mcp.tool()
async def create_meeting(
    employee: EmployeeSchema,
    start_time: str,
    duration_minutes: int,
    title: str = "Meeting"
) -> dict:
    """Назначает встречу с выбранным сотрудником

    Args:
        attendee_name (str): имя сотрудника для встречи
        attendee_email (str): емейл сотрудника для встречи
        start_time (str): начало встречи
        duration_minutes (int): длительность
        title (str, optional): названия встречи. Defaults to "Meeting".

    Returns:
        dict: _description_
    """    
    # 1. Попробовать найти существующий event type
    event_type_id = await find_event_type_by_duration(duration_minutes)
    
    # 2. Если не нашли - создать новый
    if not event_type_id:
        print(f"Creating new event type for {duration_minutes} minutes")
        create_response = await create_custom_event_type(
            title=f"{title} ({duration_minutes}min)",
            duration_minutes=duration_minutes
        )
        
        if "id" in create_response.get("event_type", {}):
            event_type_id = create_response["event_type"]["id"]
        else:
            return {"error": "Failed to create event type"}
    
    # 3. Создать встречу
    response = requests.post(
        f"{CAL_COM_URL}/v1/bookings",
        params={"apiKey": employee.api_key},
        json={
            "eventTypeId": event_type_id,
            "start": start_time,
            "responses": {
                "name": employee.name,
                "email": employee.email
            },
            "timeZone": "Europe/Moscow"
        }
    )
    
    return {
        "booking": response.json(),
        "duration_minutes": duration_minutes,
        "event_type_id": event_type_id
    }

@mcp.tool()
async def get_available_slots(
    employee: EmployeeSchema,
    date_from: str,
    date_to: str,
    duration_minutes: int = 60
) -> dict:
    """
    Получить свободные временные слоты сотрудника с заданной длительностью
    
    Args:
        employee_name (str): Имя сотрудника из базы данных (например, "Мария Иванова")
        date_from (str): Начальная дата в формате YYYY-MM-DD (например, "2025-12-10")
        date_to (str): Конечная дата в формате YYYY-MM-DD (например, "2025-12-15")
        duration_minutes (int): Длительность встречи в минутах. Defaults to 60.
    
    Returns:
        dict: Словарь со свободными слотами по дням
    """
    from datetime import datetime, timedelta
    
    logger.info(f"Tool вызван: get_available_slots(employee={employee.name}, {date_from} to {date_to}, duration={duration_minutes}min)")
    
    # 1. Найти сотрудника в БД
    async with SessionLocal() as session:
        result = await session.execute(
            select(Employee).where(Employee.name == employee.name)
        )
        employee_result = result.scalar_one_or_none()
        
        if not employee_result:
            logger.error(f"Сотрудник '{employee.name}' не найден")
            return {
                "error": f"Сотрудник '{employee.name}' не найден в базе данных",
                "employee": employee.name
            }
        
        # Получаем Cal.com username (если есть поле в модели)
        cal_username = getattr(employee_result, 'cal_com_username', None)
    
    # 2. Найти или создать event type с нужной длительностью
    event_type_id = await find_event_type_by_duration(duration_minutes)
    
    if not event_type_id:
        logger.info(f"Event type на {duration_minutes} минут не найден, создаём новый")
        create_response = await create_custom_event_type(
            title=f"Meeting {duration_minutes}min",
            duration_minutes=duration_minutes
        )
        
        if "event_type" in create_response and "id" in create_response["event_type"]:
            event_type_id = create_response["event_type"]["id"]
            logger.info(f"Создан event type ID: {event_type_id}")
        else:
            logger.error(f"Не удалось создать event type: {create_response}")
            return {
                "error": f"Не удалось создать event type для {duration_minutes} минут",
                "details": create_response.get("error", "Unknown error")
            }
    
    # 3. Запросить свободные слоты из Cal.com API
    start_time = f"{date_from}T00:00:00Z"
    end_time = f"{date_to}T23:59:59Z"
    
    try:
        response = requests.get(
            f"{CAL_COM_URL}/v1/slots",
            params={
                "apiKey": employee.api_key,
                "username": cal_username,
                "eventTypeId": event_type_id,
                "startTime": start_time,
                "endTime": end_time,
                "timeZone": "Europe/Moscow"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Cal.com API error: {response.status_code} - {response.text}")
            return {
                "error": f"Ошибка Cal.com API: {response.status_code}",
                "details": response.text,
                "employee": employee.name
            }
        
        api_response = response.json()
        slots_data = api_response.get("slots", {})
        
        # 4. Обогатить слоты информацией о времени окончания
        enhanced_slots = {}
        total_count = 0
        
        for date, slots in slots_data.items():
            enhanced_slots[date] = []
            for slot in slots:
                start = datetime.fromisoformat(slot["time"].replace('Z', '+00:00'))
                end = start + timedelta(minutes=duration_minutes)
                
                enhanced_slots[date].append({
                    "start": slot["time"],
                    "end": end.isoformat()
                })
                total_count += 1
        
        logger.info(f"Найдено {total_count} свободных слотов для {employee.name}")
        
        return {
            "employee": employee.name,
            "cal_username": cal_username,
            "duration_minutes": duration_minutes,
            "date_range": {
                "from": date_from,
                "to": date_to
            },
            "slots": enhanced_slots,
            "total_slots": total_count
        }
        
    except requests.exceptions.Timeout:
        logger.error("Timeout при запросе к Cal.com API")
        return {
            "error": "Превышено время ожидания ответа от Cal.com",
            "employee": employee.name
        }
    except Exception as e:
        logger.error(f"Исключение при получении слотов: {str(e)}")
        return {
            "error": "Внутренняя ошибка при получении слотов",
            "details": str(e),
            "employee": employee.name
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8007)

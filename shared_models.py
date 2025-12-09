import uuid

from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base

class Employee(Base):
    __tableename_ = 'employees'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default_factory=uuid.uuid4, 
        init=False
    )
    name: Mapped[str] = mapped_column(
        String(50), 
        comment="Имя и фамилия сотрудника",
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(50),
        comment="Электронная почта сотрудника",
    )
    position: Mapped[int] = mapped_column(
        Integer, 
        comment="Позиция в компании: чем больше - тем больше полномочий"
    )
    department: Mapped[str] = mapped_column(
        String(50),
        comment="Отдел, в котором находится сотрудник",
        index=True
    )
    preference: Mapped[str] = mapped_column(
        String(255), 
        comment="Предпочтения сотрудника по времени встреч"
    )
    cal_com_username: Mapped[str] = mapped_column(
        String(50),
        comment="Имя пользователя в календаре"
    )
    cal_com_api_key: Mapped[str] = mapped_column(
        String(100),
        comment="Ключ доступа к календарю"
    )

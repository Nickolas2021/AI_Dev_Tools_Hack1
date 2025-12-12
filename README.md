# Идея проекта:
AI-агент, выполняющий роль офис менеджера, подключен к календарям сотрудников
через публичный API Cal.com, может проверять наличие свободных слотов для сотрудников
и назначать встречи

# Реализация
В демо версии реализовано взаимодействие с агентом через консоль (была попытка внедрить тг-бота - @DataSuetolog_bot, но не успели)
База данных развернута в PostgreSQL 

# !!!ВАЖНО!!!
в файле backend/database.py подключение к БД выполняется так:
1) для WSL/Linux
<SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:password@localhost:5433/office_manager">
2) для Windows
<SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5433/office_manager">
# !!!ВАЖНО!!!

# Инструкция по запуску проекта
Развернуть PostgreSQL:
docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_DB=office_manager postgres

создать и заполнить БД
uv run -m backend.app

запустить MCP сервер:
uv run fastmcp run mcp_server.py:mcp --transport http --port 8007

запустить агента:
uv run -m backend.langchain_agent

# .env
CALCOM_HOST = "https://api.cal.com"
TG_TOKEN = '8068949172:AAHirUVlp7D14nmDsxH1xaz9b4S4D54vunw'
AI_API_KEY='ZTI2NDc2NjAtNjc2ZC00MzQwLTlkY2YtMTYxYzc4ZmQ1ODgx.8493e437c0e787e6cff9e12002db0a74'
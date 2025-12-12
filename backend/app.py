import os
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, Application
from openai import AsyncOpenAI
from dotenv import load_dotenv
from sqlalchemy import select
from langchain.messages import HumanMessage, AIMessage
import sys
import traceback

# ... ваши импорты БД ...
from backend.database import Base, engine, SessionLocal
from shared_models import Employee
from backend.langchain_agent import init_agent

load_dotenv()

agent = None

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

with open("secret.json", "r", encoding="utf-8") as f:
    cal_com_api_keys = json.load(f)

# --- Настройка Бота ---
ptb_app: Application = None

client = AsyncOpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url="https://foundation-models.api.cloud.ru/v1"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"START from {update.effective_user.id}")
    await update.message.reply_text("ping")

#history = {"messages": []}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"MSG from {update.effective_user.id}: {update.message.text}")
    await update.message.reply_text("pong")
    # 1. ЛОГ: Видим ли мы вообще сообщение?
    print(f"📩 DEBUG: Пришло сообщение от {update.effective_user.first_name}: {update.message.text}")

    # 2. Инициализация истории для конкретного пользователя (вместо глобальной)
    if "history" not in context.user_data:
        context.user_data["history"] = {"messages": []}
    
    # Получаем ссылку на историю пользователя
    history = context.user_data["history"]
    
    user_text = HumanMessage(content=update.message.text)

    try:
        # Добавляем сообщение пользователя
        history["messages"].append(user_text)

        # Вызываем агента
        print("🤖 DEBUG: Отправляю запрос агенту...")
        # Важно: agent.ainvoke возвращает новый стейт
        new_history = await agent.ainvoke(history)
        
        # Обновляем историю в user_data
        context.user_data["history"] = new_history
        
        # Получаем последний ответ
        last_message = new_history["messages"][-1]
        
        # Проверка: last_message может быть объектом или строкой
        response_text = last_message.content if hasattr(last_message, "content") else str(last_message)

        print(f"📤 DEBUG: Ответ агента: {response_text[:50]}...")
        await update.message.reply_text(response_text)

    except Exception as e:
        # 3. ЛОГ: Если упало, то почему?
        print("❌ ОШИБКА В HANDLER:")
        traceback.print_exc() # Выведет полный текст ошибки в консоль
        await update.message.reply_text(f"Внутренняя ошибка бота: {e}")

def setup_bot():
    app = ApplicationBuilder().token(os.getenv("TG_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

# --- LIFESPAN (Самое важное) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ БД готова")
    global agent
    agent = await init_agent()

    print("DEBUG: Проверяю сотрудников...")
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
            employee3 = Employee(
                name="Vadim Denisov",
                position=3,
                email="denisovoof@gmail.com",
                department="AI",
                preference="Нет",
                cal_com_username="vadim-denisov-lwyxaf",
                cal_com_api_key=cal_com_api_keys["vadim-denisov-lwyxaf"]
            )
            session.add_all([employee1, employee2, employee3])
            await session.commit()
            print("Созданы сотрудники")
        else:
            print("В БД уже есть сотрудники")

    # 2. Инициализация и Запуск Бота (Polling)
    print("DEBUG: Настраиваю бота...")
    global ptb_app
    ptb_app = setup_bot()
    
    print("DEBUG: Инициализация ptb_app...")
    await ptb_app.initialize()
    print("DEBUG: Старт ptb_app...")
    await ptb_app.start()
    
    # ⚠️ ВАЖНО: Удаляем вебхук перед поллингом (иначе ошибка 409)
    print("DEBUG: Удаление вебхука...")
    await ptb_app.bot.delete_webhook()
    print("DEBUG: Вебхук удален")
    
    # Запускаем поллинг в фоне (Updater)
    print("🚀 Запускаю Polling...")
    await ptb_app.updater.start_polling()

    yield # Приложение работает

    # 3. Остановка
    print("🛑 Остановка бота...")
    await ptb_app.updater.stop()
    await ptb_app.stop()
    await ptb_app.shutdown()

app = FastAPI(lifespan=lifespan)

# Эндпоинт /webhook больше НЕ НУЖЕН!
# Ваши API эндпоинты работают параллельно с ботом
@app.get("/")
async def root():
    return {"message": "FastAPI работает, Бот тоже работает!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8002, reload=False)

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

# ... ваши импорты БД ...
from backend.database import Base, engine, SessionLocal
from shared_models import Employee

load_dotenv()

with open("secret.json", "r", encoding="utf-8") as f:
    cal_com_api_keys = json.load(f)

# --- Настройка Бота ---
ptb_app: Application = None

client = AsyncOpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url="https://foundation-models.api.cloud.ru/v1"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я работаю через Polling внутри FastAPI 🚀")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # ... ваша логика AI ...
    try:
        response = await client.chat.completions.create(
             model="ai-sage/GigaChat3-10B-A1.8B",
             messages=[{"role": "user", "content": user_text}]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except:
        await update.message.reply_text("Ошибка AI")

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

    # 2. Инициализация и Запуск Бота (Polling)
    global ptb_app
    ptb_app = setup_bot()
    
    await ptb_app.initialize()
    await ptb_app.start()
    
    # ⚠️ ВАЖНО: Удаляем вебхук перед поллингом (иначе ошибка 409)
    await ptb_app.bot.delete_webhook()
    
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

import asyncio
import os
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import sys

load_dotenv()

# Импортируем адаптеры для MCP
from langchain_mcp_adapters.tools import load_mcp_tools

MODEL_NAME = "Qwen/Qwen3-235B-A22B-Instruct-2507"

SYSTEM_PROMPT = \
f"""
Ты — интеллектуальный ассистент по планированию встреч, интегрированный с тулами на MCP-серверами, работающими с Cal.com.
            
Твои правила:
    1. Используй доступные инструменты для проверки слотов и создания встреч. Не выдумывай данные.
    2. Текущая дата: {datetime.now().strftime("%Y-%m-%d")}. Все относительные даты ("завтра", "через неделю") считай от неё. Также ВСЕГДА передавай дату ровно в таком же формате.
    3. Для бронирования ОБЯЗАТЕЛЬНО узнай имена обоих пользователей, чтобы получить их свободные слоты из базы данных соответствующим тулом. Если пользователь не предоставил их - спроси.
       После этого запланируй встречу соответствующим тулом.
    4. При каждом новом обращении о проверке свободных слотов ОБЯЗАТЕЛЬНО делай это с помощью соответствующего тула.
"""



client = MultiServerMCPClient(
    {
        "Office manager": {
            "transport": "http",
            "url": "http://127.0.0.1:8000/mcp",
        }
    }
)

model = ChatOpenAI(
    base_url="https://foundation-models.api.cloud.ru/v1/",
    api_key=os.getenv("AI_API_KEY"),
    model=MODEL_NAME,
    temperature=0.1,
    max_tokens=10000,
    timeout=30
)


async def init_agent():
    tools = await client.get_tools()
    # print("Tools loaded successully! Available:", tools)
    agent = create_agent(model, tools, system_prompt=SystemMessage(SYSTEM_PROMPT))

    return agent

async def main():
    agent = await init_agent()
    print(f"Agent {MODEL_NAME} initialized successfuly!")
    history = {"messages": []}
    while True:
        print()
        user_message = HumanMessage(input("...> "))
        history["messages"].append(user_message)
        history = await agent.ainvoke(history)
        response = history["messages"][-1]
        print(f"ai:", response.content)
        
if __name__ == "__main__":
    asyncio.run(main())
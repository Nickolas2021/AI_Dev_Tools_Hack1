import requests
from datetime import datetime, timedelta

API_KEY = "cal_live_4c7d2f066b83ecf9a17b8b1a722c1463"
CALCOM_HOST = "https://api.cal.com"

# 1. Получаем event types
print("Получаем event types...")
event_types_response = requests.get(
    f"{CALCOM_HOST}/v1/event-types",
    params={"apiKey": API_KEY}
)

if event_types_response.status_code == 200:
    event_types = event_types_response.json().get('event_types', [])
    if event_types:
        event_type = event_types[0]
        print(f"✅ Event Type: {event_type['title']} (ID: {event_type['id']})")
        event_type_id = event_type['id']
    else:
        print("❌ Event types не найдены")
        exit()
else:
    print(f"❌ Ошибка: {event_types_response.text}")
    exit()

# 2. Создаём событие (упрощённый формат)
print("\nСоздаём событие...")
start = datetime.now() + timedelta(days=1, hours=10)

# ИСПРАВЛЕННАЯ структура запроса
booking_data = {
    "eventTypeId": event_type_id,
    "start": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    "responses": {
        "name": "Bob Johnson",
        "email": "bob@demo.com"
    },
    "timeZone": "Europe/Moscow",
    "metadata": {},  # Пустой объект вместо данных
    "language": "en"
}

print(f"Отправляем запрос: {booking_data}")

booking_response = requests.post(
    f"{CALCOM_HOST}/v1/bookings",
    params={"apiKey": API_KEY},
    json=booking_data
)

print(f"Статус ответа: {booking_response.status_code}")
print(f"Ответ: {booking_response.text}")

if booking_response.status_code in [200, 201]:
    booking = booking_response.json()
    print(f"\n✅ Событие создано!")
    print(f"   ID: {booking.get('id')}")
    print(f"   Время: {start.strftime('%d.%m.%Y %H:%M')}")
    print(f"\n🎉 Проверьте: https://app.cal.com/bookings")
else:
    print(f"\n❌ Ошибка создания события")

# src/create_session.py

from telethon import TelegramClient
import yaml
import os

# Загрузка конфигурации
with open('config/secrets.yaml', 'r') as file:
    secrets = yaml.safe_load(file)

# Настройки для подключения
phone_number = secrets['telegram']['phone_number']
api_id = secrets['telegram']['api_id']
api_hash = secrets['telegram']['api_hash']
session_folder = 'sessions'
os.makedirs(session_folder, exist_ok=True)
session_file = os.path.join(session_folder, f'{phone_number}.session')  # Имя файла сессии на основе номера телефона

# Создание клиента
client = TelegramClient(session_file, api_id, api_hash)


async def main():
    # Подключение к клиенту
    await client.start()
    print("Сессия успешно создана.")

# Запуск создания сессии
if __name__ == "__main__":
    client.loop.run_until_complete(main())

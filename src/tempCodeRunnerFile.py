# src/main.py

import pandas as pd
import asyncio
from telethon import TelegramClient
import yaml
import os
from telegram.create_chats import create_group
from telegram.add_admins import add_admins
from telegram.configure_chats import configure_chat


# Загрузка конфиденциальных данных из файла secrets.yaml
with open('config/secrets.yaml', 'r') as file:
    secrets = yaml.safe_load(file)

API_ID = secrets['telegram']['api_id']
API_HASH = secrets['telegram']['api_hash']
PHONE_NUMBER = secrets['telegram']['phone_number']

# Использование ранее сохраненной сессии
session_folder = 'sessions'
os.makedirs(session_folder, exist_ok=True)
session_file = os.path.join(session_folder, f'{PHONE_NUMBER}.session')
client = TelegramClient(session_file, API_ID, API_HASH)


async def main():
    await client.start()
    print("Сессия успешно подключена.")

    # Загрузка данных
    excel_path = 'TERRA.xlsx'
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Файл '{excel_path}' не найден.")
    mentors_data = pd.read_excel(excel_path)
    active_mentors = mentors_data[mentors_data['mentor_active'].str.lower() == 'да']

    for _, mentor in active_mentors.iterrows():
        mentor_info = mentor.to_dict()

        # Создание группы
        chat_id = await create_group(client, mentor_info)
        if not chat_id:
            continue

        # Добавление администраторов
        await add_admins(client, chat_id, mentor_info)

        # Настройка группы
        await configure_chat(client, chat_id)


# Запуск асинхронного клиента
if __name__ == "__main__":
    asyncio.run(main())

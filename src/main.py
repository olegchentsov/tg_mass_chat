import pandas as pd
import asyncio
from telethon import TelegramClient
import yaml
import os

from utils.logger import set_logger
from loguru import logger
from telegram.create_chats import create_group
from telegram.add_admins import add_admins
from telegram.configure_chats import configure_chat
from google_sheets.result_data import save_result
from google_sheets.fetch_data import fetch_mentors_data

# Настройка логирования
set_logger()

# Загрузка конфиденциальных данных из файла secrets.yaml
CONFIG_DIR = 'config'
SECRETS_FILE = os.path.join(CONFIG_DIR, 'secrets.yaml')
if not os.path.exists(SECRETS_FILE):
    logger.critical(f"Файл '{SECRETS_FILE}' не найден. Проверьте, что он существует в папке '{CONFIG_DIR}'.")
    raise FileNotFoundError(f"Файл '{SECRETS_FILE}' не найден.")

with open(SECRETS_FILE, 'r') as file:
    secrets = yaml.safe_load(file)

API_ID = secrets['telegram']['api_id']
API_HASH = secrets['telegram']['api_hash']
PHONE_NUMBER = secrets['telegram']['phone_number']

# Использование ранее сохраненной сессии
SESSION_FOLDER = 'sessions'
os.makedirs(SESSION_FOLDER, exist_ok=True)
SESSION_FILE = os.path.join(SESSION_FOLDER, f'{PHONE_NUMBER}.session')
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

# Путь для сохранения результатов
RESULTS_FILE = "TERRA_Results.xlsx"

# Инициализация Excel-файла для результатов
if not os.path.exists(RESULTS_FILE):
    pd.DataFrame(columns=["mentor_name", "mentor_username", "mentor_chat", "chat_link", "mentor_add", "message"]).to_excel(
        RESULTS_FILE, index=False
    )


async def process_mentors(mentors_data):
    """
    Обработка данных о наставниках.
    """
    # Проверка наличия столбца 'mentor_active'
    if 'mentor_active' not in mentors_data.columns:
        logger.error("Столбец 'mentor_active' отсутствует в Excel-файле.")
        raise KeyError("Столбец 'mentor_active' отсутствует в Excel-файле.")

    # Фильтрация активных наставников
    active_mentors = mentors_data[mentors_data['mentor_active'].str.lower() == 'да']
    if active_mentors.empty:
        logger.warning("Нет активных наставников для обработки.")
        return

    # Обработка каждого наставника
    for _, mentor in active_mentors.iterrows():
        mentor_info = mentor.to_dict()
        mentor_name = mentor_info.get("mentor_name", "Неизвестный наставник")
        mentor_username = mentor_info.get("mentor_tg_username", "")
        mentor_category = mentor_info.get("mentor_category", "")
        group_name = None
        invite_link = None
        mentor_added = False
        message_to_mentor = None

        try:
            logger.info(f"Создание группы для наставника: {mentor_name}")
            input_channel, group_name, invite_link = await create_group(client, mentor_info)

            if input_channel:
                logger.info(f"Группа для наставника '{mentor_name}' успешно создана.")
                mentor_added = await add_admins(client, input_channel, mentor_info)
                await configure_chat(client, input_channel, mentor_name)
            else:
                logger.error(f"Не удалось создать группу для наставника '{mentor_name}'.")

            # Извлечение первого слова из имени
            first_name = mentor_name.split()[0]

            # Формирование сообщения
            message_to_mentor = (
                f"Здравствуйте, {first_name}!\n\n"
                f"Приглашаю вас присоединиться к чату {group_name} для проведения наставничества TERRA 8.0 {mentor_category}.\n\n"
                f"Ссылка на чат: {invite_link}"
            ) if group_name and invite_link else f"Чат для наставника '{mentor_name}' не удалось создать."

        except Exception as e:
            logger.exception(f"Ошибка при обработке наставника '{mentor_name}': {e}")
            message_to_mentor = f"При обработке наставника '{mentor_name}' произошла ошибка."

        # Сохраняем результат в файл Excel
        new_row = {
            "mentor_name": mentor_name,
            "mentor_username": mentor_username,
            "mentor_chat": group_name or "Не создано",
            "chat_link": invite_link or "Нет",
            "mentor_add": "Да" if mentor_added else "Нет",
            "message": message_to_mentor,
        }
        save_result(RESULTS_FILE, new_row)


async def main():
    """
    Главная функция для управления процессом.
    """
    try:
        # Подключение к Telegram Client
        await client.start()
        logger.info("Сессия Telegram успешно подключена.")

        # Проверка существования Excel-файла
        EXCEL_PATH = "TERRA.xlsx"
        if not os.path.exists(EXCEL_PATH):
            logger.critical(f"Файл '{EXCEL_PATH}' не найден. Убедитесь, что путь правильный и файл существует.")
            raise FileNotFoundError(f"Файл '{EXCEL_PATH}' не найден.")

        # Загрузка данных о наставниках
        mentors_data = fetch_mentors_data(EXCEL_PATH, sheet_name="Наставники")
        if mentors_data is None:
            logger.warning("Файл не содержит активных наставников.")
            return

        # Обработка наставников
        await process_mentors(mentors_data)

    except FileNotFoundError as e:
        logger.critical(f"Ошибка: {e}")
    except KeyError as e:
        logger.error(f"Ошибка: {e}")
    except Exception as e:
        logger.exception(f"Общая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("Клиент Telegram отключен.")


# Запуск асинхронного клиента
if __name__ == "__main__":
    asyncio.run(main())

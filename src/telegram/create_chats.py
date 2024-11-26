from telethon import functions, types
from telethon.errors import RPCError, FloodWaitError
import os
import yaml
import asyncio
from loguru import logger
import re


# Загрузка настроек из файла settings.yaml
def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Преобразуем тройные кавычки в многострочный текст
    content = re.sub(r'"""(.*?)"""', lambda m: f'"{m.group(1).replace("\n", "\\n")}"', content, flags=re.S)

    # Загружаем обработанный YAML
    return yaml.safe_load(content)


settings = load_yaml("config/settings.yaml")


async def create_group(client, mentor):
    """
    Создаёт супергруппу в Telegram для конкретного наставника.

    :param client: Аутентифицированный клиент Telethon.
    :param mentor: Словарь с информацией о наставнике.
    :return: Кортеж (input_channel, group_title, invite_link) или (None, None, None) в случае ошибки.
    """
    # Формируем название группы из шаблона из настроек
    group_title = settings['group']['name_format'].format(
        mentor_name=mentor['mentor_name'],
        mentor_category=mentor['mentor_category'],
        mentor_id=mentor['mentor_id']
    )

    input_channel = None
    invite_link = None

    try:
        # Создание новой супергруппы (мегагруппы)
        result = await client(functions.channels.CreateChannelRequest(
            title=group_title,
            about='',
            megagroup=True
        ))
        logger.info(f"Группа '{group_title}' успешно создана.")

        # Получение идентификатора канала и access_hash
        channel = result.chats[0]
        channel_id = channel.id
        access_hash = channel.access_hash
        logger.debug(f"ID группы: {channel_id}, access_hash: {access_hash}")

        # Создание объекта InputChannel
        input_channel = types.InputChannel(channel_id, access_hash)

        # Сохранение ссылки-приглашения
        invite_link_result = await client(functions.messages.ExportChatInviteRequest(
            peer=input_channel
        ))
        invite_link = invite_link_result.link
        logger.info(f"Ссылка-приглашение для группы '{group_title}': {invite_link}")

        # Установка аватара группы
        logo_path = os.path.join(os.getcwd(), 'TERRA-logo.jpeg')
        if os.path.exists(logo_path):
            try:
                await client(functions.channels.EditPhotoRequest(
                    channel=input_channel,
                    photo=await client.upload_file(logo_path)
                ))
                logger.info(f"Аватар группы '{group_title}' установлен на TERRA-logo.jpeg.")
            except FloodWaitError as e:
                logger.warning(f"Ошибка FloodWait при установке аватара. Ожидание {e.seconds} секунд.")
                await asyncio.sleep(e.seconds)
                await client(functions.channels.EditPhotoRequest(
                    channel=input_channel,
                    photo=await client.upload_file(logo_path)
                ))
                logger.info(f"Аватар группы '{group_title}' установлен после ожидания.")
        else:
            logger.warning(f"Файл '{logo_path}' не найден. Аватар группы не установлен.")

        return input_channel, group_title, invite_link

    except FloodWaitError as e:
        logger.warning(f"Ошибка FloodWait при создании группы. Ожидание {e.seconds} секунд.")
        await asyncio.sleep(e.seconds)
        logger.info(f"Повторное создание группы '{group_title}' после ожидания.")
        return await create_group(client, mentor)
    except RPCError as e:
        logger.error(f"Ошибка при создании группы '{group_title}': {e}")
    except Exception as e:
        logger.exception(f"Общая ошибка при создании группы '{group_title}': {e}")

    return None, None, None

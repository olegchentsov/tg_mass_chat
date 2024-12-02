from telethon import functions, types
from telethon.errors import FloodWaitError
from loguru import logger
import yaml
import re
import asyncio


# Загрузка настроек из файла settings.yaml
def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Преобразуем тройные кавычки в многострочный текст
    content = re.sub(r'"""(.*?)"""', lambda m: f'"{m.group(1).replace("\n", "\\n")}"', content, flags=re.S)

    # Загружаем обработанный YAML
    return yaml.safe_load(content)


settings = load_yaml("config/settings.yaml")


async def configure_chat(client, input_channel, mentor_name):
    """
    Конфигурирует супергруппу: устанавливает права, включает темы и отправляет сообщения.

    :param client: Аутентифицированный клиент Telethon.
    :param input_channel: Объект InputChannel группы.
    :param mentor_name: Имя наставника для подстановки в сообщения.
    """
    config = settings['settings']
    topics = settings['topics']

    # Отключение разрешений для участников
    default_banned_rights = types.ChatBannedRights(
        until_date=None,
        view_messages=False,
        send_messages=False if config.get('disable_participant_addition') else True,
        send_media=False,
        send_stickers=False,
        send_gifs=False,
        send_games=False,
        send_inline=False,
        embed_links=False,
        send_polls=False,
        change_info=config.get('disable_profile_edit', False),
        invite_users=False,
        pin_messages=False
    )

    await client(functions.channels.EditBannedRequest(
        channel=input_channel,
        participant='@channel',  # Применить ко всем участникам
        banned_rights=default_banned_rights
    ))
    logger.info("Права участников успешно настроены.")

    # Включение мультигрупп (тем) с обработкой FloodWaitError
    if config.get('enable_topics', False):
        try:
            await client(functions.channels.ToggleForumRequest(
                channel=input_channel,
                enabled=True
            ))
            logger.info("Мультигруппы включены.")
        except FloodWaitError as e:
            logger.warning(f"Слишком частый запрос. Необходимо подождать {e.seconds} секунд.")
            await asyncio.sleep(e.seconds)
            logger.info("Повторное включение мультигрупп после ожидания.")
            await client(functions.channels.ToggleForumRequest(
                channel=input_channel,
                enabled=True
            ))
            logger.info("Мультигруппы включены после ожидания.")

    # Обработка темы General
    general_topic_id = None
    all_topics = await client(functions.channels.GetForumTopicsRequest(
        channel=input_channel,
        q='',
        offset_date=None,
        offset_id=0,
        offset_topic=0,
        limit=100
    ))

    for topic_info in all_topics.topics:
        if topic_info.title.lower() == 'general':
            general_topic_id = topic_info.id
            try:
                # Переименование "General" в "Общий чат"
                await client(functions.channels.EditForumTopicRequest(
                    channel=input_channel,
                    topic_id=general_topic_id,
                    title="Общий чат"
                ))
                logger.info("Тема 'General' успешно переименована в 'Общий чат'.")

                # Отправка сообщения в тему "Общий чат"
                for topic in topics:
                    if topic['name'].lower() == 'general' and 'pinned_message' in topic:
                        general_message = topic['pinned_message'].strip().format(mentor_name=mentor_name)
                        message = await client.send_message(
                            entity=input_channel,
                            message=general_message,
                            reply_to=general_topic_id
                        )
                        await client.pin_message(input_channel, message.id)
                        logger.info("Сообщение для темы 'General' отправлено и закреплено.")

                # Удаление системных сообщений после переименования
                await remove_system_messages(client, input_channel)
                logger.info("Системные сообщения удалены после переименования 'General'.")
            except Exception as rename_error:
                logger.error(f"Ошибка при переименовании темы 'General': {rename_error}")
            break

    if not general_topic_id:
        logger.warning("Тема 'General' не найдена.")

    # Обработка остальных тем
    for topic in topics:
        if topic['name'].lower() == 'general':
            continue  # Пропускаем, так как тема General уже обработана

        logger.info(f"Обработка темы: {topic['name']}")

        try:
            # Создаём тему
            await client(functions.channels.CreateForumTopicRequest(
                channel=input_channel,
                title=topic['name']
            ))

            # Ищем созданную тему
            updated_topics = await client(functions.channels.GetForumTopicsRequest(
                channel=input_channel,
                q=topic['name'],
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100  # Увеличили лимит, чтобы гарантировать нахождение темы
            ))
            new_topic_id = next(
                (t.id for t in updated_topics.topics if t.title == topic['name']),
                None
            )

            if not new_topic_id:
                logger.warning(f"Не удалось определить ID для темы '{topic['name']}'.")
                continue

            logger.info(f"Тема '{topic['name']}' успешно создана. ID: {new_topic_id}")

            # Закрепляем pinned_message, если есть
            if 'pinned_message' in topic:
                pinned_message_text = topic['pinned_message'].strip().format(mentor_name=mentor_name)
                pinned_message = await client.send_message(
                    entity=input_channel,
                    message=pinned_message_text,
                    reply_to=new_topic_id
                )
                await client.pin_message(input_channel, pinned_message.id)
                logger.info(f"Сообщение для темы '{topic['name']}' закреплено.")

            # Отправляем messages, если есть
            if 'messages' in topic and topic['messages']:
                # Убедимся, что 'messages' является списком
                if isinstance(topic['messages'], list):
                    for msg in topic['messages']:
                        msg_text = msg.strip()
                        if msg_text:
                            await client.send_message(
                                entity=input_channel,
                                message=msg_text,
                                reply_to=new_topic_id
                            )
                            logger.info(f"Сообщение для темы '{topic['name']}' отправлено.")
                        else:
                            logger.warning(f"Пустое сообщение в теме '{topic['name']}' пропущено.")
                else:
                    # Если 'messages' не список, логируем ошибку
                    logger.error(f"Поле 'messages' для темы '{topic['name']}' должно быть списком.")
        except FloodWaitError as e:
            logger.warning(f"Ошибка FloodWait при создании темы '{topic['name']}': {e}")
            await asyncio.sleep(e.seconds)
            logger.info(f"Повторное создание темы '{topic['name']}' после ожидания.")
        except Exception as topic_error:
            logger.error(f"Ошибка при создании темы '{topic['name']}': {topic_error}")


async def remove_system_messages(client, input_channel):
    """
    Удаляет все сообщения с действиями в группе, независимо от их типа.

    :param client: Аутентифицированный клиент Telethon.
    :param input_channel: Объект InputChannel группы.
    """
    try:
        logger.info("Начинаем удаление всех сообщений с действиями.")
        async for message in client.iter_messages(input_channel, limit=50):
            if message.action:  # У сообщения есть поле `action`, значит это системное действие
                await client.delete_messages(input_channel, message.id)
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщений с действиями: {e}")

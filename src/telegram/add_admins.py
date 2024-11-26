import yaml
from loguru import logger
import re
from telethon import functions, types


# Загрузка настроек из файла settings.yaml
def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Преобразуем тройные кавычки в многострочный текст
    content = re.sub(r'"""(.*?)"""', lambda m: f'"{m.group(1).replace("\n", "\\n")}"', content, flags=re.S)

    # Загружаем обработанный YAML
    return yaml.safe_load(content)


settings = load_yaml("config/settings.yaml")


async def add_admins(client, input_channel, mentor_info):
    """
    Добавляет администраторов в группу.

    :param client: Аутентифицированный клиент Telethon.
    :param input_channel: Объект InputChannel группы.
    :param mentor_info: Информация о наставнике.
    """
    additional_admins = settings['users'].get('additional_admins', [])
    mentor_tg_username = mentor_info.get('mentor_tg_username')
    mentor_name = mentor_info.get('mentor_name', 'Неизвестный наставник')

    try:
        # Добавление наставника как администратора с ограниченными правами
        if mentor_tg_username:
            try:
                mentor_entity = await client.get_input_entity(mentor_tg_username)
                await client(functions.channels.EditAdminRequest(
                    channel=input_channel,
                    user_id=mentor_entity,
                    admin_rights=types.ChatAdminRights(
                        invite_users=False,
                        change_info=False,
                        post_messages=True,
                        edit_messages=True,
                        delete_messages=False,
                        ban_users=False,
                        pin_messages=True,
                        add_admins=False,
                        anonymous=False,
                        manage_call=False,
                        other=False
                    ),
                    rank='Наставник'
                ))
                logger.info(f"Наставник {mentor_name} успешно добавлен как администратор.")
            except Exception as e:
                logger.error(f"Ошибка при добавлении наставника {mentor_name}: {e}")

        # Добавление дополнительных администраторов
        for admin_username in additional_admins:
            try:
                admin_entity = await client.get_input_entity(admin_username)
                await client(functions.channels.EditAdminRequest(
                    channel=input_channel,
                    user_id=admin_entity,
                    admin_rights=types.ChatAdminRights(
                        invite_users=True,
                        change_info=True,
                        post_messages=True,
                        edit_messages=True,
                        delete_messages=True,
                        ban_users=True,
                        pin_messages=True,
                        add_admins=False,
                        anonymous=True,
                        manage_call=True,
                        other=True
                    ),
                    rank='Администратор'
                ))
                logger.info(f"Администратор {admin_username} успешно добавлен.")
            except Exception as e:
                logger.error(f"Ошибка при добавлении администратора {admin_username}: {e}")

    except Exception as e:
        logger.error(f"Общая ошибка при добавлении администраторов: {e}")

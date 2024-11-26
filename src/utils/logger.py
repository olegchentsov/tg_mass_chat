from loguru import logger
import os
import sys


def set_logger(log_file_path='chat.log', log_level="DEBUG"):
    # Если log_file_path находится в текущей директории, лог-директорию не создаем
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Удаление предыдущих обработчиков логов
    logger.remove()

    # Обработчик для терминала
    logger.add(
        sink=sys.stdout,  # Вывод в терминал
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{module}</cyan>.<cyan>{function}</cyan> | <level>{message}</level>",
        level=log_level
    )

    # Обработчик для файла
    logger.add(
        log_file_path,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{module}</cyan>.<cyan>{function}</cyan> | <level>{message}</level>",
        level=log_level,
        rotation="2 MB",
        compression="zip"
    )
    logger.debug("Логгер успешно настроен.")

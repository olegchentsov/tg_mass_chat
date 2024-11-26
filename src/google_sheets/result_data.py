import os
from loguru import logger
import pandas as pd


def save_result(result_path, result_row):
    """
    Сохраняет результаты обработки в Excel-файл.

    :param result_path: Путь к файлу Excel для сохранения результатов.
    :param result_row: Словарь с результатами, добавляемый в файл.
    """
    try:
        # Если файл уже существует, читаем его
        if os.path.exists(result_path):
            results_df = pd.read_excel(result_path)
        else:
            # Создаем новый DataFrame с нужными колонками
            results_df = pd.DataFrame(columns=[
                'mentor_name', 'mentor_usermane', 'mentor_chat', 'chat_link', 'mentor_add', 'message'
            ])

        # Добавляем новую строку
        new_row = pd.DataFrame([result_row])
        results_df = pd.concat([results_df, new_row], ignore_index=True)

        # Сохраняем результаты в Excel
        results_df.to_excel(result_path, index=False)
        logger.info(f"Результат успешно сохранён в файл '{result_path}'.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении результата: {e}")

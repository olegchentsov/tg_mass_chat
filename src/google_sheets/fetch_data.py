import pandas as pd
from loguru import logger


def fetch_mentors_data(excel_path):
    """
    Загружает данные о наставниках из Excel-файла и фильтрует активных наставников.

    :param excel_path: Путь к файлу Excel с данными наставников.
    :return: DataFrame с активными наставниками.
    """
    try:
        # Чтение данных из Excel
        logger.info(f"Попытка загрузить файл Excel: {excel_path}")
        df = pd.read_excel(excel_path)
        logger.info("Данные успешно загружены из Excel.")

        # Проверка наличия необходимых колонок
        required_columns = [
            'mentor_name', 'mentor_active', 'mentor_category', 'mentor_tg_username',
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}.")

        logger.info("Все необходимые колонки присутствуют.")

        # Фильтрация наставников, у которых mentor_active = "Да"
        active_mentors = df[df['mentor_active'].str.lower() == 'да']

        if active_mentors.empty:
            logger.warning("Нет активных наставников для создания чатов.")
            return None

        logger.info(f"Найдено {len(active_mentors)} активных наставников.")
        return active_mentors

    except FileNotFoundError:
        logger.error(f"Файл {excel_path} не найден. Пожалуйста, проверьте путь.")
    except Exception as e:
        logger.exception(f"Произошла ошибка при чтении файла: {e}")


# Пример использования
if __name__ == "__main__":
    mentors_data = fetch_mentors_data('TERRA.xlsx')
    if mentors_data is not None:
        logger.info(f"Загруженные данные:\n{mentors_data}")

Автоматизация создания чатов Telegram для наставников программы TERRA. 
Скрипт включает функции создания супергрупп, назначения администраторов, настройки чатов и отправки приветственных сообщений.

📋 Функционал
Создание Telegram-супергрупп с использованием Telethon.
Настройка группы: изменение прав, включение мультигрупп, добавление тем.
Назначение администраторов, включая проверку на ошибки приватности.
Формирование и сохранение результатов работы в Excel.
Генерация сообщений для отправки наставникам.

🛠️ Используемые библиотеки
pandas – для работы с Excel-файлами.
telethon – для взаимодействия с Telegram API.
PyYAML – для чтения конфигурационных файлов.
loguru – для логирования.
openpyxl – для работы с Excel-файлами через pandas.

📦 Установка
pip install -r requirements.txt

🚀 Запуск
Убедитесь, что у вас настроен файл config/secrets.yaml с вашими Telegram API-данными:

telegram:
  api_id: <ваш_api_id>
  api_hash: <ваш_api_hash>
  phone_number: <ваш_номер_телефона>

Убедитесь, что у вас есть файл Excel с данными наставников (по умолчанию: TERRA.xlsx на листе "Наставники").

Запустите скрипт:
python main.py

📂 Структура проекта

project-name/
├── config/
│   ├── secrets.yaml          # Конфиденциальные данные для Telegram API
│   └── settings.yaml         # Конфигурация приложения
├── sessions/                 # Сессии Telethon
├── google_sheets/
│   ├── fetch_data.py         # Загрузка данных из Excel
│   └── result_data.py        # Сохранение результатов работы
├── telegram/
│   ├── create_chats.py       # Создание чатов
│   ├── add_admins.py         # Назначение администраторов
│   └── configure_chats.py    # Настройка чатов
├── utils/
│   └── logger.py             # Настройка логирования
├── TERRA.xlsx                # Файл с данными наставников
├── TERRA_Results.xlsx        # Результаты выполнения
├── requirements.txt          # Зависимости проекта
└── main.py                   # Главный скрипт
# Парсер задач из PDF 

Программа читает PDF-файлы с задачами, выделяет суть с помощью нейросети, сохраняет в Excel, Google Sheets и Google Calendar.

## Возможности

- **Чтение PDF** — извлекает задачи из любого PDF-файла
- **Умная суммаризация** — нейросеть сокращает описание до главного
- **Excel** — сохраняет задачи в красивый отчёт
- **Google Sheets** — автоматически обновляет онлайн-таблицу
- **Google Calendar** — создаёт события из задач с датами

## Структура проекта

─ **credentials** - Сюда класть JSON-ключ 
─ **data** - Сюда класть PDF файлы
─ **output** - Сюда сохраняются Excel файлы
─ **src** - Исходный код
─ **.gitignore** - Что не загружать на GitHub
─ **README.md** - Это описание
─ **requirements.txt** - Зависимости
─ **run.py** - Запуск программы



##  Cтарт

## 1. Клонирование репозитория
git clone https://github.com/balancet1/pdf_task_parser.git
cd pdf_task_parser

2. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

3. Установить зависимости
pip install -r requirements.txt

4. Настроить Google API
4.1 Создать проект в Google Cloud Console или использовать уже существующий

4.2 Включить Google Sheets API и Google Calendar API (APIs & Services/Library, либо через поиск)

4.3 Создать сервисный аккаунт с ролью Editor - (APIs & Services/Credentials)/ +CREATE CREDENTIALS, выбрать 'Service account'. Далее выбрать созданный сервисный акк и создать ключ формата JSON

4.4 Скачать JSON-ключ и положить в credentials/google-credentials.json

4.5 Расшарить Google таблицу на email из JSON-ключа

4.6 Расшарить Google Calendar на тот же email

5. Запуск программы
# Только Excel
python3 run.py data/НАИМЕНОВАНИЕ_ФАЙЛА

# Excel + Google Sheets
python3 run.py data/tasks.pdf --sheets "ССЫЛКА_НА_ГУГЛ_ТАБЛИЦУ"

# Excel + Google Calendar
python3 run.py data/tasks.pdf --calendar "ТВОЙ-email@gmail.com"

# Всё вместе
python3 run.py data/tasks.pdf --sheets "URL" --calendar "ID"

# Несколько PDF-файлов из папки data сразу
python3 run_all.py

## Для запуска без суммаризации нужно добавить флаг **--no-summary** ##
(python3 run.py data/tasks.pdf --no-summary)





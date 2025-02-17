# Платформа для онлайн-обучения сотрудников предприятия

## Установка и запуск

Следуйте этим шагам, чтобы запустить проект на вашем локальном компьютере.

### 1. Клонирование репозитория

Склонируйте репозиторий на ваш компьютер:

```bash
git clone git@github.com:artem213101zse/my_edycation_platform.git
cd my_edycation_platform
```

### 2. Создайте и активируйте виртуальное окружение для изоляции зависимостей:

```bash
python -m venv venv
venv\Scripts\activate # Для Windows
source venv/bin/activate # Для Linux
```

### 3. Установка зависимостей
Установите необходимые зависимости из файла requirements.txt:

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных
Выполните миграции для настройки базы данных:

```bash
python manage.py migrate
```

### 5. Создание суперпользователя (опционально)
Если вам нужен доступ к админке Django, создайте суперпользователя:

```bash
python manage.py createsuperuser
```

### 6. Запуск сервера разработки
Запустите сервер разработки:

```bash
python manage.py runserver
```

Сайт будет доступен по адресу: http://127.0.0.1:8000/.

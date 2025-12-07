#!/bin/bash
# Скрипт для запуска приложения

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Проверка установленных зависимостей
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "Установка зависимостей..."
    pip install -r requirements.txt
fi

# Запуск приложения
echo "Запуск приложения..."
python3 main.py


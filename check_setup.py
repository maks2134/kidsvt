#!/usr/bin/env python3
"""
Скрипт для проверки установки зависимостей
"""
import sys

def check_imports():
    """Проверка импортов всех модулей"""
    errors = []
    
    # Проверка внешних зависимостей
    try:
        import PyQt6
        print("✓ PyQt6 установлен")
    except ImportError:
        errors.append("PyQt6 не установлен. Установите: pip install PyQt6")
    
    try:
        import numpy
        print("✓ NumPy установлен")
    except ImportError:
        errors.append("NumPy не установлен. Установите: pip install numpy")
    
    try:
        import matplotlib
        print("✓ Matplotlib установлен")
    except ImportError:
        errors.append("Matplotlib не установлен. Установите: pip install matplotlib")
    
    # Проверка внутренних модулей
    try:
        import ram_model
        print("✓ ram_model.py импортирован успешно")
    except Exception as e:
        errors.append(f"Ошибка импорта ram_model.py: {e}")
    
    try:
        import fault_models
        print("✓ fault_models.py импортирован успешно")
    except Exception as e:
        errors.append(f"Ошибка импорта fault_models.py: {e}")
    
    try:
        import testing_algorithms
        print("✓ testing_algorithms.py импортирован успешно")
    except Exception as e:
        errors.append(f"Ошибка импорта testing_algorithms.py: {e}")
    
    try:
        import verification
        print("✓ verification.py импортирован успешно")
    except Exception as e:
        errors.append(f"Ошибка импорта verification.py: {e}")
    
    if errors:
        print("\n❌ Обнаружены ошибки:")
        for error in errors:
            print(f"  • {error}")
        print("\nУстановите зависимости командой:")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("\n✓ Все проверки пройдены успешно!")
        print("Приложение готово к запуску: python3 main.py")
        return True

if __name__ == '__main__':
    success = check_imports()
    sys.exit(0 if success else 1)




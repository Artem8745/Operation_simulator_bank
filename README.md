# Запуск Django приложения

## Требования
- Python 3.11.9
- Зависимости из requirements.txt

## Запуск приложения

1. **Установите Python 3.11.9**
2. **Создайте виртуальное окружение:**
   ```
   py -m venv venv
   venv\Scripts\activate
   ```
4. **Установите зависимости:**
   ```
   pip install -r requirements.txt
   ```
6. **Перейдите в папку backend и запустите миграции:**
   ```
   cd backend
   py manage.py migrate
   ```
8. **Запустите сервер:**
   ```
   py manage.py runserver
   ```

Приложение доступно по адресу: http://127.0.0.1:8000

## Дополнительные команды
Все действия производятся в папке backend
    ```
    cd backend
    ```
    
1. **Создание суперпользователя:**
    ```
    py create_admin.py
    ```

3. **Создание валют:**
    ```
    py create_exchange_rates.py
    ```

4. **Создание тестовых пользователей:**
   ```
   python create_test_data.py
   ```


import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cassa.settings')
django.setup()

from django.contrib.auth.models import User
from getpass import getpass

def get_user_input():
    """Функция для получения данных от пользователя"""
    print("Создание администратора")
    print("-" * 30)
    
    username = input("Введите имя пользователя (по умолчанию: admin): ").strip()
    if not username:
        username = 'admin'
    
    email = input("Введите email (по умолчанию: admin@example.com): ").strip()
    if not email:
        email = 'admin@example.com'
    
    while True:
        password = getpass("Введите пароль: ").strip()
        if not password:
            print("Пароль не может быть пустым!")
            continue
        
        password_confirm = getpass("Подтвердите пароль: ").strip()
        if password == password_confirm:
            break
        else:
            print("Пароли не совпадают! Попробуйте снова.")
    
    return username, email, password

def create_admin_user():
    # Получаем данные от пользователя
    username, email, password = get_user_input()
    
    # Проверяем, существует ли пользователь с таким username
    if User.objects.filter(username=username).exists():
        print(f"\nПользователь с именем '{username}' уже существует.")
        overwrite = input("Хотите обновить данные? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Операция отменена.")
            return
    
    # Получаем или создаем пользователя
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    if created:
        # Если пользователь создан, устанавливаем пароль
        user.set_password(password)
        user.save()
        print(f"\n Суперпользователь создан!")
        print(f"   Имя пользователя: {username}")
        print(f"   Email: {email}")
    else:
        # Если пользователь уже существует, обновляем его данные
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        print(f"\n Суперпользователь обновлен!")
        print(f"   Имя пользователя: {username}")
        print(f"   Email: {email}")

if __name__ == '__main__':
    create_admin_user()
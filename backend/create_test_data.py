import os
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cassa.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import Client, Account, Transaction

def create_test_data():
    # Очистка старых данных (осторожно!)
    print("Очистка старых данных...")
    
    # Удаляем в правильном порядке из-за foreign key constraints
    Transaction.objects.all().delete()
    Account.objects.all().delete()
    
    # Удаляем только клиентов, связанных с не-суперпользователями
    Client.objects.filter(user__is_superuser=False).delete()
    
    # Удаляем только обычных пользователей (не суперпользователей)
    User.objects.filter(is_superuser=False).delete()
    
    print("Создание тестовых пользователей...")
    # Создание тестовых пользователей
    users_data = [
        {'username': 'user1', 'email': 'ivan@mail.ru', 'password': 'password123'},
        {'username': 'user2', 'email': 'maria@mail.ru', 'password': 'password123'},
        {'username': 'user3', 'email': 'alex@mail.ru', 'password': 'password123'},
        {'username': 'user4', 'email': 'elena@mail.ru', 'password': 'password123'},
        {'username': 'user5', 'email': 'dmitry@mail.ru', 'password': 'password123'},
        {'username': '1', 'email': 'test@mail.ru', 'password': '123'},
    ]
    
    users = []
    for user_data in users_data:
        try:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            users.append(user)
            print(f"Создан пользователь: {user.username}")
        except Exception as e:
            print(f"Ошибка при создании пользователя {user_data['username']}: {e}")
            continue
    
    print("Обновление данных клиентов...")
    # Данные для клиентов
    clients_data = [
        {"name": "Иван Петров", "phone": "+79161234567"},
        {"name": "Мария Сидорова", "phone": "+79167654321"},
        {"name": "Алексей Козлов", "phone": "+79169998877"},
        {"name": "Елена Новикова", "phone": "+79165554433"},
        {"name": "Дмитрий Волков", "phone": "+79163332211"},
        {"name": "Алексей Павлов", "phone": "+79163457634"},
    ]
    
    clients = []
    for i, user in enumerate(users):
        try:
            # Получаем существующего клиента (созданного автоматически через сигнал)
            client = Client.objects.get(user=user)
            # Обновляем данные клиента
            client.name = clients_data[i]['name']
            client.phone = clients_data[i]['phone']
            client.email = user.email
            client.save()
            clients.append(client)
            print(f"Обновлен клиент: {client.name}")
        except Client.DoesNotExist:
            print(f"Клиент для пользователя {user.username} не найден, создаем...")
            try:
                client = Client.objects.create(
                    user=user,
                    name=clients_data[i]['name'],
                    phone=clients_data[i]['phone'],
                    email=user.email
                )
                clients.append(client)
                print(f"Создан клиент: {client.name}")
            except Exception as e:
                print(f"Ошибка при создании клиента для {user.username}: {e}")
                continue
        except Exception as e:
            print(f"Ошибка при обновлении клиента для {user.username}: {e}")
            continue
    
    # Проверяем, что у нас есть клиенты для работы
    if not clients:
        print(" Нет клиентов для создания счетов! Прерывание...")
        return
    
    print("Создание счетов...")
    # Создание счетов
    accounts = []
    currencies = ['RUB', 'USD', 'EUR']
    
    for i, client in enumerate(clients):
        try:
            # Создаем основной счет в RUB
            account = Account.objects.create(
                client=client,
                balance=Decimal(str(round(random.uniform(1000, 50000), 2))),
                currency='RUB'
            )
            accounts.append(account)
            print(f"Создан счет: {account.account_number} для {client.name}, баланс: {account.balance} {account.currency}")
            
            # Создаем дополнительный счет в другой валюте для некоторых пользователей
            if i % 2 == 0:  # Каждому второму пользователю
                secondary_currency = random.choice([c for c in currencies if c != 'RUB'])
                secondary_account = Account.objects.create(
                    client=client,
                    balance=Decimal(str(round(random.uniform(100, 5000), 2))),
                    currency=secondary_currency
                )
                accounts.append(secondary_account)
                print(f"Создан дополнительный счет: {secondary_account.account_number} для {client.name}, баланс: {secondary_account.balance} {secondary_account.currency}")
                
        except Exception as e:
            print(f"Ошибка при создании счета для {client.name}: {e}")
            continue
    
    # Проверяем, что у нас есть счета для работы
    if not accounts:
        print(" Нет счетов для создания транзакций! Прерывание...")
        return
    
    print("Создание транзакций...")
    # Создание тестовых транзакций с разными датами
    transactions_created = 0
    base_date = datetime.now()
    
    for i in range(50):  # Увеличим количество транзакций
        try:
            account = random.choice(accounts)
            transaction_type = random.choice(['deposit', 'withdraw', 'transfer'])
            amount = Decimal(str(round(random.uniform(100, 5000), 2)))
            
            # Создаем дату для транзакции (от 1 дня до 30 дней назад)
            transaction_date = base_date - timedelta(days=random.randint(1, 30))
            
            if transaction_type == 'transfer':
                # Выбираем другой счет для перевода (только в той же валюте)
                other_accounts = [acc for acc in accounts if acc != account and acc.currency == account.currency]
                if not other_accounts:
                    print(f"Пропуск перевода: нет других счетов в валюте {account.currency}")
                    continue
                    
                to_account = random.choice(other_accounts)
                
                # Проверяем достаточно ли средств
                if account.balance >= amount:
                    # Транзакция для отправителя
                    transaction_from = Transaction.objects.create(
                        account=account,
                        amount=amount,
                        type='transfer',
                        description=f"Перевод на счет {to_account.account_number}",
                        from_account=account,
                        to_account=to_account
                    )
                    # Устанавливаем кастомную дату
                    transaction_from.timestamp = transaction_date
                    transaction_from.save()
                    
                    # Транзакция для получателя
                    transaction_to = Transaction.objects.create(
                        account=to_account,
                        amount=amount,
                        type='transfer',
                        description=f"Перевод со счета {account.account_number}",
                        from_account=account,
                        to_account=to_account
                    )
                    # Устанавливаем ту же дату
                    transaction_to.timestamp = transaction_date
                    transaction_to.save()
                    
                    # Обновляем балансы
                    account.balance -= amount
                    account.save()
                    to_account.balance += amount
                    to_account.save()
                    
                    transactions_created += 2
                    print(f"Создан перевод #{i+1}: {amount} {account.currency} с {account.account_number} на {to_account.account_number}")
                else:
                    print(f"Пропуск перевода: недостаточно средств на счете {account.account_number}")
                    
            else:
                if transaction_type == 'deposit':
                    account.balance += amount
                    description = "Пополнение счета"
                elif transaction_type == 'withdraw':
                    if account.balance >= amount:
                        account.balance -= amount
                        description = "Снятие наличных"
                    else:
                        print(f"Пропуск снятия: недостаточно средств на счете {account.account_number}")
                        continue  # Пропускаем если недостаточно средств
                
                account.save()
                
                transaction = Transaction.objects.create(
                    account=account,
                    amount=amount,
                    type=transaction_type,
                    description=description
                )
                # Устанавливаем кастомную дату
                transaction.timestamp = transaction_date
                transaction.save()
                
                transactions_created += 1
                print(f"Создана транзакция #{i+1}: {transaction_type} на сумму {amount} {account.currency} для счета {account.account_number}")
                
        except Exception as e:
            print(f"Ошибка при создании транзакции: {e}")
            continue
    
    print("\n" + "="*50)
    print("Тестовые данные созданы успешно!")
    print("="*50)
    
    # Детальная статистика
    print(f"\nДетальная статистика:")
    print(f"   Пользователей: {User.objects.filter(is_superuser=False).count()}")
    print(f"   Клиентов: {Client.objects.count()}")
    print(f"   Счетов: {Account.objects.count()}")
    print(f"   Транзакций: {Transaction.objects.count()}")
    
    # Статистика по валютам
    print(f"\n Распределение счетов по валютам:")
    for currency in currencies:
        count = Account.objects.filter(currency=currency).count()
        if count > 0:
            total_balance = sum(acc.balance for acc in Account.objects.filter(currency=currency))
            print(f"   {currency}: {count} счетов, общий баланс: {total_balance:.2f}")
    
    # Вывод информации для тестирования
    print("\n Тестовые учетные данные:")
    print("-" * 50)
    for user in users:
        user_accounts = Account.objects.filter(client__user=user)
        print(f"Логин: {user.username}")
        print(f"Пароль: password123")
        print(f"Email: {user.email}")
        print(f"Клиент: {user.client.name if hasattr(user, 'client') else 'Нет клиента'}")
        print(f"Счета:")
        for acc in user_accounts:
            print(f"  - {acc.account_number}: {acc.balance} {acc.currency} (создан: {acc.created_at.strftime('%d.%m.%Y %H:%M')})")
        print("-" * 50)

if __name__ == '__main__':
    create_test_data()
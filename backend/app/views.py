from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction as db_transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Account, Transaction, Client, ExchangeRate
from django.db import models
from .forms import UserRegisterForm
from decimal import Decimal
import json
import random

# Проверка на staff пользователя
def staff_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url='/api/admin/denied/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

# Аутентификация
def login_view(request):
    """Страница входа"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Перенаправляем в зависимости от прав пользователя
            if user.is_staff:
                return redirect('/api/admin-panel/')
            else:
                return redirect('/api/dashboard/')
        else:
            return render(request, 'login.html', {'error': 'Неверное имя пользователя или пароль'})
    
    return render(request, 'login.html')

def register_view(request):
    """Страница регистрации"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Автоматический вход после регистрации
            login(request, user)
            return redirect('/api/dashboard/')
    else:
        form = UserRegisterForm()
    
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('/api/auth/login/')

# Основные страницы
@login_required
def dashboard_view(request):
    """Главная страница после входа"""
    return render(request, 'dashboard.html')

@login_required
def admin_panel_view(request):
    """Админ-панель (только для staff)"""
    if not request.user.is_staff:
        return render(request, 'admin_denied.html', {
            'message': 'У вас нет прав доступа к админ-панели'
        }, status=403)
    
    # Получаем данные для админ-панели
    try:
        accounts_count = Account.objects.count()
        clients_count = Client.objects.count()
        transactions_count = Transaction.objects.count()
        active_accounts = Account.objects.filter(is_active=True).count()
        
        # Для начального отображения используем только базовую статистику
        # Транзакции будут загружаться через JavaScript
        
        context = {
            'accounts_count': accounts_count,
            'clients_count': clients_count,
            'transactions_count': transactions_count,
            'active_accounts': active_accounts,
            'total_transactions_count': transactions_count,
        }
        
        return render(request, 'admin_panel.html', context)
        
    except Exception as e:
        print(f"Ошибка в admin_panel_view: {str(e)}")
        return render(request, 'admin_panel.html', {
            'error': f'Ошибка загрузки данных: {str(e)}',
            'accounts_count': 0,
            'clients_count': 0,
            'transactions_count': 0,
            'active_accounts': 0,
            'total_transactions_count': 0,
        })
    """Админ-панель (только для staff)"""
    if not request.user.is_staff:
        return render(request, 'admin_denied.html', {
            'message': 'У вас нет прав доступа к админ-панели'
        }, status=403)
    
    # Получаем данные для админ-панели
    try:
        accounts_count = Account.objects.count()
        clients_count = Client.objects.count()
        transactions_count = Transaction.objects.count()
        active_accounts = Account.objects.filter(is_active=True).count()
        
        # Последние транзакции с ограничением (по умолчанию 5)
        recent_limit = 5  # Ограничение для начального отображения
        recent_transactions = Transaction.objects.select_related(
            'account__client', 'from_account', 'to_account'
        ).order_by('-timestamp')[:recent_limit]
        
        # Обрабатываем транзакции для правильного отображения валют
        processed_transactions = []
        for trans in recent_transactions:
            # Определяем правильную валюту
            display_currency = trans.account.currency
            display_amount = trans.amount
            
            if trans.type == 'transfer':
                if trans.from_account and trans.from_account.id == trans.account.id:
                    # Исходящий перевод
                    display_currency = trans.from_account.currency
                elif trans.to_account and trans.to_account.id == trans.account.id:
                    # Входящий перевод
                    display_currency = trans.to_account.currency
            
            processed_transactions.append({
                'transaction': trans,
                'display_currency': display_currency,
                'display_amount': display_amount,
                'is_incoming': trans.description and '←' in trans.description if trans.type == 'transfer' else False
            })
        
        context = {
            'accounts_count': accounts_count,
            'clients_count': clients_count,
            'transactions_count': transactions_count,
            'active_accounts': active_accounts,
            'processed_transactions': processed_transactions,
            'recent_limit': recent_limit,
            'total_transactions_count': transactions_count,
        }
        
        return render(request, 'admin_panel.html', context)
        
    except Exception as e:
        print(f"Ошибка в admin_panel_view: {str(e)}")
        return render(request, 'admin_panel.html', {
            'error': f'Ошибка загрузки данных: {str(e)}',
            'accounts_count': 0,
            'clients_count': 0,
            'transactions_count': 0,
            'active_accounts': 0,
            'processed_transactions': [],
            'recent_limit': 5,
            'total_transactions_count': 0,
        })
    """Админ-панель (только для staff)"""
    if not request.user.is_staff:
        return render(request, 'admin_denied.html', {
            'message': 'У вас нет прав доступа к админ-панели'
        }, status=403)
    
    # Получаем данные для админ-панели
    try:
        accounts_count = Account.objects.count()
        clients_count = Client.objects.count()
        transactions_count = Transaction.objects.count()
        active_accounts = Account.objects.filter(is_active=True).count()
        
        # Последние транзакции
        recent_transactions = Transaction.objects.select_related(
            'account__client', 'from_account', 'to_account'
        ).order_by('-timestamp')[:10]
        
        context = {
            'accounts_count': accounts_count,
            'clients_count': clients_count,
            'transactions_count': transactions_count,
            'active_accounts': active_accounts,
            'recent_transactions': recent_transactions,
        }
        
        return render(request, 'admin_panel.html', context)
        
    except Exception as e:
        print(f"Ошибка в admin_panel_view: {str(e)}")
        return render(request, 'admin_panel.html', {
            'error': f'Ошибка загрузки данных: {str(e)}',
            'accounts_count': 0,
            'clients_count': 0,
            'transactions_count': 0,
            'active_accounts': 0,
            'recent_transactions': []
        })

# API endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_accounts(request):
    """Получить счета текущего пользователя"""
    try:
        # Для администраторов возвращаем все счета
        if request.user.is_staff or request.user.is_superuser:
            accounts = Account.objects.filter(is_active=True)[:10]  # Ограничим для производительности
            accounts_data = []
            for acc in accounts:
                accounts_data.append({
                    'id': acc.id,
                    'account_number': acc.account_number,
                    'client_name': acc.client.name,
                    'balance': float(acc.balance),
                    'currency': acc.currency,
                    'created_at': acc.created_at.isoformat(),  # Добавляем дату создания
                    'is_active': acc.is_active
                })
            return Response(accounts_data)
        
        # Для обычных пользователей
        try:
            client = request.user.client
        except Client.DoesNotExist:
            # Если у пользователя нет клиента, создаем его
            client = Client.objects.create(
                user=request.user,
                name=request.user.username,
                email=request.user.email
            )
        
        accounts = Account.objects.filter(client=client, is_active=True)
        accounts_data = []
        for acc in accounts:
            accounts_data.append({
                'id': acc.id,
                'account_number': acc.account_number,
                'client_name': acc.client.name,
                'balance': float(acc.balance),
                'currency': acc.currency,
                'created_at': acc.created_at.isoformat(),  # Добавляем дату создания
                'is_active': acc.is_active
            })
        return Response(accounts_data)
        
    except Exception as e:
        print(f"Ошибка в get_user_accounts: {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_account_detail(request, account_id):
    """Получить детальную информацию о счете"""
    try:
        # Для администраторов разрешаем доступ ко всем счетам
        if request.user.is_staff or request.user.is_superuser:
            account = Account.objects.get(id=account_id, is_active=True)
        else:
            # Для обычных пользователей - только свои счета
            try:
                client = request.user.client
            except Client.DoesNotExist:
                return Response({'error': 'Профиль клиента не найден'}, status=status.HTTP_404_NOT_FOUND)
            
            account = Account.objects.get(id=account_id, client=client, is_active=True)
        
        transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:20]
        
        transactions_data = []
        for trans in transactions:
            # Для каждой транзакции используем валюту счета, к которому она привязана
            display_currency = trans.account.currency
            
            transactions_data.append({
                'id': trans.id,
                'amount': float(trans.amount),
                'type': trans.type,
                'type_display': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': display_currency,  # Валюта счета транзакции
                'from_currency': trans.from_account.currency if trans.from_account else None,
                'to_currency': trans.to_account.currency if trans.to_account else None,
            })
        
        account_data = {
            'id': account.id,
            'account_number': account.account_number,
            'client_name': account.client.name,
            'client_phone': account.client.phone,
            'client_email': account.client.email,
            'balance': float(account.balance),
            'currency': account.currency,
            'created_at': account.created_at.isoformat(),  # Добавляем дату создания
            'is_active': account.is_active,
            'transactions': transactions_data
        }
        return Response(account_data)
    except Account.DoesNotExist:
        return Response({'error': 'Счет не найден или у вас нет доступа'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Ошибка в get_account_detail: {str(e)}")
        return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_account(request):
    """Создать новый счет для текущего пользователя"""
    try:
        data = request.data
        currency = data.get('currency', 'RUB')
        
        # Проверяем доступные валюты
        available_currencies = ['RUB', 'USD', 'EUR']
        if currency not in available_currencies:
            return Response({
                'error': f'Недопустимая валюта. Доступные валюты: {", ".join(available_currencies)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Получаем клиента
        try:
            client = request.user.client
        except Client.DoesNotExist:
            # Если у пользователя нет клиента, создаем его
            client = Client.objects.create(
                user=request.user,
                name=request.user.username,
                email=request.user.email
            )
        
        # Создаем счет
        account = Account.objects.create(
            client=client,
            balance=Decimal('0.00'),
            currency=currency
        )
        
        return Response({
            'success': True,
            'message': 'Счет успешно создан',
            'account': {
                'id': account.id,
                'account_number': account.account_number,
                'currency': account.currency,
                'balance': float(account.balance),
                'created_at': account.created_at.isoformat(),  # Добавляем дату создания
                'is_active': account.is_active
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit(request):
    """Пополнение счета"""
    try:
        data = request.data
        account_id = data.get('account_id')
        amount = Decimal(str(data.get('amount')))
        description = data.get('description', 'Пополнение счета')
        
        if amount <= 0:
            return Response({'error': 'Сумма должна быть положительной'}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            # Для администраторов разрешаем операции со всеми счетами
            if request.user.is_staff or request.user.is_superuser:
                account = Account.objects.select_for_update().get(
                    id=account_id,
                    is_active=True
                )
            else:
                # Для обычных пользователей - только свои счета
                try:
                    client = request.user.client
                except Client.DoesNotExist:
                    return Response({'error': 'Профиль клиента не найден'}, status=status.HTTP_404_NOT_FOUND)
                
                account = Account.objects.select_for_update().get(
                    id=account_id, 
                    client=client,
                    is_active=True
                )
            
            account.balance += amount
            account.save()
            
            transaction = Transaction.objects.create(
                account=account,
                amount=amount,
                type='deposit',
                description=description
            )
            
            return Response({
                'success': True,
                'message': 'Счет успешно пополнен',
                'new_balance': float(account.balance),
                'transaction_id': transaction.id
            })
            
    except Account.DoesNotExist:
        return Response({'error': 'Счет не найден или у вас нет доступа'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Ошибка в deposit: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw(request):
    """Снятие со счета"""
    try:
        data = request.data
        account_id = data.get('account_id')
        amount = Decimal(str(data.get('amount')))
        description = data.get('description', 'Снятие наличных')
        
        if amount <= 0:
            return Response({'error': 'Сумма должна быть положительной'}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            # Для администраторов разрешаем операции со всеми счетами
            if request.user.is_staff or request.user.is_superuser:
                account = Account.objects.select_for_update().get(
                    id=account_id,
                    is_active=True
                )
            else:
                # Для обычных пользователей - только свои счета
                try:
                    client = request.user.client
                except Client.DoesNotExist:
                    return Response({'error': 'Профиль клиента не найден'}, status=status.HTTP_404_NOT_FOUND)
                
                account = Account.objects.select_for_update().get(
                    id=account_id, 
                    client=client,
                    is_active=True
                )
            
            if account.balance < amount:
                return Response({'error': 'Недостаточно средств на счете'}, status=status.HTTP_400_BAD_REQUEST)
            
            account.balance -= amount
            account.save()
            
            transaction = Transaction.objects.create(
                account=account,
                amount=amount,
                type='withdraw',
                description=description
            )
            
            return Response({
                'success': True,
                'message': 'Средства успешно сняты',
                'new_balance': float(account.balance),
                'transaction_id': transaction.id
            })
            
    except Account.DoesNotExist:
        return Response({'error': 'Счет не найден или у вас нет доступа'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Ошибка в withdraw: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer(request):
    """Перевод между счетами с конвертацией валют"""
    try:
        data = request.data
        from_account_id = data.get('from_account_id')
        to_account_number = data.get('to_account_number')
        amount = Decimal(str(data.get('amount')))
        description = data.get('description', 'Перевод средств')
        
        if amount <= 0:
            return Response({'error': 'Сумма должна быть положительной'}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            # Проверяем что счет отправителя доступен пользователю
            if request.user.is_staff or request.user.is_superuser:
                from_account = Account.objects.select_for_update().get(
                    id=from_account_id,
                    is_active=True
                )
            else:
                try:
                    client = request.user.client
                except Client.DoesNotExist:
                    return Response({'error': 'Профиль клиента не найден'}, status=status.HTTP_404_NOT_FOUND)
                
                from_account = Account.objects.select_for_update().get(
                    id=from_account_id, 
                    client=client,
                    is_active=True
                )
            
            # Ищем счет получателя по номеру
            try:
                to_account = Account.objects.select_for_update().get(
                    account_number=to_account_number,
                    is_active=True
                )
            except Account.DoesNotExist:
                return Response({'error': 'Счет получателя не найден'}, status=status.HTTP_404_NOT_FOUND)
            
            if from_account.balance < amount:
                return Response({'error': 'Недостаточно средств для перевода'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем курс обмена
            exchange_rate = get_exchange_rate(from_account.currency, to_account.currency)
            converted_amount = amount * exchange_rate
            
            # Снимаем с отправителя
            from_account.balance -= amount
            from_account.save()
            
            # Зачисляем получателю с конвертацией
            to_account.balance += converted_amount
            to_account.save()
            
            # Создаем транзакцию для отправителя (в его валюте)
            transaction_from = Transaction.objects.create(
                account=from_account,
                amount=amount,  # Сумма в валюте отправителя
                type='transfer',
                description=f"{description} → {to_account.account_number} (курс: {exchange_rate:.4f})",
                from_account=from_account,
                to_account=to_account
            )
            
            # Создаем транзакцию для получателя (в его валюте)
            transaction_to = Transaction.objects.create(
                account=to_account,
                amount=converted_amount,  # Сумма в валюте получателя
                type='transfer',
                description=f"{description} ← {from_account.account_number} (курс: {exchange_rate:.4f})",
                from_account=from_account,
                to_account=to_account
            )
            
            return Response({
                'success': True,
                'message': f'Перевод выполнен успешно. Курс: {exchange_rate:.4f}',
                'from_account_balance': float(from_account.balance),
                'to_account_balance': float(to_account.balance),
                'exchange_rate': float(exchange_rate),
                'converted_amount': float(converted_amount),
                'transaction_id': transaction_from.id
            })
            
    except Account.DoesNotExist:
        return Response({'error': 'Счет не найден или у вас нет доступа'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Ошибка в transfer: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_exchange_rate(from_currency, to_currency):
    """Получить курс обмена между валютами"""
    if from_currency == to_currency:
        return Decimal('1.0')
    
    try:
        # Прямой курс
        rate = ExchangeRate.objects.get(
            from_currency=from_currency, 
            to_currency=to_currency
        )
        return rate.rate
    except ExchangeRate.DoesNotExist:
        try:
            # Обратный курс
            reverse_rate = ExchangeRate.objects.get(
                from_currency=to_currency, 
                to_currency=from_currency
            )
            return Decimal('1.0') / reverse_rate.rate
        except ExchangeRate.DoesNotExist:
            # Курс по умолчанию (можно заменить на API)
            default_rates = {
                ('RUB', 'USD'): Decimal('0.011'),
                ('RUB', 'EUR'): Decimal('0.009'),
                ('USD', 'RUB'): Decimal('90.0'),
                ('USD', 'EUR'): Decimal('0.85'),
                ('EUR', 'RUB'): Decimal('110.0'),
                ('EUR', 'USD'): Decimal('1.18'),
            }
            return default_rates.get((from_currency, to_currency), Decimal('1.0'))

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_all_transactions(request):
    """Получить все транзакции (только для администраторов)"""
    try:
        transactions = Transaction.objects.select_related('account__client', 'from_account', 'to_account').order_by('-timestamp')[:100]
        
        transactions_data = []
        for trans in transactions:
            # Определяем правильную валюту для отображения
            display_currency = trans.account.currency
            
            # Для переводов определяем правильную валюту
            if trans.type == 'transfer':
                if trans.from_account and trans.from_account.id == trans.account.id:
                    # Исходящий перевод - показываем в валюте отправителя
                    display_currency = trans.from_account.currency
                elif trans.to_account and trans.to_account.id == trans.account.id:
                    # Входящий перевод - показываем в валюте получателя
                    display_currency = trans.to_account.currency
            
            transactions_data.append({
                'id': trans.id,
                'account_number': trans.account.account_number,
                'client_name': trans.account.client.name,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': display_currency,  # Правильная валюта для отображения
                'from_currency': trans.from_account.currency if trans.from_account else None,
                'to_currency': trans.to_account.currency if trans.to_account else None,
            })
        
        return Response(transactions_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    """Получить все транзакции (только для администраторов)"""
    try:
        transactions = Transaction.objects.select_related('account__client', 'from_account', 'to_account').order_by('-timestamp')[:100]
        
        transactions_data = []
        for trans in transactions:
            # Определяем правильную валюту для отображения
            display_currency = trans.account.currency
            
            # Для переводов определяем правильную валюту
            if trans.type == 'transfer':
                if trans.from_account and trans.from_account.id == trans.account.id:
                    # Исходящий перевод - показываем в валюте отправителя
                    display_currency = trans.from_account.currency
                elif trans.to_account and trans.to_account.id == trans.account.id:
                    # Входящий перевод - показываем в валюте получателя
                    display_currency = trans.to_account.currency
            
            transactions_data.append({
                'id': trans.id,
                'account_number': trans.account.account_number,
                'client_name': trans.account.client.name,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': display_currency,  # Правильная валюта для отображения
            })
        
        return Response(transactions_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    """Получить все транзакции (только для администраторов)"""
    try:
        transactions = Transaction.objects.select_related('account__client', 'from_account', 'to_account').order_by('-timestamp')[:100]
        
        transactions_data = []
        for trans in transactions:
            transactions_data.append({
                'id': trans.id,
                'account_number': trans.account.account_number,
                'client_name': trans.account.client.name,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': trans.account.currency,  # Добавляем валюту счета
            })
        
        return Response(transactions_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_recent_transactions(request):
    """Получить последние транзакции для админ-панели с ограничением количества"""
    try:
        # Получаем параметр limit из запроса (по умолчанию 10)
        limit = request.GET.get('limit', 10)
        try:
            limit = int(limit)
            # Ограничиваем максимальное количество
            if limit > 4000:
                limit = 4000
            elif limit < 1:
                limit = 10
        except (ValueError, TypeError):
            limit = 10
        
        transactions = Transaction.objects.select_related(
            'account__client', 
            'from_account', 
            'to_account'
        ).order_by('-timestamp')[:limit]
        
        transactions_data = []
        for trans in transactions:
            # Определяем правильную валюту для отображения
            display_currency = trans.account.currency
            
            # Для переводов определяем правильную валюту
            if trans.type == 'transfer':
                if trans.from_account and trans.from_account.id == trans.account.id:
                    # Исходящий перевод - показываем в валюте отправителя
                    display_currency = trans.from_account.currency
                elif trans.to_account and trans.to_account.id == trans.account.id:
                    # Входящий перевод - показываем в валюте получателя
                    display_currency = trans.to_account.currency
            
            transactions_data.append({
                'id': trans.id,
                'account_number': trans.account.account_number,
                'client_name': trans.account.client.name,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': display_currency,
                'from_currency': trans.from_account.currency if trans.from_account else None,
                'to_currency': trans.to_account.currency if trans.to_account else None,
            })
        
        return Response({
            'transactions': transactions_data,
            'total_count': len(transactions_data),
            'limit': limit
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    """Получить последние транзакции для админ-панели"""
    try:
        transactions = Transaction.objects.select_related(
            'account__client', 
            'from_account', 
            'to_account'
        ).order_by('-timestamp')[:10]  # Последние 10 транзакций
        
        transactions_data = []
        for trans in transactions:
            # Определяем правильную валюту для отображения
            display_currency = trans.account.currency
            
            # Для переводов определяем правильную валюту
            if trans.type == 'transfer':
                if trans.from_account and trans.from_account.id == trans.account.id:
                    # Исходящий перевод - показываем в валюте отправителя
                    display_currency = trans.from_account.currency
                elif trans.to_account and trans.to_account.id == trans.account.id:
                    # Входящий перевод - показываем в валюте получателя
                    display_currency = trans.to_account.currency
            
            transactions_data.append({
                'id': trans.id,
                'account_number': trans.account.account_number,
                'client_name': trans.account.client.name,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': display_currency,
                'from_currency': trans.from_account.currency if trans.from_account else None,
                'to_currency': trans.to_account.currency if trans.to_account else None,
            })
        
        return Response(transactions_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_all_accounts(request):
    """Получить все счета (только для администраторов)"""
    try:
        accounts = Account.objects.select_related('client').filter(is_active=True)
        accounts_data = []
        for acc in accounts:
            accounts_data.append({
                'id': acc.id,
                'account_number': acc.account_number,
                'client_name': acc.client.name,
                'client_email': acc.client.email,
                'balance': float(acc.balance),
                'currency': acc.currency,
                'created_at': acc.created_at.isoformat(),  # Добавляем дату создания
                'is_active': acc.is_active
            })
        return Response(accounts_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_accounts(request):
    """Поиск счетов по номеру (для переводов)"""
    try:
        query = request.GET.get('q', '')
        if len(query) < 4:
            return Response({'error': 'Введите минимум 4 символа для поиска'}, status=400)
        
        accounts = Account.objects.filter(
            account_number__icontains=query,
            is_active=True
        ).exclude(client=request.user.client)[:10]
        
        accounts_data = []
        for acc in accounts:
            accounts_data.append({
                'account_number': acc.account_number,
                'client_name': acc.client.name,
            })
        
        return Response(accounts_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_check(request):
    """Проверка прав администратора"""
    return Response({
        'is_admin': True,
        'user': request.user.username,
        'message': 'Доступ разрешен'
    })

@api_view(['GET'])
def api_test(request):
    """Тест всех API endpoints"""
    endpoints = {
        'admin_transactions': '/api/admin/transactions/',
        'admin_accounts': '/api/admin/accounts/',
        'user_accounts': '/api/accounts/my/',
        'admin_check': '/api/admin/check/',
    }
    return Response({
        'message': 'API тест',
        'endpoints': endpoints,
        'user': {
            'is_authenticated': request.user.is_authenticated,
            'username': request.user.username if request.user.is_authenticated else None,
            'is_staff': request.user.is_staff if request.user.is_authenticated else False,
        }
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_transactions(request):
    """Поиск транзакций с фильтрами (только для администраторов)"""
    try:
        # Получаем параметры фильтрации
        search_query = request.GET.get('q', '')
        transaction_type = request.GET.get('type', '')
        limit = request.GET.get('limit', 50)
        
        # Преобразуем limit в int с обработкой ошибок
        try:
            limit = int(limit)
            if limit > 4000:  # Максимальный лимит
                limit = 4000
        except (ValueError, TypeError):
            limit = 4000
        
        # Базовый запрос
        transactions_query = Transaction.objects.select_related(
            'account__client', 'from_account', 'to_account'
        )
        
        # Применяем фильтры
        if search_query:
            transactions_query = transactions_query.filter(
                models.Q(account__client__name__icontains=search_query) |
                models.Q(account__account_number__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        if transaction_type and transaction_type != 'all':
            type_mapping = {
                'deposit': 'deposit',
                'withdraw': 'withdraw', 
                'transfer': 'transfer'
            }
            if transaction_type in type_mapping:
                transactions_query = transactions_query.filter(type=type_mapping[transaction_type])
        
        # Сортируем и ограничиваем
        transactions = transactions_query.order_by('-timestamp')[:limit]
        
        # Формируем ответ
        transactions_data = []
        for trans in transactions:
            # Определяем правильную валюту для отображения
            display_currency = trans.account.currency
            
            # Для переводов определяем правильную валюту
            if trans.type == 'transfer':
                if trans.from_account and trans.from_account.id == trans.account.id:
                    # Исходящий перевод - показываем в валюте отправителя
                    display_currency = trans.from_account.currency
                elif trans.to_account and trans.to_account.id == trans.account.id:
                    # Входящий перевод - показываем в валюте получателя
                    display_currency = trans.to_account.currency
            
            transactions_data.append({
                'id': trans.id,
                'account_number': trans.account.account_number,
                'client_name': trans.account.client.name,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': display_currency,
                'from_currency': trans.from_account.currency if trans.from_account else None,
                'to_currency': trans.to_account.currency if trans.to_account else None,
            })
        
        return Response({
            'transactions': transactions_data,
            'total_count': len(transactions_data),
            'search_query': search_query,
            'limit': limit
        })
        
    except Exception as e:
        print(f"Ошибка в search_transactions: {str(e)}")  # Для отладки
        return Response({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    """Поиск транзакций с фильтрами (только для администраторов)"""
    try:
        # Получаем параметры фильтрации
        search_query = request.GET.get('q', '')
        transaction_type = request.GET.get('type', '')
        limit = int(request.GET.get('limit', 50))
        
        # Базовый запрос
        transactions_query = Transaction.objects.select_related(
            'account__client', 'from_account', 'to_account'
        )
        
        # Применяем фильтры
        if search_query:
            transactions_query = transactions_query.filter(
                models.Q(account__client__name__icontains=search_query) |
                models.Q(account__account_number__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        if transaction_type and transaction_type != 'all':
            type_mapping = {
                'deposit': 'deposit',
                'withdraw': 'withdraw', 
                'transfer': 'transfer'
            }
            if transaction_type in type_mapping:
                transactions_query = transactions_query.filter(type=type_mapping[transaction_type])
        
        # Сортируем и ограничиваем
        transactions = transactions_query.order_by('-timestamp')[:limit]
        
        # Формируем ответ
        transactions_data = []
        for trans in transactions:
            display_currency = trans.account.currency
            
            if trans.type == 'transfer':
                if trans.from_account and trans.from_account.id == trans.account.id:
                    display_currency = trans.from_account.currency
                elif trans.to_account and trans.to_account.id == trans.account.id:
                    display_currency = trans.to_account.currency
            
            transactions_data.append({
                'id': trans.id,
                'account_number': trans.account.account_number,
                'client_name': trans.account.client.name,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'description': trans.description,
                'timestamp': trans.timestamp.isoformat(),
                'from_account': trans.from_account.account_number if trans.from_account else None,
                'to_account': trans.to_account.account_number if trans.to_account else None,
                'currency': display_currency,
                'from_currency': trans.from_account.currency if trans.from_account else None,
                'to_currency': trans.to_account.currency if trans.to_account else None,
            })
        
        return Response({
            'transactions': transactions_data,
            'total_count': len(transactions_data),
            'search_query': search_query
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_transaction(request):
    """Тестовый endpoint для проверки работы с телом запроса"""
    try:
        return Response({
            'success': True,
            'message': 'Тест пройден успешно',
            'received_data': request.data
        })
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Ошибка при обработке запроса'
        }, status=400)

def test_page(request):
    """Тестовая страница для проверки работы"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Тестовая страница</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>Тестовая страница Онлайн-кассы</h1>
        <div id="status">Проверка подключения...</div>
        
        <script>
            // Простой тест API
            fetch('/api/test/')
                .then(response => {
                    document.getElementById('status').innerHTML = 
                        '<p class="success">✅ API отвечает. Статус: ' + response.status + '</p>';
                    return response.json();
                })
                .then(data => {
                    console.log('Данные:', data);
                    document.getElementById('status').innerHTML += 
                        '<p>Пользователь: ' + (data.user.username || 'не аутентифицирован') + '</p>' +
                        '<p>Админ: ' + data.user.is_staff + '</p>';
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = 
                        '<p class="error">❌ Ошибка: ' + error + '</p>';
                });
        </script>
        
        <p><a href="/api/auth/login/">Страница входа</a></p>
        <p><a href="/api/auth/register/">Страница регистрации</a></p>
        <p><a href="/admin/">Админ-панель Django</a></p>
        <p><a href="/api/admin-panel/">Веб-админка</a></p>
    </body>
    </html>
    """)
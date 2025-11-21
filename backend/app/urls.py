from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Страницы
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    
    # API - пользовательские
    path('accounts/my/', views.get_user_accounts, name='get_user_accounts'),
    path('accounts/create/', views.create_account, name='create_account'),
    path('accounts/<int:account_id>/', views.get_account_detail, name='get_account_detail'),
    path('accounts/search/', views.search_accounts, name='search_accounts'),
    path('deposit/', views.deposit, name='deposit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('transfer/', views.transfer, name='transfer'),
    
    # API - административные
    path('admin/transactions/', views.get_all_transactions, name='get_all_transactions'),
    path('admin/recent-transactions/', views.get_recent_transactions, name='get_recent_transactions'),
    path('admin/accounts/', views.get_all_accounts, name='get_all_accounts'),
    path('admin/check/', views.admin_check, name='admin_check'),
    path('admin/search-transactions/', views.search_transactions, name='search_transactions'),
    
    # Тестовые endpoints
    path('test-transaction/', views.test_transaction, name='test_transaction'),
    path('test/', views.api_test, name='api_test'),
    path('test-page/', views.test_page, name='test_page'),
    
    # Главная страница
    path('', views.dashboard_view, name='home'),
]
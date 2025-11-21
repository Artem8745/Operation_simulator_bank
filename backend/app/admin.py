from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Client, Account, Transaction, ExchangeRate

class ClientInline(admin.StackedInline):
    model = Client
    can_delete = False
    verbose_name_plural = 'Клиенты'
    fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email', 'user__username']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'phone', 'email')
        }),
        ('Дополнительная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'client', 'balance', 'currency', 'is_active', 'created_at']
    search_fields = ['account_number', 'client__name']
    list_filter = ['currency', 'is_active', 'created_at']
    readonly_fields = ['created_at']
    fieldsets = (
        (None, {
            'fields': ('client', 'account_number', 'balance', 'currency', 'is_active')
        }),
        ('Дополнительная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'amount', 'type', 'timestamp', 'from_account', 'to_account']
    list_filter = ['type', 'timestamp']
    search_fields = ['account__client__name', 'description']
    readonly_fields = ['timestamp']
    fieldsets = (
        (None, {
            'fields': ('account', 'amount', 'type', 'description')
        }),
        ('Информация о переводе', {
            'fields': ('from_account', 'to_account'),
            'classes': ('collapse',)
        }),
        ('Дополнительная информация', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['from_currency', 'to_currency', 'rate', 'updated_at']
    list_editable = ['rate']
    list_filter = ['from_currency', 'to_currency']
    search_fields = ['from_currency', 'to_currency']

# Убираем кастомный UserAdmin и используем стандартный
# Вместо этого добавим Client как отдельную модель в админке
# Если нужно связать User и Client, лучше использовать отдельные страницы

# Удаляем перерегистрацию User, чтобы использовать стандартный UserAdmin
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)
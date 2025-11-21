import random
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Client(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='client',
        verbose_name="Пользователь"
    )
    name = models.CharField(max_length=100, verbose_name="Имя клиента")
    phone = models.CharField(max_length=15, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Автоматически заполняем email из пользователя, если не указан
        if not self.email and self.user.email:
            self.email = self.user.email
        # Автоматически заполняем имя из username, если не указано
        if not self.name:
            self.name = self.user.username
        super().save(*args, **kwargs)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client')
    name = models.CharField(max_length=100, verbose_name="Имя клиента")
    phone = models.CharField(max_length=15, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return self.name

class Account(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Баланс")
    currency = models.CharField(max_length=3, default='RUB', verbose_name="Валюта")
    account_number = models.CharField(max_length=20, unique=True, verbose_name="Номер счета")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Счет"
        verbose_name_plural = "Счета"

    def __str__(self):
        return f"{self.client.name} - {self.balance} {self.currency}"

    @classmethod
    def generate_account_number(cls):
        """Генерация уникального номера счета"""
        while True:
            # Формат: 40817810 + 8 случайных цифр
            account_number = f"40817810{random.randint(10000000, 99999999)}"
            if not cls.objects.filter(account_number=account_number).exists():
                return account_number

    def save(self, *args, **kwargs):
        """Автоматическая генерация номера счета при создании"""
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Пополнение'),
        ('withdraw', 'Снятие'),
        ('transfer', 'Перевод'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Счет", related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма")
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="Тип операции")
    description = models.TextField(blank=True, verbose_name="Описание")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время операции")
    from_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='outgoing_transactions', verbose_name="Со счета")
    to_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='incoming_transactions', verbose_name="На счет")

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.account.client.name} - {self.get_type_display()} {self.amount}"

# Сигнал для автоматического создания клиента при создании пользователя
@receiver(post_save, sender=User)
def create_client_profile(sender, instance, created, **kwargs):
    """Автоматически создает профиль Client при создании User"""
    if created:
        Client.objects.get_or_create(
            user=instance,
            defaults={
                'name': instance.username,
                'email': instance.email
            }
        )

@receiver(post_save, sender=User)
def save_client_profile(sender, instance, **kwargs):
    """Сохраняет профиль Client при сохранении User"""
    if hasattr(instance, 'client'):
        instance.client.save()



class ExchangeRate(models.Model):
    from_currency = models.CharField(max_length=3, verbose_name="Из валюты")
    to_currency = models.CharField(max_length=3, verbose_name="В валюту")
    rate = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Курс")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Курс валют"
        verbose_name_plural = "Курсы валют"
        unique_together = ['from_currency', 'to_currency']

    def __str__(self):
        return f"{self.from_currency} → {self.to_currency}: {self.rate}"
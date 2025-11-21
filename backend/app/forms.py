from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Client, Account
from decimal import Decimal

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'field__input', 'autocomplete': 'email'})
    )
    phone = forms.CharField(
        max_length=15, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'field__input', 'autocomplete': 'tel'})
    )
    full_name = forms.CharField(
        max_length=100, 
        required=True, 
        label="Полное имя",
        widget=forms.TextInput(attrs={'class': 'field__input', 'autocomplete': 'name'})
    )
    currency = forms.ChoiceField(
        choices=[('RUB', 'Рубли (RUB)'), ('USD', 'Доллары (USD)'), ('EUR', 'Евро (EUR)')],
        initial='RUB',
        label="Валюта основного счета",
        widget=forms.Select(attrs={'class': 'field__input'})
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone', 'currency', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка поля username
        self.fields['username'].widget.attrs.update({
            'class': 'field__input',
            'autocomplete': 'username'
        })
        
        # Настройка поля password1 с правильными атрибутами для автозаполнения
        self.fields['password1'].widget.attrs.update({
            'class': 'field__input',
            'autocomplete': 'new-password'
        })
        
        # Настройка поля password2 с правильными атрибутами для автозаполнения
        self.fields['password2'].widget.attrs.update({
            'class': 'field__input',
            'autocomplete': 'new-password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Создаем или обновляем профиль клиента
            client, created = Client.objects.get_or_create(
                user=user,
                defaults={
                    'name': self.cleaned_data['full_name'],
                    'email': self.cleaned_data['email'],
                    'phone': self.cleaned_data['phone']
                }
            )
            if not created:
                client.name = self.cleaned_data['full_name']
                client.email = self.cleaned_data['email']
                client.phone = self.cleaned_data['phone']
                client.save()
            
            # Создаем счет для пользователя с выбранной валютой
            Account.objects.create(
                client=client,
                balance=Decimal('0.00'),
                currency=self.cleaned_data['currency']
            )
        return user
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cassa.settings')
django.setup()

from app.models import ExchangeRate

def create_initial_rates():
    rates = [
        {'from_currency': 'RUB', 'to_currency': 'USD', 'rate': '0.011'},
        {'from_currency': 'RUB', 'to_currency': 'EUR', 'rate': '0.009'},
        {'from_currency': 'USD', 'to_currency': 'RUB', 'rate': '90.0'},
        {'from_currency': 'USD', 'to_currency': 'EUR', 'rate': '0.85'},
        {'from_currency': 'EUR', 'to_currency': 'RUB', 'rate': '110.0'},
        {'from_currency': 'EUR', 'to_currency': 'USD', 'rate': '1.18'},
    ]
    
    for rate_data in rates:
        rate, created = ExchangeRate.objects.get_or_create(
            from_currency=rate_data['from_currency'],
            to_currency=rate_data['to_currency'],
            defaults={'rate': rate_data['rate']}
        )
        if created:
            print(f"Создан курс: {rate}")
        else:
            rate.rate = rate_data['rate']
            rate.save()
            print(f"Обновлен курс: {rate}")

if __name__ == '__main__':
    create_initial_rates()
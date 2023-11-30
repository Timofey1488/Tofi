from accounts.constants import CURRENCY


def convert_currency(amount, from_currency, to_currency, rate):
    if from_currency == to_currency:
        return amount
    else:
        # Используем словари для удобства работы с константами
        currency_mapping = {'USD': 'U', 'BYN': 'B'}
        reversed_currency_mapping = {v: k for k, v in currency_mapping.items()}

        # Преобразуем валюты в формат из констант
        from_currency = reversed_currency_mapping.get(from_currency, from_currency)
        to_currency = reversed_currency_mapping.get(to_currency, to_currency)

        return amount * rate if from_currency == 'U' and to_currency == 'B' else amount

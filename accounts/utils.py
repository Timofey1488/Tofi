import logging
from decimal import Decimal

from accounts.constants import CURRENCY


def convert_currency(amount, from_currency, to_currency, rate):
    valid_currencies = {'USD', 'BYN', 'U', 'B'}

    if from_currency not in valid_currencies or to_currency not in valid_currencies:
        raise ValueError("Invalid currency code")

    if from_currency == to_currency:
        return amount
    else:
        # Ensure amount is a Decimal
        amount = Decimal(str(amount))
        # Ensure rate is a Decimal
        rate = Decimal(str(rate))
        # Perform the multiplication
        result = amount / rate

        return result

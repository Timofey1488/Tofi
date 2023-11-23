from celery import shared_task
from django.utils import timezone
from .models import Card


@shared_task
def check_credit_card_payments():
    # Эту функцию нужно будет вызывать из celery beat в начале каждого месяца
    current_month = timezone.now().month
    credit_cards = Card.objects.filter(card_type='C')

    for credit_card in credit_cards:
        # Проверка и погашение задолженности для каждой кредитной карты(временно)
        if credit_card.balance < 0 and credit_card.last_payment_month != current_month:
            credit_card.balance = 0
            credit_card.last_payment_month = current_month
            credit_card.save()
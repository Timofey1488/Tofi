from celery import shared_task
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.http import request
from django.utils import timezone

from banking_system import settings
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


@shared_task
def process_pending_deposits():
    # Get cards with pending deposits
    cards = Card.objects.filter(is_deposit_allowed=True, pending_deposit_amount__gt=0)

    for card in cards:
        # Process the deposit and update the balance
        card.balance += card.pending_deposit_amount
        card.pending_deposit_amount = 0
        card.save()

        # Log the deposit in the admin panel
        content_type = ContentType.objects.get_for_model(card)
        LogEntry.objects.create(
            user_id=user.id,  # Use the appropriate user ID
            content_type_id=content_type.id,
            object_id=card.id,
            object_repr=str(card),
            action_flag=CHANGE,
            change_message='Manual deposit processed.'
        )
            
import random
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models

from .constants import GENDER_CHOICE, CURRENCY, CARD_TYPE, PERIOD_DEPOSIT
from .managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, null=False, blank=False)
    objects = UserManager()

    USERNAME_FIELD = 'email'
    is_active = models.BooleanField(
        default=False,
    )
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def has_cards(self):
        return self.user_cards.exists()

    # @property
    # def balance(self):
    #     if hasattr(self, 'user_cards'):
    #         return self.user_cards.balance
    #     return 0


class UserBankAccount(models.Model):
    user = models.OneToOneField(
        User,
        related_name='account',
        on_delete=models.CASCADE,
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICE)
    birth_date = models.DateField(null=True, blank=True)
    interest_start_date = models.DateField(
        null=True, blank=True,
        help_text=(
            'The month number that interest calculation will start from'
        )
    )
    initial_deposit_date = models.DateField(null=True, blank=True)


class Card(models.Model):
    account_no = models.CharField(max_length=16, unique=True)
    user = models.ForeignKey(
        User,
        related_name='user_cards',
        on_delete=models.CASCADE,
    )
    balance = models.DecimalField(
        default=0,
        max_digits=12,
        decimal_places=2
    )
    cvv_code = models.CharField(max_length=3)
    card_type = models.CharField(max_length=1, choices=CARD_TYPE)
    currency = models.CharField(max_length=1, choices=CURRENCY)

    def save(self, *args, **kwargs):
        # Generate values for some fields
        if not self.account_no:
            self.account_no = ''.join(str(random.randint(0, 9)) for _ in range(16))
        if not self.cvv_code:
            self.cvv_code = random.randint(100, 999)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account_no} {self.user.first_name} {self.user.last_name}"


class UserAddress(models.Model):
    user = models.OneToOneField(
        User,
        related_name='user_address',
        on_delete=models.CASCADE,
    )
    street_address = models.CharField(max_length=512)
    city = models.CharField(max_length=256)
    postal_code = models.PositiveIntegerField()
    country = models.CharField(max_length=256)

    def __str__(self):
        return self.user.email


#  Class for create of Money Box
class UserAim(models.Model):
    user = models.OneToOneField(
        User,
        related_name='address',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=512)
    amount_of_deposit_withdraw = models.PositiveIntegerField()
    period_of_deposit = models.CharField(max_length=1, choices=PERIOD_DEPOSIT)
    date_start = models.CharField(max_length=256)
    date_end = models.PositiveIntegerField()

    def __str__(self):
        return self.user.email

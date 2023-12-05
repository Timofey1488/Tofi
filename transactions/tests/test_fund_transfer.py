from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from decimal import Decimal
from accounts.models import Card
from transactions.models import Transaction


class FundTransferViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user_data = {
            'email': 'testuser',
            'password': 'testpassword123',
        }
        self.user = User.objects.create_user(**self.user_data)

        # Create test cards for the user
        self.card1 = Card.objects.create(user=self.user, balance=100, currency='U')
        self.card2 = Card.objects.create(user=self.user, balance=50, currency='B')

    def test_fund_transfer_view(self):
        self.client.login(email='testuser@example.com', password='testpassword')

        # Make a POST request to fund_transfer view
        response = self.client.post(
            reverse('transactions:fund_transfer', kwargs={'card_id': self.card1.id}),
            {'receiver_account_number': 'receiver_account_number', 'amount': 20, 'card': self.card1.id},
        )

        # Check if the transfer was successful and the user is redirected
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:card_list'))

        # Check if the balances were updated
        sender_card = Card.objects.get(id=self.card1.id)
        receiver_card = Card.objects.get(account_no='receiver_account_number')

        self.assertEqual(sender_card.balance, 80)
        self.assertEqual(receiver_card.balance, Decimal('20') * Decimal('3.116'))  # Assuming conversion rate is 1 USD = 3.116 BYN

        # Check if the transaction was recorded
        transactions = Transaction.objects.all()
        self.assertEqual(transactions.count(), 2)  # Two transactions are recorded (sender and receiver)

    def test_fund_transfer_card_by_card_view(self):
        self.client.login(email='testuser@example.com', password='testpassword')

        # Make a POST request to fund_transfer_card_by_card view
        response = self.client.post(
            reverse('transactions:fund_transfer_card_by_card', kwargs={'card_id': self.card1.id}),
            {'card_one': self.card1.id, 'card_two': self.card2.id, 'amount': 10},
        )

        # Check if the transfer was successful and the user is redirected
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:card_list'))

        # Check if the balances were updated
        sender_card = Card.objects.get(id=self.card1.id)
        receiver_card = Card.objects.get(id=self.card2.id)

        self.assertEqual(sender_card.balance, 90)
        self.assertEqual(receiver_card.balance, 10)

        # Check if the transaction was recorded
        transactions = Transaction.objects.all()
        self.assertEqual(transactions.count(), 2)  # Two transactions are recorded (sender and receiver)

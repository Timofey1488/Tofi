from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import Card, UserAddress

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(email='testuser@example.com')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('testpassword123'))

    def test_has_cards_method(self):
        # Проверка, что у пользователя нет карточек по умолчанию
        self.assertFalse(self.user.has_cards())

        # Создание карточки для пользователя
        card_data = {
            'user': self.user,
            'card_name': 'Test Card',
            'account_no': '1234567890123456',
            'balance': 1000.00,
            'cvv_code': '123',
            'card_type': 'C',
            'currency': 'B',
        }
        Card.objects.create(**card_data)

        self.assertTrue(self.user.has_cards())


class UserAddressModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
        }
        self.user = User.objects.create_user(**self.user_data)
        self.address_data = {
            'user': self.user,
            'street_address': '123 Main St',
            'city': 'Cityville',
            'postal_code': 12345,
            'country': 'Countryland',
        }
        self.address = UserAddress.objects.create(**self.address_data)

    def test_address_creation(self):
        self.assertEqual(UserAddress.objects.count(), 1)
        address = UserAddress.objects.get(user=self.user)
        self.assertEqual(address.street_address, '123 Main St')

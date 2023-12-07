from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from accounts.models import Card, Payment

User = get_user_model()


class FundTransferViewTest(TestCase):
    def create_user(self, email='test@example.com', password='testpassword'):
        return User.objects.create_user(email=email, password=password)

    def setUp(self):
        # Создаем тестового пользователя и карту
        self.user = self.create_user()
        self.card = Card.objects.create(user=self.user, balance=100, currency='U', card_type='D', account_no='123456789')

    def test_fund_transfer_view(self):
        # Входим в систему от имени пользователя
        self.client.login(username='test@example.com', password='testpassword')

        # Формируем URL и данные для передачи в представление
        url = reverse('transactions:fund_transfer')
        data = {
            'receiver_account_number': '123456789',
            'amount': 50,
            'card': self.card.id
        }

        # Отправляем POST-запрос на представление
        response = self.client.post(url, data)
        # Проверяем, что запрос был успешным (код ответа 302 - перенаправление)
        self.assertEqual(response.status_code, 302)

        # Проверяем, что балансы обновлены правильно
        sender_card = Card.objects.get(id=self.card.id)
        receiver_card = Card.objects.get(account_no='123456789')
        self.assertEqual(sender_card.balance, 50)
        self.assertEqual(receiver_card.balance, 50)


class FundTransferByCardViewTest(TestCase):
    def create_user(self, email='test@example.com', password='testpassword'):
        return User.objects.create_user(email=email, password=password)

    def setUp(self):
        # Создаем тестового пользователя и две карты
        self.user = self.create_user()
        self.card_one = Card.objects.create(user=self.user, balance=100, currency='U', card_type='D')
        self.card_two = Card.objects.create(user=self.user, balance=100, currency='B', card_type='C')

    def test_fund_transfer_by_card_view(self):
        # Входим в систему от имени пользователя
        self.client.login(username='test@example.com', password='testpassword')

        # Формируем URL и данные для передачи в представление
        url = reverse('transactions:fund_transfer_card_by_card')
        data = {
            'card_one': self.card_one.id,
            'card_two': self.card_two.id,
            'amount': 50
        }

        # Отправляем POST-запрос на представление
        response = self.client.post(url, data)
        # Проверяем, что запрос был успешным (код ответа 302 - перенаправление)
        self.assertEqual(response.status_code, 302)

        # Получаем сообщения из контекста запроса
        messages = [m.message for m in get_messages(response.wsgi_request)]
        # Проверяем, что хотя бы одно сообщение содержит "Error"
        self.assertFalse(any('Error' in message for message in messages))

        # Проверяем, что балансы обновлены правильно
        sender_card = Card.objects.get(id=self.card_one.id)
        receiver_card = Card.objects.get(id=self.card_two.id)
        print(f"Sender Card Balance Before Transaction: {sender_card.balance}")
        print(f"Receiver Card Balance Before Transaction: {receiver_card.balance}")
        self.assertEqual(sender_card.balance, 50)
        self.assertEqual(receiver_card.balance, 150)

        sender_card = Card.objects.get(id=self.card_one.id)
        receiver_card = Card.objects.get(id=self.card_two.id)
        print(f"Sender Card Balance After Transaction: {sender_card.balance}")
        print(f"Receiver Card Balance After Transaction: {receiver_card.balance}")
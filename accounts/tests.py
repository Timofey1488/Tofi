from django.core import mail
from django.test import TestCase
from django.urls import reverse

import accounts
from accounts.models import User


class UserRegistrationTest(TestCase):
    def test_email_sending(self):
        # Создайте тестового пользователя
        user = User.objects.create_user(email='timofeysidorenko@gmail.com', password='testpassword')

        # Перейдите на страницу регистрации (замените 'your_registration_url' на реальный URL вашей страницы регистрации)
        response = self.client.get(reverse('accounts:user_registration'))

        # Проверьте, что страница регистрации возвращает код состояния 200
        self.assertEqual(response.status_code, 200)

        # Заполните данные формы регистрации (замените 'your_form_data' на реальные данные формы)
        form_data = {
            'email': 'timofeysidorenko@gmail.com',
            'password1': 'testpassword',
            'password2': 'testpassword',
            # Другие поля формы, если они есть
        }

        # Отправьте POST-запрос с данными формы
        response = self.client.post(reverse('accounts:user_registration'), form_data, follow=True)

        # Проверьте, что пользователь был создан успешно
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='timofeysidorenko@gmail.com').exists())

        # Проверьте, что было отправлено электронное письмо
        print("Number of emails sent:", len(mail.outbox))
        self.assertEqual(len(mail.outbox), 1)

        # Получите отправленное электронное письмо
        sent_email = mail.outbox[0]

        # Проверьте адрес отправителя
        self.assertEqual(sent_email.from_email, 'timosidorenko@yandex.ru')

        # Проверьте адрес получателя
        self.assertEqual(sent_email.to, ['timofeysidorenko@gmail.com'])

        # Проверьте содержимое письма
        self.assertIn('Follow this link', sent_email.body)
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.forms import SavingsGoalForm
from accounts.models import SavingsGoal, User


class SavingsGoalViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@gmail.com', password='testpass')

        self.goal = SavingsGoal.objects.create(
            user=self.user,
            goal_name='Test Goal',
            target_amount=Decimal('1000.00'),
            target_date=timezone.now().date() + timedelta(days=60),
            monthly_payment=Decimal('100.00')
        )

    def test_create_savings_goal_authenticated(self):
        self.client.login(email='testuser@gmail.com', password='testpass')
        response = self.client.post(reverse('accounts:create_savings_goal'),
                                    {'target_amount': 1000, 'target_date': '2024-12-31'})

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

    def test_create_savings_goal_unauthenticated(self):
        response = self.client.post(reverse('accounts:create_savings_goal'),
                                    {'target_amount': 1000, 'target_date': '2024-12-31'})

        # Проверяем, что пользователь перенаправлен на страницу входа
        self.assertRedirects(response, '/accounts/login/?next=' + reverse('accounts:create_savings_goal'))

    def test_review_savings_plan_authenticated(self):
        goal = SavingsGoal.objects.create(user=self.user, target_amount=1000, target_date='2024-12-31')

        self.client.login(email='testuser@gmail.com', password='testpass')
        response = self.client.post(reverse('accounts:review_savings_plan', kwargs={'goal_id': goal.id}))
        self.assertEqual(response.status_code, 302)
        goal.refresh_from_db()
        self.assertTrue(goal.approved)
        self.assertFalse(goal.is_active)

    def test_save_form_with_existing_goal_name(self):
        existing_goal = SavingsGoal.objects.create(user=self.user, goal_name='Existing Goal', target_amount=500,
                                                   target_date=timezone.now() + timezone.timedelta(days=365))

        data = {
            'goal_name': 'Existing Goal',
            'target_amount': 800,
            'target_date': timezone.now() + timezone.timedelta(days=365),
        }

        form = SavingsGoalForm(data, instance=None)
        self.assertFalse(form.is_valid())
        self.assertIn('goal_name', form.errors)

    def test_delete_savings_goal_authenticated(self):
        self.client.login(email='testuser@gmail.com', password='testpass')

        # Удаляем цель накопления
        response = self.client.post(reverse('accounts:delete_savings_goal', args=[self.goal.id]))

        # Проверяем, что цель успешно удалена
        self.assertEqual(response.status_code, 302)  # Ожидаем редирект
        with self.assertRaises(SavingsGoal.DoesNotExist):
            SavingsGoal.objects.get(id=self.goal.id)

    def test_edit_savings_goal_unauthenticated(self):
        # Попытка изменить цель накопления без аутентификации
        response = self.client.get(reverse('accounts:edit_savings_goal', args=[self.goal.id]))

        # Проверяем, что пользователь перенаправлен на страницу входа
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             '/accounts/login/?next=' + reverse('accounts:edit_savings_goal', args=[self.goal.id]))

    def test_delete_savings_goal_unauthenticated(self):
        # Попытка удалить цель накопления без аутентификации
        response = self.client.get(reverse('accounts:delete_savings_goal', args=[self.goal.id]))

        # Проверяем, что пользователь перенаправлен на страницу входа
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             '/accounts/login/?next=' + reverse('accounts:delete_savings_goal', args=[self.goal.id]))


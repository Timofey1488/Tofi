from datetime import timedelta
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView, FormView
from django_otp import match_token, devices_for_user
from django_otp.forms import OTPAuthenticationForm
from django_otp.plugins.otp_totp.models import TOTPDevice

from .forms import UserRegistrationForm, UserAddressForm, CardCreationForm, \
    DepositCardForm, PaymentForm, StatementFilterForm, DepositApprovalForm, SavingsGoalForm, SignUpForm
from .models import UserAddress, User, Card, Payment, SavingsGoal
import logging

from .utils import convert_currency

logger = logging.getLogger(__name__)


class SignUpView(View):
    form_class = SignUpForm
    template_name = 'commons/signup.html'

    def get_user_totp_device(self, user, confirmed=None):
        devices = devices_for_user(user, confirmed=confirmed)
        for device in devices:
            if isinstance(device, TOTPDevice):
                return device

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():

            user = form.save(commit=False)
            user.is_active = True  # Deactivate account till it is confirmed
            user.save()
            device = self.get_user_totp_device(user)
            if not device:
                device = user.totpdevice_set.create(confirmed=True)
                print(device.config_url)
            current_site = get_current_site(request)
            mail_subject = 'DJANGO OTP DEMO'
            message = render_to_string('emails/account_activation_email.html', {
                'user': user,
                'qr_code': device.config_url,
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.content_subtype = "html"
            email.send()

            messages.success(request, 'Please Confirm your email to complete registration.')

            return redirect('login')

        return render(request, self.template_name, {'form': form})


class AccountLoginView(LoginView):
    template_name = 'commons/login.html'
    form_class = OTPAuthenticationForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        # Let the custom authentication form handle authentication
        user = form.get_user()

        if user is not None:
            otp_token = form.cleaned_data.get('otp_token')
            device_match = match_token(user=user, token=otp_token)

            if device_match:
                # Log the user in
                login(self.request, user)
                return super().form_valid(form)
            else:
                # Handle token mismatch
                form.add_error('otp_token', 'Invalid OTP token')
        else:
            # Handle authentication failure
            form.add_error(None, 'Invalid email or password')

        return super().form_valid(form)


class UserRegistrationView(TemplateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'

    def post(self, request, *args, **kwargs):
        registration_form = UserRegistrationForm(self.request.POST)
        address_form = UserAddressForm(self.request.POST)

        if registration_form.is_valid() and address_form.is_valid():
            user = registration_form.save()
            address = address_form.save(commit=False)
            address.user = user
            address.save()

            messages.success(
                self.request,
                (
                    f'Account successfully created. '
                )
            )
            return HttpResponseRedirect(
                reverse_lazy('accounts:user_profile')
            )

        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form,
                address_form=address_form
            )
        )

    def get_context_data(self, **kwargs):
        if 'registration_form' not in kwargs:
            kwargs['registration_form'] = UserRegistrationForm()
        if 'address_form' not in kwargs:
            kwargs['address_form'] = UserAddressForm()

        return super().get_context_data(**kwargs)


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)


class UserProfileView(TemplateView):
    template_name = 'accounts/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_staff:
            return redirect('accounts:staff_profile')
        context['user_profile_exists'] = True

        try:
            user_address = UserAddress.objects.get(user=user)
            context['address'] = user_address
        except UserAddress.DoesNotExist:
            context['address'] = None

        return context


class EditUserAddressView(FormView):
    template_name = 'accounts/edit_user_address.html'
    form_class = UserAddressForm
    success_url = reverse_lazy('accounts:user_profile')

    def form_valid(self, form):
        user = self.request.user

        try:
            user_address = UserAddress.objects.get(user=user)
            form = UserAddressForm(self.request.POST, instance=user_address)
        except UserAddress.DoesNotExist:
            form = UserAddressForm(self.request.POST)

        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            messages.success(self.request, 'Address successfully updated.')
            return super().form_valid(form)

        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            user_address = UserAddress.objects.get(user=user)
            form = UserAddressForm(instance=user_address)
        except UserAddress.DoesNotExist:
            form = UserAddressForm()

        return render(request, self.template_name, {'form': form})


def make_payment(request, card_id=None):
    card = get_object_or_404(Card, id=card_id) if card_id else 1

    if request.method == 'POST':
        form = PaymentForm(request.user, request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            selected_card = form.cleaned_data['card']

            # Извлекаем card_type из выбранной карты
            card_type = selected_card.card_type
            if selected_card.currency == 'U':
                converted_amount = convert_currency(amount, 'USD', 'BYN', 3.116)
            else:
                converted_amount = amount

            # Выполняем платеж
            success, message = selected_card.make_payment(converted_amount, card_type)

            if success:
                messages.success(request, f"{message}")
                return redirect('accounts:make_payment')
            else:
                messages.error(request, f"{message}")
                return redirect('accounts:make_payment')

    else:
        form = PaymentForm(request.user)

    return render(request, 'accounts/payment_form.html', {'form': form, 'card': card})


class StaffProfileView(TemplateView):
    template_name = 'accounts/staff_profile.html'


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Обновление хеша сессии, чтобы избежать разлогинивания
            messages.success(request, 'Password successfully changed.')
            return redirect('accounts:user_profile')
        else:
            messages.error(request, 'Invalid old password or new passwords do not match.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})


class CardCreateView(View):
    template_name = 'accounts/create_card.html'
    success_url = 'accounts:card_list'

    def get(self, request):
        form = CardCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        try:
            form = CardCreationForm(request.POST)
            if form.is_valid():
                card = form.save(commit=False)
                card.user = request.user
                card.save()
                logger.warning("Card creation successful")
                return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error during card creation: {str(e)}")
            # Raise the exception again for debugging purposes
            raise
        return render(request, self.template_name, {'form': form})


class CardListView(View):
    template_name = 'accounts/card_list.html'

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            if not user.has_cards():
                return render(request, 'accounts/no_cards.html')
            cards = user.user_cards.all()
            return render(request, self.template_name, {'cards': cards})
        else:
            return render(request, 'accounts/no_cards.html')


@login_required
def deposit_card(request, card_id):
    card = Card.objects.get(id=card_id)

    if card.deposit_pending:
        messages.success(request, "You alrealy have pending deposit. Awaiting admin approval.")
        return redirect('accounts:card_list')

    if request.method == 'POST':
        form = DepositCardForm(request.POST)
        if form.is_valid():
            deposit_amount = form.cleaned_data['deposit_amount']

            # Set the pending deposit amount instead of updating the balance directly
            card.pending_deposit_amount += deposit_amount
            card.deposit_pending = True
            card.save()
            payment = Payment.objects.create(
                card=card,
                amount=card.pending_deposit_amount,
                currency='B',
                card_type=card.card_type,
                deposit_pending=True
            )

            # Redirect to a success page or wherever needed
            messages.success(request, "Deposit request submitted. Awaiting admin approval.")
            return redirect('accounts:card_list')
    else:
        form = DepositCardForm()

    return render(request, 'accounts/deposit_form.html', {'form': form, 'card': card})


@staff_member_required
def deposit_approval_list(request):
    pending_deposit_cards = Card.objects.filter(deposit_pending=True)
    return render(request, 'accounts/deposit_approval_list.html', {'pending_deposit_cards': pending_deposit_cards})


@staff_member_required
def deposit_approval(request, card_id):
    card = get_object_or_404(Card, id=card_id)

    if request.method == 'POST':
        form = DepositApprovalForm(request.POST)
        if form.is_valid():
            approved = form.cleaned_data['approved']

            if approved:
                # Process the approved deposit
                card.balance += card.pending_deposit_amount
                card.pending_deposit_amount = 0
                card.deposit_pending = False
                card.save()

                messages.success(request, f"Deposit request for Card {card.account_no} approved.")
            else:
                # Reject the deposit
                card.pending_deposit_amount = 0
                card.deposit_pending = False
                card.save()

                messages.warning(request, f"Deposit request for Card {card.account_no} rejected.")

            return redirect('accounts:deposit_approval_list')

    else:
        form = DepositApprovalForm()

    return render(request, 'accounts/deposit_approval_form.html', {'form': form, 'card': card})


@login_required
def statement(request, card_id):
    form = StatementFilterForm(request.GET or None)
    card = Card.objects.get(id=card_id)

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date'] + timedelta(days=1)

        payments = Payment.objects.filter(card=card, timestamp__range=[start_date, end_date])

        # Separate payments and pending deposits
        regular_payments = payments.filter(deposit_pending=False)
        pending_deposits = payments.filter(deposit_pending=True)

        total_spent = regular_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    else:
        regular_payments = []
        pending_deposits = []
        total_spent = 0

    return render(request, 'accounts/statement.html', {
        'form': form,
        'regular_payments': regular_payments,
        'pending_deposits': pending_deposits,
        'total_spent': total_spent,
        'card': card,
    })


# ----------------Savings Goals-----------------------


@login_required
def create_savings_goal(request):
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            savings_goal = form.save(commit=False)
            savings_goal.user = request.user
            savings_goal.save()
            return redirect('accounts:review_savings_plan', goal_id=savings_goal.id)
    else:
        form = SavingsGoalForm()

    return render(request, 'accounts/create_savings_goal.html', {'form': form})


@login_required
def review_savings_plan(request, goal_id):
    savings_goal = get_object_or_404(SavingsGoal, id=goal_id)

    total_months = (
                               savings_goal.target_date.year - savings_goal.created_at.year) * 12 + savings_goal.target_date.month - savings_goal.created_at.month
    monthly_savings_amount = round(savings_goal.target_amount / total_months)

    context = {
        'savings_goal': savings_goal,
        'total_months': total_months,
        'monthly_savings_amount': monthly_savings_amount,
    }

    if request.method == 'POST':
        # Обработка нажатия кнопки "Approve"
        savings_goal.approved = True
        savings_goal.is_active = False  # Отключаем цель после одобрения
        savings_goal.monthly_payment = monthly_savings_amount
        savings_goal.save()
        return redirect('accounts:savings_goal_list')

    return render(request, 'accounts/review_savings_plan.html', context)


@login_required
def savings_goal_list(request):
    user = request.user
    active_goals = SavingsGoal.objects.filter(user=user, approved=True)

    context = {
        'active_goals': active_goals,
    }

    return render(request, 'accounts/savings_goal_list.html', context)


@login_required
def edit_savings_goal(request, goal_id):
    savings_goal = get_object_or_404(SavingsGoal, id=goal_id)

    if request.method == 'POST':
        form = SavingsGoalForm(request.POST, instance=savings_goal)
        if form.is_valid():
            savings_goal = form.save(commit=False)

            # Пересчитываем monthly_amount при изменении target_amount или target_date
            if 'target_amount' in form.changed_data or 'target_date' in form.changed_data:
                total_months = (
                                       savings_goal.target_date.year - savings_goal.created_at.year) * 12 + savings_goal.target_date.month - savings_goal.created_at.month
                savings_goal.monthly_amount = savings_goal.target_amount / total_months

            savings_goal.save()

            return redirect('accounts:savings_goal_list')
    else:
        form = SavingsGoalForm(instance=savings_goal)

    context = {
        'form': form,
        'savings_goal': savings_goal,
    }

    return render(request, 'accounts/edit_savings_goal.html', context)


@login_required
def delete_savings_goal(request, goal_id):
    goal = get_object_or_404(SavingsGoal, id=goal_id)

    if request.method == 'POST':
        goal.delete()
        messages.success(request, f"Goal was successfully deleted!.")
        return redirect('accounts:savings_goal_list')

    return render(request, 'accounts/delete_savings_goal.html', {'goal': goal})

import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView

from banking_system import settings
from credits.models import CreditApplication
from .constants import CURRENCY
from .forms import UserRegistrationForm, UserAddressForm, ChangePasswordForm, CardCreationForm, EmailVerificationForm, \
    DepositCardForm, PaymentForm, StatementFilterForm, DepositApprovalForm
from .models import UserAddress, UserBankAccount, User, Card, Payment
import logging

from .utils import convert_currency

logger = logging.getLogger(__name__)


class UserRegistrationView(TemplateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse_lazy('transactions:transaction_report')
            )
        return super().dispatch(request, *args, **kwargs)

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


class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    redirect_authenticated_user = True


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
            user_bank_account = UserBankAccount.objects.get(user=user)
            context['bank_account'] = user_bank_account
        except UserAddress.DoesNotExist:
            context['bank_account'] = None

        try:
            user_address = UserAddress.objects.get(user=user)
            context['address'] = user_address
        except UserAddress.DoesNotExist:
            context['address'] = None

        return context


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
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            old_password = form.cleaned_data['old_password']
            new_password1 = form.cleaned_data['new_password1']
            new_password2 = form.cleaned_data['new_password2']

            if user.check_password(old_password) and new_password1 == new_password2:
                user.set_password(new_password1)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password successfully changed.')

                user = authenticate(request, username=request.user.username, password=new_password1)
                login(request, user)
                return HttpResponseRedirect(
                    reverse_lazy('accounts:user_profile')
                )
            else:
                messages.error(request, 'Invalid old password or new passwords do not match.')
    else:
        form = ChangePasswordForm()

    return render(request, 'accounts/password_change.html', {'form': form})


class CardCreateView(View):
    template_name = 'accounts/create_card.html'

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
                return redirect('accounts:card_list')
        except Exception as e:
            logger.error(f"Error during card creation: {str(e)}")
            # Raise the exception again for debugging purposes
            raise
        return render(request, self.template_name, {'form': form})


class CardListView(View):
    template_name = 'accounts/card_list.html'

    def get(self, request):
        user = request.user
        if not user.has_cards():
            return render(request, 'accounts/no_cards.html')
        cards = user.user_cards.all()
        return render(request, self.template_name, {'cards': cards})


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

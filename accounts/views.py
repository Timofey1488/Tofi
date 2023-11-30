import uuid

import requests
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.template.defaulttags import url
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView

from banking_system import settings
from .forms import UserRegistrationForm, UserAddressForm, ChangePasswordForm, CardCreationForm, EmailVerificationForm, \
    DepositCardForm
from .models import UserAddress, UserBankAccount, User, Card
import logging

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
                reverse_lazy('transactions:deposit_money')
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


def register_confirm(request, token):
    redis_key = settings.BANK_USER_CONFIRMATION_KEY.format(token=token)
    user_info = cache.get(redis_key) or {}

    if user_id := user_info.get("user_id"):
        user = get_object_or_404(User, id=user_id)
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user)
        messages.success(
            request,
            (
                f'Thank You For Creating A Bank Account. '
            )
        )
        return redirect(to=reverse_lazy("accounts:user_profile"))
    else:
        return redirect(to=reverse_lazy("accounts:user_registration"))


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
                logger.warning("Success")
                return redirect('accounts:card_list')
        except Exception as e:
            logger.error(f"Some error:{str(e)}")
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

    if not card.is_deposit_allowed:
        # Redirect or display an error message indicating that deposits are not allowed
        return redirect('accounts:create_card')

    if request.method == 'POST':
        form = DepositCardForm(request.POST)
        if form.is_valid():
            deposit_amount = form.cleaned_data['deposit_amount']

            # Set the pending deposit amount instead of updating the balance directly
            card.pending_deposit_amount += deposit_amount
            card.save()

            # Redirect to a success page or wherever needed
            messages.success(request, "Deposit request submitted. Awaiting admin approval.")
            return redirect('accounts:create_card')
    else:
        form = DepositCardForm()

    return render(request, 'accounts/deposit_form.html', {'form': form, 'card': card})


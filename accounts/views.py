from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from .forms import UserRegistrationForm, UserAddressForm, ChangePasswordForm
from .models import UserAddress, UserBankAccount, User


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

            login(self.request, user)
            messages.success(
                self.request,
                (
                    f'Thank You For Creating A Bank Account. '
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

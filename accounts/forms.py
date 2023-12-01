from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms import SelectDateWidget

from .models import User, UserBankAccount, UserAddress, Card
from .constants import GENDER_CHOICE, CARD_TYPE, CURRENCY


class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = [
            'street_address',
            'city',
            'postal_code',
            'country'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })


class UserRegistrationForm(UserCreationForm):
    gender = forms.ChoiceField(choices=GENDER_CHOICE)
    birth_date = forms.DateField()

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 '
                    'rounded py-3 px-4 leading-tight '
                    'focus:outline-none focus:bg-white '
                    'focus:border-gray-500'
                )
            })

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            gender = self.cleaned_data.get('gender')
            birth_date = self.cleaned_data.get('birth_date')

            UserBankAccount.objects.create(
                user=user,
                gender=gender,
                birth_date=birth_date,
            )
        return user


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)


class CardCreationForm(forms.ModelForm):
    card_name = forms.CharField()
    card_type = forms.ChoiceField(choices=CARD_TYPE)
    currency = forms.ChoiceField(choices=CURRENCY)

    class Meta:
        model = Card
        fields = [
            'card_name',
            'card_type',
            'currency',
        ]


class EmailVerificationForm(forms.Form):
    email = forms.EmailField(label='Email')
    verification_code = forms.CharField(label='Verification Code')


class DepositCardForm(forms.Form):
    deposit_amount = forms.DecimalField()


class PaymentForm(forms.Form):
    amount = forms.DecimalField(required=True)
    card = forms.ModelChoiceField(queryset=None, empty_label="Select Card", label="Select Card")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_cards = Card.objects.filter(user=user)
        self.fields['card'].queryset = user_cards

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class StatementFilterForm(forms.Form):
    start_date = forms.DateField(widget=SelectDateWidget(empty_label=("Choose Year", "Choose Month", "Choose Day")))
    end_date = forms.DateField(widget=SelectDateWidget(empty_label=("Choose Year", "Choose Month", "Choose Day")))
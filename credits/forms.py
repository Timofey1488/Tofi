from django import forms

from credits.models import CreditApplication


class CreditApplicationForm(forms.ModelForm):
    class Meta:
        model = CreditApplication
        fields = ['amount', 'purpose']


class CreditApprovalForm(forms.Form):
    approved = forms.BooleanField(label='Approve credits', required=False)
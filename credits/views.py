from decimal import Decimal

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from credits.forms import CreditApprovalForm, CreditApplicationForm
from credits.models import CreditApplication, Credit


@staff_member_required
def credit_list(request):
    credit_applications = CreditApplication.objects.all()
    return render(request, 'credits/credit_list.html', {'credit_applications': credit_applications})


def apply_credit(request):
    if request.method == 'POST':
        form = CreditApplicationForm(request.POST)
        if form.is_valid():
            credit_application = form.save(commit=False)
            credit_application.user = request.user
            credit_application.status = 'PENDING'
            credit_application.save()

            messages.success(request, "Credit application submitted. Awaiting approval.")
            return redirect('credits:credit_list')
    else:
        form = CreditApplicationForm()

    return render(request, 'credits/credit_application_form.html', {'form': form})


@staff_member_required
def approve_credit(request, credit_app_id):
    credit_application = get_object_or_404(CreditApplication, id=credit_app_id)

    if request.method == 'POST':
        form = CreditApprovalForm(request.POST)
        if form.is_valid():
            approved = form.cleaned_data['approved']

            if approved:
                # Process the approved credits application
                credit = Credit.objects.create(
                    user=credit_application.user,
                    amount=credit_application.amount,
                    interest_rate=5.0,  # Set your interest rate here
                    term_months=12,  # Set your term duration here
                    monthly_payment=calculate_monthly_payment(credit_application.amount),
                    remaining_amount=credit_application.amount,
                    status='APPROVED'
                )

                credit_application.status = 'APPROVED'
                credit_application.save()

                messages.success(request, f"Credit application approved.")
            else:
                # Reject the credits application
                credit_application.status = 'REJECTED'
                credit_application.save()

                messages.warning(request, f"Credit application rejected.")

            return redirect('credits:credit_list')

    else:
        form = CreditApprovalForm()

    return render(request, 'credits/credit_approval_form.html',
                  {'form': form, 'credit_application': credit_application})


def calculate_monthly_payment(loan_amount):
    # You need to implement a function to calculate the monthly payment based on your interest rate and term duration.
    # This is a simplified example; you may want to use a library or a more complex formula.
    interest_rate = Decimal('0.05')  # Example interest rate of 5%
    term_months = Decimal('12')  # Example term duration of 12 months

    monthly_interest_rate = interest_rate / Decimal('12')
    monthly_payment = (loan_amount * monthly_interest_rate) / (
                Decimal('1') - (Decimal('1') + monthly_interest_rate) ** -term_months)

    return round(monthly_payment, 2)


def active_credits(request):
    user_credits = Credit.objects.filter(user=request.user, status='APPROVED')
    return render(request, 'credits/active_credits.html', {'user_credits': user_credits})

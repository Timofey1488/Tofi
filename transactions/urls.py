from django.urls import path

from .views import fund_transfer, fund_transfer_card_by_card, TransactionMenu

app_name = 'transactions'


urlpatterns = [
    path('fund_transfer/', fund_transfer, name='fund_transfer'),
    path('fund_transfer_card_by_card/', fund_transfer_card_by_card, name='fund_transfer_card_by_card'),
    path('transaction_menu/', TransactionMenu.as_view(), name='transaction_menu'),
]

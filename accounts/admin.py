from django.contrib import admin

from .models import UserAim, User, UserAddress, UserBankAccount, Card, Payment

admin.site.register(UserAim)
admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount)
admin.site.register(Card)
admin.site.register(Payment)

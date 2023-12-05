from django.contrib import admin

from .models import UserAim, User, UserAddress, Card, Payment, SavingsGoal

admin.site.register(UserAim)
admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(Card)
admin.site.register(Payment)
admin.site.register(SavingsGoal)

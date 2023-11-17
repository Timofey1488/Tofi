from django.contrib import admin

from .models import UserAim, User, UserAddress, UserBankAccount


admin.site.register(UserAim)
admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount)

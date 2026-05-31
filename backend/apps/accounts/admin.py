from django.contrib import admin
from .models import UserAccount, Profile, ComplexManagerRequest


admin.site.register(UserAccount)
admin.site.register(Profile)
admin.site.register(ComplexManagerRequest)

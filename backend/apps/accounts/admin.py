from django.contrib import admin

from .models import ComplexManagerRequest, Profile, UserAccount

admin.site.register(UserAccount)
admin.site.register(Profile)
admin.site.register(ComplexManagerRequest)

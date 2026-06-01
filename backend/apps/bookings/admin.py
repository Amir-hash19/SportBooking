from django.contrib import admin

from .models import Booking, Payment

admin.site.register(Payment)
admin.site.register(Booking)

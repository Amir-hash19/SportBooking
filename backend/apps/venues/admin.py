from django.contrib import admin

from .models import Image, Pitch, Venue, WorkingHours

admin.site.register(Pitch)
admin.site.register(Image)
admin.site.register(WorkingHours)
admin.site.register(Venue)

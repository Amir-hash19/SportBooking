from django.contrib import admin

from .models import Image, Pitch, Venue, PitchSchedule

admin.site.register(Pitch)
admin.site.register(Image)
admin.site.register(PitchSchedule)
admin.site.register(Venue)

from django.contrib import admin
from .models import Event, EventRequest, EventComment

# Register your models here.
admin.site.register(Event)
admin.site.register(EventRequest)
admin.site.register(EventComment)

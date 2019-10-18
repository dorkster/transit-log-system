from django.contrib import admin
from schedule.models import Trip, Driver, Vehicle, TripType, Shift, Client

# Register your models here.
admin.site.register(Trip)
admin.site.register(Driver)
admin.site.register(Vehicle)
admin.site.register(TripType)
admin.site.register(Shift)
admin.site.register(Client)


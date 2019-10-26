from django.contrib import admin
from transit.models import Trip, Driver, Vehicle, TripType, Shift, Client, VehicleIssue

# Register your models here.
admin.site.register(Trip)
admin.site.register(Driver)
admin.site.register(Vehicle)
admin.site.register(TripType)
admin.site.register(Shift)
admin.site.register(Client)
admin.site.register(VehicleIssue)


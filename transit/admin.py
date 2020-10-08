from django.contrib import admin
from transit.models import Trip, Driver, Vehicle, TripType, Shift, Client, VehicleIssue, Template, TemplateTrip, ScheduleMessage, PreTrip, Fare, Tag, SiteSettings

# Register your models here.
admin.site.register(Trip)
admin.site.register(Driver)
admin.site.register(Vehicle)
admin.site.register(TripType)
admin.site.register(Shift)
admin.site.register(Client)
admin.site.register(VehicleIssue)
admin.site.register(Template)
admin.site.register(TemplateTrip)
admin.site.register(ScheduleMessage)
admin.site.register(PreTrip)
admin.site.register(Fare)
admin.site.register(Tag)
admin.site.register(SiteSettings)


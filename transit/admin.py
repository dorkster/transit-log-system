# Copyright © 2019-2021 Justin Jacobs
#
# This file is part of the Transit Log System.
#
# The Transit Log System is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# The Transit Log System is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# The Transit Log System.  If not, see http://www.gnu.org/licenses/

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


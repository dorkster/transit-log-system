# Copyright © 2019-2023 Justin Jacobs
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

import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Trip, TripDeltaTimeAverage

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

# from transit.common.eventlog import *
# from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

# from transit.common.util import move_item_in_queryset

@permission_required(['transit.change_trip'])
def tripDeltaTimeAverageRegen(request):
    trips = []
    regen = False

    if 'regen' in request.POST:
        regen = True

        TripDeltaTimeAverage.objects.all().delete()

        trips = Trip.objects.filter(format=Trip.FORMAT_NORMAL, status=Trip.STATUS_NORMAL).exclude(start_miles='', start_time='', end_miles='', end_time='')

        for trip in trips:
            try:
                start_time = datetime.datetime.strptime(trip.start_time, '%I:%M %p')
            except:
                print('Could not parse start time for: ' + str(trip))
                continue # time parsing failed, skip trip

            try:
                end_time = datetime.datetime.strptime(trip.end_time, '%I:%M %p')
            except:
                print('Could not parse end time for: ' + str(trip))
                continue # time parsing failed, skip trip

            if start_time > end_time:
                print('Invalid time delta for: ' + str(trip))
                continue # invalid time delta, skip trip

            trip_delta_time = end_time - start_time

            address_concat = ''
            if trip.address <= trip.destination:
                address_concat = trip.address + trip.destination
            else:
                address_concat = trip.destination + trip.address

            address_uuid = uuid.uuid5(uuid.NAMESPACE_URL, address_concat)

            query = TripDeltaTimeAverage.objects.filter(id=address_uuid)
            if len(query) > 0:
                trip_delta_time_obj = query[0]
            else:
                trip_delta_time_obj = TripDeltaTimeAverage()
                trip_delta_time_obj.id = address_uuid
            
            if (trip_delta_time_obj.avg_time == 0):
                trip_delta_time_obj.avg_time = trip_delta_time.total_seconds()
            else:
                trip_delta_time_obj.avg_time = int((trip_delta_time_obj.avg_time + trip_delta_time.total_seconds()) / 2)

            trip_delta_time_obj.save()

    context = {
        'trip_delta_times': TripDeltaTimeAverage.objects.all(),
        'regen': regen,
        'trips': trips,
    }
    return render(request, 'trip_delta_time_avg/regen.html', context=context)


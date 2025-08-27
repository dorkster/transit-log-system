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
from django.db.models import Q

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

        trips = Trip.objects.filter(format=Trip.FORMAT_NORMAL, status=Trip.STATUS_NORMAL, passenger=True).exclude(start_miles='', start_time='', end_miles='', end_time='')
        trip_times = {}

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

            if address_uuid not in trip_times:
                trip_times[address_uuid] = 0

            if trip_times[address_uuid] == 0:
                trip_times[address_uuid] = trip_delta_time.total_seconds()
            else:
                trip_times[address_uuid] = int((trip_times[address_uuid] + trip_delta_time.total_seconds()) / 2)

        for key in trip_times:
            trip_delta_time_obj = TripDeltaTimeAverage()
            trip_delta_time_obj.id = key
            trip_delta_time_obj.avg_time = trip_times[key]
            trip_delta_time_obj.save()


    context = {
        'trip_delta_times': TripDeltaTimeAverage.objects.all(),
        'regen': regen,
        'trips': trips,
    }
    return render(request, 'trip_delta_time_avg/regen.html', context=context)



def TripDeltaTimeAverageRegenSingle(src_trip):
    print('Generating avg trip time for: ' + str(src_trip))

    trips = Trip.objects.filter(format=Trip.FORMAT_NORMAL, status=Trip.STATUS_NORMAL, passenger=True).exclude(start_miles='', start_time='', end_miles='', end_time='')
    trips = trips.filter(Q(address=src_trip.address, destination=src_trip.destination) | Q(address=src_trip.destination, destination=src_trip.address))

    trip_times = {}

    address_concat = ''
    if src_trip.address <= src_trip.destination:
        address_concat = src_trip.address + src_trip.destination
    else:
        address_concat = src_trip.destination + src_trip.address

    address_uuid = uuid.uuid5(uuid.NAMESPACE_URL, address_concat)

    query = TripDeltaTimeAverage.objects.filter(id=address_uuid)
    if len(query) > 0:
        trip_delta_time_obj = query[0]
        trip_delta_time_obj.avg_time = 0
    else:
        trip_delta_time_obj = TripDeltaTimeAverage()
        trip_delta_time_obj.id = address_uuid

    trip_times[address_uuid] = trip_delta_time_obj.avg_time

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

        if trip_times[address_uuid] == 0:
            trip_times[address_uuid] = trip_delta_time.total_seconds()
        else:
            trip_times[address_uuid] = int((trip_times[address_uuid] + trip_delta_time.total_seconds()) / 2)

    trip_delta_time_obj.avg_time = trip_times[address_uuid]
    trip_delta_time_obj.save()


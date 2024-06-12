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

import datetime, uuid
import json
from difflib import SequenceMatcher

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core import serializers
from django.db.models import Q
from django.utils import timezone

from transit.models import Trip, Driver, Vehicle, Client, Shift, Tag, SiteSettings, Destination, Fare, Volunteer
from transit.forms import EditTripForm, tripStartForm, tripEndForm, EditActivityForm

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

def tripCreate(request, mode, year, month, day):
    trip = Trip()
    trip.date = datetime.date(year, month, day)
    return tripCreateEditCommon(request, mode, trip, is_new=True)

def tripCreateToday(request, mode):
    today = datetime.datetime.now().date()
    return tripCreate(request, mode, today.year, today.month, today.day)

def tripCreateTomorrow(request, mode):
    tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
    return tripCreate(request, mode, tomorrow.year, tomorrow.month, tomorrow.day)

def tripEdit(request, mode, id):
    trip = get_object_or_404(Trip, id=id)
    return tripCreateEditCommon(request, mode, trip, is_new=False)

def tripEditFromReport(request, start_year, start_month, start_day, end_year, end_month, end_day, id):
    date_start = {'year':start_year, 'month':start_month, 'day':start_day}
    date_end = {'year':end_year, 'month':end_month, 'day':end_day}
    trip = get_object_or_404(Trip, id=id)
    return tripCreateEditCommon(request, 'edit', trip, is_new=False, report_start=date_start, report_end=date_end)

def tripCreateReturn(request, mode, id):
    origin_trip = get_object_or_404(Trip, id=id)
    trip = Trip()
    trip.date = origin_trip.date
    trip.name = origin_trip.name
    trip.address = origin_trip.destination
    trip.phone_home = origin_trip.phone_home
    trip.phone_cell = origin_trip.phone_cell
    trip.phone_alt = origin_trip.phone_alt
    trip.phone_address = origin_trip.phone_destination
    trip.phone_destination = origin_trip.phone_address
    trip.destination = origin_trip.address
    trip.trip_type = origin_trip.trip_type
    trip.tags = origin_trip.tags
    trip.elderly = origin_trip.elderly
    trip.ambulatory = origin_trip.ambulatory
    trip.driver = origin_trip.driver
    trip.vehicle = origin_trip.vehicle
    trip.passenger = origin_trip.passenger
    trip.volunteer = origin_trip.volunteer

    return tripCreateEditCommon(request, mode, trip, is_new=True, is_return_trip=True)

def tripCopy(request, mode, id):
    origin_trip = get_object_or_404(Trip, id=id)
    trip = Trip()
    trip_id = trip.id
    trip = origin_trip
    trip.id = trip_id
    return tripCreateEditCommon(request, mode, trip, is_new=True)

def tripCreateActivity(request, mode, year, month, day):
    trip = Trip()
    trip.date = datetime.date(year, month, day)
    trip.format = Trip.FORMAT_ACTIVITY
    return tripCreateEditCommon(request, mode, trip, is_new=True)

def tripCreateFromClient(request, mode, id):
    client = get_object_or_404(Client, id=id)
    trip = Trip()
    trip.date = datetime.datetime.now().date()
    trip.name = client.name
    trip.phone_home = client.phone_home
    trip.phone_cell = client.phone_cell
    trip.phone_alt = client.phone_alt
    trip.elderly = client.elderly
    trip.ambulatory = client.ambulatory
    trip.tags = client.tags
    trip.reminder_instructions = client.reminder_instructions

    return tripCreateEditCommon(request, mode, trip, is_new=True)

@permission_required(['transit.change_trip'])
def tripCreateEditCommon(request, mode, trip, is_new, is_return_trip=False, report_start=None, report_end=None):
    if is_new == True:
        query = Trip.objects.filter(date=trip.date).order_by('-sort_index')
        if query.count() > 0:
            trip.sort_index = query[0].sort_index + 1
        else:
            trip.sort_index = 0

    if 'cancel' in request.POST:
        if report_start and report_end:
            return HttpResponseRedirect(reverse('report', kwargs={'start_year':report_start['year'], 'start_month':report_start['month'], 'start_day':report_start['day'], 'end_year':report_end['year'], 'end_month':report_end['month'], 'end_day':report_end['day']}))
        else:
            url_hash = '' if is_new else '#trip_' + str(trip.id)
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + url_hash)
    elif 'delete' in request.POST:
        return HttpResponseRedirect(reverse('trip-delete', kwargs={'mode':mode, 'id':trip.id}))

    if request.method == 'POST':
        if trip.format == Trip.FORMAT_ACTIVITY:
            form = EditActivityForm(request.POST)
        else:
            form = EditTripForm(request.POST)

        if trip.driver:
            form.fields['driver'].queryset = Driver.objects.filter(Q(is_active=True) | Q(id=trip.driver.id))

        if trip.volunteer:
            form.fields['volunteer'].queryset = Volunteer.objects.filter(Q(is_active=True) | Q(id=trip.volunteer.id))

        if form.is_valid():
            old_date = trip.date

            if trip.format == Trip.FORMAT_ACTIVITY:
                trip.date = form.cleaned_data['date']
                trip.pick_up_time = form.cleaned_data['start_time']
                trip.appointment_time = form.cleaned_data['end_time']
                trip.note = form.cleaned_data['description']
                trip.status = form.cleaned_data['status']
                trip.activity_color = form.cleaned_data['activity_color']

                if trip.pick_up_time == trip.appointment_time:
                    trip.appointment_time = ''

                trip.driver = form.cleaned_data['driver']
                trip.passenger = form.cleaned_data['driver_is_available']
            else:
                trip.date = form.cleaned_data['date']
                trip.name = form.cleaned_data['name']
                trip.address = form.cleaned_data['address']
                trip.phone_home = form.cleaned_data['phone_home']
                trip.phone_cell = form.cleaned_data['phone_cell']
                trip.phone_alt = form.cleaned_data['phone_alt']
                trip.phone_address = form.cleaned_data['phone_address']
                trip.phone_destination = form.cleaned_data['phone_destination']
                trip.destination = form.cleaned_data['destination']
                trip.pick_up_time = form.cleaned_data['pick_up_time']
                trip.appointment_time = form.cleaned_data['appointment_time']
                trip.trip_type = form.cleaned_data['trip_type']
                trip.tags = form.cleaned_data['tags']
                trip.elderly = form.cleaned_data['elderly']
                trip.ambulatory = form.cleaned_data['ambulatory']
                trip.driver = form.cleaned_data['driver']
                trip.vehicle = form.cleaned_data['vehicle']
                trip.start_miles = form.cleaned_data['start_miles']
                trip.start_time = form.cleaned_data['start_time']
                trip.end_miles = form.cleaned_data['end_miles']
                trip.end_time = form.cleaned_data['end_time']
                trip.note = form.cleaned_data['notes']
                trip.status = form.cleaned_data['status']
                trip.collected_cash = money_string_to_int(form.cleaned_data['collected_cash'])
                trip.collected_check = money_string_to_int(form.cleaned_data['collected_check'])
                trip.fare = money_string_to_int(form.cleaned_data['fare'])
                trip.passenger = form.cleaned_data['passenger']
                trip.reminder_instructions = form.cleaned_data['reminder_instructions']
                trip.volunteer = form.cleaned_data['volunteer']

                # set the wheelchair flag if the corresponding tag exists
                tag_list = trip.get_tag_list()
                trip.wheelchair = ('Wheelchair' in tag_list)

            trip.cancel_date = None
            try:
                if int(trip.status) == Trip.STATUS_CANCELED:
                    trip.cancel_date = timezone.make_aware(datetime.datetime.combine(form.cleaned_data['cancel_date'], datetime.datetime.min.time()))
            except:
                pass

            if trip.cancel_date:
                try:
                    cancel_time = datetime.datetime.strptime(form.cleaned_data['cancel_time'], '%I:%M %p')
                    cancel_datetime = datetime.datetime.combine(trip.cancel_date, cancel_time.time())
                    trip.cancel_date = timezone.make_aware(cancel_datetime)
                except:
                    pass

            # trip date changed, which means sort indexes need to be updated
            if old_date != trip.date:
                # decrease sort indexes on the old date to fill in the gap
                if not is_new:
                    trips_below = Trip.objects.filter(date=old_date, sort_index__gt=trip.sort_index)
                    for i in trips_below:
                        i.sort_index -= 1
                        i.save()
                # set the sort index on the new day
                query = Trip.objects.filter(date=trip.date).order_by('-sort_index')
                if query.count() > 0:
                    trip.sort_index = query[0].sort_index + 1
                else:
                    trip.sort_index = 0

            trip.save()

            if trip.format == Trip.FORMAT_ACTIVITY:
                log_model = LoggedEventModel.TRIP_ACTIVITY
            else:
                log_model = LoggedEventModel.TRIP

            if is_new:
                log_event(request, LoggedEventAction.CREATE, log_model, str(trip))
            else:
                log_event(request, LoggedEventAction.EDIT, log_model, str(trip))

            # Update empty Elderly/Ambulatory fields in Client data if they've been defined in this Trip
            if trip.format == Trip.FORMAT_NORMAL and (trip.elderly != None or trip.ambulatory != None):
                update_clients = Client.objects.filter(Q(elderly=None) | Q(ambulatory=None)).filter(name=trip.name)
                if update_clients.count() == 1:
                    update_client = update_clients[0]
                    client_was_updated = False
                    if update_client.elderly == None:
                        client_was_updated = True
                        update_client.elderly = trip.elderly
                    if update_client.ambulatory == None:
                        client_was_updated = True
                        update_client.ambulatory = trip.ambulatory
                    if client_was_updated == True:
                        update_client.save()
                        log_event(request, LoggedEventAction.EDIT, LoggedEventModel.CLIENT, str(update_client))

            if is_new and not is_return_trip and trip.format == Trip.FORMAT_NORMAL:
                if form.cleaned_data['add_client'] == True:
                    client = Client()
                    client.name = form.cleaned_data['name']
                    client.address = form.cleaned_data['address']
                    client.phone_home = form.cleaned_data['phone_home']
                    client.phone_cell = form.cleaned_data['phone_cell']
                    client.phone_alt = form.cleaned_data['phone_alt']
                    client.elderly = form.cleaned_data['elderly']
                    client.ambulatory = form.cleaned_data['ambulatory']
                    client.reminder_instructions = form.cleaned_data['reminder_instructions']
                    client.save()
                    log_event(request, LoggedEventAction.CREATE, LoggedEventModel.CLIENT, str(client))
                if form.cleaned_data['add_dest1'] == True:
                    destination = Destination()
                    destination.address = form.cleaned_data['address']
                    destination.phone = form.cleaned_data['phone_address']
                    destination.save()
                if form.cleaned_data['add_dest2'] == True:
                    destination = Destination()
                    destination.address = form.cleaned_data['destination']
                    destination.phone = form.cleaned_data['phone_destination']
                    destination.save()

                if form.cleaned_data['create_return_trip'] == True:
                    return HttpResponseRedirect(reverse('trip-create-return', kwargs={'mode':mode, 'id':trip.id}))

            if report_start and report_end:
                return HttpResponseRedirect(reverse('report', kwargs={'start_year':report_start['year'], 'start_month':report_start['month'], 'start_day':report_start['day'], 'end_year':report_end['year'], 'end_month':report_end['month'], 'end_day':report_end['day']}))
            else:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))
    else:
        cancel_date = trip.cancel_date
        cancel_time = ''

        if cancel_date == None:
            cancel_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

        if timezone.is_aware(cancel_date):
            cancel_date = timezone.make_naive(cancel_date)
            try:
                cancel_time = cancel_date.strftime('%-I:%M %p')
            except:
                pass
        else:
            cancel_time = datetime.datetime.now().strftime('%-I:%M %p')

        if trip.format == Trip.FORMAT_ACTIVITY:
            initial = {
                'date': trip.date,
                'start_time': trip.pick_up_time,
                'end_time': trip.appointment_time,
                'description': trip.note,
                'status': trip.status,
                'cancel_date': cancel_date.date(),
                'cancel_time': cancel_time,
                'activity_color': trip.activity_color,
                'driver': trip.driver,
                'driver_is_available': False if is_new else trip.passenger
            }
            form = EditActivityForm(initial=initial)
        else:
            initial = {
                'date': trip.date,
                'name': trip.name,
                'address': trip.address,
                'phone_home': trip.phone_home,
                'phone_cell': trip.phone_cell,
                'phone_alt': trip.phone_alt,
                'phone_address': trip.phone_address,
                'phone_destination': trip.phone_destination,
                'destination': trip.destination,
                'pick_up_time': trip.pick_up_time,
                'appointment_time': trip.appointment_time,
                'trip_type': trip.trip_type,
                'tags': trip.tags,
                'elderly': trip.elderly,
                'ambulatory': trip.ambulatory,
                'driver': trip.driver,
                'vehicle': trip.vehicle,
                'start_miles': trip.start_miles,
                'start_time': trip.start_time,
                'end_miles': trip.end_miles,
                'end_time': trip.end_time,
                'notes': trip.note,
                'status': trip.status,
                'collected_cash': int_to_money_string(trip.collected_cash, blank_zero=True),
                'collected_check': int_to_money_string(trip.collected_check, blank_zero=True),
                'fare': int_to_money_string(trip.fare, blank_zero=True),
                'passenger': trip.passenger,
                'reminder_instructions': trip.reminder_instructions,
                'volunteer': trip.volunteer,
                'cancel_date': cancel_date.date(),
                'cancel_time': cancel_time,
            }
            form = EditTripForm(initial=initial)

        if trip.driver:
            form.fields['driver'].queryset = Driver.objects.filter(Q(is_active=True) | Q(id=trip.driver.id))

        if trip.volunteer:
            form.fields['volunteer'].queryset = Volunteer.objects.filter(Q(is_active=True) | Q(id=trip.volunteer.id))

    addresses = set()
    destinations = Destination.objects.filter(is_active=True)

    if destinations.count() == 0:
        site_settings = SiteSettings.load()
        if site_settings.autocomplete_history_days > 0:
            for i in Trip.objects.filter(date__gte=(datetime.date.today() - datetime.timedelta(days=site_settings.autocomplete_history_days-1))):
                if i.address:
                    addresses.add(str(i.address))
                if i.destination:
                    addresses.add(str(i.destination))

    clients = Client.objects.filter(is_active=True)

    driver_vehicle_pairs = {}
    nonlogged_vehicles = Vehicle.objects.filter(is_logged=False)
    active_drivers = Driver.objects.filter(is_active=True)
    todays_shifts = Shift.objects.filter(date=trip.date)

    for driver in active_drivers:
        if driver.is_logged:
            for shift in todays_shifts:
                if driver == shift.driver:
                    driver_vehicle_pairs[str(driver.id)] = {'vehicle': str(shift.vehicle.id), 'volunteer': 0}
                    break
            if not str(driver.id) in driver_vehicle_pairs:
                driver_vehicle_pairs[str(driver.id)] = {'vehicle': '', 'volunteer': 0}
        elif not driver.is_logged and nonlogged_vehicles.count() == 1:
            driver_vehicle_pairs[str(driver.id)] = {'vehicle': str(nonlogged_vehicles[0].id), 'volunteer': 0}
        else:
            driver_vehicle_pairs[str(driver.id)] = {'vehicle': '', 'volunteer': 0}

        # TODO get from SiteSettings
        if driver.name == 'Volunteer':
            driver_vehicle_pairs[str(driver.id)]['volunteer'] = 1

    context = {
        'form': form,
        'trip': trip,
        'clients': clients,
        'clients_json': serializers.serialize('json', clients),
        'addresses': sorted(addresses),
        'destinations': destinations,
        'destinations_json': serializers.serialize('json', destinations),
        'is_new': is_new,
        'is_return_trip': is_return_trip,
        'tags': Tag.objects.all(),
        'fares': Fare.objects.all(),
        'Trip': Trip,
        'driver_vehicle_pairs': json.dumps(driver_vehicle_pairs),
    }

    return render(request, 'trip/edit.html', context)

@permission_required(['transit.delete_trip'])
def tripDelete(request, mode, id):
    trip = get_object_or_404(Trip, id=id)
    date = trip.date

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('trip-edit', kwargs={'mode':mode, 'id':id}))

        query = Trip.objects.filter(date=trip.date)
        for i in query:
            if i.sort_index > trip.sort_index:
                i.sort_index -= 1;
                i.save()

        log_model = LoggedEventModel.TRIP_ACTIVITY if trip.format == Trip.FORMAT_ACTIVITY else LoggedEventModel.TRIP
        log_event(request, LoggedEventAction.DELETE, log_model, str(trip))

        trip.delete()
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':date.year, 'month':date.month, 'day':date.day}))

    context = {
        'model': trip,
    }

    return render(request, 'model_delete.html', context)

def getStartAndPrevMiles(date, start_miles, prev_miles, vehicles, all_trips):
    active_shift_driver = None

    # get the starting mileage for all vehicles
    all_previous_shifts = Shift.objects.exclude(start_miles='').exclude(end_miles='')
    for vehicle in vehicles.filter(is_logged=True):
        start_miles[str(vehicle)] = ''
        previous_shift = None
        previous_shifts = all_previous_shifts.filter(vehicle=vehicle)
        for i in previous_shifts:
            try:
                if previous_shift == None or float(i.end_miles) >= float(previous_shift.end_miles):
                    previous_shift = i
            except:
                continue

        if previous_shift != None:
            start_miles[str(vehicle)] = previous_shift.end_miles

    day_shifts = Shift.objects.filter(date=date)
    for shift in day_shifts:
        if shift.start_miles != '':
            try:
                if float(shift.start_miles) > float(start_miles[str(shift.vehicle)]):
                    start_miles[str(shift.vehicle)] = shift.start_miles
            except:
                continue

            if shift.end_miles == '':
                active_shift_driver = shift.driver

    # get the previous trip milage for all vehicles
    for vehicle in vehicles:
        if str(vehicle) in start_miles:
            start_miles_str = start_miles[str(vehicle)]
        else:
            start_miles_str = start_miles[str(vehicle)] = ''
        prev_miles[str(vehicle)] = start_miles_str
        vehicle_trips = all_trips.filter(vehicle=vehicle, driver=active_shift_driver)
        for vehicle_trip in vehicle_trips:
            if vehicle_trip.end_miles != '':
                mile_str = vehicle_trip.end_miles
            elif vehicle_trip.start_miles != '':
                mile_str = vehicle_trip.start_miles
            else:
                continue

            if len(mile_str) < len(start_miles_str):
                mile_str = start_miles_str[0:len(start_miles_str) - len(mile_str)] + mile_str

            try:
                if mile_str != '' and float(mile_str) > float(prev_miles[str(vehicle)]):
                    prev_miles[str(vehicle)] = mile_str
            except:
                continue

@permission_required(['transit.change_trip'])
def tripStart(request, id):
    trip = get_object_or_404(Trip, id=id)
    date = trip.date

    start_miles = dict()
    prev_miles = dict()
    all_trips = Trip.objects.filter(date=trip.date, status=Trip.STATUS_NORMAL)
    getStartAndPrevMiles(date, start_miles, prev_miles, Vehicle.objects.all(), all_trips)

    if request.method == 'POST':
        form = tripStartForm(request.POST)

        if trip.driver:
            form.fields['driver'].queryset = Driver.objects.filter(Q(is_active=True, is_logged=True) | Q(id=trip.driver.id))

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))

        if form.is_valid():
            trip.start_miles = form.cleaned_data['miles']
            trip.start_time = form.cleaned_data['time']
            trip.driver = form.cleaned_data['driver']
            trip.vehicle = form.cleaned_data['vehicle']
            trip.collected_cash = money_string_to_int(form.cleaned_data['collected_cash'])
            trip.collected_check = money_string_to_int(form.cleaned_data['collected_check'])
            trip.save()
            log_event(request, LoggedEventAction.LOG_START, LoggedEventModel.TRIP, str(trip))

            if form.cleaned_data['additional_pickups'] != '':
                additional_pickups = json.loads(form.cleaned_data['additional_pickups'])
                for key in additional_pickups:
                    if additional_pickups[key] is True:
                        a_trip = Trip.objects.get(id=uuid.UUID(key))
                        a_trip.start_miles = form.cleaned_data['miles']
                        a_trip.start_time = form.cleaned_data['time']
                        a_trip.driver = form.cleaned_data['driver']
                        a_trip.vehicle = form.cleaned_data['vehicle']
                        a_trip.save()
                        log_event(request, LoggedEventAction.LOG_START, LoggedEventModel.TRIP, str(a_trip))

            # check to see if a matching Shift exists. If not, create it
            trip_shifts = Shift.objects.filter(date=trip.date, driver=trip.driver, vehicle=trip.vehicle)
            trip_shift = None
            if trip_shifts.exists():
                if trip_shifts[0].start_miles == '' and trip_shifts[0].start_time == '':
                    trip_shift = trip_shifts[0]
            else:
                trip_shift = Shift()
                trip_shift.date = trip.date
                trip_shift.driver = trip.driver
                trip_shift.vehicle = trip.vehicle
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.SHIFT, str(trip_shift))

            if trip_shift and trip_shift.vehicle.is_logged:
                if str(trip_shift.vehicle) in start_miles:
                    shift_start_miles = start_miles[str(trip_shift.vehicle)]
                else:
                    shift_start_miles = start_miles[str(trip_shift.vehicle)] = ''
                if len(trip.start_miles) < len(shift_start_miles):
                    trip_shift.start_miles = shift_start_miles[0:len(shift_start_miles)-len(trip.start_miles)] + trip.start_miles
                else:
                    trip_shift.start_miles = trip.start_miles
                trip_shift.start_time = trip.start_time
                trip_shift.save()
                log_event(request, LoggedEventAction.LOG_START, LoggedEventModel.SHIFT, str(trip_shift))

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))
    else:
        auto_time = trip.start_time
        if auto_time == '':
            auto_time = datetime.datetime.now().strftime('%-I:%M %p')

        initial = {
            'miles': trip.start_miles,
            'time': auto_time,
            'driver': trip.driver,
            'vehicle': trip.vehicle,
            'collected_cash': int_to_money_string(trip.collected_cash, blank_zero=True),
            'collected_check': int_to_money_string(trip.collected_check, blank_zero=True),
        }
        form = tripStartForm(initial=initial)
        if trip.driver:
            form.fields['driver'].queryset = Driver.objects.filter(Q(is_active=True, is_logged=True) | Q(id=trip.driver.id))

    site_settings = SiteSettings.load()
    additional_pickups = []
    additional_pickups_fuzzy = []
    if trip.address != '':
        for i in all_trips:
            if i.id == trip.id:
                continue
            if i.start_miles == '' and i.start_time == '':
                ratio = SequenceMatcher(None, i.address, trip.address).ratio()
                if ratio >= 1:
                    additional_pickups.append(i)
                elif ratio >= site_settings.additional_pickup_fuzziness:
                    additional_pickups_fuzzy.append(i)

    driver_vehicle_pairs = {}
    nonlogged_vehicles = Vehicle.objects.filter(is_logged=False)
    active_drivers = Driver.objects.filter(is_active=True)
    todays_shifts = Shift.objects.filter(date=trip.date)

    for driver in active_drivers:
        if driver.is_logged:
            for shift in todays_shifts:
                if driver == shift.driver:
                    driver_vehicle_pairs[str(driver.id)] = {'vehicle': str(shift.vehicle.id), 'volunteer': 0}
                    break
            if not str(driver.id) in driver_vehicle_pairs:
                driver_vehicle_pairs[str(driver.id)] = {'vehicle': '', 'volunteer': 0}
        elif not driver.is_logged and nonlogged_vehicles.count() == 1:
            driver_vehicle_pairs[str(driver.id)] = {'vehicle': str(nonlogged_vehicles[0].id), 'volunteer': 0}
        else:
            driver_vehicle_pairs[str(driver.id)] = {'vehicle': '', 'volunteer': 0}

        # TODO get from SiteSettings
        if driver.name == 'Volunteer':
            driver_vehicle_pairs[str(driver.id)]['volunteer'] = 1

    context = {
        'form': form,
        'trip': trip,
        'start_miles': start_miles,
        'prev_miles': prev_miles,
        'additional_pickups': additional_pickups,
        'additional_pickups_fuzzy': additional_pickups_fuzzy,
        'driver_vehicle_pairs': json.dumps(driver_vehicle_pairs),
    }

    return render(request, 'trip/start.html', context)

@permission_required(['transit.change_trip'])
def tripEnd(request, id):
    trip = get_object_or_404(Trip, id=id)
    date = trip.date

    start_miles = dict()
    prev_miles = dict()
    all_trips = Trip.objects.filter(date=trip.date, status=Trip.STATUS_NORMAL)
    getStartAndPrevMiles(date, start_miles, prev_miles, Vehicle.objects.filter(id=trip.vehicle.id, is_logged=True), all_trips)

    clients = Client.objects.filter(name=trip.name)
    if clients.count() == 1:
        client = clients[0]
    else:
        client = None

    if request.method == 'POST':
        form = tripEndForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))

        if form.is_valid():
            trip.end_miles = form.cleaned_data['miles']
            trip.end_time = form.cleaned_data['time']
            trip.collected_cash = money_string_to_int(form.cleaned_data['collected_cash'])
            trip.collected_check = money_string_to_int(form.cleaned_data['collected_check'])

            if client and form.cleaned_data['home_drop_off'] == True:
                trip.destination = client.address

            trip.save()
            log_event(request, LoggedEventAction.LOG_END, LoggedEventModel.TRIP, str(trip))

            if form.cleaned_data['additional_pickups'] != '':
                additional_pickups = json.loads(form.cleaned_data['additional_pickups'])
                for key in additional_pickups:
                    if additional_pickups[key] is True:
                        a_trip = Trip.objects.get(id=uuid.UUID(key))
                        a_trip.end_miles = form.cleaned_data['miles']
                        a_trip.end_time = form.cleaned_data['time']

                        if client and form.cleaned_data['home_drop_off'] == True:
                            a_trip.destination = client.address

                        a_trip.save()
                        log_event(request, LoggedEventAction.LOG_END, LoggedEventModel.TRIP, str(a_trip))

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))
    else:
        auto_time = trip.end_time
        if auto_time == '':
            auto_time = datetime.datetime.now().strftime('%-I:%M %p')

        initial = {
            'miles': trip.end_miles,
            'time': auto_time,
            'collected_cash': int_to_money_string(trip.collected_cash, blank_zero=True),
            'collected_check': int_to_money_string(trip.collected_check, blank_zero=True),
            'home_drop_off': False,
        }
        form = tripEndForm(initial=initial)

    site_settings = SiteSettings.load()
    additional_pickups = []
    additional_pickups_fuzzy = []
    if trip.destination != '':
        for i in all_trips:
            if i.id == trip.id:
                continue
            if i.end_miles == '' and i.end_time == '':
                ratio = SequenceMatcher(None, i.destination, trip.destination).ratio()
                if ratio >= 1:
                    additional_pickups.append(i)
                elif ratio >= site_settings.additional_pickup_fuzziness:
                    additional_pickups_fuzzy.append(i)

    context = {
        'form': form,
        'trip': trip,
        'client': client,
        'start_miles': start_miles,
        'prev_miles': prev_miles,
        'additional_pickups': additional_pickups,
        'additional_pickups_fuzzy': additional_pickups_fuzzy,
    }

    return render(request, 'trip/end.html', context)


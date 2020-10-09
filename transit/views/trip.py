import datetime, uuid
import json

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers

from transit.models import Trip, Driver, Vehicle, Client, Shift, Tag, SiteSettings, Destination, Fare
from transit.forms import EditTripForm, tripStartForm, tripEndForm, EditActivityForm

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

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
    trip.phone_address = origin_trip.phone_destination
    trip.phone_destination = origin_trip.phone_address
    trip.destination = origin_trip.address
    trip.trip_type = origin_trip.trip_type
    trip.tags = origin_trip.tags
    trip.elderly = origin_trip.elderly
    trip.ambulatory = origin_trip.ambulatory
    trip.driver = origin_trip.driver
    trip.vehicle = origin_trip.vehicle

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
    trip.is_activity = True
    return tripCreateEditCommon(request, mode, trip, is_new=True)

def tripCreateFromClient(request, mode, id):
    client = get_object_or_404(Client, id=id)
    trip = Trip()
    trip.date = datetime.datetime.now().date()
    trip.name = client.name
    trip.phone_home = client.phone_home
    trip.phone_cell = client.phone_cell
    trip.elderly = client.elderly
    trip.ambulatory = client.ambulatory
    trip.tags = client.tags

    return tripCreateEditCommon(request, mode, trip, is_new=True)

@permission_required(['transit.change_trip'])
def tripCreateEditCommon(request, mode, trip, is_new, is_return_trip=False, report_start=None, report_end=None):
    if is_new == True:
        query = Trip.objects.filter(date=trip.date).order_by('-sort_index')
        if len(query) > 0:
            last_trip = query[0]
            trip.sort_index = last_trip.sort_index + 1
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
        if trip.is_activity:
            form = EditActivityForm(request.POST)
        else:
            form = EditTripForm(request.POST)

        if form.is_valid():
            old_date = trip.date

            if trip.is_activity:
                trip.date = form.cleaned_data['date']
                trip.pick_up_time = form.cleaned_data['start_time']
                trip.appointment_time = form.cleaned_data['end_time']
                trip.note = form.cleaned_data['description']
                trip.status = form.cleaned_data['status']

                if trip.pick_up_time == trip.appointment_time:
                    trip.appointment_time = ''
            else:
                trip.date = form.cleaned_data['date']
                trip.name = form.cleaned_data['name']
                trip.address = form.cleaned_data['address']
                trip.phone_home = form.cleaned_data['phone_home']
                trip.phone_cell = form.cleaned_data['phone_cell']
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
                if len(query) > 0:
                    trip.sort_index = query[0].sort_index + 1
                else:
                    trip.sort_index = 0

            trip.save()

            if is_new and not is_return_trip and not trip.is_activity:
                if form.cleaned_data['add_client'] == True:
                    client = Client()
                    client.name = form.cleaned_data['name']
                    client.address = form.cleaned_data['address']
                    client.phone_home = form.cleaned_data['phone_home']
                    client.phone_cell = form.cleaned_data['phone_cell']
                    client.elderly = form.cleaned_data['elderly']
                    client.ambulatory = form.cleaned_data['ambulatory']
                    client.save()

                if form.cleaned_data['create_return_trip'] == True:
                    return HttpResponseRedirect(reverse('trip-create-return', kwargs={'mode':mode, 'id':trip.id}))

            if report_start and report_end:
                return HttpResponseRedirect(reverse('report', kwargs={'start_year':report_start['year'], 'start_month':report_start['month'], 'start_day':report_start['day'], 'end_year':report_end['year'], 'end_month':report_end['month'], 'end_day':report_end['day']}))
            else:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))
    else:
        if trip.is_activity:
            initial = {
                'date': trip.date,
                'start_time': trip.pick_up_time,
                'end_time': trip.appointment_time,
                'description': trip.note,
                'status': trip.status,
            }
            form = EditActivityForm(initial=initial)
        else:
            initial = {
                'date': trip.date,
                'name': trip.name,
                'address': trip.address,
                'phone_home': trip.phone_home,
                'phone_cell': trip.phone_cell,
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
            }
            form = EditTripForm(initial=initial)

    addresses = set()
    destinations = Destination.objects.all()

    if len(destinations) == 0:
        site_settings = SiteSettings.load()
        if site_settings.autocomplete_history_days > 0:
            for i in Trip.objects.filter(date__gte=(datetime.date.today() - datetime.timedelta(days=site_settings.autocomplete_history_days-1))):
                if i.address:
                    addresses.add(str(i.address))
                if i.destination:
                    addresses.add(str(i.destination))

    context = {
        'form': form,
        'trip': trip,
        'clients': Client.objects.all(),
        'clients_json': serializers.serialize('json', Client.objects.all()),
        'addresses': sorted(addresses),
        'destinations': destinations,
        'destinations_json': serializers.serialize('json', Destination.objects.all()),
        'is_new': is_new,
        'is_return_trip': is_return_trip,
        'tags': Tag.objects.all(),
        'fares': Fare.objects.all(),
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

        trip.delete()
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':date.year, 'month':date.month, 'day':date.day}))

    context = {
        'model': trip,
    }

    return render(request, 'model_delete.html', context)

@permission_required(['transit.change_trip'])
def tripStart(request, id):
    trip = get_object_or_404(Trip, id=id)
    date = trip.date

    if request.method == 'POST':
        form = tripStartForm(request.POST)

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

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))
    else:
        auto_time = trip.start_time
        if auto_time == '':
            auto_time = datetime.datetime.now().strftime('%_I:%M %p')

        initial = {
            'miles': trip.start_miles,
            'time': auto_time,
            'driver': trip.driver,
            'vehicle': trip.vehicle,
            'collected_cash': int_to_money_string(trip.collected_cash, blank_zero=True),
            'collected_check': int_to_money_string(trip.collected_check, blank_zero=True),
        }
        form = tripStartForm(initial=initial)

    start_miles = dict()
    for vehicle in Vehicle.objects.all():
        start_miles[str(vehicle)] = ''

    day_shifts = Shift.objects.filter(date=trip.date)
    for shift in day_shifts:
        if start_miles[str(shift.vehicle)] == '':
            try:
                test_float = float(shift.start_miles)
                start_miles[str(shift.vehicle)] = shift.start_miles
            except:
                continue

        try:
            if shift.start_miles != '' and float(start_miles[str(shift.vehicle)]) > float(shift.start_miles):
                start_miles[str(shift.vehicle)] = shift.start_miles
        except:
            continue

    all_trips = Trip.objects.filter(date=trip.date, status=Trip.STATUS_NORMAL)
    additional_pickups = []
    if trip.address != '':
        for i in all_trips:
            if i.id == trip.id:
                continue
            if i.address == trip.address and (i.start_miles == '' and i.start_time == ''):
                additional_pickups.append(i)

    prev_miles = dict()
    for vehicle in Vehicle.objects.all():
        start_miles_str = start_miles[str(vehicle)]
        prev_miles[str(vehicle)] = start_miles_str
        vehicle_trips = all_trips.filter(vehicle=vehicle)
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

    context = {
        'form': form,
        'trip': trip,
        'start_miles': start_miles,
        'prev_miles': prev_miles,
        'additional_pickups': additional_pickups,
    }

    return render(request, 'trip/start.html', context)

@permission_required(['transit.change_trip'])
def tripEnd(request, id):
    trip = get_object_or_404(Trip, id=id)
    date = trip.date

    if request.method == 'POST':
        form = tripEndForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))

        if form.is_valid():
            trip.end_miles = form.cleaned_data['miles']
            trip.end_time = form.cleaned_data['time']
            trip.save()

            if form.cleaned_data['additional_pickups'] != '':
                additional_pickups = json.loads(form.cleaned_data['additional_pickups'])
                for key in additional_pickups:
                    if additional_pickups[key] is True:
                        a_trip = Trip.objects.get(id=uuid.UUID(key))
                        a_trip.end_miles = form.cleaned_data['miles']
                        a_trip.end_time = form.cleaned_data['time']
                        a_trip.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + '#trip_' + str(trip.id))
    else:
        auto_time = trip.end_time
        if auto_time == '':
            auto_time = datetime.datetime.now().strftime('%_I:%M %p')

        initial = {
            'miles': trip.end_miles,
            'time': auto_time,
        }
        form = tripEndForm(initial=initial)

    start_miles = dict()
    for vehicle in Vehicle.objects.all():
        start_miles[str(vehicle)] = ''

    query = Shift.objects.filter(date=trip.date)
    for shift in query:
        if start_miles[str(shift.vehicle)] == '':
            try:
                test_float = float(shift.start_miles)
                start_miles[str(shift.vehicle)] = shift.start_miles
            except:
                continue

        try:
            if shift.start_miles != '' and float(start_miles[str(shift.vehicle)]) > float(shift.start_miles):
                start_miles[str(shift.vehicle)] = shift.start_miles
        except:
            continue

    all_trips = Trip.objects.filter(date=trip.date, status=Trip.STATUS_NORMAL)
    additional_pickups = []
    if trip.destination != '':
        for i in all_trips:
            if i.id == trip.id:
                continue
            if i.destination == trip.destination and (i.end_miles == '' and i.end_time == ''):
                additional_pickups.append(i)

    prev_miles = dict()
    for vehicle in Vehicle.objects.all():
        start_miles_str = start_miles[str(vehicle)]
        prev_miles[str(vehicle)] = start_miles_str
        vehicle_trips = all_trips.filter(vehicle=vehicle)
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

    context = {
        'form': form,
        'trip': trip,
        'start_miles': start_miles,
        'prev_miles': prev_miles,
        'additional_pickups': additional_pickups,
    }

    return render(request, 'trip/end.html', context)

@permission_required(['transit.change_trip'])
def ajaxSetVehicleFromDriver(request):
    date = datetime.date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))

    data = {}

    if request.GET['driver'] == '':
        data['vehicle'] = ''
    else:
        driver = Driver.objects.filter(id=uuid.UUID(request.GET['driver']))[0]
        shifts = Shift.objects.filter(date=date, driver=driver)
        if len(shifts) > 0:
            data['vehicle'] = str(shifts[0].vehicle.id)
        else:
            data['vehicle'] = ''

            # if there's only 1 non-logged vehicle (e.g. 'personal'), use it for non-logged drivers
            if not driver.is_logged:
                nonlogged_vehicles = Vehicle.objects.filter(is_logged=False)
                if len(nonlogged_vehicles) == 1:
                    data['vehicle'] = str(nonlogged_vehicles[0].id)

    return JsonResponse(data)


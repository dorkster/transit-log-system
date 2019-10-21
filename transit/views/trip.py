import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers

from transit.models import Trip, Driver, Vehicle, Client, Shift
from transit.forms import EditTripForm, tripStartForm, tripEndForm

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

def tripCreateEditCommon(request, mode, trip, is_new):
    if is_new == True:
        query = Trip.objects.filter(date=trip.date).order_by('-sort_index')
        if len(query) > 0:
            last_trip = query[0]
            trip.sort_index = last_trip.sort_index + 1
        else:
            trip.sort_index = 0

    if 'cancel' in request.POST:
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + "#trip_" + str(trip.id))
    elif 'delete' in request.POST:
        return HttpResponseRedirect(reverse('trip-delete', kwargs={'mode':mode, 'id':trip.id}))

    if request.method == 'POST':
        form = EditTripForm(request.POST)

        if form.is_valid():
            old_date = trip.date

            trip.date = form.cleaned_data['date']
            trip.name = form.cleaned_data['name']
            trip.address = form.cleaned_data['address']
            trip.phone = form.cleaned_data['phone']
            trip.destination = form.cleaned_data['destination']
            trip.pick_up_time = form.cleaned_data['pick_up_time']
            trip.appointment_time = form.cleaned_data['appointment_time']
            trip.trip_type = form.cleaned_data['trip_type']
            trip.elderly = form.cleaned_data['elderly']
            trip.ambulatory = form.cleaned_data['ambulatory']
            trip.driver = form.cleaned_data['driver']
            trip.vehicle = form.cleaned_data['vehicle']
            trip.start_miles = form.cleaned_data['start_miles']
            trip.start_time = form.cleaned_data['start_time']
            trip.end_miles = form.cleaned_data['end_miles']
            trip.end_time = form.cleaned_data['end_time']
            trip.note = form.cleaned_data['notes']
            trip.is_canceled = form.cleaned_data['is_canceled']

            # trip date changed, which means sort indexes need to be updated
            if old_date != trip.date:
                trips_below = Trip.objects.filter(date=old_date, sort_index__gt=trip.sort_index)
                for i in trips_below:
                    i.sort_index -= 1
                    i.save()
                query = Trip.objects.filter(date=trip.date).order_by('-sort_index')
                if len(query) > 0:
                    trip.sort_index = query[0].sort_index + 1
                else:
                    trip.sort_index = 0

            trip.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + "#trip_" + str(trip.id))
    else:
        initial = {
            'date': trip.date,
            'name': trip.name,
            'address': trip.address,
            'phone': trip.phone,
            'destination': trip.destination,
            'pick_up_time': trip.pick_up_time,
            'appointment_time': trip.appointment_time,
            'trip_type': trip.trip_type,
            'elderly': trip.elderly,
            'ambulatory': trip.ambulatory,
            'driver': trip.driver,
            'vehicle': trip.vehicle,
            'start_miles': trip.start_miles,
            'start_time': trip.start_time,
            'end_miles': trip.end_miles,
            'end_time': trip.end_time,
            'notes': trip.note,
            'is_canceled': trip.is_canceled,
        }
        form = EditTripForm(initial=initial)

    context = {
        'form': form,
        'trip': trip,
        'clients': Client.objects.all(),
        'clients_json': serializers.serialize("json", Client.objects.all()),
        'is_new': is_new,
    }

    return render(request, 'trip/edit.html', context)

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

def tripStart(request, id):
    trip = get_object_or_404(Trip, id=id)
    date = trip.date

    if request.method == 'POST':
        form = tripStartForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + "#trip_" + str(trip.id))

        if form.is_valid():
            trip.start_miles = form.cleaned_data['miles']
            trip.start_time = form.cleaned_data['time']
            trip.driver = form.cleaned_data['driver']
            trip.vehicle = form.cleaned_data['vehicle']
            trip.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + "#trip_" + str(trip.id))
    else:
        auto_time = trip.start_time
        if auto_time == "":
            auto_time = datetime.datetime.now().strftime("%_I:%M %p")

        initial = {
            'miles': trip.start_miles,
            'time': auto_time,
            'driver': trip.driver,
            'vehicle': trip.vehicle,
        }
        form = tripStartForm(initial=initial)
        form.fields['driver'].queryset = Driver.objects.filter(is_logged=True)
        form.fields['vehicle'].queryset = Vehicle.objects.filter(is_logged=True)

    start_miles = dict()
    for vehicle in Vehicle.objects.all():
        start_miles[str(vehicle)] = ""

    query = Shift.objects.filter(date=trip.date)
    for shift in query:
        if start_miles[str(shift.vehicle)] == "" or (shift.start_miles != "" and float(start_miles[str(shift.vehicle)]) > float(shift.start_miles)):
            start_miles[str(shift.vehicle)] = shift.start_miles

    context = {
        'form': form,
        'trip': trip,
        'start_miles': start_miles,
    }

    return render(request, 'trip/start.html', context)

def tripEnd(request, id):
    trip = get_object_or_404(Trip, id=id)
    date = trip.date

    if request.method == 'POST':
        form = tripEndForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + "#trip_" + str(trip.id))

        if form.is_valid():
            trip.end_miles = form.cleaned_data['miles']
            trip.end_time = form.cleaned_data['time']
            trip.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':trip.date.year, 'month':trip.date.month, 'day':trip.date.day}) + "#trip_" + str(trip.id))
    else:
        auto_time = trip.end_time
        if auto_time == "":
            auto_time = datetime.datetime.now().strftime("%_I:%M %p")

        initial = {
            'miles': trip.end_miles,
            'time': auto_time,
        }
        form = tripEndForm(initial=initial)

    start_miles = dict()
    for vehicle in Vehicle.objects.all():
        start_miles[str(vehicle)] = ""

    query = Shift.objects.filter(date=trip.date)
    for shift in query:
        if start_miles[str(shift.vehicle)] == "" or (shift.start_miles != "" and float(start_miles[str(shift.vehicle)]) > float(shift.start_miles)):
            start_miles[str(shift.vehicle)] = shift.start_miles

    context = {
        'form': form,
        'trip': trip,
        'start_miles': start_miles,
    }

    return render(request, 'trip/end.html', context)

def ajaxSetVehicleFromDriver(request):
    date = datetime.date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))
    shifts = Shift.objects.filter(date=date, driver__name=request.GET['driver'])

    data = {}

    if len(shifts) > 0:
        data['vehicle'] = str(shifts[0].vehicle)
    else:
        data['vehicle'] = ''

    return JsonResponse(data)


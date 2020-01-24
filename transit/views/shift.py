import datetime, uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Shift, Driver, Vehicle, Trip
from transit.forms import EditShiftForm, shiftStartEndForm, shiftFuelForm

def shiftCreate(request, mode, year, month, day):
    shift = Shift()
    shift.date = datetime.date(year, month, day)
    return shiftCreateEditCommon(request, mode, shift, is_new=True)

def shiftCreateToday(request, mode):
    today = datetime.datetime.now().date()
    return shiftCreate(request, mode, today.year, today.month, today.day)

def shiftCreateTomorrow(request, mode):
    tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
    return shiftCreate(request, mode, tomorrow.year, tomorrow.month, tomorrow.day)

def shiftEdit(request, mode, id):
    shift = get_object_or_404(Shift, id=id)
    return shiftCreateEditCommon(request, mode, shift, is_new=False)

def shiftCreateEditCommon(request, mode, shift, is_new):
    if request.method == 'POST':
        form = EditShiftForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('shift-delete', kwargs={'mode':mode, 'id':shift.id}))

        if form.is_valid():
            prev = {
                'driver': shift.driver,
                'vehicle': shift.vehicle
            }

            shift.date = form.cleaned_data['date']
            shift.driver = form.cleaned_data['driver']
            shift.vehicle = form.cleaned_data['vehicle']
            shift.start_miles = form.cleaned_data['start_miles']
            shift.start_time = form.cleaned_data['start_time']
            shift.end_miles = form.cleaned_data['end_miles']
            shift.end_time = form.cleaned_data['end_time']
            shift.fuel = form.cleaned_data['fuel']
            shift.note = form.cleaned_data['notes']
            shift.save()

            new_day_trips = Trip.objects.filter(date=shift.date)
            for trip in new_day_trips:
                if trip.driver is None and trip.vehicle is None:
                    continue

                if trip.driver == prev['driver'] and trip.vehicle == prev['vehicle']:
                    trip.driver = shift.driver
                    trip.vehicle = shift.vehicle
                elif trip.driver is None and trip.vehicle == shift.vehicle:
                    trip.driver = shift.driver
                elif trip.vehicle is None and trip.driver == shift.driver:
                    trip.vehicle = shift.vehicle

                trip.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
    else:
        initial = {
            'date': shift.date,
            'driver': shift.driver,
            'vehicle': shift.vehicle,
            'start_miles': shift.start_miles,
            'start_time': shift.start_time,
            'end_miles': shift.end_miles,
            'end_time': shift.end_time,
            'fuel': shift.fuel,
            'notes': shift.note,
        }
        form = EditShiftForm(initial=initial)

    context = {
        'form': form,
        'shift': shift,
        'is_new': is_new,
    }

    return render(request, 'shift/edit.html', context)

def shiftDelete(request, mode, id):
    shift = get_object_or_404(Shift, id=id)
    date = shift.date

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('shift-edit', kwargs={'mode':mode, 'id':id}))

        shift.delete()
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':date.year, 'month':date.month, 'day':date.day}))

    context = {
        'model': shift,
    }

    return render(request, 'model_delete.html', context)

def shiftStart(request, id):
    shift = get_object_or_404(Shift, id=id)
    date = shift.date

    if request.method == 'POST':
        form = shiftStartEndForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

        if form.is_valid():
            shift.start_miles = form.cleaned_data['miles']
            shift.start_time = form.cleaned_data['time']
            shift.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
    else:
        auto_time = shift.start_time
        if auto_time == '':
            auto_time = datetime.datetime.now().strftime('%_I:%M %p')

        initial = {
            'miles': shift.start_miles,
            'time': auto_time,
        }
        form = shiftStartEndForm(initial=initial)

    context = {
        'form': form,
        'shift': shift,
    }

    return render(request, 'shift/start.html', context)

def shiftEnd(request, id):
    shift = get_object_or_404(Shift, id=id)
    date = shift.date

    if request.method == 'POST':
        form = shiftStartEndForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

        if form.is_valid():
            shift.end_miles = form.cleaned_data['miles']
            shift.end_time = form.cleaned_data['time']
            shift.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
    else:
        auto_time = shift.end_time
        if auto_time == '':
            auto_time = datetime.datetime.now().strftime('%_I:%M %p')

        initial = {
            'miles': shift.end_miles,
            'time': auto_time,
        }
        form = shiftStartEndForm(initial=initial)

    context = {
        'form': form,
        'shift': shift,
    }

    return render(request, 'shift/end.html', context)

def shiftFuel(request, id):
    shift = get_object_or_404(Shift, id=id)
    date = shift.date

    if request.method == 'POST':
        form = shiftFuelForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

        if form.is_valid():
            shift.fuel = form.cleaned_data['fuel']
            shift.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
    else:
        initial = {
            'fuel': shift.fuel,
        }
        form = shiftFuelForm(initial=initial)

    context = {
        'form': form,
        'shift': shift,
    }

    return render(request, 'shift/fuel.html', context)


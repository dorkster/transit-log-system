import datetime
import uuid

from django.shortcuts import render
from django.views import generic

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

from django.core import serializers

# from django.contrib.auth.decorators import login_required

from transit.models import Driver, Vehicle, Trip, Shift, Client
from transit.forms import DatePickerForm, EditTripForm, EditShiftForm, shiftStartEndForm, shiftFuelForm, tripStartForm, tripEndForm, EditClientForm, EditDriverForm

# Create your views here.

def index(request):
    return render(request, 'index.html', context={})



def schedule(request, mode, year, month, day):
    day_date = datetime.date(year, month, day)
    day_date_prev = day_date + datetime.timedelta(days=-1)
    day_date_next = day_date + datetime.timedelta(days=1)

    query_trips = Trip.objects.filter(date=day_date)
    query_shifts = Shift.objects.filter(date=day_date)

    if request.method == 'POST':
        date_picker = DatePickerForm(request.POST)
        if date_picker.is_valid():
            date_picker_date = date_picker.cleaned_data['date']
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':date_picker_date.year, 'month':date_picker_date.month, 'day':date_picker_date.day}))
    else:
        date_picker = DatePickerForm(initial={'date':day_date})

    context = {
        'date': day_date,
        'date_str': day_date.strftime('%A, %B %d, %Y'),
        'trips': query_trips,
        'shifts': query_shifts,
        'date_picker': date_picker,
        'date_prev': reverse('schedule', kwargs={'mode':mode, 'year':day_date_prev.year, 'month':day_date_prev.month, 'day':day_date_prev.day}),
        'date_next': reverse('schedule', kwargs={'mode':mode, 'year':day_date_next.year, 'month':day_date_next.month, 'day':day_date_next.day}),
    }
    if mode == 'view':
        return render(request, 'schedule/view.html', context=context)
    else:
        return render(request, 'schedule/edit.html', context=context)

def scheduleToday(request, mode):
    today = datetime.datetime.now().date()
    return schedule(request, mode, today.year, today.month, today.day)

def scheduleTomorrow(request, mode):
    tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
    return schedule(request, mode, tomorrow.year, tomorrow.month, tomorrow.day)



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
        query_trips = Trip.objects.filter(date=trip.date).order_by('-sort_index')
        if len(query_trips) > 0:
            last_trip = query_trips[0]
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

        query_trips = Trip.objects.filter(date=trip.date)
        for i in query_trips:
            if i.sort_index > trip.sort_index:
                i.sort_index -= 1;
                i.save()

        trip.delete()
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':date.year, 'month':date.month, 'day':date.day}))

    context = {
        'model': trip,
    }

    return render(request, 'model_delete.html', context)




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
            shift.date = form.cleaned_data['date']
            shift.driver = form.cleaned_data['driver']
            shift.vehicle = form.cleaned_data['vehicle']
            shift.start_miles = form.cleaned_data['start_miles']
            shift.start_time = form.cleaned_data['start_time']
            shift.end_miles = form.cleaned_data['end_miles']
            shift.end_time = form.cleaned_data['end_time']
            shift.fuel = form.cleaned_data['fuel']
            shift.save()

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
            'fuel': shift.fuel
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
        if auto_time == "":
            auto_time = datetime.datetime.now().strftime("%_I:%M %p")

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
        if auto_time == "":
            auto_time = datetime.datetime.now().strftime("%_I:%M %p")

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

    start_miles = dict()
    for vehicle in Vehicle.objects.all():
        start_miles[str(vehicle)] = ""

    query_shifts = Shift.objects.filter(date=trip.date)
    for shift in query_shifts:
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

    query_shifts = Shift.objects.filter(date=trip.date)
    for shift in query_shifts:
        if start_miles[str(shift.vehicle)] == "" or (shift.start_miles != "" and float(start_miles[str(shift.vehicle)]) > float(shift.start_miles)):
            start_miles[str(shift.vehicle)] = shift.start_miles

    context = {
        'form': form,
        'trip': trip,
        'start_miles': start_miles,
    }

    return render(request, 'trip/end.html', context)




def clientList(request):
    context = {
        'clients': Client.objects.all(),
    }
    return render(request, 'client/list.html', context=context)

def clientCreate(request):
    client = Client()
    return clientCreateEditCommon(request, client, is_new=True)

def clientEdit(request, id):
    client = get_object_or_404(Client, id=id)
    return clientCreateEditCommon(request, client, is_new=False)

def clientCreateEditCommon(request, client, is_new):
    if request.method == 'POST':
        form = EditClientForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('clients') + "#client_" + str(client.id))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('client-delete', kwargs={'id':client.id}))

        if form.is_valid():
            client.name = form.cleaned_data['name']
            client.address = form.cleaned_data['address']
            client.phone_home = form.cleaned_data['phone_home']
            client.phone_mobile = form.cleaned_data['phone_mobile']
            client.phone_default = form.cleaned_data['phone_default']
            client.elderly = form.cleaned_data['elderly']
            client.ambulatory = form.cleaned_data['ambulatory']
            client.save()

            return HttpResponseRedirect(reverse('clients') + "#client_" + str(client.id))
    else:
        initial = {
            'name': client.name,
            'address': client.address,
            'phone_home': client.phone_home,
            'phone_mobile': client.phone_mobile,
            'phone_default': client.phone_default,
            'elderly': client.elderly,
            'ambulatory': client.ambulatory,
        }
        form = EditClientForm(initial=initial)

    context = {
        'form': form,
        'client': client,
        'is_new': is_new,
    }

    return render(request, 'client/edit.html', context)

def clientDelete(request, id):
    client = get_object_or_404(Client, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('client-edit', kwargs={'id':id}))

        client.delete()
        return HttpResponseRedirect(reverse('clients'))

    context = {
        'model': client,
    }

    return render(request, 'model_delete.html', context)




def driverList(request):
    context = {
        'driver': Driver.objects.all(),
    }
    return render(request, 'driver/list.html', context=context)

def driverCreate(request):
    driver = Driver()
    return driverCreateEditCommon(request, driver, is_new=True)

def driverEdit(request, id):
    driver = get_object_or_404(Driver, id=id)
    return driverCreateEditCommon(request, driver, is_new=False)

def driverCreateEditCommon(request, driver, is_new):
    if is_new == True:
        query_drivers = Trip.objects.all().order_by('-sort_index')
        if len(query_drivers) > 0:
            last_driver = query_drivers[0]
            driver.sort_index = last_driver.sort_index + 1
        else:
            driver.sort_index = 0

    if request.method == 'POST':
        form = EditDriverForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('drivers') + "#driver_" + str(driver.id))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('driver-delete', kwargs={'id':driver.id}))

        if form.is_valid():
            driver.name = form.cleaned_data['name']
            driver.color = form.cleaned_data['color']
            driver.save()

            return HttpResponseRedirect(reverse('drivers') + "#driver_" + str(driver.id))
    else:
        initial = {
            'name': driver.name,
            'color': driver.color,
        }
        form = EditDriverForm(initial=initial)

    context = {
        'form': form,
        'driver': driver,
        'is_new': is_new,
    }

    return render(request, 'driver/edit.html', context)

def driverDelete(request, id):
    driver = get_object_or_404(Driver, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('driver-edit', kwargs={'id':id}))

        query_drivers = Driver.objects.all()
        for i in query_drivers:
            if i.sort_index > driver.sort_index:
                i.sort_index -= 1;
                i.save()

        driver.delete()
        return HttpResponseRedirect(reverse('drivers'))

    context = {
        'model': driver,
    }

    return render(request, 'model_delete.html', context)




def ajaxScheduleEdit(request):
    return ajaxScheduleCommon(request, 'schedule/ajax/edit.html')

def ajaxScheduleView(request):
    return ajaxScheduleCommon(request, 'schedule/ajax/view.html')

def ajaxScheduleCommon(request, template):
    request_id = ''
    if request.GET['trip_id'] != '':
        request_id = uuid.UUID(request.GET['trip_id'])

    request_action = request.GET['trip_action']
    request_data = request.GET['trip_data']

    if request_action == 'mv':
        trip = get_object_or_404(Trip, id=request_id)

        do_sort = False
        if request_data == 'u':
            query_trips = Trip.objects.filter(date=trip.date).filter(sort_index=trip.sort_index-1)
            do_sort = True
        elif request_data == 'd':
            query_trips = Trip.objects.filter(date=trip.date).filter(sort_index=trip.sort_index+1)
            do_sort = True

        if do_sort and len(query_trips) > 0:
            swap_index = query_trips[0].sort_index
            query_trips[0].sort_index = trip.sort_index
            trip.sort_index = swap_index
            query_trips[0].save()
            trip.save()

    date = datetime.date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))
    shifts = Shift.objects.filter(date=date)
    trips = Trip.objects.filter(date=date)
    return render(request, template, {'shifts': shifts, 'trips':trips, 'date':date})

def ajaxSetVehicleFromDriver(request):
    date = datetime.date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))
    shifts = Shift.objects.filter(date=date, driver__name=request.GET['driver'])

    data = {}

    if len(shifts) > 0:
        data['vehicle'] = str(shifts[0].vehicle)
    else:
        data['vehicle'] = ''

    return JsonResponse(data)

def ajaxClientList(request):
    request_id = ''
    if request.GET['client_id'] != '':
        request_id = uuid.UUID(request.GET['trip_id'])

    request_action = request.GET['client_action']
    request_data = request.GET['client_data']

    clients = Client.objects.all()
    return render(request, 'client/ajax/list.html', {'clients': clients})

def ajaxDriverList(request):
    request_id = ''
    if request.GET['driver_id'] != '':
        request_id = uuid.UUID(request.GET['driver_id'])

    request_action = request.GET['driver_action']
    request_data = request.GET['driver_data']

    if request_action == 'mv':
        driver = get_object_or_404(Driver, id=request_id)

        do_sort = False
        if request_data == 'u':
            query_drivers = Driver.objects.filter(sort_index=driver.sort_index-1)
            do_sort = True
        elif request_data == 'd':
            query_drivers = Driver.objects.filter(sort_index=driver.sort_index+1)
            do_sort = True

        if do_sort and len(query_drivers) > 0:
            swap_index = query_drivers[0].sort_index
            query_drivers[0].sort_index = driver.sort_index
            driver.sort_index = swap_index
            query_drivers[0].save()
            driver.save()

    drivers = Driver.objects.all()
    return render(request, 'driver/ajax/list.html', {'drivers': drivers})


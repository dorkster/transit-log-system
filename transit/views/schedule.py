import datetime, uuid

from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from transit.models import Trip, Shift, Driver, Vehicle
from transit.forms import DatePickerForm

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

def ajaxScheduleEdit(request):
    return ajaxScheduleCommon(request, 'schedule/ajax_edit.html')

def ajaxScheduleView(request):
    return ajaxScheduleCommon(request, 'schedule/ajax_view.html')

def ajaxScheduleCommon(request, template):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'mv':
        trip = get_object_or_404(Trip, id=request_id)

        do_sort = False
        if request_data == 'u':
            query = Trip.objects.filter(date=trip.date).filter(sort_index=trip.sort_index-1)
            do_sort = True
        elif request_data == 'd':
            query = Trip.objects.filter(date=trip.date).filter(sort_index=trip.sort_index+1)
            do_sort = True

        if do_sort and len(query) > 0:
            swap_index = query[0].sort_index
            query[0].sort_index = trip.sort_index
            trip.sort_index = swap_index
            query[0].save()
            trip.save()
    elif request_action == 'set_driver':
        trip = get_object_or_404(Trip, id=request_id)
        prev_driver = trip.driver

        if request_data == '---------':
            trip.driver = None;
            trip.vehicle = None;
        else:
            driver = get_object_or_404(Driver, id=uuid.UUID(request_data))
            trip.driver = driver

            # if there's only 1 non-logged vehicle (e.g. 'personal'), use it for non-logged drivers
            if not driver.is_logged:
                nonlogged_vehicles = Vehicle.objects.filter(is_logged=False)
                if len(nonlogged_vehicles) == 1:
                    trip.vehicle = nonlogged_vehicles[0]

        # attempt to set vehicle from Shift data
        if prev_driver != trip.driver:
            new_query = Shift.objects.filter(date=trip.date).filter(driver=trip.driver)
            if len(new_query) > 0:
                trip.vehicle = new_query[0].vehicle
            elif trip.driver is None or trip.driver.is_logged == True:
                trip.vehicle = None

        trip.save()

    elif request_action == 'set_vehicle':
        trip = get_object_or_404(Trip, id=request_id)
        if request_data == '---------':
            trip.vehicle = None;
        else:
            vehicle = get_object_or_404(Vehicle, id=uuid.UUID(request_data))
            trip.vehicle = vehicle
        trip.save()
    elif request_action == 'toggle_canceled':
        trip = get_object_or_404(Trip, id=request_id)
        trip.is_canceled = not trip.is_canceled
        trip.save()

    date = datetime.date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))
    shifts = Shift.objects.filter(date=date)
    trips = Trip.objects.filter(date=date)
    drivers = Driver.objects.all()
    vehicles = Vehicle.objects.all()
    return render(request, template, {'shifts': shifts, 'trips':trips, 'date':date, 'drivers':drivers, 'vehicles': vehicles})


import datetime, uuid

from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from transit.models import Trip, Shift, Driver, Vehicle, Template, TemplateTrip, ScheduleMessage
from transit.forms import DatePickerForm, EditScheduleMessageForm

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

def schedulePrint(request, year, month, day):
    day_date = datetime.date(year, month, day)

    query_trips = Trip.objects.filter(date=day_date)
    query_shifts = Shift.objects.filter(date=day_date)

    messages = ScheduleMessage.objects.filter(date=day_date)
    if len(messages) > 0:
        message = messages[0].message
    else:
        message = ''

    context = {
        'date': day_date,
        'date_str': day_date.strftime('%A, %B %d, %Y'),
        'trips': query_trips,
        'shifts': query_shifts,
        'message': message,
    }
    return render(request, 'schedule/print.html', context=context)

def scheduleMessage(request, year, month, day):
    date = datetime.date(year, month, day)

    is_new = True
    messages = ScheduleMessage.objects.filter(date=date)
    if len(messages) > 0:
        is_new = False
        message = messages[0]
    else:
        message = ScheduleMessage()
        message.date = date

    if request.method == 'POST':
        form = EditScheduleMessageForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':date.year, 'month':date.month, 'day':date.day}))
        elif 'delete' in request.POST:
            if not is_new:
                message.delete()
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':date.year, 'month':date.month, 'day':date.day}))

        if form.is_valid():
            message.message = form.cleaned_data['message']

            if not is_new and message.message == '':
                message.delete()
            else:
                message.save()

            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':date.year, 'month':date.month, 'day':date.day}))
    else:
        initial = {
            'message': message.message,
        }
        form = EditScheduleMessageForm(initial=initial)
    context = {
        'date': date,
        'date_str': date.strftime('%A, %B %d, %Y'),
        'form': form,
    }
    return render(request, 'schedule/message_edit.html', context=context)

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
    date = datetime.date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))

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
        if request_data == '0':
            trip.status = Trip.STATUS_NORMAL
        elif request_data == '1':
            trip.status = Trip.STATUS_CANCELED
        elif request_data == '2':
            trip.status = Trip.STATUS_NO_SHOW
        trip.save()
    elif request_action == 'load_template':
        parent_template = Template.objects.get(id=uuid.UUID(request_data))
        template_trips = TemplateTrip.objects.filter(parent=parent_template)

        sort_index = 0
        query = Trip.objects.filter(date=date)
        if (len(query) > 0):
            sort_index = query[len(query)-1].sort_index + 1

        for temp_trip in template_trips:
            trip = Trip()
            trip.date = date
            trip.sort_index = sort_index
            sort_index += 1
            trip.name = temp_trip.name
            trip.address = temp_trip.address
            trip.phone_home = temp_trip.phone_home
            trip.phone_cell = temp_trip.phone_cell
            trip.destination = temp_trip.destination
            trip.pick_up_time = temp_trip.pick_up_time
            trip.appointment_time = temp_trip.appointment_time
            trip.trip_type = temp_trip.trip_type
            trip.elderly = temp_trip.elderly
            trip.ambulatory = temp_trip.ambulatory
            trip.note = temp_trip.note
            trip.save()

    filter_hide_canceled_str = request.GET.get('filter_hide_canceled', None)

    if filter_hide_canceled_str is not None:
        filter_hide_canceled_str = filter_hide_canceled_str.lower()
        request.session['schedule_view_hide_canceled'] = True if filter_hide_canceled_str == 'true' else False

    filter_hide_canceled = request.session.get('schedule_view_hide_canceled', False)

    filter_hide_completed_str = request.GET.get('filter_hide_completed', None)

    if filter_hide_completed_str is not None:
        filter_hide_completed_str = filter_hide_completed_str.lower()
        request.session['schedule_view_hide_completed'] = True if filter_hide_completed_str == 'true' else False

    filter_hide_completed = request.session.get('schedule_view_hide_completed', False)

    trips = Trip.objects.filter(date=date)

    # TODO don't use template filename to check if we're on the View page!!!
    if template == 'schedule/ajax_view.html':
        if filter_hide_canceled:
            trips = trips.filter(status=Trip.STATUS_NORMAL)

        if filter_hide_completed:
            trips = trips.filter(Q(start_miles='') | Q(start_time='') | Q(end_miles='') | Q(end_time=''))

    shifts = Shift.objects.filter(date=date)
    drivers = Driver.objects.all()
    vehicles = Vehicle.objects.all()

    messages = ScheduleMessage.objects.filter(date=date)
    if len(messages) > 0:
        message = messages[0].message
    else:
        message = ''

    context = {
        'shifts': shifts,
        'trips': trips,
        'date': date,
        'drivers': drivers,
        'vehicles': vehicles,
        'filter_hide_canceled': filter_hide_canceled,
        'filter_hide_completed': filter_hide_completed,
        'templates': Template.objects.all(),
        'message': message,
    }
    return render(request, template, context=context)


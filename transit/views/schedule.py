import datetime, uuid

from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from transit.models import Trip, Shift, Driver, Vehicle, Template, TemplateTrip, ScheduleMessage, SiteSettings, TripType
from transit.forms import DatePickerForm, EditScheduleMessageForm, SchedulePrintFilterForm
from transit.views.report import Report

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_trip'])
def schedule(request, mode, year, month, day):
    if mode != 'read-only' and (not request.user.has_perm('transit.change_shift') and not request.user.has_perm('transit.change_trip')):
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'read-only', 'year':year, 'month':month, 'day':day}))
    elif mode == 'view' and not request.user.has_perm('transit.change_vehicle'):
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':year, 'month':month, 'day':day}))

    day_date = datetime.date(year, month, day)

    date_week = []
    date_week_range_max = 10
    for day_delta in range(-1, date_week_range_max):
        date_week.append(day_date + datetime.timedelta(days=day_delta))

    site_settings = SiteSettings.load()
    if site_settings.skip_weekends:
        # only skip weekends if the current day is a weekday
        if date_week[1].weekday() != 5 and date_week[1].weekday() != 6:
            # yesterday
            if date_week[0].weekday() == 5:
                date_week[0] = date_week[0] + datetime.timedelta(days=-1)
            elif date_week[0].weekday() == 6:
                date_week[0] = date_week[0] + datetime.timedelta(days=-2)
            # future
            for day_delta in range(2, date_week_range_max+1):
                if date_week[day_delta].weekday() == 5:
                    for skip_delta in range(day_delta, date_week_range_max+1):
                        date_week[skip_delta] = date_week[skip_delta] + datetime.timedelta(days=2)

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
        'trips': query_trips,
        'shifts': query_shifts,
        'date_picker': date_picker,
        'date_week': date_week,
    }
    if mode == 'view':
        return render(request, 'schedule/view.html', context=context)
    elif mode == 'read-only':
        return render(request, 'schedule/read_only.html', context=context)
    else:
        return render(request, 'schedule/edit.html', context=context)

@permission_required(['transit.view_shift', 'transit.view_trip'])
def schedulePrint(request, year, month, day):
    day_date = datetime.date(year, month, day)

    query_trips = Trip.objects.filter(date=day_date)
    query_shifts = Shift.objects.filter(date=day_date)

    messages = ScheduleMessage.objects.filter(date=day_date)
    if len(messages) > 0:
        message = messages[0].message
    else:
        message = ''

    filter_form = SchedulePrintFilterForm(request.GET)

    filter_hide_canceled = True if request.GET.get('hide_canceled') == '1' else False
    filter_hide_completed = True if request.GET.get('hide_completed') == '1' else False
    filter_hide_nolog = True if request.GET.get('hide_nolog') == '1' else False
    filter_search = '' if request.GET.get('search') == None else request.GET.get('search')
    filter_driver = '' if request.GET.get('driver') == None else request.GET.get('driver')
    filter_vehicle = '' if request.GET.get('vehicle') == None else request.GET.get('vehicle')

    unfiltered_count = len(query_trips)

    if filter_hide_canceled:
        query_trips = query_trips.filter(status=Trip.STATUS_NORMAL)

    if filter_hide_completed:
        query_trips = query_trips.filter(Q(start_miles='') | Q(start_time='') | Q(end_miles='') | Q(end_time='') | Q(is_activity=True))

    if filter_hide_nolog:
        query_trips = query_trips.filter(Q(driver=None) | Q(driver__is_logged=True) | Q(is_activity=True))

    if filter_search != '':
        query_trips = query_trips.filter(Q(name__icontains=filter_search) | Q(address__icontains=filter_search) | Q(destination__icontains=filter_search) | Q(note__icontains=filter_search) | Q(tags__icontains=filter_search) | Q(trip_type__name__icontains=filter_search))

    if filter_driver != '':
        query_trips = query_trips.filter(Q(driver__id=filter_driver) | Q(is_activity=True))

    if filter_vehicle != '':
        query_trips = query_trips.filter(Q(vehicle__id=filter_vehicle) | Q(is_activity=True))

    filtered_count = len(query_trips)

    # if the GET request is populated, the filter has been used. So we don't want to auto-show the print dialog
    show_dialog = True
    for i in request.GET:
        if i == 'driver':
            show_dialog = False
            break

    context = {
        'date': day_date,
        'trips': query_trips,
        'shifts': query_shifts,
        'message': message,
        'drivers': Driver.objects.all(),
        'vehicles': Vehicle.objects.all(),
        'filter_form': filter_form,
        'is_filtered': (filter_hide_canceled or filter_hide_completed or filter_hide_nolog or filter_search != '' or filter_driver != '' or filter_vehicle != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'filter_hide_canceled': filter_hide_canceled,
        'filter_hide_completed': filter_hide_completed,
        'filter_hide_nolog': filter_hide_nolog,
        'filter_search': filter_search,
        'filter_driver': None if filter_driver == '' else Driver.objects.get(id=filter_driver),
        'filter_vehicle': None if filter_vehicle == '' else Vehicle.objects.get(id=filter_vehicle),
        'show_dialog': show_dialog,
    }
    return render(request, 'schedule/print.html', context=context)

@permission_required(['transit.change_schedulemessage'])
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
    return ajaxScheduleCommon(request, 'schedule/ajax_view.html', has_filter=True)

def ajaxScheduleReadOnly(request):
    return ajaxScheduleCommon(request, 'schedule/ajax_read_only.html', has_filter=True)

def ajaxScheduleCommon(request, template, has_filter=False):
    if not request.user.has_perm('transit.view_trip'):
        return HttpResponseRedirect(reverse('login_redirect'))

    date = datetime.date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_trip'):
        if request_action == 'mv':
            trip = get_object_or_404(Trip, id=request_id)
            original_index = trip.sort_index
            trip.sort_index = -1

            # "remove" the selected trip by shifting everything below it up by 1
            below_items = Trip.objects.filter(date=trip.date).filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(Trip, id=request_data)
                if trip.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the trip at the new index by shifting everything below it down by 1
            below_items = Trip.objects.filter(date=trip.date).filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            trip.sort_index = new_index
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
            log_model = LoggedEventModel.TRIP_ACTIVITY if trip.is_activity else LoggedEventModel.TRIP
            log_event(request, LoggedEventAction.STATUS, log_model, str(trip))
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
                trip.driver = temp_trip.driver
                trip.vehicle = temp_trip.vehicle
                trip.name = temp_trip.name
                trip.address = temp_trip.address
                trip.phone_home = temp_trip.phone_home
                trip.phone_cell = temp_trip.phone_cell
                trip.phone_address = temp_trip.phone_address
                trip.phone_destination = temp_trip.phone_destination
                trip.destination = temp_trip.destination
                trip.pick_up_time = temp_trip.pick_up_time
                trip.appointment_time = temp_trip.appointment_time
                trip.trip_type = temp_trip.trip_type
                trip.tags = temp_trip.tags
                trip.elderly = temp_trip.elderly
                trip.ambulatory = temp_trip.ambulatory
                trip.note = temp_trip.note
                trip.is_activity = temp_trip.is_activity
                trip.status = temp_trip.status
                trip.fare = temp_trip.fare
                trip.passenger = temp_trip.passenger
                trip.save()
    if request_action == 'filter_toggle_completed':
        request.session['schedule_view_hide_completed'] = not request.session.get('schedule_view_hide_completed', False)
    elif request_action == 'filter_toggle_canceled':
        request.session['schedule_view_hide_canceled'] = not request.session.get('schedule_view_hide_canceled', False)
    elif request_action == 'filter_toggle_nolog':
        request.session['schedule_view_hide_nolog'] = not request.session.get('schedule_view_hide_nolog', False)
    elif request_action == 'filter_search':
        request.session['schedule_view_search'] = request_data
    elif request_action == 'filter_driver':
        request.session['schedule_view_driver'] = request_data
    elif request_action == 'filter_vehicle':
        request.session['schedule_view_vehicle'] = request_data
    elif request_action == 'filter_reset':
        request.session['schedule_view_hide_completed'] = False
        request.session['schedule_view_hide_canceled'] = False
        request.session['schedule_view_hide_nolog'] = False
        request.session['schedule_view_search'] = ''
        request.session['schedule_view_driver'] = ''
        request.session['schedule_view_vehicle'] = ''
    elif request.user.is_superuser and request_action == 'delete_all_shifts':
        for i in Shift.objects.filter(date=date):
            i.delete()
    elif request.user.is_superuser and request_action == 'delete_all_trips':
        for i in Trip.objects.filter(date=date):
            # no need to update sort_index when deleting all trips
            i.delete()
    elif request_action == 'toggle_extra_columns':
        request.session['schedule_edit_extra_columns'] = not request.session.get('schedule_edit_extra_columns', False)

    filter_hide_canceled = request.session.get('schedule_view_hide_canceled', False)
    filter_hide_completed = request.session.get('schedule_view_hide_completed', False)
    filter_hide_nolog = request.session.get('schedule_view_hide_nolog', False)
    filter_search = request.session.get('schedule_view_search', '')
    filter_driver = request.session.get('schedule_view_driver', '')
    filter_vehicle = request.session.get('schedule_view_vehicle', '')

    trips = Trip.objects.filter(date=date)

    unfiltered_count = len(trips)

    if has_filter:
        if filter_hide_canceled:
            trips = trips.filter(status=Trip.STATUS_NORMAL)

        if filter_hide_completed:
            trips = trips.filter(Q(start_miles='') | Q(start_time='') | Q(end_miles='') | Q(end_time='') | Q(is_activity=True))

        if filter_hide_nolog:
            trips = trips.filter(Q(driver=None) | Q(driver__is_logged=True) | Q(is_activity=True))

        if filter_search != '':
            trips = trips.filter(Q(name__icontains=filter_search) | Q(address__icontains=filter_search) | Q(destination__icontains=filter_search) | Q(note__icontains=filter_search) | Q(tags__icontains=filter_search) | Q(trip_type__name__icontains=filter_search))

        if filter_driver != '':
            trips = trips.filter(Q(driver__id=filter_driver) | Q(is_activity=True))

        if filter_vehicle != '':
            trips = trips.filter(Q(vehicle__id=filter_vehicle) | Q(is_activity=True))

    filtered_count = len(trips)

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
        'is_filtered': (filter_hide_canceled or filter_hide_completed or filter_hide_nolog or filter_search != '' or filter_driver != '' or filter_vehicle != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'filter_hide_canceled': filter_hide_canceled,
        'filter_hide_completed': filter_hide_completed,
        'filter_hide_nolog': filter_hide_nolog,
        'filter_search': filter_search,
        'filter_driver': None if filter_driver == '' else Driver.objects.get(id=filter_driver),
        'filter_vehicle': None if filter_vehicle == '' else Vehicle.objects.get(id=filter_vehicle),
        'templates': Template.objects.all(),
        'message': message,
        'show_extra_columns': request.session.get('schedule_edit_extra_columns', False),
    }
    return render(request, template, context=context)


def schedulePrintDailyLog(request, year, month, day):
    request.session['schedule_print_daily_log_id'] = None
    context = {
        'year': year,
        'month': month,
        'day': day,
    }
    return render(request, 'schedule/print_daily_log.html', context=context)

def ajaxSchedulePrintDailyLog(request, year, month, day):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'select_id':
        request.session['schedule_print_daily_log_id'] = request_data
    elif request_action == 'select_all':
        request.session['schedule_print_daily_log_id'] = None

    day_date = datetime.date(year, month, day)

    shifts = Shift.objects.filter(date=day_date)
    shifts = shifts.exclude(start_miles='')
    shifts = shifts.exclude(end_miles='')
    report = Report()

    shift_id = request.session.get('schedule_print_daily_log_id', None)

    if shift_id == None:
        current_shift = None
        report.load(day_date, day_date)
        if len(report.report_all) > 0:
            report_summary = report.all_vehicles
    else:
        current_shift = get_object_or_404(Shift, id=shift_id)
        report.load(day_date, day_date, daily_log_shift=shift_id)
        if len(report.report_all) > 0:
            report_summary = report.report_all[0].by_vehicle[current_shift.vehicle]

    try:
        trips_medical = report_summary.trip_types[TripType.objects.get(name='Medical')]
    except:
        trips_medical = 0

    try:
        trips_nutrition = report_summary.trip_types[TripType.objects.get(name='Nutrition')]
    except:
        trips_nutrition = 0

    try:
        trips_social = report_summary.trip_types[TripType.objects.get(name='Social/Recreation')]
    except:
        trips_social = 0

    try:
        trips_shopping = report_summary.trip_types[TripType.objects.get(name='Shopping')]
    except:
        trips_shopping = 0

    try:
        trips_other = report_summary.trip_types[TripType.objects.get(name='Other')]
    except:
        trips_other = 0

    try:
        money_cash = report_summary.collected_cash
    except:
        money_cash = Report.Money(0)

    try:
        money_check = report_summary.collected_check
    except:
        money_check = Report.Money(0)

    money_total = money_cash + money_check

    trips_employment = report_summary.other_employment

    context = {
        'date': day_date,
        'shifts': shifts,
        'current_shift': current_shift,
        'report': report,
        'trips_medical': trips_medical,
        'trips_nutrition': trips_nutrition,
        'trips_social': trips_social,
        'trips_shopping': trips_shopping,
        'trips_other': trips_other,
        'trips_total': trips_medical + trips_nutrition + trips_social + trips_shopping + trips_other,
        'money_cash': money_cash,
        'money_check': money_check,
        'money_total': money_total,
        'trips_employment': trips_employment,
    }

    return render(request, 'schedule/ajax_print_daily_log.html', context)

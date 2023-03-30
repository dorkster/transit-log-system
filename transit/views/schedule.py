# Copyright © 2019-2021 Justin Jacobs
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

from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from transit.models import Trip, Shift, Driver, Vehicle, Template, TemplateTrip, ScheduleMessage, SiteSettings, TripType
from transit.forms import DatePickerForm, EditScheduleMessageForm
from transit.views.report import Report

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import move_item_in_queryset

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

    if request.method == 'POST':
        date_picker = DatePickerForm(request.POST)
        if date_picker.is_valid():
            date_picker_date = date_picker.cleaned_data['date']
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':date_picker_date.year, 'month':date_picker_date.month, 'day':date_picker_date.day}))
    else:
        date_picker = DatePickerForm(initial={'date':day_date})

    context = {
        'date': day_date,
        'date_picker': date_picker,
        'date_week': date_week,
    }
    if mode == 'view':
        return render(request, 'schedule/view.html', context=context)
    elif mode == 'read-only':
        return render(request, 'schedule/read_only.html', context=context)
    else:
        return render(request, 'schedule/edit.html', context=context)

def schedulePrintFilterReset(request):
    request.session['schedule_print_filter_completed'] = False
    request.session['schedule_print_filter_canceled'] = False
    request.session['schedule_print_filter_nolog'] = False
    request.session['schedule_print_filter_search'] = ''
    request.session['schedule_print_filter_driver'] = ''
    request.session['schedule_print_filter_vehicle'] = ''
    request.session['schedule_print_filter_log_columns'] = True

@permission_required(['transit.view_shift', 'transit.view_trip'])
def schedulePrint(request, year, month, day):
    schedulePrintFilterReset(request)
    context = {
        'date': datetime.date(year, month, day),
    }
    return render(request, 'schedule/print.html', context=context)

@permission_required(['transit.view_shift', 'transit.view_trip'])
def schedulePrintSimple(request, year, month, day):
    schedulePrintFilterReset(request)
    request.session['schedule_print_filter_log_columns'] = False
    context = {
        'date': datetime.date(year, month, day),
    }
    return render(request, 'schedule/print.html', context=context)

def ajaxSchedulePrint(request, year, month, day):
    if not request.user.has_perm('transit.view_shift') or not request.user.has_perm('transit.view_trip'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'filter_toggle_completed':
        request.session['schedule_print_filter_completed'] = not request.session['schedule_print_filter_completed']
    elif request_action == 'filter_toggle_canceled':
        request.session['schedule_print_filter_canceled'] = not request.session['schedule_print_filter_canceled']
    elif request_action == 'filter_toggle_nolog':
        request.session['schedule_print_filter_nolog'] = not request.session['schedule_print_filter_nolog']
    elif request_action == 'filter_search':
        request.session['schedule_print_filter_search'] = request_data
    elif request_action == 'filter_driver':
        request.session['schedule_print_filter_driver'] = request_data
    elif request_action == 'filter_vehicle':
        request.session['schedule_print_filter_vehicle'] = request_data
    elif request_action == 'filter_toggle_log_columns':
        request.session['schedule_print_filter_log_columns'] = not request.session['schedule_print_filter_log_columns']
    elif request_action == 'filter_reset':
        schedulePrintFilterReset(request)

    day_date = datetime.date(year, month, day)

    query_trips = Trip.objects.filter(date=day_date).select_related('driver', 'vehicle', 'trip_type', 'volunteer')
    query_shifts = Shift.objects.filter(date=day_date).select_related('driver', 'vehicle')

    messages = ScheduleMessage.objects.filter(date=day_date)
    if len(messages) > 0:
        message = messages[0].message
    else:
        message = ''

    filter_hide_canceled = request.session.get('schedule_print_filter_canceled', False)
    filter_hide_completed = request.session.get('schedule_print_filter_completed', False)
    filter_hide_nolog = request.session.get('schedule_print_filter_nolog', False)
    filter_search = request.session.get('schedule_print_filter_search', '')
    filter_driver = request.session.get('schedule_print_filter_driver', '')
    filter_vehicle = request.session.get('schedule_print_filter_vehicle', '')
    filter_log_columns = request.session.get('schedule_print_filter_log_columns', True)

    unfiltered_count = len(query_trips)

    if filter_hide_canceled:
        query_trips = query_trips.filter(status=Trip.STATUS_NORMAL)

    if filter_hide_completed:
        query_trips = query_trips.filter(Q(start_miles='') | Q(start_time='') | Q(end_miles='') | Q(end_time='') | ~Q(format=Trip.FORMAT_NORMAL))

    if filter_hide_nolog:
        query_trips = query_trips.filter(Q(driver=None) | Q(driver__is_logged=True) | ~Q(format=Trip.FORMAT_NORMAL))

    if filter_search != '':
        query_trips = query_trips.filter(Q(name__icontains=filter_search) | Q(address__icontains=filter_search) | Q(destination__icontains=filter_search) | Q(note__icontains=filter_search) | Q(tags__icontains=filter_search) | Q(trip_type__name__icontains=filter_search) | Q(reminder_instructions__icontains=filter_search))

    if filter_driver != '':
        query_trips = query_trips.filter(Q(driver__id=filter_driver) | ~Q(format=Trip.FORMAT_NORMAL))
        query_shifts = query_shifts.filter(driver__id=filter_driver)

    if filter_vehicle != '':
        query_trips = query_trips.filter(Q(vehicle__id=filter_vehicle) | ~Q(format=Trip.FORMAT_NORMAL))
        query_shifts = query_shifts.filter(vehicle__id=filter_vehicle)

    filtered_count = len(query_trips)

    # don't auto-show the print dialog if a filter has been set
    show_dialog = (request_action == '')

    context = {
        'date': day_date,
        'trips': query_trips,
        'shifts': query_shifts,
        'message': message,
        'drivers': Driver.objects.all(),
        'vehicles': Vehicle.objects.all(),
        'is_filtered': (filter_hide_canceled or filter_hide_completed or filter_hide_nolog or filter_search != '' or filter_driver != '' or filter_vehicle != '' or not filter_log_columns),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'filter_hide_canceled': filter_hide_canceled,
        'filter_hide_completed': filter_hide_completed,
        'filter_hide_nolog': filter_hide_nolog,
        'filter_search': filter_search,
        'filter_driver': None if filter_driver == '' else Driver.objects.get(id=filter_driver),
        'filter_vehicle': None if filter_vehicle == '' else Vehicle.objects.get(id=filter_vehicle),
        'filter_log_columns': filter_log_columns,
        'show_dialog': show_dialog,
        'Trip': Trip,
        'Shift': Shift,
    }
    return render(request, 'schedule/ajax_print.html', context=context)

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
            move_item_in_queryset(request_id, request_data, Trip.objects.filter(date=date))
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
            if trip.driver != prev_driver:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.TRIP, 'Set Driver -> ' + trip.get_driver_str() + ' | ' + str(trip))
        elif request_action == 'set_vehicle':
            trip = get_object_or_404(Trip, id=request_id)
            prev_vehicle = trip.vehicle
            if request_data == '---------':
                trip.vehicle = None;
            else:
                vehicle = get_object_or_404(Vehicle, id=uuid.UUID(request_data))
                trip.vehicle = vehicle
            trip.save()
            if trip.vehicle != prev_vehicle:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.TRIP, 'Set Vehicle -> ' + trip.get_vehicle_str() + ' | ' + str(trip))
        elif request_action == 'toggle_canceled':
            trip = get_object_or_404(Trip, id=request_id)
            if request_data == '0':
                trip.status = Trip.STATUS_NORMAL
                trip.cancel_date = None
            elif request_data == '1':
                trip.status = Trip.STATUS_CANCELED
                trip.cancel_date = datetime.date.today()
            elif request_data == '2':
                trip.status = Trip.STATUS_NO_SHOW
                trip.cancel_date = None
            trip.save()
            log_model = LoggedEventModel.TRIP_ACTIVITY if trip.format == Trip.FORMAT_ACTIVITY else LoggedEventModel.TRIP
            log_event(request, LoggedEventAction.STATUS, log_model, 'Set Status -> ' + trip.get_status_str() + ' | ' + str(trip))
        elif request_action == 'load_template':
            parent_template = Template.objects.get(id=uuid.UUID(request_data))
            template_trips = TemplateTrip.objects.filter(parent=parent_template).select_related('driver', 'vehicle', 'trip_type', 'volunteer')

            sort_index = 0
            query = Trip.objects.filter(date=date)
            if (len(query) > 0):
                sort_index = query[len(query)-1].sort_index + 1

            for temp_trip in template_trips:
                trip = Trip()
                trip.date = date
                trip.sort_index = sort_index
                sort_index += 1
                trip.format = temp_trip.format
                trip.driver = temp_trip.driver
                trip.vehicle = temp_trip.vehicle
                trip.name = temp_trip.name
                trip.address = temp_trip.address
                trip.phone_home = temp_trip.phone_home
                trip.phone_cell = temp_trip.phone_cell
                trip.phone_alt = temp_trip.phone_alt
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
                trip.status = temp_trip.status
                trip.fare = temp_trip.fare
                trip.passenger = temp_trip.passenger
                trip.activity_color = temp_trip.activity_color
                trip.reminder_instructions = temp_trip.reminder_instructions
                trip.volunteer = temp_trip.volunteer
                trip.wheelchair = temp_trip.wheelchair

                if trip.status == Trip.STATUS_CANCELED:
                    trip.cancel_date = datetime.date.today()

                trip.save()
            log_event(request, LoggedEventAction.CREATE, LoggedEventModel.TRIP, 'Insert Template -> ' + str(parent_template) + ' | [' + str(date) + ']')

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
        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.SHIFT, 'Delete all Shifts | [' + str(date) + ']')
    elif request.user.is_superuser and request_action == 'delete_all_trips':
        for i in Trip.objects.filter(date=date):
            # no need to update sort_index when deleting all trips
            i.delete()
        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.TRIP, 'Delete all Trips | [' + str(date) + ']')
    elif request_action == 'toggle_extra_columns':
        request.session['schedule_edit_extra_columns'] = not request.session.get('schedule_edit_extra_columns', False)

    filter_hide_canceled = request.session.get('schedule_view_hide_canceled', False)
    filter_hide_completed = request.session.get('schedule_view_hide_completed', False)
    filter_hide_nolog = request.session.get('schedule_view_hide_nolog', False)
    filter_search = request.session.get('schedule_view_search', '')
    filter_driver = request.session.get('schedule_view_driver', '')
    filter_vehicle = request.session.get('schedule_view_vehicle', '')

    trips = Trip.objects.filter(date=date).select_related('driver', 'vehicle', 'trip_type', 'volunteer')

    unfiltered_count = len(trips)

    if has_filter:
        if filter_hide_canceled:
            trips = trips.filter(status=Trip.STATUS_NORMAL)

        if filter_hide_completed:
            trips = trips.filter(Q(start_miles='') | Q(start_time='') | Q(end_miles='') | Q(end_time='') | ~Q(format=Trip.FORMAT_NORMAL))

        if filter_hide_nolog:
            trips = trips.filter(Q(driver=None) | Q(driver__is_logged=True) | ~Q(format=Trip.FORMAT_NORMAL))

        if filter_search != '':
            trips = trips.filter(Q(name__icontains=filter_search) | Q(address__icontains=filter_search) | Q(destination__icontains=filter_search) | Q(note__icontains=filter_search) | Q(tags__icontains=filter_search) | Q(trip_type__name__icontains=filter_search) | Q(reminder_instructions__icontains=filter_search))

        if filter_driver != '':
            trips = trips.filter(Q(driver__id=filter_driver) | ~Q(format=Trip.FORMAT_NORMAL))

        if filter_vehicle != '':
            trips = trips.filter(Q(vehicle__id=filter_vehicle) | ~Q(format=Trip.FORMAT_NORMAL))

    filtered_count = len(trips)

    shifts = Shift.objects.filter(date=date).select_related('driver', 'vehicle')
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
        'Trip': Trip,
        'Shift': Shift,
    }
    return render(request, template, context=context)


def schedulePrintDailyLog(request, year, month, day):
    request.session['schedule_print_daily_log_id'] = None
    context = {
        'date': datetime.date(year, month, day),
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
        current_shift = get_object_or_404(Shift, id=uuid.UUID(shift_id))
        report.load(day_date, day_date, daily_log_shift=uuid.UUID(shift_id))
        if len(report.report_all) > 0:
            report_summary = report.report_all[0].by_vehicle[Report.getVehicleIndex(current_shift.vehicle)]

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

    try:
        trips_employment = report_summary.other_employment
    except:
        trips_employment = 0

    # don't include employment/education in Other total
    trips_other = trips_other - trips_employment

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
        'trips_total': trips_medical + trips_nutrition + trips_social + trips_shopping + trips_other + trips_employment,
        'money_cash': money_cash,
        'money_check': money_check,
        'money_total': money_total,
        'trips_employment': trips_employment,
    }

    return render(request, 'schedule/ajax_print_daily_log.html', context)

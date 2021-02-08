import datetime, uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Shift, Driver, Vehicle, Trip, SiteSettings
from transit.forms import EditShiftForm, shiftStartEndForm, shiftFuelForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

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

def shiftEditFromReport(request, start_year, start_month, start_day, end_year, end_month, end_day, id):
    date_start = {'year':start_year, 'month':start_month, 'day':start_day}
    date_end = {'year':end_year, 'month':end_month, 'day':end_day}
    shift = get_object_or_404(Shift, id=id)
    return shiftCreateEditCommon(request, 'edit', shift, is_new=False, report_start=date_start, report_end=date_end)

@permission_required(['transit.change_shift'])
def shiftCreateEditCommon(request, mode, shift, is_new, report_start=None, report_end=None):
    if request.method == 'POST':
        form = EditShiftForm(request.POST)

        if 'cancel' in request.POST:
            if report_start and report_end:
                return HttpResponseRedirect(reverse('report', kwargs={'start_year':report_start['year'], 'start_month':report_start['month'], 'start_day':report_start['day'], 'end_year':report_end['year'], 'end_month':report_end['month'], 'end_day':report_end['day']}))
            else:
                url_hash = '' if is_new else '#shift_' + str(shift.id)
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}) + url_hash)
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

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.SHIFT, str(shift))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.SHIFT, str(shift))

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

            if report_start and report_end:
                return HttpResponseRedirect(reverse('report', kwargs={'start_year':report_start['year'], 'start_month':report_start['month'], 'start_day':report_start['day'], 'end_year':report_end['year'], 'end_month':report_end['month'], 'end_day':report_end['day']}))
            else:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}) + '#shift_' + str(shift.id))
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

@permission_required(['transit.delete_shift'])
def shiftDelete(request, mode, id):
    shift = get_object_or_404(Shift, id=id)
    date = shift.date

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('shift-edit', kwargs={'mode':mode, 'id':id}))

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.SHIFT, str(shift))

        shift.delete()
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':mode, 'year':date.year, 'month':date.month, 'day':date.day}))

    context = {
        'model': shift,
    }

    return render(request, 'model_delete.html', context)

@permission_required(['transit.change_shift'])
def shiftStart(request, id):
    shift = get_object_or_404(Shift, id=id)
    date = shift.date

    previous_shift = None
    previous_shifts = Shift.objects.filter(vehicle=shift.vehicle).exclude(start_miles='').exclude(end_miles='')
    for i in previous_shifts:
        if previous_shift == None:
            previous_shift = i
            continue

        try:
            if float(i.end_miles) >= float(previous_shift.end_miles):
                previous_shift = i
        except:
            continue

    if previous_shift == None:
        previous_shift_end_miles = ''
    else:
        previous_shift_end_miles = previous_shift.end_miles

    if request.method == 'POST':
        form = shiftStartEndForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

        if form.is_valid():
            if len(form.cleaned_data['miles']) < len(previous_shift_end_miles):
                shift.start_miles = previous_shift_end_miles[0:len(previous_shift_end_miles)-len(form.cleaned_data['miles'])] + form.cleaned_data['miles']
            else:
                shift.start_miles = form.cleaned_data['miles']
            shift.start_time = form.cleaned_data['time']
            shift.save()

            log_event(request, LoggedEventAction.LOG_START, LoggedEventModel.SHIFT, str(shift))

            site_settings = SiteSettings.load()
            if site_settings.reset_filter_on_shift_change:
                # reset schedule filter
                request.session['schedule_view_hide_completed'] = False
                request.session['schedule_view_hide_canceled'] = False
                request.session['schedule_view_hide_nolog'] = False
                request.session['schedule_view_search'] = ''
                request.session['schedule_view_driver'] = ''
                request.session['schedule_view_vehicle'] = ''

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
        'previous_shift_end_miles': previous_shift_end_miles,
    }

    return render(request, 'shift/start.html', context)

@permission_required(['transit.change_shift'])
def shiftEnd(request, id):
    shift = get_object_or_404(Shift, id=id)
    date = shift.date

    if request.method == 'POST':
        form = shiftStartEndForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

        if form.is_valid():
            if len(form.cleaned_data['miles']) < len(shift.start_miles):
                shift.end_miles = shift.start_miles[0:len(shift.start_miles)-len(form.cleaned_data['miles'])] + form.cleaned_data['miles']
            else:
                shift.end_miles = form.cleaned_data['miles']
            shift.end_time = form.cleaned_data['time']
            shift.save()

            log_event(request, LoggedEventAction.LOG_END, LoggedEventModel.SHIFT, str(shift))

            site_settings = SiteSettings.load()
            if site_settings.reset_filter_on_shift_change:
                # reset schedule filter
                request.session['schedule_view_hide_completed'] = False
                request.session['schedule_view_hide_canceled'] = False
                request.session['schedule_view_hide_nolog'] = False
                request.session['schedule_view_search'] = ''
                request.session['schedule_view_driver'] = ''
                request.session['schedule_view_vehicle'] = ''

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

    shift_prev_trip_miles = shift.start_miles
    vehicle_trips = Trip.objects.filter(date=shift.date, status=Trip.STATUS_NORMAL, vehicle=shift.vehicle)
    for vehicle_trip in vehicle_trips:
        if vehicle_trip.end_miles != '':
            mile_str = vehicle_trip.end_miles
        elif vehicle_trip.start_miles != '':
            mile_str = vehicle_trip.start_miles
        else:
            continue

        if len(mile_str) < len(shift.start_miles):
            mile_str = shift.start_miles[0:len(shift.start_miles) - len(mile_str)] + mile_str

        try:
            if mile_str != '' and float(mile_str) > float(shift_prev_trip_miles):
                shift_prev_trip_miles = mile_str
        except:
            continue

    context = {
        'form': form,
        'shift': shift,
        'shift_prev_trip_miles': shift_prev_trip_miles,
    }

    return render(request, 'shift/end.html', context)

@permission_required(['transit.change_shift'])
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

            log_event(request, LoggedEventAction.LOG_FUEL, LoggedEventModel.SHIFT, str(shift))

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


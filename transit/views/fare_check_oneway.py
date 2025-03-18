import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.db.models import Q

from transit.models import Trip, Driver
from transit.forms import DatePickerForm, DateRangePickerForm, FareCheckOneWayFixForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import *

@permission_required(['transit.view_trip'])
def fareCheckOneWayBase(request, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)
    date_end_plus_one = date_end + datetime.timedelta(days=1)

    if date_start > date_end:
        swap_date = date_start
        date_start = date_end
        date_end = swap_date

    if request.method == 'POST':
        date_picker = DatePickerForm(request.POST)
        date_range_picker = DateRangePickerForm(request.POST)
        fixer_form = FareCheckOneWayFixForm(request.POST)

        if 'fix_fare' in request.POST:
            if fixer_form.is_valid():
                trip_src = get_object_or_404(Trip, id=fixer_form.cleaned_data['trip_src'])
                trip_dst = get_object_or_404(Trip, id=fixer_form.cleaned_data['trip_dst'])

                if trip_src.fare > 0 and trip_dst.fare == 0:
                    trip_dst.fare = trip_src.fare
                    trip_src.fare = 0
                    trip_src.save()
                    log_event(request, LoggedEventAction.EDIT, LoggedEventModel.TRIP, 'Set Fare -> $' + trip_src.get_fare_str() + ' | ' + str(trip_src))
                    trip_dst.save()
                    log_event(request, LoggedEventAction.EDIT, LoggedEventModel.TRIP, 'Set Fare -> $' + trip_dst.get_fare_str() + ' | ' + str(trip_dst))

                return HttpResponseRedirect(reverse('report-fare-check-oneway', kwargs={'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))
        elif 'date_range' in request.POST:
            if date_range_picker.is_valid():
                new_start = date_range_picker.cleaned_data['date_start']
                new_end = date_range_picker.cleaned_data['date_end']
                return HttpResponseRedirect(reverse('report-fare-check-oneway', kwargs={'start_year':new_start.year, 'start_month':new_start.month, 'start_day':new_start.day, 'end_year':new_end.year, 'end_month':new_end.month, 'end_day':new_end.day}))
        else:
            if date_picker.is_valid():
                date_picker_date = date_picker.cleaned_data['date']
                return HttpResponseRedirect(reverse('report-fare-check-oneway-month', kwargs={'year':date_picker_date.year, 'month':date_picker_date.month}))
    else:
        date_picker = DatePickerForm(initial={'date':date_start})
        date_range_picker = DateRangePickerForm(initial={'date_start':date_start, 'date_end':date_end})
        fixer_form = FareCheckOneWayFixForm()

    month_prev = date_start + datetime.timedelta(days=-1)
    month_prev.replace(day=1)
    month_next = date_end + datetime.timedelta(days=1)

    url_month_prev = reverse('report-fare-check-oneway-month', kwargs={'year': month_prev.year, 'month': month_prev.month})
    url_month_next = reverse('report-fare-check-oneway-month', kwargs={'year': month_next.year, 'month': month_next.month})
    url_this_month = reverse('report-fare-check-oneway-this-month')

    all_trips = Trip.objects.filter(date__gte=date_start, date__lt=date_end_plus_one, format=Trip.FORMAT_NORMAL, fare__gt=0).exclude(status=Trip.STATUS_NORMAL)
    all_trips.select_related('vehicle')

    matched_trips = []

    try:
        return_trip_query = Q()

        for trip in all_trips:
            return_trip_query |= Q(date=trip.date, name=trip.name, address=trip.destination, destination=trip.address, status=Trip.STATUS_NORMAL, fare=0, vehicle__is_logged=True, format=Trip.FORMAT_NORMAL)

        return_trips = Trip.objects.filter(return_trip_query)

        for trip in all_trips:
            for return_trip in return_trips:
                if trip.date == return_trip.date and trip.name == return_trip.name and trip.address == return_trip.destination and trip.destination == return_trip.address:
                    matched_trips.append((trip, return_trip))
    except:
        # slow path
        # if we end up here, it's likely because the expression tree is too large for sqlite
        for trip in all_trips:
            return_trips = Trip.objects.filter(date=trip.date, name=trip.name, address=trip.destination, destination=trip.address, status=Trip.STATUS_NORMAL, fare=0, vehicle__is_logged=True, format=Trip.FORMAT_NORMAL)
            if len(return_trips) > 0:
                matched_trips.append((trip, return_trips[0]))

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'date_picker': date_picker,
        'date_range_picker': date_range_picker,
        'url_month_prev': url_month_prev,
        'url_month_next': url_month_next,
        'url_this_month': url_this_month,
        'matched_trips': matched_trips,
        'fixer_form': fixer_form,
    }
    return render(request, 'report/fare_check_oneway.html', context=context)

def fareCheckOneWayMonthBase(request, year, month):
    date_start = datetime.date(year, month, 1)
    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

    return HttpResponseRedirect(reverse('report-fare-check-oneway', kwargs={'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))

def fareCheckOneWay(request, start_year, start_month, start_day, end_year, end_month, end_day):
    return fareCheckOneWayBase(request, start_year, start_month, start_day, end_year, end_month, end_day)

def fareCheckOneWayMonth(request, year, month):
    return fareCheckOneWayMonthBase(request, year, month)

def fareCheckOneWayThisMonth(request):
    date = datetime.datetime.now().date()
    return fareCheckOneWayMonth(request, date.year, date.month)


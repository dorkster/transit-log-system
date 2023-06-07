import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.db.models import Q
from django.db.models import F

from transit.models import Client, Trip, ClientPayment, Driver
from transit.forms import DatePickerForm, DateRangePickerForm
from transit.views.report import Report

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

@permission_required(['transit.view_trip'])
def clientReportBase(request, parent, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)
    date_end_plus_one = date_end + datetime.timedelta(days=1)

    if date_start > date_end:
        swap_date = date_start
        date_start = date_end
        date_end = swap_date

    filtered_drivers = Driver.objects.filter(id=driver_id, is_active=True)
    if len(filtered_drivers) > 0:
        selected_driver = filtered_drivers[0]
    else:
        selected_driver = None

    if request.method == 'POST':
        date_picker = DatePickerForm(request.POST)
        date_range_picker = DateRangePickerForm(request.POST)

        if 'date_range' in request.POST:
            if date_range_picker.is_valid():
                new_start = date_range_picker.cleaned_data['date_start']
                new_end = date_range_picker.cleaned_data['date_end']
                if selected_driver:
                    return HttpResponseRedirect(reverse('client-report-by-driver', kwargs={'parent':parent, 'driver_id': selected_driver.id, 'start_year':new_start.year, 'start_month':new_start.month, 'start_day':new_start.day, 'end_year':new_end.year, 'end_month':new_end.month, 'end_day':new_end.day}))
                else:
                    return HttpResponseRedirect(reverse('client-report', kwargs={'parent':parent, 'start_year':new_start.year, 'start_month':new_start.month, 'start_day':new_start.day, 'end_year':new_end.year, 'end_month':new_end.month, 'end_day':new_end.day}))
        else:
            if date_picker.is_valid():
                date_picker_date = date_picker.cleaned_data['date']
                if selected_driver:
                    return HttpResponseRedirect(reverse('client-report-by-driver-month', kwargs={'parent':parent, 'driver_id': selected_driver.id, 'year':date_picker_date.year, 'month':date_picker_date.month}))
                else:
                    return HttpResponseRedirect(reverse('client-report-month', kwargs={'parent':parent, 'year':date_picker_date.year, 'month':date_picker_date.month}))
    else:
        date_picker = DatePickerForm(initial={'date':date_start})
        date_range_picker = DateRangePickerForm(initial={'date_start':date_start, 'date_end':date_end})

    month_prev = date_start + datetime.timedelta(days=-1)
    month_prev.replace(day=1)
    month_next = date_end + datetime.timedelta(days=1)

    if selected_driver:
        url_month_prev = reverse('client-report-by-driver-month', kwargs={'parent':parent, 'driver_id': selected_driver.id, 'year': month_prev.year, 'month': month_prev.month})
        url_month_next = reverse('client-report-by-driver-month', kwargs={'parent':parent, 'driver_id': selected_driver.id, 'year': month_next.year, 'month': month_next.month})
        url_this_month = reverse('client-report-by-driver-this-month', kwargs={'parent':parent, 'driver_id': selected_driver.id})
    else:
        url_month_prev = reverse('client-report-month', kwargs={'parent':parent, 'year': month_prev.year, 'month': month_prev.month})
        url_month_next = reverse('client-report-month', kwargs={'parent':parent, 'year': month_next.year, 'month': month_next.month})
        url_this_month = reverse('client-report-this-month', kwargs={'parent':parent})

    client = Client.objects.get(id=parent)

    all_trips = Trip.objects.filter(date__gte=date_start, date__lt=date_end_plus_one, name=client.name, format=Trip.FORMAT_NORMAL)
    if selected_driver:
        all_trips = all_trips.filter(driver=selected_driver)

    blank_log = Q(start_miles='') & Q(end_miles='') & Q(start_time='') & Q(end_time='')
    filled_log = ~Q(start_miles='') & ~Q(end_miles='') & ~Q(start_time='') & ~Q(end_time='')

    trips_normal = all_trips.filter(status=Trip.STATUS_NORMAL)
    if not selected_driver:
        trips_normal = trips_normal.filter(filled_log)
    else:
        trips_normal = trips_normal.filter(blank_log | filled_log)
    trips_canceled = all_trips.filter(status=Trip.STATUS_CANCELED)
    trips_no_show = all_trips.filter(status=Trip.STATUS_NO_SHOW)
    trips_canceled_late = trips_canceled.filter(cancel_date__gte=F('date'))
    trips_money = trips_normal.filter(Q(fare__gt=0) | Q(collected_cash__gt=0) | Q(collected_check__gt=0))

    payments = ClientPayment.objects.filter(parent=client.id, date_paid__gte=date_start, date_paid__lt=date_end_plus_one)

    total_fares_and_payments = len(trips_money) + len(payments)

    # run report to get all fares/payments
    report = Report()
    if selected_driver:
        report.load(date_start, date_end, client_name=client.name, filter_by_money=True, driver_id=selected_driver.id)
    else:
        report.load(date_start, date_end, client_name=client.name, filter_by_money=True)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'date_picker': date_picker,
        'date_range_picker': date_range_picker,
        'url_month_prev': url_month_prev,
        'url_month_next': url_month_next,
        'url_this_month': url_this_month,
        'client': client,
        'trips_normal': trips_normal,
        'trips_canceled': trips_canceled,
        'trips_no_show': trips_no_show,
        'trips_canceled_late': trips_canceled_late,
        'trips_money': trips_money,
        'payments': payments,
        'total_fares_and_payments': total_fares_and_payments,
        'report': report,
        'selected_driver': selected_driver,
        'drivers': Driver.objects.filter(is_active=True)
    }
    return render(request, 'client/report/view.html', context=context)

def clientReportMonthBase(request, parent, driver_id, year, month):
    date_start = datetime.date(year, month, 1)
    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

    if driver_id:
        return HttpResponseRedirect(reverse('client-report-by-driver', kwargs={'parent':parent, 'driver_id': driver_id, 'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))
    else:
        return HttpResponseRedirect(reverse('client-report', kwargs={'parent':parent, 'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))

def clientReport(request, parent, start_year, start_month, start_day, end_year, end_month, end_day):
    return clientReportBase(request, parent, None, start_year, start_month, start_day, end_year, end_month, end_day)

def clientReportMonth(request, parent, year, month):
    return clientReportMonthBase(request, parent, None, year, month)

def clientReportThisMonth(request, parent):
    date = datetime.datetime.now().date()
    return clientReportMonth(request, parent, date.year, date.month)

def clientReportByDriver(request, parent, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    return clientReportBase(request, parent, driver_id, start_year, start_month, start_day, end_year, end_month, end_day)

def clientReportByDriverMonth(request, parent, driver_id, year, month):
    return clientReportMonthBase(request, parent, driver_id, year, month)

def clientReportByDriverThisMonth(request, parent, driver_id):
    date = datetime.datetime.now().date()
    return clientReportByDriverMonth(request, parent, driver_id, date.year, date.month)


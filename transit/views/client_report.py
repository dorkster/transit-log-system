import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.db.models import Q
from django.db.models import F

from transit.models import Client, Trip
from transit.forms import DatePickerForm, DateRangePickerForm
from transit.views.report import Report

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

@permission_required(['transit.view_trip'])
def clientReportBase(request, parent, start_year, start_month, start_day, end_year, end_month, end_day):
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

        if 'date_range' in request.POST:
            if date_range_picker.is_valid():
                new_start = date_range_picker.cleaned_data['date_start']
                new_end = date_range_picker.cleaned_data['date_end']
                return HttpResponseRedirect(reverse('client-report', kwargs={'parent':parent, 'start_year':new_start.year, 'start_month':new_start.month, 'start_day':new_start.day, 'end_year':new_end.year, 'end_month':new_end.month, 'end_day':new_end.day}))
        else:
            if date_picker.is_valid():
                date_picker_date = date_picker.cleaned_data['date']
                return HttpResponseRedirect(reverse('client-report-month', kwargs={'parent':parent, 'year':date_picker_date.year, 'month':date_picker_date.month}))
    else:
        date_picker = DatePickerForm(initial={'date':date_start})
        date_range_picker = DateRangePickerForm(initial={'date_start':date_start, 'date_end':date_end})

    month_prev = date_start + datetime.timedelta(days=-1)
    month_prev.replace(day=1)
    month_next = date_end + datetime.timedelta(days=1)

    url_month_prev = reverse('client-report-month', kwargs={'parent':parent, 'year': month_prev.year, 'month': month_prev.month})
    url_month_next = reverse('client-report-month', kwargs={'parent':parent, 'year': month_next.year, 'month': month_next.month})
    url_this_month = reverse('client-report-this-month', kwargs={'parent':parent})

    client = Client.objects.get(id=parent)

    all_trips = Trip.objects.filter(date__gte=date_start, date__lt=date_end_plus_one, name=client.name, format=Trip.FORMAT_NORMAL)
    trips_normal = all_trips.filter(status=Trip.STATUS_NORMAL).exclude(Q(start_miles='') | Q(end_miles='') | Q(start_time='') | Q(end_time=''))
    trips_canceled = all_trips.filter(status=Trip.STATUS_CANCELED)
    trips_no_show = all_trips.filter(status=Trip.STATUS_NO_SHOW)
    trips_canceled_late = trips_canceled.filter(cancel_date__gte=F('date'))

    # run report to get all fares/payments
    report = Report()
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
        'report': report,
    }
    return render(request, 'client/report/view.html', context=context)

def clientReport(request, parent, start_year, start_month, start_day, end_year, end_month, end_day):
    return clientReportBase(request, parent, start_year, start_month, start_day, end_year, end_month, end_day)

def clientReportMonth(request, parent, year, month):
    date_start = datetime.date(year, month, 1)
    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

    return HttpResponseRedirect(reverse('client-report', kwargs={'parent':parent, 'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))

def clientReportThisMonth(request, parent):
    date = datetime.datetime.now().date()
    return clientReportMonth(request, parent, date.year, date.month)

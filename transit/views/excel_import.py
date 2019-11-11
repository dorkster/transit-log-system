import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from openpyxl import load_workbook

from transit.models import Shift, Trip, Driver, Vehicle, TripType
from transit.forms import UploadFileForm

def excelImport(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            log_data_only = form.cleaned_data['log_data_only']
            shifts = []
            trips = []
            for i in request.FILES.getlist('file'):
                excelParseFile(i, shifts, trips, log_data_only)
            # return HttpResponseRedirect(reverse('excel-import'))
            return render(request, 'excel_import.html', {'form': form, 'trips':trips, 'shifts':shifts})
    else:
        form = UploadFileForm()
    return render(request, 'excel_import.html', {'form': form})

def excelParseFile(file_obj, shifts, trips, log_data_only):
    workbook = load_workbook(file_obj, data_only=True)
    sheet = workbook['Schedule']

    date_str = sheet['C1'].value
    date = datetime.datetime.strptime(date_str, '%B %d. %Y').date()

    shift_range = range(98,101)
    for i in shift_range:
        shift = Shift()
        shift.date = date

        # determine which rows to skip
        if log_data_only:
            if sheet['D' + str(i)].value == None and sheet['E' + str(i)].value == None and sheet['F' + str(i)].value == None and sheet['G' + str(i)].value == None:
                continue
        else:
            if sheet['A' + str(i)].value == None:
                continue

        if sheet['A' + str(i)].value != None:
            query = Driver.objects.filter(name=str(sheet['A' + str(i)].value))
            if query:
                shift.driver = query[0]

        if sheet['C' + str(i)].value != None:
            query = Vehicle.objects.filter(name=str(sheet['C' + str(i)].value))
            if query:
                shift.vehicle = query[0]

        if sheet['D' + str(i)].value != None:
            shift.start_miles = '{:.1f}'.format(float(sheet['D' + str(i)].value)).strip()

        if sheet['E' + str(i)].value != None:
            shift.start_time = sheet['E' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet['F' + str(i)].value != None:
            shift.end_miles = '{:.1f}'.format(float(sheet['F' + str(i)].value)).strip()

        if sheet['G' + str(i)].value != None:
            shift.end_time = sheet['G' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet['H' + str(i)].value != None:
            shift.fuel = '{:.1f}'.format(float(sheet['H' + str(i)].value)).strip()

        shifts.append(shift)
        shift.save()

    trip_query = Trip.objects.filter(date=date).order_by('-sort_index')
    if trip_query:
        sort_index = trip_query[0]
    else:
        sort_index = 0

    trip_ranges = list(range(5,27)) + list(range(30, 50)) + list(range(53, 73)) + list(range(76, 96))
    for i in trip_ranges:
        trip = Trip()
        trip.date = date

        # determine which rows to skip
        if log_data_only:
            if sheet['G' + str(i)].value == None and sheet['H' + str(i)].value == None and sheet['I' + str(i)].value == None and sheet['J' + str(i)].value == None:
                continue
        else:
            if sheet['C' + str(i)].value == None:
                continue

        if sheet['A' + str(i)].value != None:
            trip.pick_up_time = sheet['A' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet['B' + str(i)].value != None:
            trip.appointment_time = sheet['B' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet['C' + str(i)].value != None:
            trip.name = str(sheet['C' + str(i)].value).strip()

        if sheet['D' + str(i)].value != None:
            trip.address = str(sheet['D' + str(i)].value).strip()

        # TODO actually validate phone number formatting
        if sheet['E' + str(i)].value != None:
            trip.phone_home = str(sheet['E' + str(i)].value).split(' ')[0].strip()

        if sheet['F' + str(i)].value != None:
            trip.destination = str(sheet['F' + str(i)].value).strip()

        if sheet['G' + str(i)].value != None:
            trip.start_miles = '{:.1f}'.format(float(sheet['G' + str(i)].value)).strip()

        if sheet['H' + str(i)].value != None:
            trip.start_time = sheet['H' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet['I' + str(i)].value != None:
            trip.end_miles = '{:.1f}'.format(float(sheet['I' + str(i)].value)).strip()

        if sheet['J' + str(i)].value != None:
            trip.end_time = sheet['J' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet['K' + str(i)].value != None:
            trip.note = str(sheet['K' + str(i)].value).strip()

        if sheet['L' + str(i)].value != None:
            driver_name = str(sheet['L' + str(i)].value).strip()
            if driver_name == 'Canceled':
                trip.status = Trip.STATUS_CANCELED
            else:
                query = Driver.objects.filter(name=driver_name)
                if query:
                    trip.driver = query[0]

        if sheet['M' + str(i)].value != None:
            query = Vehicle.objects.filter(name=str(sheet['M' + str(i)].value).strip())
            if query:
                trip.vehicle = query[0]

        if sheet['N' + str(i)].value != None:
            trip_type = str(sheet['N' + str(i)].value).strip()
            query = None
            if trip_type == 'Social/Rec.':
                query = TripType.objects.filter(name='Social/Recreation')
            else:
                query = TripType.objects.filter(name=trip_type)
            if query:
                trip.trip_type = query[0]

        trip.sort_index = sort_index
        sort_index += 1

        trips.append(trip)
        trip.save()


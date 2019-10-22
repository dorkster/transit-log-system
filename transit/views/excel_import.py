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
            shifts = []
            trips = []
            for i in request.FILES.getlist('file'):
                excelParseFile(i, shifts, trips)
            # return HttpResponseRedirect(reverse('excel-import'))
            return render(request, 'excel_import.html', {'form': form, 'trips':trips, 'shifts':shifts})
    else:
        form = UploadFileForm()
    return render(request, 'excel_import.html', {'form': form})

def excelParseFile(file_obj, shifts, trips):
    workbook = load_workbook(file_obj, data_only=True)
    sheet_schedule = workbook['Schedule']

    date_str = sheet_schedule['C1'].value
    date = datetime.datetime.strptime(date_str, "%B %d. %Y").date()

    shift_range = range(98,101)
    for i in shift_range:
        start_miles = sheet_schedule['D' + str(i)].value
        start_time = sheet_schedule['E' + str(i)].value
        end_miles = sheet_schedule['F' + str(i)].value
        end_time = sheet_schedule['G' + str(i)].value

        shift = Shift()
        shift.date = date

        # if we dont' have any log data, we want to skip this row
        if start_miles == None and start_time == None and end_miles == None and end_time == None:
            continue

        if sheet_schedule['A' + str(i)].value != None:
            query = Driver.objects.filter(name=str(sheet_schedule['A' + str(i)].value))
            if query:
                shift.driver = query[0]

        if sheet_schedule['C' + str(i)].value != None:
            query = Vehicle.objects.filter(name=str(sheet_schedule['C' + str(i)].value))
            if query:
                shift.vehicle = query[0]

        if sheet_schedule['D' + str(i)].value != None:
            shift.start_miles = '{:.1f}'.format(float(sheet_schedule['D' + str(i)].value)).strip()

        if sheet_schedule['E' + str(i)].value != None:
            shift.start_time = sheet_schedule['E' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet_schedule['F' + str(i)].value != None:
            shift.end_miles = '{:.1f}'.format(float(sheet_schedule['F' + str(i)].value)).strip()

        if sheet_schedule['G' + str(i)].value != None:
            shift.end_time = sheet_schedule['G' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet_schedule['H' + str(i)].value != None:
            shift.fuel = '{:.1f}'.format(float(sheet_schedule['H' + str(i)].value)).strip()

        shifts.append(shift)
        shift.save()

    query = Trip.objects.filter(date=date).order_by('-sort_index')
    if query:
        sort_index = query[0]
    else:
        sort_index = 0

    trip_ranges = list(range(5,27)) + list(range(30, 50)) + list(range(53, 73)) + list(range(76, 96))
    for i in trip_ranges:
        start_miles = sheet_schedule['G' + str(i)].value
        start_time = sheet_schedule['H' + str(i)].value
        end_miles = sheet_schedule['I' + str(i)].value
        end_time = sheet_schedule['J' + str(i)].value

        trip = Trip()
        trip.date = date

        # if we dont' have any log data, we want to skip this row
        if start_miles == None and start_time == None and end_miles == None and end_time == None:
            continue

        if sheet_schedule['A' + str(i)].value != None:
            trip.pick_up_time = sheet_schedule['A' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet_schedule['B' + str(i)].value != None:
            trip.appointment_time = sheet_schedule['B' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet_schedule['C' + str(i)].value != None:
            trip.name = str(sheet_schedule['C' + str(i)].value).strip()

        if sheet_schedule['D' + str(i)].value != None:
            trip.address = str(sheet_schedule['D' + str(i)].value).strip()

        # TODO actually validate phone number formatting
        if sheet_schedule['E' + str(i)].value != None:
            trip.phone = str(sheet_schedule['E' + str(i)].value).split(' ')[0].strip()

        if sheet_schedule['F' + str(i)].value != None:
            trip.destination = str(sheet_schedule['F' + str(i)].value).strip()

        if sheet_schedule['G' + str(i)].value != None:
            trip.start_miles = '{:.1f}'.format(float(sheet_schedule['G' + str(i)].value)).strip()

        if sheet_schedule['H' + str(i)].value != None:
            trip.start_time = sheet_schedule['H' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet_schedule['I' + str(i)].value != None:
            trip.end_miles = '{:.1f}'.format(float(sheet_schedule['I' + str(i)].value)).strip()

        if sheet_schedule['J' + str(i)].value != None:
            trip.end_time = sheet_schedule['J' + str(i)].value.strftime('%_I:%M %p').strip()

        if sheet_schedule['K' + str(i)].value != None:
            trip.notes = str(sheet_schedule['K' + str(i)].value).strip()

        if sheet_schedule['L' + str(i)].value != None:
            query = Driver.objects.filter(name=str(sheet_schedule['L' + str(i)].value).strip())
            if query:
                trip.driver = query[0]

        if sheet_schedule['M' + str(i)].value != None:
            query = Vehicle.objects.filter(name=str(sheet_schedule['M' + str(i)].value).strip())
            if query:
                trip.vehicle = query[0]

        if sheet_schedule['N' + str(i)].value != None:
            trip_type = str(sheet_schedule['N' + str(i)].value).strip()
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


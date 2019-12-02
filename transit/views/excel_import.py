import datetime, re

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from openpyxl import load_workbook

from transit.models import Shift, Trip, Driver, Vehicle, TripType
from transit.forms import UploadFileForm

def getWorkHourTime(t_time):
    if t_time.hour >= 1 and t_time.hour <= 6:
        return t_time.replace(hour=(t_time.hour+12))
    return t_time

def excelImport(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            options = {}
            options['log_data_only'] = True if form.cleaned_data['log_data_only'] == 'True' else False
            options['dry_run'] = True if form.cleaned_data['dry_run'] == 'True' else False
            shifts = []
            trips = []
            errors = []
            for i in request.FILES.getlist('file'):
                excelParseFile(i, shifts, trips, errors, options)
            # return HttpResponseRedirect(reverse('excel-import'))
            return render(request, 'excel_import.html', {'form': form, 'import_done': True, 'trips':trips, 'shifts':shifts, 'errors':errors})
    else:
        form = UploadFileForm()
    return render(request, 'excel_import.html', {'form': form, 'import_done': False, })

def excelParseFile(file_obj, shifts, trips, errors, options):
    workbook = load_workbook(file_obj, data_only=True)
    sheet = workbook['Schedule']

    date_str = sheet['C1'].value
    try:
        date = datetime.datetime.strptime(str(date_str), '%B %d. %Y').date()
    except:
        errors.append(str(file_obj) + ': Could not parse date string')
        return

    S_DRIVER = 0
    S_VEHICLE = 2
    S_START_MILES = 3
    S_START_TIME = 4
    S_END_MILES = 5
    S_END_TIME = 6
    S_FUEL = 7

    # TODO verify that this range hasn't been altered by adding/deleting rows
    shift_data = sheet['A98:H100']
    for row in shift_data:
        shift = Shift()
        shift.date = date

        # determine which rows to skip
        if options['log_data_only']:
            if row[S_START_MILES].value == None and row[S_START_TIME].value == None and row[S_END_MILES].value == None and row[S_END_TIME].value == None:
                continue
        else:
            if row[S_DRIVER].value == None:
                continue

        if row[S_DRIVER].value != None:
            query = Driver.objects.filter(name=str(row[S_DRIVER].value))
            if query:
                shift.driver = query[0]

        if row[S_VEHICLE].value != None:
            query = Vehicle.objects.filter(name=str(row[S_VEHICLE].value))
            if query:
                shift.vehicle = query[0]

        if type(row[S_START_MILES].value) == int or type(row[S_START_MILES].value) == float:
            shift.start_miles = '{:.1f}'.format(float(row[S_START_MILES].value)).strip()
        elif row[S_START_MILES].value != None:
            errors.append(str(file_obj) + ': Could not parse shift start miles, "' + str(row[S_START_MILES].value) + '"')

        if type(row[S_START_TIME].value) == datetime.time:
            shift.start_time = getWorkHourTime(row[S_START_TIME].value).strftime('%_I:%M %p').strip()
        elif row[S_START_TIME].value != None:
            errors.append(str(file_obj) + ': Could not parse shift start time, "' + str(row[S_START_TIME].value) + '"')

        if type(row[S_END_MILES].value) == int or type(row[S_END_MILES].value) == float:
            shift.end_miles = '{:.1f}'.format(float(row[S_END_MILES].value)).strip()
        elif row[S_END_MILES].value != None:
            errors.append(str(file_obj) + ': Could not parse shift end miles, "' + str(row[S_END_MILES].value) + '"')

        if type(row[S_END_TIME].value) == datetime.time:
            shift.end_time = getWorkHourTime(row[S_END_TIME].value).strftime('%_I:%M %p').strip()
        elif row[S_END_TIME].value != None:
            errors.append(str(file_obj) + ': Could not parse shift end time, "' + str(row[S_END_TIME].value) + '"')

        if type(row[S_FUEL].value) == int or type(row[S_FUEL].value) == float:
            shift.fuel = '{:.1f}'.format(float(row[S_FUEL].value)).strip()
        elif row[S_FUEL].value != None:
            errors.append(str(file_obj) + ': Could not parse shift fuel, "' + str(row[S_FUEL].value) + '"')

        shifts.append(shift)
        if not options['dry_run']:
            shift.save()

    trip_query = Trip.objects.filter(date=date).order_by('-sort_index')
    if trip_query:
        sort_index = trip_query[0].sort_index + 1
    else:
        sort_index = 0

    T_PICKUP = 0
    T_APPOINTMENT = 1
    T_NAME = 2
    T_ADDRESS = 3
    T_PHONE = 4
    T_DESTINATION = 5
    T_START_MILES = 6
    T_START_TIME = 7
    T_END_MILES = 8
    T_END_TIME = 9
    T_NOTE = 10
    T_DRIVER = 11
    T_VEHICLE = 12
    T_TRIPTYPE = 13

    # NOTE These were never used
    # T_ELDERLY = 14
    # T_AMBULATORY = 15

    pages = []
    # TODO verify that these ranges haven't been altered by adding/deleting rows
    pages.append(sheet['A5:P26'])
    pages.append(sheet['A30:P49'])
    pages.append(sheet['A53:P72'])
    pages.append(sheet['A76:P95'])

    for page in pages:
        for row in page:
            trip = Trip()
            trip.date = date

            # determine which rows to skip
            if options['log_data_only']:
                if row[T_START_MILES].value == None and row[T_START_TIME].value == None and row[T_END_MILES].value == None and row[T_END_TIME].value == None:
                    continue
            else:
                if row[T_NAME].value == None:
                    continue

            if type(row[T_PICKUP].value) == datetime.time:
                trip.pick_up_time = getWorkHourTime(row[T_PICKUP].value).strftime('%_I:%M %p').strip()
            elif row[T_PICKUP].value != None:
                errors.append(str(file_obj) + ': Could not parse pick-up start time, "' + str(row[T_PICKUP].value) + '"')

            if type(row[T_APPOINTMENT].value) == datetime.time:
                trip.appointment_time = getWorkHourTime(row[T_APPOINTMENT].value).strftime('%_I:%M %p').strip()
            elif row[T_APPOINTMENT].value != None:
                errors.append(str(file_obj) + ': Could not parse appointment start time, "' + str(row[T_APPOINTMENT].value) + '"')

            if row[T_NAME].value != None:
                trip.name = str(row[T_NAME].value).strip()

            if row[T_ADDRESS].value != None:
                trip.address = str(row[T_ADDRESS].value).strip()

            if row[T_PHONE].value != None:
                phone_str = str(row[T_PHONE].value).split(' ')[0].strip()

                matches = re.findall('\d*', phone_str)
                phone_str = ''
                for i in matches:
                    phone_str += i

                if len(phone_str) >= 10:
                    phone_str = phone_str[len(phone_str)-10:len(phone_str)-7] + '-' + phone_str[len(phone_str)-7:len(phone_str)-4] + '-' + phone_str[len(phone_str)-4:]
                elif len(phone_str) >= 7:
                    phone_str = phone_str[len(phone_str)-7:len(phone_str)-4] + '-' + phone_str[len(phone_str)-4:]
                else:
                    phone_str = ''

                trip.phone_home = phone_str

            if row[T_DESTINATION].value != None:
                trip.destination = str(row[T_DESTINATION].value).strip()

            if type(row[T_START_MILES].value) == int or type(row[T_START_MILES].value) == float:
                trip.start_miles = '{:.1f}'.format(float(row[T_START_MILES].value)).strip()
            elif row[T_START_MILES].value != None:
                errors.append(str(file_obj) + ': Could not parse trip start miles, "' + str(row[T_START_MILES].value) + '"')

            if type(row[T_START_TIME].value) == datetime.time:
                trip.start_time = getWorkHourTime(row[T_START_TIME].value).strftime('%_I:%M %p').strip()
            elif row[T_START_TIME].value != None:
                errors.append(str(file_obj) + ': Could not parse trip start time, "' + str(row[T_START_TIME].value) + '"')

            if type(row[T_END_MILES].value) == int or type(row[T_END_MILES].value) == float:
                trip.end_miles = '{:.1f}'.format(float(row[T_END_MILES].value)).strip()
            elif row[T_END_MILES].value != None:
                errors.append(str(file_obj) + ': Could not parse trip end miles, "' + str(row[T_END_MILES].value) + '"')

            if type(row[T_END_TIME].value) == datetime.time:
                trip.end_time = getWorkHourTime(row[T_END_TIME].value).strftime('%_I:%M %p').strip()
            elif row[T_END_TIME].value != None:
                errors.append(str(file_obj) + ': Could not parse trip end time, "' + str(row[T_END_TIME].value) + '"')

            if row[T_NOTE].value != None:
                trip.note = str(row[T_NOTE].value).strip()

            if row[T_DRIVER].value != None:
                driver_name = str(row[T_DRIVER].value).strip()
                if driver_name == 'Canceled':
                    trip.status = Trip.STATUS_CANCELED
                else:
                    query = Driver.objects.filter(name=driver_name)
                    if query:
                        trip.driver = query[0]

            if row[T_VEHICLE].value != None:
                query = Vehicle.objects.filter(name=str(row[T_VEHICLE].value).strip())
                if query:
                    trip.vehicle = query[0]

            if row[T_TRIPTYPE].value != None:
                trip_type = str(row[T_TRIPTYPE].value).strip()
                query = None
                if trip_type == 'Social/Rec.':
                    query = TripType.objects.filter(name='Social/Recreation')
                else:
                    query = TripType.objects.filter(name=trip_type)
                if query:
                    trip.trip_type = query[0]

            trip.sort_index = sort_index
            sort_index += 1

            if trip.name and not trip.address and not trip.destination and not trip.driver and not trip.vehicle and trip.check_blank(''):
                trip.is_activity = True
                trip.note = trip.name
                trip.name = ''

            trips.append(trip)
            if not options['dry_run']:
                trip.save()


import datetime, re

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from openpyxl import load_workbook

from transit.models import Shift, Trip, Driver, Vehicle, TripType
from transit.forms import UploadFileForm

from django.contrib.auth.decorators import permission_required

@permission_required(['transit.change_trip', 'transit.change_shift'])
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
    def parseString(cell_value):
        if cell_value != None:
            return str(cell_value).strip()
        else:
            return ''

    def parseTime(cell_value, file_obj, errors, error_str):
        def getWorkHourTime(t_time):
            if t_time.hour >= 1 and t_time.hour <= 6:
                return t_time.replace(hour=(t_time.hour+12))
            return t_time

        if type(cell_value) == datetime.time:
            return getWorkHourTime(cell_value).strftime('%_I:%M %p').strip()
        elif cell_value != None:
            errors.append(str(file_obj) + ': Could not parse ' + error_str + ' time, "' + str(cell_value) + '"')
        return ''

    def parseMiles(cell_value, file_obj, errors, error_str):
        if type(cell_value) == int or type(cell_value) == float:
            return '{:.1f}'.format(float(cell_value)).strip()
        elif cell_value != None:
            errors.append(str(file_obj) + ': Could not parse ' + error_str + ' miles, "' + str(cell_value) + '"')
        return ''

    def parseFuel(cell_value, file_obj, errors):
        if type(cell_value) == int or type(cell_value) == float:
            return '{:.1f}'.format(float(cell_value)).strip()
        elif cell_value != None:
            errors.append(str(file_obj) + ': Could not parse fuel, "' + str(cell_value) + '"')
        return ''

    def parseDriver(cell_value):
        if cell_value == None:
            return (None, Trip.STATUS_NORMAL)

        driver_name = str(cell_value).strip()
        driver = None
        status = Trip.STATUS_NORMAL
        if driver_name == 'Canceled':
            status = Trip.STATUS_CANCELED
        else:
            query = Driver.objects.filter(name=driver_name)
            if query:
                driver = query[0]

        return (driver, status)

    def parseVehicle(cell_value):
        if cell_value == None:
            return None

        vehicle_name = str(cell_value).strip()
        query = Vehicle.objects.filter(name=vehicle_name)
        if query:
            return query[0]
        else:
            return None

    def parsePhone(cell_value):
        if cell_value == None:
            return ''

        phone_str = str(cell_value).split(' ')[0].strip()

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

        return phone_str

    def parseTripType(cell_value):
        if cell_value == None:
            return None

        trip_type = str(cell_value).strip()
        query = None
        if trip_type == 'Social/Rec.':
            query = TripType.objects.filter(name='Social/Recreation')
        else:
            query = TripType.objects.filter(name=trip_type)
        if query:
            return query[0]
        else:
            return None

    workbook = load_workbook(file_obj, data_only=True)
    sheet = workbook['Schedule']

    date_str = sheet['C1'].value
    try:
        date = datetime.datetime.strptime(str(date_str), '%B %d. %Y').date()
    except:
        errors.append(str(file_obj) + ': Could not parse date string')
        return

    # Sanity check the template format
    santity_check_failed = False
    page_error = ' is not on the correct row/column, which is a sign that rows/columns have been added/deleted.'
    if str(sheet['K1'].value).strip() != 'Page 1':
        errors.append(str(file_obj) + ': "Page 1"' + page_error) 
        santity_check_failed = True
    if str(sheet['K27'].value).strip() != 'Page 2':
        errors.append(str(file_obj) + ': "Page 2"' + page_error)
        santity_check_failed = True
    if str(sheet['K50'].value).strip() != 'Page 3':
        errors.append(str(file_obj) + ': "Page 3"' + page_error)
        santity_check_failed = True
    if str(sheet['K73'].value).strip() != 'Page 4':
        errors.append(str(file_obj) + ': "Page 4"' + page_error)
        santity_check_failed = True
    if str(sheet['A97'].value).strip() != 'DRIVER':
        errors.append(str(file_obj) + ': The shift summary header is not on the correct row, which is a sign that rows have been added/deleted.')
        santity_check_failed = True

    if santity_check_failed:
        errors.append(str(file_obj) +': Incorrect template format detected. Canceling import!')
        return

    S_DRIVER = 0
    S_VEHICLE = 2
    S_START_MILES = 3
    S_START_TIME = 4
    S_END_MILES = 5
    S_END_TIME = 6
    S_FUEL = 7

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

        shift.driver = parseDriver(row[S_DRIVER].value)[0]
        shift.vehicle = parseVehicle(row[S_VEHICLE].value)
        shift.start_miles = parseMiles(row[S_START_MILES].value, file_obj, errors, 'shift start')
        shift.start_time = parseTime(row[S_START_TIME].value, file_obj, errors, 'shift start')
        shift.end_miles = parseMiles(row[S_END_MILES].value, file_obj, errors, 'shift end')
        shift.end_time = parseTime(row[S_END_TIME].value, file_obj, errors, 'shift end')
        shift.fuel = parseFuel(row[S_FUEL].value, file_obj, errors)

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

            trip.pick_up_time = parseTime(row[T_PICKUP].value, file_obj, errors, 'pick-up')
            trip.appointment_time = parseTime(row[T_APPOINTMENT].value, file_obj, errors, 'appointment')
            trip.name = parseString(row[T_NAME].value)
            trip.address = parseString(row[T_ADDRESS].value)
            trip.phone_home = parsePhone(row[T_PHONE].value)
            trip.destination = parseString(row[T_DESTINATION].value)
            trip.start_miles = parseMiles(row[T_START_MILES].value, file_obj, errors, 'trip start')
            trip.start_time = parseTime(row[T_START_TIME].value, file_obj, errors, 'trip start')
            trip.end_miles = parseMiles(row[T_END_MILES].value, file_obj, errors, 'trip end')
            trip.end_time = parseTime(row[T_END_TIME].value, file_obj, errors, 'trip end')
            trip.note = parseString(row[T_NOTE].value)

            driver_query = parseDriver(row[T_DRIVER].value)
            trip.driver = driver_query[0]
            trip.status = driver_query[1]

            trip.vehicle = parseVehicle(row[T_VEHICLE].value)
            trip.trip_type = parseTripType(row[T_TRIPTYPE].value)

            trip.sort_index = sort_index
            sort_index += 1

            if trip.name and not trip.address and not trip.destination and not trip.driver and not trip.vehicle and trip.check_blank(''):
                trip.is_activity = True
                trip.note = trip.name
                trip.name = ''

            trips.append(trip)
            if not options['dry_run']:
                trip.save()


import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from transit.models import Driver, Vehicle, Trip, Shift, TripType, Client
from transit.forms import DatePickerForm

def report(request, year, month):
    T_STR = 0
    T_FLOAT = 1
    class Money():
        def __init__(self, default_value=0):
            self.value = default_value
        def __add__(self, other):
            return Money(self.value + other.value)
        def __str__(self):
            if self.value < 10:
                return '$0.0' + str(self.value)
            elif self.value < 100:
                return '$0.' + str(self.value)
            else:
                val_str = str(self.value)
                return '$' + val_str[0:len(val_str)-2] + '.' + val_str[len(val_str)-2:]

    class ReportShift():
        def __init__(self):
            self.shift = None
            self.start_miles = { T_STR:None, T_FLOAT:None }
            self.start_time = None
            self.end_miles = { T_STR:None, T_FLOAT:None }
            self.end_time = None
            self.fuel = 0
            self.start_trip = None
            self.end_trip = None

    class ReportTrip():
        def __init__(self):
            self.trip = None
            self.shift = None
            self.start_miles = { T_STR:None, T_FLOAT: None }
            self.start_time = None
            self.end_miles = { T_STR:None, T_FLOAT: None }
            self.end_time = None
            self.trip_type = None
            self.collected_cash = Money(0)
            self.collected_check = Money(0)

    class ReportDay():
        def __init__(self):
            self.date = None
            self.shifts = []
            self.trips = []

            self.by_vehicle = {}
            for i in Vehicle.objects.all():
                self.by_vehicle[i] = ReportSummary()

            self.by_driver = {}
            for i in Driver.objects.filter(is_logged=True):
                self.by_driver[i] = ReportSummary()

        def hasVehicleInShift(self, vehicle):
            for i in self.shifts:
                if i.shift.vehicle == vehicle:
                    return True
            return False
        
        def hasDriverInShift(self, driver):
            for i in self.shifts:
                if i.shift.driver == driver:
                    return True
            return False

    class ReportSummary():
        def __init__(self):
            self.service_miles = 0
            self.service_hours = 0
            self.deadhead_miles = 0
            self.deadhead_hours = 0
            self.total_miles = 0
            self.total_hours = 0
            self.pmt = 0
            self.fuel = 0
            self.trip_types = {}
            self.collected_cash = Money(0)
            self.collected_check = Money(0)

            for i in TripType.objects.all():
                self.trip_types[i] = 0

        def __add__(self, other):
            r = self
            r.service_miles += other.service_miles
            r.service_hours += other.service_hours
            r.deadhead_miles += other.deadhead_miles
            r.deadhead_hours += other.deadhead_hours
            r.total_miles += other.total_miles
            r.total_hours += other.total_hours
            r.pmt += other.pmt
            r.fuel += other.fuel
            for i in TripType.objects.all():
                r.trip_types[i] += other.trip_types[i]
            r.collected_cash += other.collected_cash
            r.collected_check += other.collected_check
            return r

    class ReportOutputVehicles():
        def __init__(self):
            self.vehicle = None
            self.days = []
            self.totals = ReportSummary()

    class ReportOutputDrivers():
        def __init__(self):
            self.driver = None
            self.days = []
            self.totals = ReportSummary()

    class ReportErrors():
        SHIFT_INCOMPLETE = 0
        TRIP_INCOMPLETE = 1
        TRIP_NO_SHIFT = 2
        TRIP_MILES_OOB = 3
        TRIP_TIME_OOB = 4

        def __init__(self):
            self.errors = []
        def add(self, date, error_code, error_shift=None, error_trip=None):
            self.errors.append({'date':date, 'error_code':error_code, 'error_shift': error_shift, 'error_trip': error_trip})

    class UniqueRiderSummary():
        class Rider():
            def __init__(self, name, elderly, ambulatory):
                self.name = name
                self.elderly = elderly
                self.ambulatory = ambulatory
            def __lt__(self, other):
                return self.name < other.name

        def __init__(self):
            self.names = []
            self.elderly_ambulatory = 0
            self.elderly_nonambulatory = 0
            self.nonelderly_ambulatory = 0
            self.nonelderly_nonambulatory = 0
            self.unknown = 0

        def __contains__(self, item):
            for i in self.names:
                if i.name == item:
                    return True

    report_errors = ReportErrors()
    unique_riders = UniqueRiderSummary()

    date_start = datetime.date(year, month, 1)

    if request.method == 'POST':
        date_picker = DatePickerForm(request.POST)
        if date_picker.is_valid():
            date_picker_date = date_picker.cleaned_data['date']
            return HttpResponseRedirect(reverse('report', kwargs={'year':date_picker_date.year, 'month':date_picker_date.month}))
    else:
        date_picker = DatePickerForm(initial={'date':date_start})

    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

    month_prev = date_start + datetime.timedelta(days=-1)
    month_prev.replace(day=1)
    month_next = date_end + datetime.timedelta(days=1)

    report_all = []

    money_trips = []
    money_trips_summary = ReportSummary()

    for day in range(date_start.day, date_end.day+1):
        day_date = datetime.date(year, month, day)

        report_day = ReportDay()
        report_day.date = day_date

        shifts = Shift.objects.filter(date=day_date)
        for i in shifts:
            if i.start_miles == '' or i.start_time == '' or i.end_miles == '' or i.end_time == '' or not i.driver or not i.vehicle:
                # skip incomplete shift
                if i.start_miles != '' or i.start_time != '' or i.end_miles != '' or i.end_time != '':
                    report_errors.add(day_date, report_errors.SHIFT_INCOMPLETE, error_shift=i)
                continue

            report_shift = ReportShift()
            report_shift.shift = i
            report_shift.start_miles[T_STR] = i.start_miles
            report_shift.start_miles[T_FLOAT] = float(i.start_miles)
            report_shift.start_time = datetime.datetime.strptime(i.start_time, '%I:%M %p')
            report_shift.end_miles[T_STR] = i.end_miles
            report_shift.end_miles[T_FLOAT] = float(i.end_miles)
            report_shift.end_time = datetime.datetime.strptime(i.end_time, '%I:%M %p')
            if i.fuel:
                report_shift.fuel = float(i.fuel)

            report_day.shifts.append(report_shift)

        trips = Trip.objects.filter(date=day_date, status=Trip.STATUS_NORMAL, is_activity=False)
        for i in trips:
            if i.driver and not i.driver.is_logged:
                # skip non-logged drivers
                continue

            if i.start_miles == '' and i.start_time == '' and i.end_miles == '' and i.end_time == '':
                # skip empty trip
                continue

            if i.start_miles == '' or i.start_time == '' or i.end_miles == '' or i.end_time == '' or not i.driver or not i.vehicle:
                # skip incomplete shift
                if i.driver and i.vehicle:
                    report_errors.add(day_date, report_errors.TRIP_INCOMPLETE, error_trip=i)
                continue

            report_trip = ReportTrip()
            report_trip.trip = i

            for j in range(0, len(report_day.shifts)):
                if i.driver == report_day.shifts[j].shift.driver and i.vehicle == report_day.shifts[j].shift.vehicle:
                    report_trip.shift = j
                    break

            if report_trip.shift == None:
                for j in range(0, len(report_day.shifts)):
                    if i.vehicle == report_day.shifts[j].shift.vehicle:
                        report_trip.shift = j
                        break

            if report_trip.shift == None:
                # if i.vehicle.is_logged:
                #     report_errors.add(day_date, report_errors.TRIP_NO_SHIFT, error_trip=i)
                continue

            shift = report_day.shifts[report_trip.shift]
            report_trip.start_miles[T_STR] = shift.start_miles[T_STR][0:len(shift.start_miles[T_STR]) - len(i.start_miles)] + i.start_miles
            report_trip.start_miles[T_FLOAT] = float(report_trip.start_miles[T_STR])
            report_trip.start_time = datetime.datetime.strptime(i.start_time, '%I:%M %p')
            report_trip.end_miles[T_STR] = shift.start_miles[T_STR][0:len(shift.start_miles[T_STR]) - len(i.end_miles)] + i.end_miles
            report_trip.end_miles[T_FLOAT] = float(report_trip.end_miles[T_STR])
            report_trip.end_time = datetime.datetime.strptime(i.end_time, '%I:%M %p')

            report_trip.trip_type = i.trip_type
            report_trip.collected_cash = Money(i.collected_cash)
            report_trip.collected_check = Money(i.collected_check)

            report_day.trips.append(report_trip)

            if shift.start_trip == None or report_trip.start_miles[T_FLOAT] < report_day.trips[shift.start_trip].start_miles[T_FLOAT]:
                report_day.shifts[report_trip.shift].start_trip = len(report_day.trips) - 1;

            if shift.end_trip == None or report_trip.end_miles[T_FLOAT] > report_day.trips[shift.end_trip].end_miles[T_FLOAT]:
                report_day.shifts[report_trip.shift].end_trip = len(report_day.trips) - 1;

            # check for trip errors
            if report_trip.start_miles[T_FLOAT] < shift.start_miles[T_FLOAT] or report_trip.end_miles[T_FLOAT] > shift.end_miles[T_FLOAT]:
                report_errors.add(day_date, report_errors.TRIP_MILES_OOB, error_trip=i)
            if report_trip.start_time < shift.start_time or report_trip.end_time > shift.end_time:
                report_errors.add(day_date, report_errors.TRIP_TIME_OOB, error_trip=i)

            # add money trip
            if i.collected_cash > 0 or i.collected_check > 0:
                money_trips.append(report_trip)
                money_trips_summary.collected_cash += report_trip.collected_cash
                money_trips_summary.collected_check += report_trip.collected_check

            # add unique rider
            found_unique_rider = False
            for j in unique_riders.names:
                if j.name == i.name:
                    if j.elderly == None:
                        j.elderly = i.elderly
                    if j.ambulatory == None:
                        j.ambulatory = i.ambulatory

                    found_unique_rider = True
                    break
            if not found_unique_rider:
                if i.elderly == None or i.ambulatory == None:
                    # try to get info from Clients
                    clients = Client.objects.filter(name=i.name)
                    if len(clients) > 0:
                        elderly = i.elderly
                        ambulatory = i.ambulatory
                        if elderly == None:
                            elderly = clients[0].elderly
                        if ambulatory == None:
                            ambulatory = clients[0].ambulatory
                        unique_riders.names.append(UniqueRiderSummary.Rider(i.name, elderly, ambulatory))
                else:
                    unique_riders.names.append(UniqueRiderSummary.Rider(i.name, i.elderly, i.ambulatory))
                unique_riders.names = sorted(unique_riders.names)

        for i in range(0, len(report_day.shifts)):
            shift = report_day.shifts[i]
            if shift.start_trip == None or shift.end_trip == None:
                # print(shift.shift.vehicle)
                continue
            
            service_miles = shift.end_miles[T_FLOAT] - shift.start_miles[T_FLOAT]
            service_hours = (shift.end_time - shift.start_time).seconds / 60 / 60
            deadhead_miles = (report_day.trips[shift.start_trip].start_miles[T_FLOAT] - shift.start_miles[T_FLOAT]) + (shift.end_miles[T_FLOAT] - report_day.trips[shift.end_trip].end_miles[T_FLOAT])
            deadhead_hours = ((report_day.trips[shift.start_trip].start_time - shift.start_time).seconds + (shift.end_time - report_day.trips[shift.end_trip].end_time).seconds) / 60 / 60

            # per-vehicle log
            report_day.by_vehicle[shift.shift.vehicle].service_miles += service_miles
            report_day.by_vehicle[shift.shift.vehicle].service_hours += service_hours
            report_day.by_vehicle[shift.shift.vehicle].deadhead_miles += deadhead_miles
            report_day.by_vehicle[shift.shift.vehicle].deadhead_hours += deadhead_hours
            report_day.by_vehicle[shift.shift.vehicle].total_miles += service_miles + deadhead_miles
            report_day.by_vehicle[shift.shift.vehicle].total_hours += service_hours + deadhead_hours
            for trip in report_day.trips:
                if i != trip.shift:
                    continue
                report_day.by_vehicle[shift.shift.vehicle].pmt += trip.end_miles[T_FLOAT] - trip.start_miles[T_FLOAT]
                if trip.trip_type != None:
                    report_day.by_vehicle[shift.shift.vehicle].trip_types[trip.trip_type] += 1
                report_day.by_vehicle[shift.shift.vehicle].collected_cash += trip.collected_cash
                report_day.by_vehicle[shift.shift.vehicle].collected_check += trip.collected_check
            report_day.by_vehicle[shift.shift.vehicle].fuel += shift.fuel

            # per-driver log
            report_day.by_driver[shift.shift.driver].service_miles += service_miles
            report_day.by_driver[shift.shift.driver].service_hours += service_hours
            report_day.by_driver[shift.shift.driver].deadhead_miles += deadhead_miles
            report_day.by_driver[shift.shift.driver].deadhead_hours += deadhead_hours
            report_day.by_driver[shift.shift.driver].total_miles += service_miles + deadhead_miles
            report_day.by_driver[shift.shift.driver].total_hours += service_hours + deadhead_hours
            for trip in report_day.trips:
                if i != trip.shift:
                    continue
                report_day.by_driver[shift.shift.driver].pmt += trip.end_miles[T_FLOAT] - trip.start_miles[T_FLOAT]
                if trip.trip_type != None:
                    report_day.by_driver[shift.shift.driver].trip_types[trip.trip_type] += 1
                report_day.by_driver[shift.shift.driver].collected_cash += trip.collected_cash
                report_day.by_driver[shift.shift.driver].collected_check += trip.collected_check
            report_day.by_driver[shift.shift.driver].fuel += shift.fuel

        report_all.append(report_day)

    vehicle_reports = []
    for vehicle in Vehicle.objects.filter(is_logged=True):
        vehicle_report = ReportOutputVehicles()
        vehicle_report.vehicle = vehicle
        for report_day in report_all:
            if report_day.hasVehicleInShift(vehicle):
                vehicle_report.days.append({'date':report_day.date, 'data': report_day.by_vehicle[vehicle]})
                vehicle_report.totals += report_day.by_vehicle[vehicle]

        vehicle_reports.append(vehicle_report)

    all_vehicles = ReportSummary()
    for vehicle_report in vehicle_reports:
        all_vehicles += vehicle_report.totals

    driver_reports = []
    for driver in Driver.objects.filter(is_logged=True):
        driver_report = ReportOutputVehicles()
        driver_report.driver = driver
        for report_day in report_all:
            if report_day.hasDriverInShift(driver):
                driver_report.days.append({'date':report_day.date, 'data': report_day.by_driver[driver]})
                driver_report.totals += report_day.by_driver[driver]

        driver_reports.append(driver_report)

    for rider in unique_riders.names:
        if rider.elderly == None or rider.ambulatory == None:
            unique_riders.unknown += 1
        elif rider.elderly and rider.ambulatory:
            unique_riders.elderly_ambulatory += 1
        elif rider.elderly and not rider.ambulatory:
            unique_riders.elderly_nonambulatory += 1
        elif not rider.elderly and rider.ambulatory:
            unique_riders.nonelderly_ambulatory += 1
        elif not rider.elderly and not rider.ambulatory:
            unique_riders.nonelderly_nonambulatory += 1

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'month_prev': reverse('report', kwargs={'year':month_prev.year, 'month':month_prev.month}),
        'month_next': reverse('report', kwargs={'year':month_next.year, 'month':month_next.month}),
        'date_picker': date_picker,
        'vehicles': Vehicle.objects.filter(is_logged=True),
        'reports': report_all,
        'vehicle_reports': vehicle_reports,
        'all_vehicles': all_vehicles,
        'driver_reports': driver_reports,
        'unique_riders': unique_riders,
        'money_trips': money_trips,
        'money_trips_summary': money_trips_summary,
        'report_errors': report_errors,
    }
    return render(request, 'report/view.html', context)

def reportThisMonth(request):
    date = datetime.datetime.now().date()
    return report(request, date.year, date.month)

def reportLastMonth(request):
    date = (datetime.datetime.now().date()).replace(day=1) # first day of this month 
    date = date + datetime.timedelta(days=-1) # last day of the previous month
    return report(request, date.year, date.month)


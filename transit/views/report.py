import datetime
import tempfile

from django.http import HttpResponseRedirect
from django.http import FileResponse
from django.shortcuts import render
from django.urls import reverse

from transit.models import Driver, Vehicle, Trip, Shift, TripType, Client, ClientPayment
from transit.forms import DatePickerForm, DateRangePickerForm

from django.contrib.auth.decorators import permission_required

from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter

from transit.common.util import *

T_STR = 0
T_FLOAT = 1

class Report():
    class Money():
        def __init__(self, default_value=0):
            self.value = default_value
        def __add__(self, other):
            return Report.Money(self.value + other.value)
        def __sub__(self, other):
            return Report.Money(self.value - other.value)
        def __str__(self):
            return int_to_money_string(self.value, show_currency=True)
        def to_float(self):
            return float(self.value) / 100

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
            self.collected_cash = Report.Money(0)
            self.collected_check = Report.Money(0)

    class ReportDay():
        query_vehicles = Vehicle.objects.all()
        query_drivers = Driver.objects.filter(is_logged=True)

        def __init__(self):
            self.date = None
            self.shifts = []
            self.trips = []

            self.by_vehicle = {}
            for i in self.query_vehicles:
                self.by_vehicle[i] = Report.ReportSummary()

            self.by_driver = {}
            for i in self.query_drivers:
                self.by_driver[i] = Report.ReportSummary()

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
        query_triptypes = TripType.objects.all()

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
            self.collected_cash = Report.Money(0)
            self.collected_check = Report.Money(0)

            for i in self.query_triptypes:
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
            for i in self.query_triptypes:
                r.trip_types[i] += other.trip_types[i]
            r.collected_cash += other.collected_cash
            r.collected_check += other.collected_check
            return r

    class ReportOutputVehicles():
        def __init__(self):
            self.vehicle = None
            self.days = []
            self.totals = Report.ReportSummary()

    class ReportOutputDrivers():
        def __init__(self):
            self.driver = None
            self.days = []
            self.totals = Report.ReportSummary()

    class ReportErrors():
        SHIFT_INCOMPLETE = 0
        TRIP_INCOMPLETE = 1
        TRIP_NO_SHIFT = 2
        TRIP_MILES_OOB = 3
        TRIP_TIME_OOB = 4
        SHIFT_PARSE = 5
        TRIP_PARSE = 6
        SHIFT_MILES_LESS = 7
        SHIFT_TIME_LESS = 8
        TRIP_MILES_LESS = 9
        TRIP_TIME_LESS = 10

        def __init__(self):
            self.errors = []

        def add(self, date, error_code, error_shift=None, error_trip=None):
            self.errors.append({'date':date, 'error_code':error_code, 'error_shift': error_shift, 'error_trip': error_trip, 'error_msg': self.getErrorMsg(error_code, error_shift, error_trip)})

        def getErrorMsg(self, error_code, error_shift=None, error_trip=None):
            if (error_shift):
                shift_start_miles = error_shift.start_miles
                shift_end_miles = error_shift.end_miles
                shift_start_time = error_shift.start_time
                shift_end_time = error_shift.end_time
            else:
                shift_start_miles = shift_end_miles = shift_start_time = shift_end_time = ''

            if (error_trip):
                trip_start_miles = error_trip.start_miles
                trip_end_miles = error_trip.end_miles
                trip_start_time = error_trip.start_time
                trip_end_time = error_trip.end_time
            else:
                trip_start_miles = trip_end_miles = trip_start_time = trip_end_time = ''

            if error_code == self.SHIFT_INCOMPLETE:
                return 'Shift contains partial log data.'

            elif error_code == self.TRIP_INCOMPLETE:
                return 'Trip contains partial log data.'

            elif error_code == self.TRIP_NO_SHIFT:
                return 'Trip does not have a matching Shift.'

            elif error_code == self.TRIP_MILES_OOB:
                return 'Trip mileage ( ' + trip_start_miles + ' - ' + trip_end_miles + ' ) is not within Shift mileage ( ' + shift_start_miles + ' - ' + shift_end_miles + ' ).'

            elif error_code == self.TRIP_TIME_OOB:
                return 'Trip time ( ' + trip_start_time + ' - ' + trip_end_time + ' ) is not within Shift time ( ' + shift_start_time + ' - ' + shift_end_time + ' ).'

            elif error_code == self.SHIFT_PARSE:
                return 'Unable to parse Shift data.'

            elif error_code == self.TRIP_PARSE:
                return 'Unable to parse Trip data.'

            elif error_code == self.SHIFT_MILES_LESS:
                return 'Shift start mileage ( ' + shift_start_miles + ' ) is greater than Shift end mileage ( ' + shift_end_miles + ' ).'

            elif error_code == self.SHIFT_TIME_LESS:
                return 'Shift start time ( ' + shift_start_time + ' ) is later than Shift end time ( ' + shift_end_time + ' ).'

            elif error_code == self.TRIP_MILES_LESS:
                return 'Trip start mileage ( ' + trip_start_miles + ' ) is greater than Trip end mileage ( ' + trip_end_miles + ' ).'

            elif error_code == self.TRIP_TIME_LESS:
                return 'Trip start time ( ' + trip_start_time + ' ) is later than Trip end time ( ' + trip_end_time + ' ).'

            else:
                return 'Unknown error'

    class UniqueRiderSummary():
        class Rider():
            def __init__(self, name):
                self.name = name
                self.client_id = None
                self.trips = 1
                self.elderly = None
                self.ambulatory = None
                self.collected_cash = Report.Money(0)
                self.collected_check = Report.Money(0)
                self.paid_cash = Report.Money(0)
                self.paid_check = Report.Money(0)
                self.total_payments = Report.Money(0)
                self.total_fares = Report.Money(0)
                self.total_owed = Report.Money(0)
                self.staff = False
            def __lt__(self, other):
                return self.name < other.name

        def __init__(self):
            self.names = []
            self.elderly_ambulatory = 0
            self.elderly_nonambulatory = 0
            self.nonelderly_ambulatory = 0
            self.nonelderly_nonambulatory = 0
            self.unknown = 0
            self.total = 0
            self.staff = 0
            # fares & payments totals
            self.total_collected_cash = Report.Money(0)
            self.total_collected_check = Report.Money(0)
            self.total_paid_cash = Report.Money(0)
            self.total_paid_check = Report.Money(0)
            self.total_total_payments = Report.Money(0)
            self.total_total_fares = Report.Money(0)
            self.total_total_owed = Report.Money(0)

        def __contains__(self, item):
            for i in self.names:
                if i.name == item:
                    return True

    class ReportPayment():
        def __init__(self):
            self.date = None
            self.id = None
            self.client = None
            self.cash = Report.Money(0)
            self.check = Report.Money(0)

    def __init__(self):
        self.report_all = []
        self.vehicle_reports = []
        self.driver_reports = []
        self.all_vehicles = Report.ReportSummary()
        self.unique_riders = Report.UniqueRiderSummary()
        self.money_trips = []
        self.money_trips_summary = Report.ReportSummary()
        self.money_payments = []
        self.money_payments_summary = Report.ReportPayment()
        self.report_errors = Report.ReportErrors()

    def load(self, date_start, date_end, daily_log_shift=None):
        # refresh related fields
        # without this, select_related can fail if new entries are used
        all_drivers = Driver.objects.all()
        all_vehicles = Vehicle.objects.all()
        all_triptypes = TripType.objects.all()

        if date_start != date_end:
            daily_log_shift = None

        day_date = date_start
        while day_date < (date_end + datetime.timedelta(days=1)):
            # TODO is this an acceptable "fallback" value? Does it matter? This is a worst case anyway...
            fallback_time = datetime.datetime(year=day_date.year, month=day_date.month, day=day_date.day, hour=8, minute=0)

            report_day = Report.ReportDay()
            report_day.date = day_date

            shifts = Shift.objects.filter(date=day_date)
            shifts = shifts.select_related('driver').select_related('vehicle')
            for i in shifts:
                if i.start_miles == '' or i.start_time == '' or i.end_miles == '' or i.end_time == '' or not i.driver or not i.vehicle:
                    # skip incomplete shift
                    if i.start_miles != '' or i.start_time != '' or i.end_miles != '' or i.end_time != '':
                        self.report_errors.add(day_date, self.report_errors.SHIFT_INCOMPLETE, error_shift=i)
                    continue

                report_shift = Report.ReportShift()
                report_shift.shift = i

                report_shift.start_miles[T_STR] = i.start_miles
                try:
                    report_shift.start_miles[T_FLOAT] = float(i.start_miles)
                except:
                    report_shift.start_miles[T_FLOAT] = 0
                    self.report_errors.add(day_date, self.report_errors.SHIFT_PARSE, error_shift=i)


                try:
                    report_shift.start_time = datetime.datetime.strptime(i.start_time, '%I:%M %p')
                except:
                    report_shift.start_time = fallback_time
                    self.report_errors.add(day_date, self.report_errors.SHIFT_PARSE, error_shift=i)

                report_shift.end_miles[T_STR] = i.end_miles
                try:
                    report_shift.end_miles[T_FLOAT] = float(i.end_miles)
                except:
                    report_shift.end_miles[T_FLOAT] = 0
                    self.report_errors.add(day_date, self.report_errors.SHIFT_PARSE, error_shift=i)

                try:
                    report_shift.end_time = datetime.datetime.strptime(i.end_time, '%I:%M %p')
                except:
                    report_shift.end_time = fallback_time
                    self.report_errors.add(day_date, self.report_errors.SHIFT_PARSE, error_shift=i)

                if i.fuel:
                    try:
                        report_shift.fuel = float(i.fuel)
                    except:
                        report_shift.fuel = 0
                        self.report_errors.add(day_date, self.report_errors.SHIFT_PARSE, error_shift=i)

                if report_shift.start_miles[T_FLOAT] > report_shift.end_miles[T_FLOAT]:
                    self.report_errors.add(day_date, self.report_errors.SHIFT_MILES_LESS, error_shift=i)

                if report_shift.start_time > report_shift.end_time:
                    self.report_errors.add(day_date, self.report_errors.SHIFT_TIME_LESS, error_shift=i)

                report_day.shifts.append(report_shift)

            trips = Trip.objects.filter(date=day_date, status=Trip.STATUS_NORMAL, is_activity=False)
            trips = trips.select_related('driver').select_related('vehicle').select_related('trip_type')
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
                        self.report_errors.add(day_date, self.report_errors.TRIP_INCOMPLETE, error_trip=i)
                    continue

                report_trip = Report.ReportTrip()
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
                    #     self.report_errors.add(day_date, self.report_errors.TRIP_NO_SHIFT, error_trip=i)
                    continue

                shift = report_day.shifts[report_trip.shift]

                if len(i.start_miles) < len(shift.start_miles[T_STR]):
                    report_trip.start_miles[T_STR] = shift.start_miles[T_STR][0:len(shift.start_miles[T_STR]) - len(i.start_miles)] + i.start_miles
                else:
                    report_trip.start_miles[T_STR] = i.start_miles
                try:
                    report_trip.start_miles[T_FLOAT] = float(report_trip.start_miles[T_STR])
                except:
                    report_trip.start_miles[T_FLOAT] = 0
                    self.report_errors.add(day_date, self.report_errors.TRIP_PARSE, error_trip=i)

                try:
                    report_trip.start_time = datetime.datetime.strptime(i.start_time, '%I:%M %p')
                except:
                    report_trip.start_time = fallback_time
                    self.report_errors.add(day_date, self.report_errors.TRIP_PARSE, error_trip=i)

                if len(i.end_miles) < len(shift.start_miles[T_STR]):
                    report_trip.end_miles[T_STR] = shift.start_miles[T_STR][0:len(shift.start_miles[T_STR]) - len(i.end_miles)] + i.end_miles
                else:
                    report_trip.end_miles[T_STR] = i.end_miles
                try:
                    report_trip.end_miles[T_FLOAT] = float(report_trip.end_miles[T_STR])
                except:
                    report_trip.end_miles[T_FLOAT] = 0
                    self.report_errors.add(day_date, self.report_errors.TRIP_PARSE, error_trip=i)

                try:
                    report_trip.end_time = datetime.datetime.strptime(i.end_time, '%I:%M %p')
                except:
                    report_trip.end_time = fallback_time
                    self.report_errors.add(day_date, self.report_errors.TRIP_PARSE, error_trip=i)

                report_trip.trip_type = i.trip_type
                report_trip.collected_cash = Report.Money(i.collected_cash)
                report_trip.collected_check = Report.Money(i.collected_check)

                report_day.trips.append(report_trip)

                if shift.start_trip == None or report_trip.start_miles[T_FLOAT] < report_day.trips[shift.start_trip].start_miles[T_FLOAT]:
                    report_day.shifts[report_trip.shift].start_trip = len(report_day.trips) - 1;

                if shift.end_trip == None or report_trip.end_miles[T_FLOAT] > report_day.trips[shift.end_trip].end_miles[T_FLOAT]:
                    report_day.shifts[report_trip.shift].end_trip = len(report_day.trips) - 1;

                # check for trip errors
                if report_trip.start_miles[T_FLOAT] < shift.start_miles[T_FLOAT] or report_trip.end_miles[T_FLOAT] > shift.end_miles[T_FLOAT]:
                    self.report_errors.add(day_date, self.report_errors.TRIP_MILES_OOB, error_shift=shift.shift, error_trip=i)

                if report_trip.start_time < shift.start_time or report_trip.end_time > shift.end_time:
                    self.report_errors.add(day_date, self.report_errors.TRIP_TIME_OOB, error_shift=shift.shift, error_trip=i)

                if report_trip.start_miles[T_FLOAT] > report_trip.end_miles[T_FLOAT]:
                    self.report_errors.add(day_date, self.report_errors.TRIP_MILES_LESS, error_trip=i)

                if report_trip.start_time > report_trip.end_time:
                    self.report_errors.add(day_date, self.report_errors.TRIP_TIME_LESS, error_trip=i)


                if daily_log_shift == None or (daily_log_shift != None and daily_log_shift == shift.shift.id):
                    # add money trip
                    if i.collected_cash > 0 or i.collected_check > 0:
                        self.money_trips.append(report_trip)
                        self.money_trips_summary.collected_cash += report_trip.collected_cash
                        self.money_trips_summary.collected_check += report_trip.collected_check

                    # add unique rider
                    found_unique_rider = False
                    for j in self.unique_riders.names:
                        if j.name == i.name:
                            if j.elderly == None:
                                j.elderly = i.elderly
                            if j.ambulatory == None:
                                j.ambulatory = i.ambulatory

                            found_unique_rider = True
                            j.trips += 1

                            j.total_fares += Report.Money(i.fare)
                            j.collected_cash += Report.Money(i.collected_cash)
                            j.collected_check += Report.Money(i.collected_check)

                            break
                    if not found_unique_rider:
                        rider = Report.UniqueRiderSummary.Rider(i.name)
                        rider.elderly = i.elderly
                        rider.ambulatory = i.ambulatory

                        clients = Client.objects.filter(name=i.name)
                        if len(clients) > 0:
                            rider.client_id = clients[0].id
                            rider.staff = clients[0].staff

                        if i.elderly == None or i.ambulatory == None:
                            # try to get info from Clients
                            if len(clients) > 0:
                                if rider.elderly == None:
                                    rider.elderly = clients[0].elderly
                                if rider.ambulatory == None:
                                    rider.ambulatory = clients[0].ambulatory

                        rider.total_fares += Report.Money(i.fare)
                        rider.collected_cash += Report.Money(i.collected_cash)
                        rider.collected_check += Report.Money(i.collected_check)

                        self.unique_riders.names.append(rider)
                        self.unique_riders.names = sorted(self.unique_riders.names)

            # handle payments from Clients that didn't ride (so far)
            for i in ClientPayment.objects.filter(date_paid=day_date):
                found_unique_rider = False
                for j in self.unique_riders.names:
                    if j.name == i.parent.name:
                        found_unique_rider = True

                        j.paid_cash += Report.Money(i.cash)
                        j.paid_check += Report.Money(i.check)

                        break
                if not found_unique_rider:
                    rider = Report.UniqueRiderSummary.Rider(i.parent.name)
                    rider.trips = 0
                    rider.elderly = i.parent.elderly
                    rider.ambulatory = i.parent.ambulatory
                    rider.client_id = i.parent.id

                    rider.paid_cash += Report.Money(i.cash)
                    rider.paid_check += Report.Money(i.check)

                    self.unique_riders.names.append(rider)
                    self.unique_riders.names = sorted(self.unique_riders.names)

                # create a summary of only non-driver payments
                payment = Report.ReportPayment()
                payment.date = i.date_paid
                payment.id = i.id
                payment.client = i.parent
                payment.cash = Report.Money(i.cash)
                payment.check = Report.Money(i.check)
                self.money_payments.append(payment)
                self.money_payments_summary.cash += payment.cash
                self.money_payments_summary.check += payment.check

            for i in range(0, len(report_day.shifts)):
                shift = report_day.shifts[i]

                # create dummy trip when a shift has no trips
                if shift.start_trip == None and shift.end_trip == None:
                    rt = Report.ReportTrip()
                    rt.shift = i
                    rt.start_miles[T_STR] = shift.start_miles[T_STR]
                    rt.start_miles[T_FLOAT] = shift.start_miles[T_FLOAT]
                    rt.end_miles[T_STR] = shift.end_miles[T_STR]
                    rt.end_miles[T_FLOAT] = shift.end_miles[T_FLOAT]
                    rt.start_time = shift.start_time
                    rt.end_time = shift.end_time
                    report_day.trips.append(rt)
                    shift.start_trip = len(report_day.trips) - 1
                    shift.end_trip = shift.start_trip
                elif shift.start_trip == None or shift.end_trip == None:
                    # TODO create partial dummy trips?
                    continue

                if daily_log_shift != None and daily_log_shift != shift.shift.id:
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

            self.report_all.append(report_day)

            day_date += datetime.timedelta(days=1)

        self.vehicle_reports = []
        for vehicle in Vehicle.objects.filter(is_logged=True):
            vehicle_report = Report.ReportOutputVehicles()
            vehicle_report.vehicle = vehicle
            for report_day in self.report_all:
                if report_day.hasVehicleInShift(vehicle):
                    vehicle_report.days.append({'date':report_day.date, 'data': report_day.by_vehicle[vehicle]})
                    vehicle_report.totals += report_day.by_vehicle[vehicle]

            self.vehicle_reports.append(vehicle_report)

        self.all_vehicles = Report.ReportSummary()
        for vehicle_report in self.vehicle_reports:
            self.all_vehicles += vehicle_report.totals

        self.driver_reports = []
        for driver in Driver.objects.filter(is_logged=True):
            driver_report = Report.ReportOutputVehicles()
            driver_report.driver = driver
            for report_day in self.report_all:
                if report_day.hasDriverInShift(driver):
                    driver_report.days.append({'date':report_day.date, 'data': report_day.by_driver[driver]})
                    driver_report.totals += report_day.by_driver[driver]

            self.driver_reports.append(driver_report)

        for rider in self.unique_riders.names:
            # total elderly/ambulatory counts
            if rider.trips > 0:
                if rider.staff:
                    self.unique_riders.staff += 1
                else:
                    self.unique_riders.total += 1
                    if rider.elderly == None or rider.ambulatory == None:
                        self.unique_riders.unknown += 1
                    elif rider.elderly and rider.ambulatory:
                        self.unique_riders.elderly_ambulatory += 1
                    elif rider.elderly and not rider.ambulatory:
                        self.unique_riders.elderly_nonambulatory += 1
                    elif not rider.elderly and rider.ambulatory:
                        self.unique_riders.nonelderly_ambulatory += 1
                    elif not rider.elderly and not rider.ambulatory:
                        self.unique_riders.nonelderly_nonambulatory += 1

            # calculate total owed money
            rider.total_payments = rider.collected_cash + rider.collected_check + rider.paid_cash + rider.paid_check
            if rider.total_payments.value != 0 or rider.total_fares.value != 0:
                rider.total_owed = rider.total_fares - rider.total_payments
                if (rider.total_owed.value < 0):
                    rider.total_owed.value = 0

            self.unique_riders.total_collected_cash += rider.collected_cash
            self.unique_riders.total_collected_check += rider.collected_check
            self.unique_riders.total_paid_cash += rider.paid_cash
            self.unique_riders.total_paid_check += rider.paid_check
            self.unique_riders.total_total_payments += rider.total_payments
            self.unique_riders.total_total_fares += rider.total_fares
            self.unique_riders.total_total_owed += rider.total_owed

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportMonth(request, year, month):
    date_start = datetime.date(year, month, 1)
    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

    return HttpResponseRedirect(reverse('report', kwargs={'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))

@permission_required(['transit.view_trip', 'transit.view_shift'])
def report(request, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)

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
                return HttpResponseRedirect(reverse('report', kwargs={'start_year':new_start.year, 'start_month':new_start.month, 'start_day':new_start.day, 'end_year':new_end.year, 'end_month':new_end.month, 'end_day':new_end.day}))
        else:
            if date_picker.is_valid():
                date_picker_date = date_picker.cleaned_data['date']
                return HttpResponseRedirect(reverse('report-month', kwargs={'year':date_picker_date.year, 'month':date_picker_date.month}))
    else:
        date_picker = DatePickerForm(initial={'date':date_start})
        date_range_picker = DateRangePickerForm(initial={'date_start':date_start, 'date_end':date_end})

    month_prev = date_start + datetime.timedelta(days=-1)
    month_prev.replace(day=1)
    month_next = date_end + datetime.timedelta(days=1)

    report = Report()
    report.load(date_start, date_end)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'month_prev': reverse('report-month', kwargs={'year':month_prev.year, 'month':month_prev.month}),
        'month_next': reverse('report-month', kwargs={'year':month_next.year, 'month':month_next.month}),
        'date_picker': date_picker,
        'date_range_picker': date_range_picker,
        'vehicles': Vehicle.objects.filter(is_logged=True),
        'reports': report.report_all,
        'vehicle_reports': report.vehicle_reports,
        'all_vehicles': report.all_vehicles,
        'driver_reports': report.driver_reports,
        'unique_riders': report.unique_riders,
        'money_trips': report.money_trips,
        'money_trips_summary': report.money_trips_summary,
        'money_payments': report.money_payments,
        'money_payments_summary': report.money_payments_summary,
        'report_errors': report.report_errors,
    }
    return render(request, 'report/view.html', context)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportPrint(request, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)

    if date_start > date_end:
        swap_date = date_start
        date_start = date_end
        date_end = swap_date

    report = Report()
    report.load(date_start, date_end)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'vehicles': Vehicle.objects.filter(is_logged=True),
        'reports': report.report_all,
        'vehicle_reports': report.vehicle_reports,
        'all_vehicles': report.all_vehicles,
        'driver_reports': report.driver_reports,
        'unique_riders': report.unique_riders,
        'money_trips': report.money_trips,
        'money_trips_summary': report.money_trips_summary,
        'money_payments': report.money_payments,
        'money_payments_summary': report.money_payments_summary,
        'report_errors': report.report_errors,
    }
    return render(request, 'report/print.html', context)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportThisMonth(request):
    date = datetime.datetime.now().date()
    return reportMonth(request, date.year, date.month)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportLastMonth(request):
    date = (datetime.datetime.now().date()).replace(day=1) # first day of this month 
    date = date + datetime.timedelta(days=-1) # last day of the previous month
    return reportMonth(request, date.year, date.month)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportXLSX(request, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)

    if date_start > date_end:
        swap_date = date_start
        date_start = date_end
        date_end = swap_date

    report = Report()
    report.load(date_start, date_end)

    temp_file = tempfile.NamedTemporaryFile()

    wb = Workbook()

    style_font_normal = Font(name='Arial', size=10)
    style_border_normal_side = Side(border_style='thin', color='FF000000')
    style_border_normal = Border(left=style_border_normal_side, right=style_border_normal_side, top=style_border_normal_side, bottom=style_border_normal_side)
    style_colwidth_normal = 13

    style_font_header = Font(name='Arial', size=10, bold=True)
    style_alignment_header = Alignment(horizontal='center', vertical='center', wrap_text=True)
    style_fill_header = PatternFill(fill_type='solid', fgColor='DFE0E1')
    style_rowheight_header = 25

    style_font_total = Font(name='Arial', size=10, bold=True, color='FFFFFFFF')
    style_fill_total = PatternFill(fill_type='solid', fgColor='27A343')

    #####
    #### All Vehicle Totals
    #####
    ws_vehicle_total = wb.active
    ws_vehicle_total.title = 'Totals for All Vehicles'

    row_header = 1
    row_total = 2

    ws_vehicle_total.cell(row_header, 2, 'Service Miles')
    ws_vehicle_total.cell(row_header, 3, 'Service Hours')
    ws_vehicle_total.cell(row_header, 4, 'Deadhead Miles')
    ws_vehicle_total.cell(row_header, 5, 'Deadhead Hours')
    ws_vehicle_total.cell(row_header, 6, 'Passenger Miles (PMT)')
    ws_vehicle_total.cell(row_header, 7, 'Fuel')

    ws_vehicle_total.cell(row_total, 1, 'TOTAL')
    ws_vehicle_total.cell(row_total, 2, report.all_vehicles.service_miles)
    ws_vehicle_total.cell(row_total, 3, report.all_vehicles.service_hours)
    ws_vehicle_total.cell(row_total, 4, report.all_vehicles.deadhead_miles)
    ws_vehicle_total.cell(row_total, 5, report.all_vehicles.deadhead_hours)
    ws_vehicle_total.cell(row_total, 6, report.all_vehicles.pmt)
    ws_vehicle_total.cell(row_total, 7, report.all_vehicles.fuel)

    triptype_col=8
    for i in TripType.objects.all():
        ws_vehicle_total.cell(row_header, triptype_col, 'Trip Type: ' + str(i))
        ws_vehicle_total.cell(row_total, triptype_col, report.all_vehicles.trip_types[i])
        triptype_col += 1

    ws_vehicle_total.cell(row_header, triptype_col, 'Cash Collected')
    ws_vehicle_total.cell(row_header, triptype_col+1, 'Check Collected')
    ws_vehicle_total.cell(row_total, triptype_col, report.all_vehicles.collected_cash.to_float())
    ws_vehicle_total.cell(row_total, triptype_col+1, report.all_vehicles.collected_check.to_float())

    # number formats
    ws_vehicle_total.cell(row_total, 2).number_format = '0.0'
    ws_vehicle_total.cell(row_total, 3).number_format = '0.00'
    ws_vehicle_total.cell(row_total, 4).number_format = '0.0'
    ws_vehicle_total.cell(row_total, 5).number_format = '0.00'
    ws_vehicle_total.cell(row_total, 6).number_format = '0.0'
    ws_vehicle_total.cell(row_total, 7).number_format = '0.0'
    ws_vehicle_total.cell(row_total, triptype_col).number_format = '$0.00'
    ws_vehicle_total.cell(row_total, triptype_col+1).number_format = '$0.00'

    # apply styles
    ws_vehicle_total.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, triptype_col+2):
        ws_vehicle_total.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_total+1):
            ws_vehicle_total.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_vehicle_total.cell(j, i).font = style_font_header
                ws_vehicle_total.cell(j, i).alignment = style_alignment_header
                ws_vehicle_total.cell(j, i).fill = style_fill_header
            elif j == row_total:
                ws_vehicle_total.cell(j, i).font = style_font_total
                ws_vehicle_total.cell(j, i).fill = style_fill_total
            else:
                ws_vehicle_total.cell(j, i).font = style_font_normal

    #####
    #### Per-Vehicle Reports
    #####
    for vr in report.vehicle_reports:
        ws_vehicle = wb.create_sheet('Vehicle - ' + str(vr.vehicle))
        row_header = 1
        row_total = 1 + len(vr.days) + 1
        ws_vehicle.cell(row_header, 2, 'Service Miles')
        ws_vehicle.cell(row_header, 3, 'Service Hours')
        ws_vehicle.cell(row_header, 4, 'Deadhead Miles')
        ws_vehicle.cell(row_header, 5, 'Deadhead Hours')
        ws_vehicle.cell(row_header, 6, 'Passenger Miles (PMT)')
        ws_vehicle.cell(row_header, 7, 'Fuel')

        for day in range(0, len(vr.days)):
            day_row = row_header + day + 1
            ws_vehicle.cell(day_row, 1, vr.days[day]['date'])
            ws_vehicle.cell(day_row, 2, vr.days[day]['data'].service_miles)
            ws_vehicle.cell(day_row, 3, vr.days[day]['data'].service_hours)
            ws_vehicle.cell(day_row, 4, vr.days[day]['data'].deadhead_miles)
            ws_vehicle.cell(day_row, 5, vr.days[day]['data'].deadhead_hours)
            ws_vehicle.cell(day_row, 6, vr.days[day]['data'].pmt)
            ws_vehicle.cell(day_row, 7, vr.days[day]['data'].fuel)

            triptype_col=8
            for i in TripType.objects.all():
                ws_vehicle.cell(row_header, triptype_col, 'Trip Type: ' + str(i))
                ws_vehicle.cell(day_row, triptype_col, vr.days[day]['data'].trip_types[i])
                triptype_col += 1

            ws_vehicle.cell(row_header, triptype_col, 'Cash Collected')
            ws_vehicle.cell(row_header, triptype_col+1, 'Check Collected')
            ws_vehicle.cell(day_row, triptype_col, vr.days[day]['data'].collected_cash.to_float())
            ws_vehicle.cell(day_row, triptype_col+1, vr.days[day]['data'].collected_check.to_float())

        ws_vehicle.cell(row_total, 1, 'TOTAL')
        ws_vehicle.cell(row_total, 2, vr.totals.service_miles)
        ws_vehicle.cell(row_total, 3, vr.totals.service_hours)
        ws_vehicle.cell(row_total, 4, vr.totals.deadhead_miles)
        ws_vehicle.cell(row_total, 5, vr.totals.deadhead_hours)
        ws_vehicle.cell(row_total, 6, vr.totals.pmt)
        ws_vehicle.cell(row_total, 7, vr.totals.fuel)

        triptype_col=8
        for i in TripType.objects.all():
            ws_vehicle.cell(row_header, triptype_col, 'Trip Type: ' + str(i))
            ws_vehicle.cell(row_total, triptype_col, vr.totals.trip_types[i])
            triptype_col += 1

        ws_vehicle.cell(row_header, triptype_col, 'Cash Collected')
        ws_vehicle.cell(row_header, triptype_col+1, 'Check Collected')
        ws_vehicle.cell(row_total, triptype_col, vr.totals.collected_cash.to_float())
        ws_vehicle.cell(row_total, triptype_col+1, vr.totals.collected_check.to_float())

        # number formats
        for i in range(row_header + 1, row_total + 1):
            if i < row_total:
                ws_vehicle.cell(i, 1).number_format = 'MMM DD, YYYY'
            ws_vehicle.cell(i, 2).number_format = '0.0'
            ws_vehicle.cell(i, 3).number_format = '0.00'
            ws_vehicle.cell(i, 4).number_format = '0.0'
            ws_vehicle.cell(i, 5).number_format = '0.00'
            ws_vehicle.cell(i, 6).number_format = '0.0'
            ws_vehicle.cell(i, 7).number_format = '0.0'
            ws_vehicle.cell(i, triptype_col).number_format = '$0.00'
            ws_vehicle.cell(i, triptype_col+1).number_format = '$0.00'

        # apply styles
        ws_vehicle.row_dimensions[row_header].height = style_rowheight_header
        for i in range(1, triptype_col+2):
            ws_vehicle.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
            for j in range(row_header, row_total+1):
                ws_vehicle.cell(j, i).border = style_border_normal
                if j == row_header:
                    ws_vehicle.cell(j, i).font = style_font_header
                    ws_vehicle.cell(j, i).alignment = style_alignment_header
                    ws_vehicle.cell(j, i).fill = style_fill_header
                elif j == row_total:
                    ws_vehicle.cell(j, i).font = style_font_total
                    ws_vehicle.cell(j, i).fill = style_fill_total
                else:
                    ws_vehicle.cell(j, i).font = style_font_normal

    #####
    #### Unique/Ambulatory rider summary
    #####
    ws_riders = wb.create_sheet('Rider Summary')
    row_header = 1
    row_total = 2
    ws_riders.cell(row_header, 2, 'Elderly Ambulatory')
    ws_riders.cell(row_header, 3, 'Elderly Non-Ambulatory')
    ws_riders.cell(row_header, 4, 'Non-Elderly Ambulatory')
    ws_riders.cell(row_header, 5, 'Non-Elderly Non-Ambulatory')
    ws_riders.cell(row_header, 6, 'Unknown')
    ws_riders.cell(row_header, 7, 'Staff')

    ws_riders.cell(row_total, 1, 'TOTAL')
    ws_riders.cell(row_total, 2, report.unique_riders.elderly_ambulatory)
    ws_riders.cell(row_total, 3, report.unique_riders.elderly_nonambulatory)
    ws_riders.cell(row_total, 4, report.unique_riders.nonelderly_ambulatory)
    ws_riders.cell(row_total, 5, report.unique_riders.nonelderly_nonambulatory)
    ws_riders.cell(row_total, 6, report.unique_riders.unknown)
    ws_riders.cell(row_total, 7, report.unique_riders.staff)

    row_total_riders = 0
    for i in report.unique_riders.names:
        if i.trips > 0:
            row_total_riders += 1
    row_total_riders += 1

    row_header_riders = 4
    for i in range(row_header_riders, row_header_riders + row_total_riders):
        ws_riders.merge_cells(start_row=i, start_column=1, end_row=i, end_column=2)
        if i > row_header_riders:
            ws_riders.cell(i, 3).number_format = 'BOOLEAN'
            ws_riders.cell(i, 4).number_format = 'BOOLEAN'

    ws_riders.cell(row_header_riders, 1, 'Name')
    ws_riders.cell(row_header_riders, 3, 'Elderly')
    ws_riders.cell(row_header_riders, 4, 'Ambulatory')
    ws_riders.cell(row_header_riders, 5, 'Total Trips')

    row = 0
    for i in report.unique_riders.names:
        if i.trips > 0:
            ws_riders.cell(row_header_riders + row + 1, 1, i.name)
            ws_riders.cell(row_header_riders + row + 1, 3, i.elderly)
            ws_riders.cell(row_header_riders + row + 1, 4, i.ambulatory)
            ws_riders.cell(row_header_riders + row + 1, 5, i.trips)
            row += 1

    # apply styles
    ws_riders.row_dimensions[row_header].height = style_rowheight_header
    ws_riders.row_dimensions[row_header_riders].height = style_rowheight_header
    for i in range(1, 8):
        ws_riders.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_total+1):
            ws_riders.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_riders.cell(j, i).font = style_font_header
                ws_riders.cell(j, i).alignment = style_alignment_header
                ws_riders.cell(j, i).fill = style_fill_header
            elif j == row_total:
                ws_riders.cell(j, i).font = style_font_total
                ws_riders.cell(j, i).fill = style_fill_total
            else:
                ws_riders.cell(j, i).font = style_font_normal
    for i in range(1, 6):
        for j in range(row_header_riders, row_header_riders + row_total_riders):
            ws_riders.cell(j, i).border = style_border_normal
            if j == row_header_riders:
                ws_riders.cell(j, i).font = style_font_header
                ws_riders.cell(j, i).alignment = style_alignment_header
                ws_riders.cell(j, i).fill = style_fill_header
            else:
                ws_riders.cell(j, i).font = style_font_normal

    #####
    #### Fares & Payments
    #####
    ws_fares = wb.create_sheet('Fares & Payments')
    row_header = 1

    row_total = 0
    for i in report.unique_riders.names:
        if i.total_payments.value > 0 or i.total_fares.value > 0:
            row_total += 1
    row_total += 2

    ws_fares.cell(row_header, 1, 'Name')
    ws_fares.cell(row_header, 2, 'Cash (driver collected)')
    ws_fares.cell(row_header, 3, 'Check (driver collected)')
    ws_fares.cell(row_header, 4, 'Cash (not driver collected)')
    ws_fares.cell(row_header, 5, 'Check (not driver collected)')
    ws_fares.cell(row_header, 6, 'Total Payments')
    ws_fares.cell(row_header, 7, 'Total Fares')
    ws_fares.cell(row_header, 8, 'Total Owed')

    ws_fares.cell(row_total, 1, 'TOTAL')
    ws_fares.cell(row_total, 2, report.unique_riders.total_collected_cash.to_float())
    ws_fares.cell(row_total, 3, report.unique_riders.total_collected_check.to_float())
    ws_fares.cell(row_total, 4, report.unique_riders.total_paid_cash.to_float())
    ws_fares.cell(row_total, 5, report.unique_riders.total_paid_check.to_float())
    ws_fares.cell(row_total, 6, report.unique_riders.total_total_payments.to_float())
    ws_fares.cell(row_total, 7, report.unique_riders.total_total_fares.to_float())
    ws_fares.cell(row_total, 8, report.unique_riders.total_total_owed.to_float())

    row = 0
    for i in report.unique_riders.names:
        if i.total_payments.value <= 0 and i.total_fares.value <= 0:
            continue
        ws_fares.cell(row + row_header + 1, 1, i.name)
        ws_fares.cell(row + row_header + 1, 2, i.collected_cash.to_float())
        ws_fares.cell(row + row_header + 1, 3, i.collected_check.to_float())
        ws_fares.cell(row + row_header + 1, 4, i.paid_cash.to_float())
        ws_fares.cell(row + row_header + 1, 5, i.paid_check.to_float())
        ws_fares.cell(row + row_header + 1, 6, i.total_payments.to_float())
        ws_fares.cell(row + row_header + 1, 7, i.total_fares.to_float())
        ws_fares.cell(row + row_header + 1, 8, i.total_owed.to_float())
        row += 1

    # number formats
    for i in range(row_header + 1, row_total + 1):
        for j in range(2,9):
            ws_fares.cell(i, j).number_format = '$0.00'

    # apply styles
    ws_fares.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, 9):
        if i == 1:
            ws_fares.column_dimensions[get_column_letter(i)].width = style_colwidth_normal * 2
        else:
            ws_fares.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_total+1):
            ws_fares.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_fares.cell(j, i).font = style_font_header
                ws_fares.cell(j, i).alignment = style_alignment_header
                ws_fares.cell(j, i).fill = style_fill_header
            elif j == row_total:
                ws_fares.cell(j, i).font = style_font_total
                ws_fares.cell(j, i).fill = style_fill_total
            else:
                ws_fares.cell(j, i).font = style_font_normal

    #####
    #### Money Collected by the Drivers
    #####
    ws_money = wb.create_sheet('Money Collected by the Drivers')
    row_header = 1
    row_total = len(report.money_trips) + 2

    ws_money.cell(row_header, 1, 'Date')
    ws_money.cell(row_header, 2, 'Name')
    ws_money.cell(row_header, 3, 'Cash')
    ws_money.cell(row_header, 4, 'Check')

    ws_money.cell(row_total, 1, 'TOTAL')
    ws_money.cell(row_total, 3, report.money_trips_summary.collected_cash.to_float())
    ws_money.cell(row_total, 4, report.money_trips_summary.collected_check.to_float())

    for i in range(0, len(report.money_trips)):
        ws_money.cell(i + row_header + 1, 1, report.money_trips[i].trip.date)
        ws_money.cell(i + row_header + 1, 2, report.money_trips[i].trip.name)
        ws_money.cell(i + row_header + 1, 3, report.money_trips[i].collected_cash.to_float())
        ws_money.cell(i + row_header + 1, 4, report.money_trips[i].collected_check.to_float())

    # number formats
    for i in range(row_header + 1, row_total + 1):
        if i < row_total:
            ws_money.cell(i, 1).number_format = 'MMM DD, YYYY'
        ws_money.cell(i, 3).number_format = '$0.00'
        ws_money.cell(i, 4).number_format = '$0.00'

    # apply styles
    ws_money.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, 5):
        if i == 2:
            ws_money.column_dimensions[get_column_letter(i)].width = style_colwidth_normal * 2
        else:
            ws_money.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_total+1):
            ws_money.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_money.cell(j, i).font = style_font_header
                ws_money.cell(j, i).alignment = style_alignment_header
                ws_money.cell(j, i).fill = style_fill_header
            elif j == row_total:
                ws_money.cell(j, i).font = style_font_total
                ws_money.cell(j, i).fill = style_fill_total
            else:
                ws_money.cell(j, i).font = style_font_normal

    #####
    #### Money Not Collected by the Drivers
    #####
    ws_payments = wb.create_sheet('Money Not Collected by the Drivers')
    row_header = 1
    row_total = len(report.money_payments) + 2

    ws_payments.cell(row_header, 1, 'Date')
    ws_payments.cell(row_header, 2, 'Name')
    ws_payments.cell(row_header, 3, 'Cash')
    ws_payments.cell(row_header, 4, 'Check')

    ws_payments.cell(row_total, 1, 'TOTAL')
    ws_payments.cell(row_total, 3, report.money_payments_summary.cash.to_float())
    ws_payments.cell(row_total, 4, report.money_payments_summary.check.to_float())

    for i in range(0, len(report.money_payments)):
        ws_payments.cell(i + row_header + 1, 1, report.money_payments[i].date)
        ws_payments.cell(i + row_header + 1, 2, report.money_payments[i].client.name)
        ws_payments.cell(i + row_header + 1, 3, report.money_payments[i].cash.to_float())
        ws_payments.cell(i + row_header + 1, 4, report.money_payments[i].check.to_float())

    # number formats
    for i in range(row_header + 1, row_total + 1):
        if i < row_total:
            ws_payments.cell(i, 1).number_format = 'MMM DD, YYYY'
        ws_payments.cell(i, 3).number_format = '$0.00'
        ws_payments.cell(i, 4).number_format = '$0.00'

    # apply styles
    ws_payments.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, 5):
        if i == 2:
            ws_payments.column_dimensions[get_column_letter(i)].width = style_colwidth_normal * 2
        else:
            ws_payments.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_total+1):
            ws_payments.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_payments.cell(j, i).font = style_font_header
                ws_payments.cell(j, i).alignment = style_alignment_header
                ws_payments.cell(j, i).fill = style_fill_header
            elif j == row_total:
                ws_payments.cell(j, i).font = style_font_total
                ws_payments.cell(j, i).fill = style_fill_total
            else:
                ws_payments.cell(j, i).font = style_font_normal

    #####
    #### Per-Driver Summary
    #####
    ws_drivers = wb.create_sheet('Per-Driver Summary')
    row_header = 1

    ws_drivers.cell(row_header, 1, 'Driver')
    ws_drivers.cell(row_header, 2, 'Service Miles')
    ws_drivers.cell(row_header, 3, 'Service Hours')
    ws_drivers.cell(row_header, 4, 'Deadhead Miles')
    ws_drivers.cell(row_header, 5, 'Deadhead Hours')
    ws_drivers.cell(row_header, 6, 'Total Miles')
    ws_drivers.cell(row_header, 7, 'Total Hours')

    for i in range(0, len(report.driver_reports)):
        ws_drivers.cell(row_header + i + 1, 1, str(report.driver_reports[i].driver))
        ws_drivers.cell(row_header + i + 1, 2, report.driver_reports[i].totals.service_miles)
        ws_drivers.cell(row_header + i + 1, 3, report.driver_reports[i].totals.service_hours)
        ws_drivers.cell(row_header + i + 1, 4, report.driver_reports[i].totals.deadhead_miles)
        ws_drivers.cell(row_header + i + 1, 5, report.driver_reports[i].totals.deadhead_hours)
        ws_drivers.cell(row_header + i + 1, 6, report.driver_reports[i].totals.total_miles)
        ws_drivers.cell(row_header + i + 1, 7, report.driver_reports[i].totals.total_hours)

    # number formats
    for i in range(row_header + 1, row_header + len(report.driver_reports) + 1):
        ws_drivers.cell(i, 2).number_format = '0.0'
        ws_drivers.cell(i, 3).number_format = '0.00'
        ws_drivers.cell(i, 4).number_format = '0.0'
        ws_drivers.cell(i, 5).number_format = '0.00'
        ws_drivers.cell(i, 6).number_format = '0.0'
        ws_drivers.cell(i, 7).number_format = '0.00'

    # apply styles
    ws_drivers.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, 8):
        ws_drivers.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_header + len(report.driver_reports) + 1):
            ws_drivers.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_drivers.cell(j, i).font = style_font_header
                ws_drivers.cell(j, i).alignment = style_alignment_header
                ws_drivers.cell(j, i).fill = style_fill_header
            else:
                ws_drivers.cell(j, i).font = style_font_normal
                style_fill_driver = PatternFill(fill_type='solid', fgColor=report.driver_reports[j - row_header - 1].driver.get_color())
                ws_drivers.cell(j, i).fill = style_fill_driver

    wb.save(filename=temp_file.name)

    return FileResponse(open(temp_file.name, 'rb'), filename='Transit_Report_' + date_start.strftime('%Y-%m-%d') + '_to_' + date_end.strftime('%Y-%m-%d') + '.xlsx', as_attachment=True)

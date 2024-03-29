# Copyright © 2019-2023 Justin Jacobs
#
# This file is part of the Transit Log System.
#
# The Transit Log System is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# The Transit Log System is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# The Transit Log System.  If not, see http://www.gnu.org/licenses/

import datetime
import tempfile

from django.http import HttpResponseRedirect
from django.http import FileResponse
from django.shortcuts import render
from django.urls import reverse
from time import perf_counter

from transit.models import Driver, Vehicle, Trip, Shift, TripType, Client, ClientPayment, Tag, Destination
from transit.forms import DatePickerForm, DateRangePickerForm

from django.contrib.auth.decorators import permission_required

from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter

from transit.common.util import *

class Report():
    service_mile_warning_threshold = 1000

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

    class ValueString():
        def __init__(self):
            self.value = 0
            self.string = ''
            self.is_string_valid = True
        def __lt__(self, other):
            return self.value < other.value
        def __gt__(self, other):
            return self.value > other.value
        def __le__(self, other):
            return self.value <= other.value
        def __ge__(self, other):
            return self.value >= other.value
        def __eq__(self, other):
            return self.value == other.value
        def __ne__(self, other):
            return self.value != other.value
        def empty(self):
            return self.string == ''

    class Mileage(ValueString):
        def __add__(self, other):
            r = Report.Mileage()
            r.value = self.value + other.value
            r.is_string_valid = False
            return r
        def __sub__(self, other):
            r = Report.Mileage()
            r.value = self.value - other.value
            r.is_string_valid = False
            return r
        def __str__(self):
            if not self.is_string_valid:
                self.string = f"{self.value:.1f}"
                self.is_string_valid = True
            return self.string
        def setFromString(self, string):
            try:
                self.value = float(string)
            except:
                self.value = 0
                self.string = ''
                self.is_string_valid = True
                return 1
            self.string = string
            self.is_string_valid = True
            return 0
        def mergeStrings(self, base, suffix):
            merged = ''
            if len(suffix) < len(base):
                merged = base[0:len(base) - len(suffix)] + suffix
            else:
                merged = suffix
            if self.setFromString(merged) != 0:
                return 1
            else:
                return 0

    class Time(ValueString):
        # TODO is this an acceptable "fallback" value? Does it matter? This is a worst case anyway...
        fallback_value = datetime.datetime(year=1900, month=1, day=1, hour=8, minute=0)
        fallback_string = fallback_value.strftime('%I:%M %p')

        def __str__(self):
            if not self.is_string_valid:
                self.is_string_valid = True
                if self.value != 0:
                    self.string = self.value.strftime('%I:%M %p')
            return self.string
        def setFromString(self, string, use_fallback=True):
            try:
                self.value = datetime.datetime.strptime(string, '%I:%M %p')
            except:
                if use_fallback:
                    self.value = Report.Time.fallback_value
                    self.string = Report.Time.fallback_string
                else:
                    self.value = 0
                    self.string = ''
                self.is_string_valid = True
                return 1
            self.string = string
            self.is_string_valid = True
            return 0

    class Fuel(ValueString):
        def __str__(self):
            if not self.is_string_valid:
                self.string = f"{self.value:.1f}"
                self.is_string_valid = True
            return self.string
        def setFromString(self, string):
            if string == '':
                value = 0
            else:
                try:
                    self.value = float(string)
                except:
                    self.value = 0
                    self.string = ''
                    self.is_string_valid = True
                    return 1
            self.string = string
            self.is_string_valid = True
            return 0

    class TripCount():
        def __init__(self):
            self.passenger = 0
            self.no_passenger = 0
            self.total = 0
        def __add__(self, other):
            r = Report.TripCount()
            r.passenger = self.passenger + other.passenger
            r.no_passenger = self.no_passenger + other.no_passenger
            r.total = self.total + other.total
            return r
        def __sub__(self, other):
            r = Report.TripCount()
            r.passenger = self.passenger - other.passenger
            r.no_passenger = self.no_passenger - other.no_passenger
            r.total = self.total - other.total
            return r
        def addTrips(self, value, is_passenger):
            if is_passenger == False:
                self.no_passenger += value
            else:
                self.passenger += value
            self.total = self.passenger + self.no_passenger
        def setTrips(self, value, is_passenger):
            if is_passenger == False:
                self.no_passenger = value
            else:
                self.passenger = value
            self.total = self.passenger + self.no_passenger

    class ReportShift():
        def __init__(self):
            self.shift = None
            self.start_miles = Report.Mileage()
            self.start_time = Report.Time()
            self.end_miles = Report.Mileage()
            self.end_time = Report.Time()
            self.fuel = Report.Fuel()
            self.start_trip = None
            self.end_trip = None

    class ReportTrip():
        def __init__(self):
            self.trip = None
            self.shift = None
            self.start_miles = Report.Mileage()
            self.start_time = Report.Time()
            self.end_miles = Report.Mileage()
            self.end_time = Report.Time()
            self.trip_type = None
            self.tags = []
            self.collected_cash = Report.Money(0)
            self.collected_check = Report.Money(0)
            self.other_employment = False

    class ReportDay():
        query_vehicles = ()
        query_drivers = ()

        def __init__(self):
            self.date = None
            self.shifts = []
            self.trips = []
            self.all = Report.ReportSummary()
            self.collected_cash = Report.Money(0)
            self.collected_check = Report.Money(0)
            self.paid_cash = Report.Money(0)
            self.paid_check = Report.Money(0)
            self.total_payments = Report.Money(0)
            self.total_fares = Report.Money(0)
            self.by_vehicle = [None] * len(self.query_vehicles)
            self.by_driver = [None] * len(self.query_drivers)

        def hasVehicleInShift(self, vehicle = None):
            for i in self.shifts:
                if (vehicle and i.shift and i.shift.vehicle == vehicle) or (vehicle == None and i.shift and i.shift.vehicle != None):
                    return True
            return False

        def hasDriverInShift(self, driver = None):
            for i in self.shifts:
                if (driver and i.shift and i.shift.driver == driver) or (driver == None and i.shift and i.shift.driver != None):
                    return True
            return False

    class ReportSummary():
        query_triptypes = ()
        query_tags = ()

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
            self.trip_types_unknown = Report.TripCount()
            self.trip_types_total = Report.TripCount()
            self.tags = {}
            self.collected_cash = Report.Money(0)
            self.collected_check = Report.Money(0)
            self.total_collected_money = Report.Money(0)
            self.other_employment = Report.TripCount()

            for i in self.query_triptypes:
                self.trip_types[i] = Report.TripCount()

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
            r.trip_types_unknown += other.trip_types_unknown
            r.trip_types_total += other.trip_types_total
            for i in other.tags:
                if i in r.tags:
                    r.tags[i] += other.tags[i]
                else:
                    r.tags[i] = other.tags[i]
            r.collected_cash += other.collected_cash
            r.collected_check += other.collected_check
            r.total_collected_money += other.total_collected_money
            r.other_employment += other.other_employment
            return r

    class ReportOutputVehicles():
        def __init__(self):
            self.vehicle = None
            self.start_miles = Report.Mileage()
            self.end_miles = Report.Mileage()
            self.total_miles = Report.Mileage()
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
        SHIFT_SERVICE_MILE_THRESHOLD = 11

        def __init__(self):
            self.errors = []

        def add(self, date, daily_log_shift, error_code, error_shift=None, error_trip=None):
            if daily_log_shift == None or (error_shift and daily_log_shift == error_shift.id):
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
                if (error_shift):
                    trip_start_miles = shift_start_miles[:len(shift_start_miles)-len(error_trip.start_miles)] + error_trip.start_miles
                    trip_end_miles = shift_start_miles[:len(shift_start_miles)-len(error_trip.end_miles)] + error_trip.end_miles
                else:
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

            elif error_code == self.SHIFT_SERVICE_MILE_THRESHOLD:
                return 'Shift mileage seems abnormally large.'

            else:
                return 'Unknown error'

    class FrequentDestination():
        def __init__(self):
            self.address = None
            self.trips = Report.TripCount()
            self.avg_mileage = 0
        def __lt__(self, other):
            return self.trips.total < other.trips.total
        def averageMiles(self, miles):
            if self.avg_mileage == 0:
                self.avg_mileage = miles
            else:
                self.avg_mileage = (self.avg_mileage + miles) / 2

    class UniqueRiderSummary():
        class Rider():
            def __init__(self, name):
                self.name = name
                self.client_id = None
                self.trips = Report.TripCount()
                self.trips.total = 1
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
            self.elderly_ambulatory = Report.TripCount()
            self.elderly_nonambulatory = Report.TripCount()
            self.nonelderly_ambulatory = Report.TripCount()
            self.nonelderly_nonambulatory = Report.TripCount()
            self.unknown = Report.TripCount()
            self.total = Report.TripCount()
            self.staff = Report.TripCount()
            self.all = Report.TripCount()
            self.all_with_staff = Report.TripCount()
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
        Report.ReportSummary.query_triptypes = TripType.objects.filter(is_trip_counted=True)
        Report.ReportSummary.query_tags = Tag.objects.all()

        self.report_all = []
        self.vehicle_reports = []
        self.driver_reports = []
        self.driver_reports_total = Report.ReportOutputDrivers()
        self.all_vehicles = Report.ReportSummary()
        self.unique_riders = Report.UniqueRiderSummary()
        self.money_trips = []
        self.money_trips_summary = Report.ReportSummary()
        self.money_payments = []
        self.money_payments_summary = Report.ReportPayment()
        self.frequent_destinations = []
        self.report_errors = Report.ReportErrors()
        self.filtered_vehicles = None
        self.filtered_drivers = None
        self.total_vehicle_days_of_service = 0
        self.total_vehicle_mileage = Report.Mileage()
        self.total_money = Report.Money(0)
        self.total_odometer_miles = Report.Mileage()

        self.perf_database = 0
        self.perf_processing = 0

    def load(self, date_start, date_end, daily_log_shift=None, driver_id=None, client_name=None, filter_by_money=False):
        if date_start != date_end:
            daily_log_shift = None

        # for filter() bounds
        date_end_plus_one = date_end + datetime.timedelta(days=1)

        perf_start = perf_counter()
        # refresh related fields
        # without this, select_related can fail if new entries are used
        all_drivers = Driver.objects.all()
        all_vehicles = Vehicle.objects.all()
        all_triptypes = TripType.objects.all()

        if driver_id == None:
            self.filtered_vehicles = all_vehicles.filter(is_logged=True)
            self.filtered_drivers = all_drivers.filter(is_logged=True)
        else:
            self.filtered_vehicles = all_vehicles
            self.filtered_drivers = all_drivers.filter(id=driver_id)

        # also cache destinations
        all_destinations = Destination.objects.all()
        destination_list = list(all_destinations)

        # store our database lookups in dictionaries
        all_shifts = Shift.objects.filter(date__gte=date_start, date__lt=date_end_plus_one).order_by('-date')
        all_shifts = all_shifts.select_related('driver').select_related('vehicle')
        all_shifts_list = list(all_shifts)

        all_trips = Trip.objects.filter(date__gte=date_start, date__lt=date_end_plus_one, status=Trip.STATUS_NORMAL, format=Trip.FORMAT_NORMAL)
        if filter_by_money:
            all_trips = all_trips.exclude(fare=0, collected_cash=0, collected_check=0)
        if client_name != None:
            all_trips = all_trips.filter(name=client_name)
        all_trips = all_trips.select_related('driver').select_related('vehicle').select_related('trip_type')
        all_trips_list = list(all_trips)

        all_clients = Client.objects.all()
        if client_name != None:
            all_clients = all_clients.filter(name=client_name)
        all_clients_list = list(all_clients)

        all_client_payments = ClientPayment.objects.filter(date_paid__gte=date_start, date_paid__lt=date_end_plus_one)
        all_client_payments = all_client_payments.select_related('parent')
        all_client_payments_list = list(all_client_payments)
        self.perf_database = perf_counter() - perf_start

        perf_start = perf_counter()
        Report.ReportDay.query_drivers = list(self.filtered_drivers)
        Report.ReportDay.query_vehicles = list(all_vehicles)

        all_dates = []

        # process days where non-driver money is collected, even if there were no shifts/trips
        for i in all_client_payments_list:
            if i.date_paid not in all_dates:
                all_dates.append(i.date_paid)

        for i in all_trips_list:
            if i.date not in all_dates:
                all_dates.append(i.date)

        # when given a client name, it is because we are only interested in fares/payments
        # since shifts don't contain that data, we can skip looking at the shift list (which takes more time than the filtered trip list)
        if client_name == None:
            for i in all_shifts_list:
                if i.date not in all_dates:
                    all_dates.append(i.date)

        all_dates = sorted(all_dates)

        for day_date in all_dates:
            report_day = Report.ReportDay()
            report_day.date = day_date

            for i in all_shifts_list:
                if i.date < day_date:
                    break
                if i.date != day_date:
                    continue

                if driver_id == None:
                    if i.driver and not i.driver.is_logged:
                        # skip non-logged drivers
                        continue

                    if i.vehicle and not i.vehicle.is_logged:
                        # skip non-logged vehicles
                        continue
                elif i.driver:
                    if i.driver.id != driver_id:
                        continue

                log_status = i.check_log()
                if log_status != Shift.LOG_COMPLETE or i.driver == None or i.vehicle == None:
                    # skip incomplete shift
                    if log_status == Shift.LOG_INCOMPLETE:
                        self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_INCOMPLETE, error_shift=i)
                    continue

                report_shift = Report.ReportShift()
                report_shift.shift = i

                if report_shift.start_miles.setFromString(i.start_miles) != 0:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_PARSE, error_shift=i)

                if report_shift.start_time.setFromString(i.start_time) != 0:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_PARSE, error_shift=i)

                if report_shift.end_miles.setFromString(i.end_miles) != 0:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_PARSE, error_shift=i)

                if report_shift.end_time.setFromString(i.end_time) != 0:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_PARSE, error_shift=i)

                if report_shift.fuel.setFromString(i.fuel) != 0:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_PARSE, error_shift=i)

                if report_shift.start_miles > report_shift.end_miles:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_MILES_LESS, error_shift=i)
                    report_shift.end_miles = report_shift.start_miles

                if report_shift.start_time > report_shift.end_time:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_TIME_LESS, error_shift=i)
                    report_shift.end_time = report_shift.start_time

                if report_shift.end_miles.value - report_shift.start_miles.value > Report.service_mile_warning_threshold:
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.SHIFT_SERVICE_MILE_THRESHOLD, error_shift=i)

                report_day.shifts.append(report_shift)

            for i in all_trips_list:
                if i.date < day_date:
                    break
                if i.date != day_date:
                    continue

                log_status = i.check_log()

                if driver_id == None:
                    if i.driver and not i.driver.is_logged:
                        # skip non-logged drivers
                        continue

                    if i.vehicle and not i.vehicle.is_logged:
                        # skip non-logged vehicles
                        continue

                    if log_status == Trip.LOG_EMPTY:
                        # skip empty trip
                        continue
                elif i.driver:
                    if i.driver.id != driver_id:
                        continue
                elif not i.driver or not i.vehicle:
                    # skip trip with no driver/vehicle
                    continue

                report_trip = Report.ReportTrip()
                report_trip.trip = i

                for j in range(0, len(report_day.shifts)):
                    if report_day.shifts[j].shift and i.driver == report_day.shifts[j].shift.driver and i.vehicle == report_day.shifts[j].shift.vehicle:
                        report_trip.shift = j
                        break

                if report_trip.shift == None:
                    for j in range(0, len(report_day.shifts)):
                        if report_day.shifts[j].shift and i.vehicle == report_day.shifts[j].shift.vehicle:
                            report_trip.shift = j
                            break

                if report_trip.shift == None:
                    if driver_id == None:
                        if i.driver and i.vehicle and i.vehicle.is_logged:
                            found_shift = False
                            for test_shift in all_shifts_list:
                                if test_shift.driver == i.driver and test_shift.vehicle == i.vehicle and test_shift.date == i.date:
                                    found_shift = True
                                    break
                            if not found_shift:
                                self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_NO_SHIFT, error_trip=i)
                        continue
                    else:
                        dummy_shift = Report.ReportShift()
                        dummy_shift.shift = Shift()
                        dummy_shift.driver = dummy_shift.shift.driver = i.driver
                        dummy_shift.vehicle = dummy_shift.shift.vehicle = i.vehicle
                        report_day.shifts.append(dummy_shift)
                        report_trip.shift = len(report_day.shifts)-1

                shift = report_day.shifts[report_trip.shift]

                if log_status == Trip.LOG_INCOMPLETE:
                    # skip incomplete trip
                    self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_INCOMPLETE, error_shift=shift.shift, error_trip=i)
                    continue

                if not i.driver or not i.vehicle:
                    # skip incomplete trip
                    if i.driver and i.vehicle:
                        self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_INCOMPLETE, error_shift=shift.shift, error_trip=i)
                    continue

                # don't include trip if matching shift is incomplete
                if log_status == Trip.LOG_COMPLETE and (shift.start_miles.empty() or shift.start_time.empty() or shift.end_miles.empty() or shift.end_time.empty()):
                    continue

                if log_status == Trip.LOG_COMPLETE:
                    parse_error = False

                    if report_trip.start_miles.mergeStrings(str(shift.start_miles), i.start_miles) != 0:
                        parse_error = True

                    if report_trip.start_time.setFromString(i.start_time) != 0:
                        parse_error = True

                    if report_trip.end_miles.mergeStrings(str(shift.start_miles), i.end_miles) != 0:
                        parse_error = True

                    if report_trip.end_time.setFromString(i.end_time) != 0:
                        parse_error = True

                    if parse_error:
                        self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_PARSE, error_shift=shift.shift, error_trip=i)

                    # check for trip errors
                    # TODO the above execptions add errors to the report without adding the trip to the various trip counts
                    # BUT, the below errors still count the trips where possible. Not sure which is preferable, but it's probably bad that both behaviors exist?
                    # NOTE For mileage, we also check for validity by comparing against merges of shift *end* mileage and trip mileage.

                    # mileage error checking
                    if report_trip.start_miles < shift.start_miles or report_trip.start_miles > shift.end_miles or report_trip.end_miles < shift.start_miles or report_trip.end_miles > shift.end_miles:
                        # out-of-bounds
                        mile_error = False

                        # start mileage
                        if report_trip.start_miles < shift.start_miles or report_trip.start_miles > shift.end_miles:
                            mile_error = False
                            if report_trip.start_miles.mergeStrings(str(shift.end_miles), i.start_miles) == 0:
                                if report_trip.start_miles < shift.start_miles or report_trip.start_miles > shift.end_miles:
                                    mile_error = True
                            else:
                                mile_error = True
                            if mile_error:
                                report_trip.start_miles = shift.start_miles

                        # end mileage
                        if report_trip.end_miles < shift.start_miles or report_trip.end_miles > shift.end_miles:
                            mile_error = False
                            if report_trip.end_miles.mergeStrings(str(shift.end_miles), i.end_miles) == 0:
                                if report_trip.end_miles < shift.start_miles or report_trip.end_miles > shift.end_miles:
                                    mile_error = True
                            else:
                                mile_error = True
                            if mile_error:
                                report_trip.end_miles = shift.end_miles

                        if mile_error:
                            self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_MILES_OOB, error_shift=shift.shift, error_trip=i)
                    # end > start
                    elif report_trip.start_miles > report_trip.end_miles:
                        mile_error = False
                        if report_trip.end_miles.mergeStrings(str(shift.end_miles), i.end_miles) == 0:
                            if report_trip.start_miles > report_trip.end_miles or report_trip.end_miles > shift.end_miles:
                                mile_error = True
                        else:
                            mile_error = True
                        if mile_error:
                            report_trip.start_miles = shift.start_miles
                            report_trip.end_miles = shift.start_miles
                            self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_MILES_LESS, error_shift=shift.shift, error_trip=i)

                    # time error checking
                    if report_trip.start_time and shift.start_time and report_trip.end_time and shift.end_time:
                        # out-of-bounds
                        if report_trip.start_time < shift.start_time or report_trip.end_time > shift.end_time:
                            self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_TIME_OOB, error_shift=shift.shift, error_trip=i)
                            if report_trip.start_time < shift.start_time:
                                report_trip.start_time = shift.start_time
                            if report_trip.end_time > shift.end_time:
                                report_trip.end_time = shift.end_time
                        # end > start
                        elif report_trip.start_time > report_trip.end_time:
                            self.report_errors.add(day_date, daily_log_shift, self.report_errors.TRIP_TIME_LESS, error_shift=shift.shift, error_trip=i)
                            report_trip.start_time = shift.start_time
                            report_trip.end_time = shift.start_time

                report_trip.trip_type = i.trip_type
                report_trip.collected_cash = Report.Money(i.collected_cash)
                report_trip.collected_check = Report.Money(i.collected_check)

                report_day.collected_cash += report_trip.collected_cash
                report_day.collected_check += report_trip.collected_check
                report_day.total_payments += report_trip.collected_cash + report_trip.collected_check

                report_day.total_fares += Report.Money(i.fare)

                report_trip.other_employment = i.check_tag('Employment')

                report_day.trips.append(report_trip)

                if log_status == Trip.LOG_COMPLETE:
                    if shift.start_trip == None or report_trip.start_miles < report_day.trips[shift.start_trip].start_miles:
                        report_day.shifts[report_trip.shift].start_trip = len(report_day.trips) - 1;

                    if shift.end_trip == None or report_trip.end_miles > report_day.trips[shift.end_trip].end_miles:
                        report_day.shifts[report_trip.shift].end_trip = len(report_day.trips) - 1;


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
                            j.trips.addTrips(1, i.passenger)

                            j.total_fares += Report.Money(i.fare)
                            j.collected_cash += Report.Money(i.collected_cash)
                            j.collected_check += Report.Money(i.collected_check)

                            break
                    if not found_unique_rider:
                        rider = Report.UniqueRiderSummary.Rider(i.name)
                        rider.elderly = i.elderly
                        rider.ambulatory = i.ambulatory

                        for client in all_clients_list:
                            if client.name != i.name:
                                continue

                            rider.client_id = client.id
                            rider.staff = client.staff

                            if i.elderly == None or i.ambulatory == None:
                                # try to get info from Clients
                                if rider.elderly == None:
                                    rider.elderly = client.elderly
                                if rider.ambulatory == None:
                                    rider.ambulatory = client.ambulatory
                            break

                        rider.trips.setTrips(1, i.passenger)
                        rider.total_fares += Report.Money(i.fare)
                        rider.collected_cash += Report.Money(i.collected_cash)
                        rider.collected_check += Report.Money(i.collected_check)

                        self.unique_riders.names.append(rider)
                        self.unique_riders.names = sorted(self.unique_riders.names)

                if i.tags != "":
                    report_trip.tags = i.get_tag_list()

                # add destination to frequent destinations
                found_frequent_destination = False
                for j in self.frequent_destinations:
                    if j.address == i.destination:
                        found_frequent_destination = True
                        j.trips.addTrips(1, i.passenger)
                        if log_status == Trip.LOG_COMPLETE:
                            j.averageMiles(report_trip.end_miles.value - report_trip.start_miles.value)
                        break
                if not found_frequent_destination:
                    for dest in destination_list:
                        if dest.address == i.destination:
                            temp_fd = Report.FrequentDestination()
                            temp_fd.address = i.destination
                            temp_fd.trips.addTrips(1, i.passenger)
                            if log_status == Trip.LOG_COMPLETE:
                                temp_fd.averageMiles(report_trip.end_miles.value - report_trip.start_miles.value)
                            self.frequent_destinations.append(temp_fd)
                            break

            # handle payments from Clients that didn't ride (so far)
            for i in all_client_payments_list:
                if i.date_paid != day_date:
                    continue

                if client_name and i.parent.name != client_name:
                    continue

                report_day.paid_cash += Report.Money(i.money_cash)
                report_day.paid_check += Report.Money(i.money_check)
                report_day.total_payments += report_day.paid_cash + report_day.paid_check

                found_unique_rider = False
                for j in self.unique_riders.names:
                    if j.name == i.parent.name:
                        found_unique_rider = True

                        j.paid_cash += Report.Money(i.money_cash)
                        j.paid_check += Report.Money(i.money_check)

                        break
                if not found_unique_rider:
                    rider = Report.UniqueRiderSummary.Rider(i.parent.name)
                    rider.trips.setTrips(0, False)
                    rider.elderly = i.parent.elderly
                    rider.ambulatory = i.parent.ambulatory
                    rider.client_id = i.parent.id

                    rider.paid_cash += Report.Money(i.money_cash)
                    rider.paid_check += Report.Money(i.money_check)

                    self.unique_riders.names.append(rider)
                    self.unique_riders.names = sorted(self.unique_riders.names)

                # create a summary of only non-driver payments
                payment = Report.ReportPayment()
                payment.date = i.date_paid
                payment.id = i.id
                payment.client = i.parent
                payment.cash = Report.Money(i.money_cash)
                payment.check = Report.Money(i.money_check)
                self.money_payments.append(payment)
                self.money_payments_summary.cash += payment.cash
                self.money_payments_summary.check += payment.check

            for i in range(0, len(report_day.shifts)):
                shift = report_day.shifts[i]

                # create dummy trip when a shift has no trips
                if shift.start_trip == None and shift.end_trip == None:
                    rt = Report.ReportTrip()
                    rt.shift = i
                    rt.start_miles = shift.start_miles
                    rt.end_miles = shift.end_miles
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
                
                service_miles = 0
                service_hours = 0
                deadhead_miles = 0
                deadhead_hours = 0
                if not (shift.start_miles.empty() or shift.start_time.empty() or shift.end_miles.empty() or shift.end_time.empty()):
                    service_miles = shift.end_miles.value - shift.start_miles.value
                    service_hours = (shift.end_time.value - shift.start_time.value).seconds / 60 / 60
                    deadhead_miles = (report_day.trips[shift.start_trip].start_miles.value - shift.start_miles.value) + (shift.end_miles.value - report_day.trips[shift.end_trip].end_miles.value)
                    deadhead_hours = ((report_day.trips[shift.start_trip].start_time.value - shift.start_time.value).seconds + (shift.end_time.value - report_day.trips[shift.end_trip].end_time.value).seconds) / 60 / 60

                # per-vehicle and per-driver logs
                vehicle_index = Report.getVehicleIndex(shift.shift.vehicle)
                driver_index = Report.getDriverIndex(shift.shift.driver)

                if not report_day.by_vehicle[vehicle_index]:
                    report_day.by_vehicle[vehicle_index] = Report.ReportSummary()

                if not report_day.by_driver[driver_index]:
                    report_day.by_driver[driver_index] = Report.ReportSummary()

                report_day.by_vehicle[vehicle_index].service_miles += service_miles
                report_day.by_vehicle[vehicle_index].service_hours += service_hours
                report_day.by_vehicle[vehicle_index].deadhead_miles += deadhead_miles
                report_day.by_vehicle[vehicle_index].deadhead_hours += deadhead_hours
                report_day.by_vehicle[vehicle_index].total_miles += service_miles + deadhead_miles
                report_day.by_vehicle[vehicle_index].total_hours += service_hours + deadhead_hours
                report_day.by_vehicle[vehicle_index].fuel += shift.fuel.value

                report_day.by_driver[driver_index].service_miles += service_miles
                report_day.by_driver[driver_index].service_hours += service_hours
                report_day.by_driver[driver_index].deadhead_miles += deadhead_miles
                report_day.by_driver[driver_index].deadhead_hours += deadhead_hours
                report_day.by_driver[driver_index].total_miles += service_miles + deadhead_miles
                report_day.by_driver[driver_index].total_hours += service_hours + deadhead_hours
                report_day.by_driver[driver_index].fuel += shift.fuel.value
                for trip in report_day.trips:
                    if i != trip.shift:
                        continue
                    report_day.by_vehicle[vehicle_index].pmt += trip.end_miles.value - trip.start_miles.value
                    report_day.by_vehicle[vehicle_index].collected_cash += trip.collected_cash
                    report_day.by_vehicle[vehicle_index].collected_check += trip.collected_check
                    report_day.by_vehicle[vehicle_index].total_collected_money += (trip.collected_cash + trip.collected_check)
                    report_day.by_driver[driver_index].pmt += trip.end_miles.value - trip.start_miles.value
                    report_day.by_driver[driver_index].collected_cash += trip.collected_cash
                    report_day.by_driver[driver_index].collected_check += trip.collected_check
                    report_day.by_driver[driver_index].total_collected_money += (trip.collected_cash + trip.collected_check)
                    if trip.trip != None:
                        if trip.trip_type != None and trip.trip_type.is_trip_counted:
                            report_day.by_vehicle[vehicle_index].trip_types[trip.trip_type].addTrips(1, trip.trip.passenger)
                            report_day.by_vehicle[vehicle_index].trip_types_total.addTrips(1, trip.trip.passenger)
                            report_day.by_driver[driver_index].trip_types[trip.trip_type].addTrips(1, trip.trip.passenger)
                            report_day.by_driver[driver_index].trip_types_total.addTrips(1, trip.trip.passenger)
                        elif trip.trip_type == None:
                            report_day.by_vehicle[vehicle_index].trip_types_unknown.addTrips(1, trip.trip.passenger)
                            report_day.by_vehicle[vehicle_index].trip_types_total.addTrips(1, trip.trip.passenger)
                            report_day.by_driver[driver_index].trip_types_unknown.addTrips(1, trip.trip.passenger)
                            report_day.by_driver[driver_index].trip_types_total.addTrips(1, trip.trip.passenger)
                        if trip.other_employment:
                            report_day.by_vehicle[vehicle_index].other_employment.addTrips(1, trip.trip.passenger)
                            report_day.by_driver[driver_index].other_employment.addTrips(1, trip.trip.passenger)
                        for tag in trip.tags:
                            if tag in report_day.by_vehicle[vehicle_index].tags:
                                report_day.by_vehicle[vehicle_index].tags[tag].addTrips(1, trip.trip.passenger)
                            elif tag != '':
                                report_day.by_vehicle[vehicle_index].tags[tag] = Report.TripCount()
                                report_day.by_vehicle[vehicle_index].tags[tag].setTrips(1, trip.trip.passenger)
                            if tag in report_day.by_driver[driver_index].tags:
                                report_day.by_driver[driver_index].tags[tag].addTrips(1, trip.trip.passenger)
                            elif tag != '':
                                report_day.by_driver[driver_index].tags[tag] = Report.TripCount()
                                report_day.by_driver[driver_index].tags[tag].setTrips(1, trip.trip.passenger)

            for shift_vehicle in report_day.by_vehicle:
                if shift_vehicle:
                    report_day.all += shift_vehicle

            self.report_all.append(report_day)

        self.all_vehicles = Report.ReportSummary()

        # make sure our pre-defined tags get placed first in the final list
        for i in Report.ReportSummary.query_tags:
            self.all_vehicles.tags[i.name] = Report.TripCount()

        self.vehicle_reports = []
        for vehicle in self.filtered_vehicles:
            vehicle_report = Report.ReportOutputVehicles()
            vehicle_report.vehicle = vehicle
            self.vehicle_reports.append(vehicle_report)

        self.driver_reports = []
        for driver in self.filtered_drivers:
            driver_report = Report.ReportOutputDrivers()
            driver_report.driver = driver
            self.driver_reports.append(driver_report)

        for report_day in self.report_all:
            for vehicle_report in self.vehicle_reports:
                if report_day.hasVehicleInShift(vehicle_report.vehicle):
                    vehicle_index = Report.getVehicleIndex(vehicle_report.vehicle)
                    if report_day.by_vehicle[vehicle_index] != None:
                        vehicle_report.days.append({'date':report_day.date, 'data': report_day.by_vehicle[vehicle_index]})
                        vehicle_report.totals += report_day.by_vehicle[vehicle_index]
                        for shift_iter in report_day.shifts:
                            if shift_iter.shift and vehicle_report.vehicle.id == shift_iter.shift.vehicle.id:
                                if vehicle_report.start_miles.empty() or (not vehicle_report.start_miles.empty() and vehicle_report.start_miles > shift_iter.start_miles):
                                    vehicle_report.start_miles = shift_iter.start_miles
                                if vehicle_report.end_miles.empty() or (not vehicle_report.end_miles.empty() and vehicle_report.end_miles < shift_iter.end_miles):
                                    vehicle_report.end_miles = shift_iter.end_miles
            for driver_report in self.driver_reports:
                if report_day.hasDriverInShift(driver_report.driver):
                    driver_index = Report.getDriverIndex(driver_report.driver)
                    if report_day.by_driver[driver_index] != None:
                        driver_report.days.append({'date':report_day.date, 'data': report_day.by_driver[driver_index]})
                        driver_report.totals += report_day.by_driver[driver_index]

        for driver_report in self.driver_reports:
            self.driver_reports_total.totals += driver_report.totals

        for vehicle_report in self.vehicle_reports:
            if vehicle_report.end_miles >= vehicle_report.start_miles:
                vehicle_report.total_miles = vehicle_report.end_miles - vehicle_report.start_miles
            self.total_vehicle_mileage += vehicle_report.total_miles
            self.all_vehicles += vehicle_report.totals

        for rider in self.unique_riders.names:
            # total elderly/ambulatory counts
            if rider.trips.total > 0:
                self.unique_riders.all_with_staff.addTrips(1, (rider.trips.passenger > 0))
                if rider.staff:
                    self.unique_riders.staff.addTrips(1, (rider.trips.passenger > 0))
                else:
                    self.unique_riders.all.addTrips(1, (rider.trips.passenger > 0))
                    self.unique_riders.total.addTrips(1, (rider.trips.passenger > 0))
                    if rider.elderly == None or rider.ambulatory == None:
                        self.unique_riders.unknown.addTrips(1, (rider.trips.passenger > 0))
                    elif rider.elderly and rider.ambulatory:
                        self.unique_riders.elderly_ambulatory.addTrips(1, (rider.trips.passenger > 0))
                    elif rider.elderly and not rider.ambulatory:
                        self.unique_riders.elderly_nonambulatory.addTrips(1, (rider.trips.passenger > 0))
                    elif not rider.elderly and rider.ambulatory:
                        self.unique_riders.nonelderly_ambulatory.addTrips(1, (rider.trips.passenger > 0))
                    elif not rider.elderly and not rider.ambulatory:
                        self.unique_riders.nonelderly_nonambulatory.addTrips(1, (rider.trips.passenger > 0))

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

        # sort frequent destinations by total trips
        self.frequent_destinations.sort(reverse=True)

        for day in self.report_all:
            if day.hasVehicleInShift():
                self.total_vehicle_days_of_service += 1

        self.total_money = self.all_vehicles.total_collected_money + self.money_payments_summary.cash + self.money_payments_summary.check

        for vehicle_report in self.vehicle_reports:
            self.total_odometer_miles += vehicle_report.total_miles

        self.perf_processing = perf_counter() - perf_start

    def getVehicleIndex(vehicle):
        return Report.ReportDay.query_vehicles.index(vehicle)

    def getDriverIndex(driver):
        return Report.ReportDay.query_drivers.index(driver)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def report(request, start_year, start_month, start_day, end_year, end_month, end_day):
    return reportBase(request, None, start_year, start_month, start_day, end_year, end_month, end_day)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportDriver(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    return reportBase(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportBase(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)

    show_daily_data = request.session.get('report_show_daily_data', False)
    request.session['report_show_daily_data'] = show_daily_data

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
                if driver_id == None:
                    return HttpResponseRedirect(reverse('report', kwargs={'start_year':new_start.year, 'start_month':new_start.month, 'start_day':new_start.day, 'end_year':new_end.year, 'end_month':new_end.month, 'end_day':new_end.day}))
                else:
                    return HttpResponseRedirect(reverse('report-driver', kwargs={'driver_id': driver_id, 'start_year':new_start.year, 'start_month':new_start.month, 'start_day':new_start.day, 'end_year':new_end.year, 'end_month':new_end.month, 'end_day':new_end.day}))
        elif 'show_daily_data' in request.POST:
            show_daily_data = request.session['report_show_daily_data'] = not request.session['report_show_daily_data']
            if driver_id == None:
                return HttpResponseRedirect(reverse('report', kwargs={'start_year':start_year, 'start_month':start_month, 'start_day':start_day, 'end_year':end_year, 'end_month':end_month, 'end_day':end_day}))
            else:
                return HttpResponseRedirect(reverse('report-driver', kwargs={'driver_id': driver_id, 'start_year':start_year, 'start_month':start_month, 'start_day':start_day, 'end_year':end_year, 'end_month':end_month, 'end_day':end_day}))
        else:
            if date_picker.is_valid():
                date_picker_date = date_picker.cleaned_data['date']
                if driver_id == None:
                    return HttpResponseRedirect(reverse('report-month', kwargs={'year':date_picker_date.year, 'month':date_picker_date.month}))
                else:
                    return HttpResponseRedirect(reverse('report-month-driver', kwargs={'driver_id': driver_id, 'year':date_picker_date.year, 'month':date_picker_date.month}))
    else:
        date_picker = DatePickerForm(initial={'date':date_start})
        date_range_picker = DateRangePickerForm(initial={'date_start':date_start, 'date_end':date_end})

    month_prev = date_start + datetime.timedelta(days=-1)
    month_prev.replace(day=1)
    month_next = date_end + datetime.timedelta(days=1)

    report = Report()
    report.load(date_start, date_end, driver_id=driver_id)

    if driver_id == None:
        url_month_prev = reverse('report-month', kwargs={'year': month_prev.year, 'month': month_prev.month})
        url_month_next = reverse('report-month', kwargs={'year': month_next.year, 'month': month_next.month})
        url_this_month = reverse('report-this-month')
        url_print = reverse('report-print', kwargs={'start_year': date_start.year, 'start_month': date_start.month, 'start_day': date_start.day, 'end_year': date_end.year, 'end_month': date_end.month, 'end_day': date_end.day})
        url_xlsx = reverse('report-xlsx', kwargs={'start_year': date_start.year, 'start_month': date_start.month, 'start_day': date_start.day, 'end_year': date_end.year, 'end_month': date_end.month, 'end_day': date_end.day})
    else:
        url_month_prev = reverse('report-month-driver', kwargs={'driver_id': driver_id, 'year': month_prev.year, 'month': month_prev.month})
        url_month_next = reverse('report-month-driver', kwargs={'driver_id': driver_id, 'year': month_next.year, 'month': month_next.month})
        url_this_month = reverse('report-this-month-driver', kwargs={'driver_id': driver_id})
        url_print = reverse('report-print-driver', kwargs={'driver_id': driver_id, 'start_year': date_start.year, 'start_month': date_start.month, 'start_day': date_start.day, 'end_year': date_end.year, 'end_month': date_end.month, 'end_day': date_end.day})
        url_xlsx = reverse('report-xlsx-driver', kwargs={'driver_id': driver_id, 'start_year': date_start.year, 'start_month': date_start.month, 'start_day': date_start.day, 'end_year': date_end.year, 'end_month': date_end.month, 'end_day': date_end.day})

    # we don't care about the driver for the mileage summary
    url_print_mile_summary = reverse('report-print-mileage-summary', kwargs={'start_year': date_start.year, 'start_month': date_start.month, 'start_day': date_start.day, 'end_year': date_end.year, 'end_month': date_end.month, 'end_day': date_end.day})

    selected_driver = None
    if driver_id != None:
        selected_driver = Driver.objects.get(id=driver_id)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'report': report,
        'date_picker': date_picker,
        'date_range_picker': date_range_picker,
        'url_month_prev': url_month_prev,
        'url_month_next': url_month_next,
        'url_this_month': url_this_month,
        'url_print': url_print,
        'url_print_mile_summary': url_print_mile_summary,
        'url_xlsx': url_xlsx,
        'selected_driver': selected_driver,
        'show_daily_data': show_daily_data,
        'is_short_report': len(report.report_all) <= 31,
        'vehicle_table_colspan': 13 + (3 * len(Report.ReportSummary.query_triptypes)),
        'drivers': Driver.objects.filter(is_active=True),
        'vehicles': Vehicle.objects.all(),
    }
    return render(request, 'report/view.html', context)



@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportPrint(request, start_year, start_month, start_day, end_year, end_month, end_day):
    return reportPrintBase(request, None, start_year, start_month, start_day, end_year, end_month, end_day)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportPrintDriver(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    return reportPrintBase(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportPrintBase(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)

    show_daily_data = request.session.get('report_show_daily_data', False)
    request.session['report_show_daily_data'] = show_daily_data

    if date_start > date_end:
        swap_date = date_start
        date_start = date_end
        date_end = swap_date

    report = Report()
    report.load(date_start, date_end, driver_id=driver_id)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'report': report,
        'show_daily_data': show_daily_data,
        'is_short_report': len(report.report_all) <= 31,
        'vehicle_table_colspan': 13 + (3 * len(Report.ReportSummary.query_triptypes)),
        'vehicles': Vehicle.objects.all(),
    }
    return render(request, 'report/print.html', context)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportPrintMileageSummary(request, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)

    if date_start > date_end:
        swap_date = date_start
        date_start = date_end
        date_end = swap_date

    report = Report()
    report.load(date_start, date_end, driver_id=None)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'report': report,
    }
    return render(request, 'report/print_mileage_summary.html', context)



@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportMonth(request, year, month):
    return reportMonthBase(request, None, year, month)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportMonthDriver(request, driver_id, year, month):
    return reportMonthBase(request, driver_id, year, month)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportMonthBase(request, driver_id, year, month):
    date_start = datetime.date(year, month, 1)
    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

    if driver_id:
        return HttpResponseRedirect(reverse('report-driver', kwargs={'driver_id': driver_id, 'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))
    else:
        return HttpResponseRedirect(reverse('report', kwargs={'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))


@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportYear(request, year):
    return reportYearBase(request, None, year)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportYearBase(request, driver_id, year):
    date_start = datetime.date(year, 1, 1)
    date_end = datetime.date(year+1, 1, 1) + datetime.timedelta(days=-1)

    if driver_id:
        return HttpResponseRedirect(reverse('report-driver', kwargs={'driver_id': driver_id, 'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))
    else:
        return HttpResponseRedirect(reverse('report', kwargs={'start_year':date_start.year, 'start_month':date_start.month, 'start_day':date_start.day, 'end_year':date_end.year, 'end_month':date_end.month, 'end_day':date_end.day}))


@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportThisMonth(request):
    return reportThisMonthBase(request, None)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportThisMonthDriver(request, driver_id):
    return reportThisMonthBase(request, driver_id)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportThisMonthBase(request, driver_id):
    date = datetime.datetime.now().date()
    if driver_id:
        return reportMonthDriver(request, driver_id, date.year, date.month)
    else:
        return reportMonth(request, date.year, date.month)



@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportLastMonth(request):
    return reportLastMonthBase(request, None)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportLastMonthDriver(request, driver_id):
    return reportLastMonthBase(request, driver_id)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportLastMonthBase(request, driver_id):
    date = (datetime.datetime.now().date()).replace(day=1) # first day of this month 
    date = date + datetime.timedelta(days=-1) # last day of the previous month
    if driver_id:
        return reportMonthDriver(request, driver_id, date.year, date.month)
    else:
        return reportMonth(request, date.year, date.month)



@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportXLSX(request, start_year, start_month, start_day, end_year, end_month, end_day):
    return reportXLSXBase(request, None, start_year, start_month, start_day, end_year, end_month, end_day)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportXLSXDriver(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    return reportXLSXBase(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day)

@permission_required(['transit.view_trip', 'transit.view_shift'])
def reportXLSXBase(request, driver_id, start_year, start_month, start_day, end_year, end_month, end_day):
    date_start = datetime.date(start_year, start_month, start_day)
    date_end = datetime.date(end_year, end_month, end_day)

    if date_start > date_end:
        swap_date = date_start
        date_start = date_end
        date_end = swap_date

    trip_types = TripType.objects.filter(is_trip_counted=True)

    report = Report()
    report.load(date_start, date_end, driver_id=driver_id)

    temp_file = tempfile.NamedTemporaryFile()

    wb = Workbook()

    style_font_normal = Font(name='Arial', size=10)
    style_border_normal_side = Side(border_style='thin', color='FF000000')
    style_border_normal = Border(left=style_border_normal_side, right=style_border_normal_side, top=style_border_normal_side, bottom=style_border_normal_side)
    style_colwidth_normal = 13
    style_colwidth_small = style_colwidth_normal / 3

    style_font_header = Font(name='Arial', size=10, bold=True)
    style_alignment_header = Alignment(horizontal='center', vertical='center', wrap_text=True)
    style_fill_header = PatternFill(fill_type='solid', fgColor='DFE0E1')
    style_rowheight_header = 25

    style_font_total = Font(name='Arial', size=10, bold=True, color='FFFFFFFF')
    style_fill_total = PatternFill(fill_type='solid', fgColor='27A343')

    #####
    #### All Vehicle Totals
    #####
    report_all = []
    for i in report.report_all:
        if i.hasVehicleInShift():
            report_all.append(i)

    ws_vehicle_total = wb.active
    ws_vehicle_total.title = 'Totals for All Vehicles'

    row_header = 1
    row_total = 1 + len(report_all) + 1

    ws_vehicle_total.cell(row_header, 2, 'Service Miles')
    ws_vehicle_total.cell(row_header, 3, 'Service Hours')
    ws_vehicle_total.cell(row_header, 4, 'Deadhead Miles')
    ws_vehicle_total.cell(row_header, 5, 'Deadhead Hours')
    ws_vehicle_total.cell(row_header, 6, 'Passenger Miles (PMT)')
    ws_vehicle_total.cell(row_header, 7, 'Fuel')

    for day in range(0, len(report_all)):
        day_row = row_header + day + 1
        ws_vehicle_total.cell(day_row, 1, report_all[day].date)
        ws_vehicle_total.cell(day_row, 2, report_all[day].all.service_miles)
        ws_vehicle_total.cell(day_row, 3, report_all[day].all.service_hours)
        ws_vehicle_total.cell(day_row, 4, report_all[day].all.deadhead_miles)
        ws_vehicle_total.cell(day_row, 5, report_all[day].all.deadhead_hours)
        ws_vehicle_total.cell(day_row, 6, report_all[day].all.pmt)
        ws_vehicle_total.cell(day_row, 7, report_all[day].all.fuel)

        triptype_col=8
        for i in trip_types:
            ws_vehicle_total.cell(row_header, triptype_col, 'Trip Type: ' + str(i))
            ws_vehicle_total.merge_cells(start_row=row_header, start_column=triptype_col, end_row=row_header, end_column=triptype_col+2)
            ws_vehicle_total.cell(day_row, triptype_col, report_all[day].all.trip_types[i].passenger)
            ws_vehicle_total.cell(day_row, triptype_col+1, report_all[day].all.trip_types[i].no_passenger)
            ws_vehicle_total.cell(day_row, triptype_col+2, report_all[day].all.trip_types[i].total)
            triptype_col += 3

        ws_vehicle_total.cell(row_header, triptype_col, 'Total Trips')
        ws_vehicle_total.merge_cells(start_row=row_header, start_column=triptype_col, end_row=row_header, end_column=triptype_col+2)
        ws_vehicle_total.cell(day_row, triptype_col, report_all[day].all.trip_types_total.passenger)
        ws_vehicle_total.cell(day_row, triptype_col+1, report_all[day].all.trip_types_total.no_passenger)
        ws_vehicle_total.cell(day_row, triptype_col+2, report_all[day].all.trip_types_total.total)
        triptype_col += 3

        ws_vehicle_total.cell(row_header, triptype_col, 'Cash Collected')
        ws_vehicle_total.cell(row_header, triptype_col+1, 'Check Collected')
        ws_vehicle_total.cell(row_header, triptype_col+2, 'Total Money Collected')
        ws_vehicle_total.cell(day_row, triptype_col, report_all[day].all.collected_cash.to_float())
        ws_vehicle_total.cell(day_row, triptype_col+1, report_all[day].all.collected_check.to_float())
        ws_vehicle_total.cell(day_row, triptype_col+2, report_all[day].all.total_collected_money.to_float())

    ws_vehicle_total.cell(row_total, 1, 'TOTAL')
    ws_vehicle_total.cell(row_total, 2, report.all_vehicles.service_miles)
    ws_vehicle_total.cell(row_total, 3, report.all_vehicles.service_hours)
    ws_vehicle_total.cell(row_total, 4, report.all_vehicles.deadhead_miles)
    ws_vehicle_total.cell(row_total, 5, report.all_vehicles.deadhead_hours)
    ws_vehicle_total.cell(row_total, 6, report.all_vehicles.pmt)
    ws_vehicle_total.cell(row_total, 7, report.all_vehicles.fuel)

    triptype_col=8
    for i in trip_types:
        ws_vehicle_total.cell(row_header, triptype_col, 'Trip Type: ' + str(i))
        ws_vehicle_total.merge_cells(start_row=row_header, start_column=triptype_col, end_row=row_header, end_column=triptype_col+2)
        ws_vehicle_total.cell(row_total, triptype_col, report.all_vehicles.trip_types[i].passenger)
        ws_vehicle_total.cell(row_total, triptype_col+1, report.all_vehicles.trip_types[i].no_passenger)
        ws_vehicle_total.cell(row_total, triptype_col+2, report.all_vehicles.trip_types[i].total)
        triptype_col += 3

    ws_vehicle_total.cell(row_header, triptype_col, 'Total Trips')
    ws_vehicle_total.merge_cells(start_row=row_header, start_column=triptype_col, end_row=row_header, end_column=triptype_col+2)
    ws_vehicle_total.cell(row_total, triptype_col, report.all_vehicles.trip_types_total.passenger)
    ws_vehicle_total.cell(row_total, triptype_col+1, report.all_vehicles.trip_types_total.no_passenger)
    ws_vehicle_total.cell(row_total, triptype_col+2, report.all_vehicles.trip_types_total.total)
    triptype_col += 3

    ws_vehicle_total.cell(row_header, triptype_col, 'Cash Collected')
    ws_vehicle_total.cell(row_header, triptype_col+1, 'Check Collected')
    ws_vehicle_total.cell(row_header, triptype_col+2, 'Total Money Collected')
    ws_vehicle_total.cell(row_total, triptype_col, report.all_vehicles.collected_cash.to_float())
    ws_vehicle_total.cell(row_total, triptype_col+1, report.all_vehicles.collected_check.to_float())
    ws_vehicle_total.cell(row_total, triptype_col+2, report.all_vehicles.total_collected_money.to_float())

    # number formats
    for i in range(row_header + 1, row_total + 1):
        if i < row_total:
            ws_vehicle_total.cell(i, 1).number_format = 'mmm dd, yyyy'
        ws_vehicle_total.cell(i, 2).number_format = '0.0'
        ws_vehicle_total.cell(i, 3).number_format = '0.00'
        ws_vehicle_total.cell(i, 4).number_format = '0.0'
        ws_vehicle_total.cell(i, 5).number_format = '0.00'
        ws_vehicle_total.cell(i, 6).number_format = '0.0'
        ws_vehicle_total.cell(i, 7).number_format = '0.0'
        ws_vehicle_total.cell(i, triptype_col).number_format = '$0.00'
        ws_vehicle_total.cell(i, triptype_col+1).number_format = '$0.00'
        ws_vehicle_total.cell(i, triptype_col+2).number_format = '$0.00'

    # apply styles
    ws_vehicle_total.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, triptype_col+3):
        if i >= 8 and i < triptype_col:
            ws_vehicle_total.column_dimensions[get_column_letter(i)].width = style_colwidth_small
        else:
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
            for i in trip_types:
                ws_vehicle.cell(row_header, triptype_col, 'Trip Type: ' + str(i))
                ws_vehicle.merge_cells(start_row=row_header, start_column=triptype_col, end_row=row_header, end_column=triptype_col+2)
                ws_vehicle.cell(day_row, triptype_col, vr.days[day]['data'].trip_types[i].passenger)
                ws_vehicle.cell(day_row, triptype_col+1, vr.days[day]['data'].trip_types[i].no_passenger)
                ws_vehicle.cell(day_row, triptype_col+2, vr.days[day]['data'].trip_types[i].total)
                triptype_col += 3

            ws_vehicle.cell(row_header, triptype_col, 'Total Trips')
            ws_vehicle.merge_cells(start_row=row_header, start_column=triptype_col, end_row=row_header, end_column=triptype_col+2)
            ws_vehicle.cell(day_row, triptype_col, vr.days[day]['data'].trip_types_total.passenger)
            ws_vehicle.cell(day_row, triptype_col+1, vr.days[day]['data'].trip_types_total.no_passenger)
            ws_vehicle.cell(day_row, triptype_col+2, vr.days[day]['data'].trip_types_total.total)
            triptype_col += 3

            ws_vehicle.cell(row_header, triptype_col, 'Cash Collected')
            ws_vehicle.cell(row_header, triptype_col+1, 'Check Collected')
            ws_vehicle.cell(row_header, triptype_col+2, 'Total Money Collected')
            ws_vehicle.cell(day_row, triptype_col, vr.days[day]['data'].collected_cash.to_float())
            ws_vehicle.cell(day_row, triptype_col+1, vr.days[day]['data'].collected_check.to_float())
            ws_vehicle.cell(day_row, triptype_col+2, vr.days[day]['data'].total_collected_money.to_float())

        ws_vehicle.cell(row_total, 1, 'TOTAL')
        ws_vehicle.cell(row_total, 2, vr.totals.service_miles)
        ws_vehicle.cell(row_total, 3, vr.totals.service_hours)
        ws_vehicle.cell(row_total, 4, vr.totals.deadhead_miles)
        ws_vehicle.cell(row_total, 5, vr.totals.deadhead_hours)
        ws_vehicle.cell(row_total, 6, vr.totals.pmt)
        ws_vehicle.cell(row_total, 7, vr.totals.fuel)

        triptype_col=8
        for i in trip_types:
            ws_vehicle.cell(row_total, triptype_col, vr.totals.trip_types[i].passenger)
            ws_vehicle.cell(row_total, triptype_col+1, vr.totals.trip_types[i].no_passenger)
            ws_vehicle.cell(row_total, triptype_col+2, vr.totals.trip_types[i].total)
            triptype_col += 3

        ws_vehicle.cell(row_total, triptype_col, vr.totals.trip_types_total.passenger)
        ws_vehicle.cell(row_total, triptype_col+1, vr.totals.trip_types_total.no_passenger)
        ws_vehicle.cell(row_total, triptype_col+2, vr.totals.trip_types_total.total)
        triptype_col += 3

        ws_vehicle.cell(row_header, triptype_col, 'Cash Collected')
        ws_vehicle.cell(row_header, triptype_col+1, 'Check Collected')
        ws_vehicle.cell(row_header, triptype_col+2, 'Total Money Collected')
        ws_vehicle.cell(row_total, triptype_col, vr.totals.collected_cash.to_float())
        ws_vehicle.cell(row_total, triptype_col+1, vr.totals.collected_check.to_float())
        ws_vehicle.cell(row_total, triptype_col+2, vr.totals.total_collected_money.to_float())

        # number formats
        for i in range(row_header + 1, row_total + 1):
            if i < row_total:
                ws_vehicle.cell(i, 1).number_format = 'mmm dd, yyyy'
            ws_vehicle.cell(i, 2).number_format = '0.0'
            ws_vehicle.cell(i, 3).number_format = '0.00'
            ws_vehicle.cell(i, 4).number_format = '0.0'
            ws_vehicle.cell(i, 5).number_format = '0.00'
            ws_vehicle.cell(i, 6).number_format = '0.0'
            ws_vehicle.cell(i, 7).number_format = '0.0'
            ws_vehicle.cell(i, triptype_col).number_format = '$0.00'
            ws_vehicle.cell(i, triptype_col+1).number_format = '$0.00'
            ws_vehicle.cell(i, triptype_col+2).number_format = '$0.00'

        # apply styles
        ws_vehicle.row_dimensions[row_header].height = style_rowheight_header
        for i in range(1, triptype_col+3):
            if i >= 8 and i < triptype_col:
                ws_vehicle.column_dimensions[get_column_letter(i)].width = style_colwidth_small
            else:
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
    #### Unique rider summary
    #####
    ws_riders = wb.create_sheet('Rider Summary')
    row_header = 1
    row_total = 4
    ws_riders.cell(row_header, 2, 'Elderly Ambulatory')
    ws_riders.cell(row_header, 3, 'Elderly Non-Ambulatory')
    ws_riders.cell(row_header, 4, 'Non-Elderly Ambulatory')
    ws_riders.cell(row_header, 5, 'Non-Elderly Non-Ambulatory')
    ws_riders.cell(row_header, 6, 'Unknown')
    ws_riders.cell(row_header, 7, 'Total')
    ws_riders.cell(row_header, 8, 'Staff')
    ws_riders.cell(row_header, 9, 'Total (with staff)')

    ws_riders.cell(row_header+1, 1, 'On vehicle')
    ws_riders.cell(row_header+1, 2, report.unique_riders.elderly_ambulatory.passenger)
    ws_riders.cell(row_header+1, 3, report.unique_riders.elderly_nonambulatory.passenger)
    ws_riders.cell(row_header+1, 4, report.unique_riders.nonelderly_ambulatory.passenger)
    ws_riders.cell(row_header+1, 5, report.unique_riders.nonelderly_nonambulatory.passenger)
    ws_riders.cell(row_header+1, 6, report.unique_riders.unknown.passenger)
    ws_riders.cell(row_header+1, 7, report.unique_riders.all.passenger)
    ws_riders.cell(row_header+1, 8, report.unique_riders.staff.passenger)
    ws_riders.cell(row_header+1, 9, report.unique_riders.all_with_staff.passenger)

    ws_riders.cell(row_header+2, 1, 'Not on vehicle')
    ws_riders.cell(row_header+2, 2, report.unique_riders.elderly_ambulatory.no_passenger)
    ws_riders.cell(row_header+2, 3, report.unique_riders.elderly_nonambulatory.no_passenger)
    ws_riders.cell(row_header+2, 4, report.unique_riders.nonelderly_ambulatory.no_passenger)
    ws_riders.cell(row_header+2, 5, report.unique_riders.nonelderly_nonambulatory.no_passenger)
    ws_riders.cell(row_header+2, 6, report.unique_riders.unknown.no_passenger)
    ws_riders.cell(row_header+2, 7, report.unique_riders.all.no_passenger)
    ws_riders.cell(row_header+2, 8, report.unique_riders.staff.no_passenger)
    ws_riders.cell(row_header+2, 9, report.unique_riders.all_with_staff.no_passenger)

    ws_riders.cell(row_total, 1, 'TOTAL')
    ws_riders.cell(row_total, 2, report.unique_riders.elderly_ambulatory.total)
    ws_riders.cell(row_total, 3, report.unique_riders.elderly_nonambulatory.total)
    ws_riders.cell(row_total, 4, report.unique_riders.nonelderly_ambulatory.total)
    ws_riders.cell(row_total, 5, report.unique_riders.nonelderly_nonambulatory.total)
    ws_riders.cell(row_total, 6, report.unique_riders.unknown.total)
    ws_riders.cell(row_total, 7, report.unique_riders.all.total)
    ws_riders.cell(row_total, 8, report.unique_riders.staff.total)
    ws_riders.cell(row_total, 9, report.unique_riders.all_with_staff.total)

    row_total_riders = 0
    for i in report.unique_riders.names:
        if i.trips.total > 0:
            row_total_riders += 1
    row_total_riders += 1

    row_header_riders = row_total + 2
    for i in range(row_header_riders, row_header_riders + row_total_riders):
        ws_riders.merge_cells(start_row=i, start_column=1, end_row=i, end_column=2)

    ws_riders.cell(row_header_riders, 1, 'Name')
    ws_riders.cell(row_header_riders, 3, 'Elderly')
    ws_riders.cell(row_header_riders, 4, 'Ambulatory')
    ws_riders.cell(row_header_riders, 5, 'Trips on vehicle')
    ws_riders.cell(row_header_riders, 6, 'Trips not on vehicle')
    ws_riders.cell(row_header_riders, 7, 'Total Trips')

    row = 0
    for i in report.unique_riders.names:
        if i.trips.total > 0:
            ws_riders.cell(row_header_riders + row + 1, 1, i.name)
            ws_riders.cell(row_header_riders + row + 1, 3, i.elderly)
            ws_riders.cell(row_header_riders + row + 1, 4, i.ambulatory)
            ws_riders.cell(row_header_riders + row + 1, 5, i.trips.passenger)
            ws_riders.cell(row_header_riders + row + 1, 6, i.trips.no_passenger)
            ws_riders.cell(row_header_riders + row + 1, 7, i.trips.total)
            row += 1

    # apply styles
    ws_riders.row_dimensions[row_header].height = style_rowheight_header
    ws_riders.row_dimensions[row_header_riders].height = style_rowheight_header
    for i in range(1, 10):
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
    for i in range(1, 8):
        for j in range(row_header_riders, row_header_riders + row_total_riders):
            ws_riders.cell(j, i).border = style_border_normal
            if j == row_header_riders:
                ws_riders.cell(j, i).font = style_font_header
                ws_riders.cell(j, i).alignment = style_alignment_header
                ws_riders.cell(j, i).fill = style_fill_header
            else:
                ws_riders.cell(j, i).font = style_font_normal

    #####
    #### Trip Types and Tags
    #####
    ws_tags = wb.create_sheet('Trip Types and Tags')
    row_header = 1
    ws_tags.cell(row_header, 1, 'Trip Type')
    ws_tags.cell(row_header, 2, 'Trips on vehicle')
    ws_tags.cell(row_header, 3, 'Trips not on vehicle')
    ws_tags.cell(row_header, 4, 'Total Trips')

    row_trip_type = 1
    for trip_type in trip_types:
        ws_tags.cell(row_header + row_trip_type, 1, str(trip_type))
        ws_tags.cell(row_header + row_trip_type, 2, report.all_vehicles.trip_types[trip_type].passenger)
        ws_tags.cell(row_header + row_trip_type, 3, report.all_vehicles.trip_types[trip_type].no_passenger)
        ws_tags.cell(row_header + row_trip_type, 4, report.all_vehicles.trip_types[trip_type].total)
        row_trip_type += 1

    row_trip_type_unknown = row_trip_type
    ws_tags.cell(row_header + row_trip_type_unknown, 1, 'Unknown')
    ws_tags.cell(row_header + row_trip_type_unknown, 2, report.all_vehicles.trip_types_unknown.passenger)
    ws_tags.cell(row_header + row_trip_type_unknown, 3, report.all_vehicles.trip_types_unknown.no_passenger)
    ws_tags.cell(row_header + row_trip_type_unknown, 4, report.all_vehicles.trip_types_unknown.total)

    row_trip_type_total = row_trip_type_unknown + 1
    ws_tags.cell(row_header + row_trip_type_total, 1, 'TOTAL')
    ws_tags.cell(row_header + row_trip_type_total, 2, report.all_vehicles.trip_types_total.passenger)
    ws_tags.cell(row_header + row_trip_type_total, 3, report.all_vehicles.trip_types_total.no_passenger)
    ws_tags.cell(row_header + row_trip_type_total, 4, report.all_vehicles.trip_types_total.total)

    row_header_tags = row_trip_type_total + 3
    ws_tags.cell(row_header_tags, 1, 'Tag')
    ws_tags.cell(row_header_tags, 2, 'Trips on vehicle')
    ws_tags.cell(row_header_tags, 3, 'Trips not on vehicle')
    ws_tags.cell(row_header_tags, 4, 'Total Trips')

    row_tag = 1
    for tag in Tag.objects.all():
        ws_tags.cell(row_header_tags + row_tag, 1, str(tag))
        ws_tags.cell(row_header_tags + row_tag, 2, report.all_vehicles.tags[str(tag)].passenger)
        ws_tags.cell(row_header_tags + row_tag, 3, report.all_vehicles.tags[str(tag)].no_passenger)
        ws_tags.cell(row_header_tags + row_tag, 4, report.all_vehicles.tags[str(tag)].total)
        row_tag += 1

    # apply styles
    ws_tags.row_dimensions[row_header].height = style_rowheight_header
    ws_tags.row_dimensions[row_header_tags].height = style_rowheight_header
    ws_tags.column_dimensions[get_column_letter(1)].width = style_colwidth_normal * 2
    for i in range(1, 5):
        if i > 1:
            ws_tags.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_header_tags + row_tag):
            if j == row_header + row_trip_type_total + 1:
                continue
            elif j == row_header + row_trip_type_total:
                ws_tags.cell(j, i).font = style_font_total
                ws_tags.cell(j, i).fill = style_fill_total
                ws_tags.cell(j, i).border = style_border_normal
                continue
            ws_tags.cell(j, i).border = style_border_normal
            if j == row_header or j == row_header_tags:
                ws_tags.cell(j, i).font = style_font_header
                ws_tags.cell(j, i).alignment = style_alignment_header
                ws_tags.cell(j, i).fill = style_fill_header
            else:
                ws_tags.cell(j, i).font = style_font_normal

    #####
    #### Frequent Destinations
    #####
    ws_destinations = wb.create_sheet('Frequent Destinations')
    row_header = 1
    ws_destinations.cell(row_header, 1, 'Address')
    ws_destinations.cell(row_header, 2, 'Trips on vehicle')
    ws_destinations.cell(row_header, 3, 'Trips not on vehicle')
    ws_destinations.cell(row_header, 4, 'Total Trips')
    ws_destinations.cell(row_header, 5, 'Average Mileage')

    row_dest = 1
    for destination in report.frequent_destinations:
        ws_destinations.cell(row_header + row_dest, 1, destination.address)
        ws_destinations.cell(row_header + row_dest, 2, destination.trips.passenger)
        ws_destinations.cell(row_header + row_dest, 3, destination.trips.no_passenger)
        ws_destinations.cell(row_header + row_dest, 4, destination.trips.total)
        ws_destinations.cell(row_header + row_dest, 5, destination.avg_mileage)
        # avg mileage number format
        ws_destinations.cell(row_header + row_dest, 5).number_format = '0.0'
        row_dest += 1

    # apply styles
    ws_destinations.row_dimensions[row_header].height = style_rowheight_header
    ws_destinations.column_dimensions[get_column_letter(1)].width = style_colwidth_normal * 2
    for i in range(1, 6):
        if i > 1:
            ws_destinations.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, row_header + row_dest):
            ws_destinations.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_destinations.cell(j, i).font = style_font_header
                ws_destinations.cell(j, i).alignment = style_alignment_header
                ws_destinations.cell(j, i).fill = style_fill_header
            else:
                ws_destinations.cell(j, i).font = style_font_normal

    #####
    #### Fares & Payments (by client)
    #####
    ws_fares = wb.create_sheet('Fares & Payments (by client)')
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
    #### Fares & Payments (by date)
    #####
    ws_fares_by_date = wb.create_sheet('Fares & Payments (by date)')
    row_header = 1

    row_total = 0
    for i in report.report_all:
        if i.total_payments.value > 0 or i.total_fares.value > 0:
            row_total += 1
    row_total += 2

    ws_fares_by_date.cell(row_header, 1, 'Date')
    ws_fares_by_date.cell(row_header, 2, 'Cash (driver collected)')
    ws_fares_by_date.cell(row_header, 3, 'Check (driver collected)')
    ws_fares_by_date.cell(row_header, 4, 'Cash (not driver collected)')
    ws_fares_by_date.cell(row_header, 5, 'Check (not driver collected)')
    ws_fares_by_date.cell(row_header, 6, 'Total Payments')
    ws_fares_by_date.cell(row_header, 7, 'Total Fares')

    ws_fares_by_date.cell(row_total, 1, 'TOTAL')
    ws_fares_by_date.cell(row_total, 2, report.unique_riders.total_collected_cash.to_float())
    ws_fares_by_date.cell(row_total, 3, report.unique_riders.total_collected_check.to_float())
    ws_fares_by_date.cell(row_total, 4, report.unique_riders.total_paid_cash.to_float())
    ws_fares_by_date.cell(row_total, 5, report.unique_riders.total_paid_check.to_float())
    ws_fares_by_date.cell(row_total, 6, report.unique_riders.total_total_payments.to_float())
    ws_fares_by_date.cell(row_total, 7, report.unique_riders.total_total_fares.to_float())

    row = 0
    for i in report.report_all:
        if i.total_payments.value <= 0 and i.total_fares.value <= 0:
            continue
        ws_fares_by_date.cell(row + row_header + 1, 1, i.date)
        ws_fares_by_date.cell(row + row_header + 1, 2, i.collected_cash.to_float())
        ws_fares_by_date.cell(row + row_header + 1, 3, i.collected_check.to_float())
        ws_fares_by_date.cell(row + row_header + 1, 4, i.paid_cash.to_float())
        ws_fares_by_date.cell(row + row_header + 1, 5, i.paid_check.to_float())
        ws_fares_by_date.cell(row + row_header + 1, 6, i.total_payments.to_float())
        ws_fares_by_date.cell(row + row_header + 1, 7, i.total_fares.to_float())
        row += 1

    # number formats
    for i in range(row_header + 1, row_total + 1):
        if i < row_total:
            ws_fares_by_date.cell(i, 1).number_format = 'mmm dd, yyyy'
        for j in range(2,8):
            ws_fares_by_date.cell(i, j).number_format = '$0.00'

    # apply styles
    ws_fares_by_date.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, 8):
        ws_fares_by_date.column_dimensions[get_column_letter(i)].width = style_colwidth_normal

        for j in range(row_header, row_total+1):
            ws_fares_by_date.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_fares_by_date.cell(j, i).font = style_font_header
                ws_fares_by_date.cell(j, i).alignment = style_alignment_header
                ws_fares_by_date.cell(j, i).fill = style_fill_header
            elif j == row_total:
                ws_fares_by_date.cell(j, i).font = style_font_total
                ws_fares_by_date.cell(j, i).fill = style_fill_total
            else:
                ws_fares_by_date.cell(j, i).font = style_font_normal

    #####
    #### Money Collected by the Drivers
    #####
    ws_money = wb.create_sheet('Driver-collected Money')
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
            ws_money.cell(i, 1).number_format = 'mmm dd, yyyy'
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
    ws_payments = wb.create_sheet('Non-Driver-collected Money')
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
            ws_payments.cell(i, 1).number_format = 'mmm dd, yyyy'
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
    row_total = len(report.driver_reports) + 2

    ws_drivers.cell(row_header, 1, 'Driver')
    ws_drivers.cell(row_header, 2, 'Service Miles')
    ws_drivers.cell(row_header, 3, 'Service Hours')
    ws_drivers.cell(row_header, 4, 'Deadhead Miles')
    ws_drivers.cell(row_header, 5, 'Deadhead Hours')
    ws_drivers.cell(row_header, 6, 'Total Miles')
    ws_drivers.cell(row_header, 7, 'Total Hours')

    ws_drivers.cell(row_total, 1, 'TOTAL')
    ws_drivers.cell(row_total, 2, report.driver_reports_total.totals.service_miles)
    ws_drivers.cell(row_total, 3, report.driver_reports_total.totals.service_hours)
    ws_drivers.cell(row_total, 4, report.driver_reports_total.totals.deadhead_miles)
    ws_drivers.cell(row_total, 5, report.driver_reports_total.totals.deadhead_hours)
    ws_drivers.cell(row_total, 6, report.driver_reports_total.totals.total_miles)
    ws_drivers.cell(row_total, 7, report.driver_reports_total.totals.total_hours)

    for i in range(0, len(report.driver_reports)):
        ws_drivers.cell(row_header + i + 1, 1, str(report.driver_reports[i].driver))
        ws_drivers.cell(row_header + i + 1, 2, report.driver_reports[i].totals.service_miles)
        ws_drivers.cell(row_header + i + 1, 3, report.driver_reports[i].totals.service_hours)
        ws_drivers.cell(row_header + i + 1, 4, report.driver_reports[i].totals.deadhead_miles)
        ws_drivers.cell(row_header + i + 1, 5, report.driver_reports[i].totals.deadhead_hours)
        ws_drivers.cell(row_header + i + 1, 6, report.driver_reports[i].totals.total_miles)
        ws_drivers.cell(row_header + i + 1, 7, report.driver_reports[i].totals.total_hours)

    # number formats
    for i in range(row_header + 1, row_header + row_total):
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
        for j in range(row_header, row_header + row_total):
            ws_drivers.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_drivers.cell(j, i).font = style_font_header
                ws_drivers.cell(j, i).alignment = style_alignment_header
                ws_drivers.cell(j, i).fill = style_fill_header
            elif j == row_total:
                ws_drivers.cell(j, i).font = style_font_total
                ws_drivers.cell(j, i).fill = style_fill_total
            else:
                ws_drivers.cell(j, i).font = style_font_normal
                style_fill_driver = PatternFill(fill_type='solid', fgColor=report.driver_reports[j - row_header - 1].driver.get_color())
                ws_drivers.cell(j, i).fill = style_fill_driver

    wb.save(filename=temp_file.name)

    return FileResponse(open(temp_file.name, 'rb'), filename='Transit_Report_' + date_start.strftime('%Y-%m-%d') + '_to_' + date_end.strftime('%Y-%m-%d') + '.xlsx', as_attachment=True)

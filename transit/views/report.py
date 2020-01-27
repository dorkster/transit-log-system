import datetime
import tempfile

from django.http import HttpResponseRedirect
from django.http import FileResponse
from django.shortcuts import render
from django.urls import reverse

from transit.models import Driver, Vehicle, Trip, Shift, TripType, Client
from transit.forms import DatePickerForm

from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter

T_STR = 0
T_FLOAT = 1

class Report():
    class Money():
        def __init__(self, default_value=0):
            self.value = default_value
        def __add__(self, other):
            return Report.Money(self.value + other.value)
        def __str__(self):
            if self.value < 10:
                return '$0.0' + str(self.value)
            elif self.value < 100:
                return '$0.' + str(self.value)
            else:
                val_str = str(self.value)
                return '$' + val_str[0:len(val_str)-2] + '.' + val_str[len(val_str)-2:]
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
        def __init__(self):
            self.date = None
            self.shifts = []
            self.trips = []

            self.by_vehicle = {}
            for i in Vehicle.objects.all():
                self.by_vehicle[i] = Report.ReportSummary()

            self.by_driver = {}
            for i in Driver.objects.filter(is_logged=True):
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

    def __init__(self):
        self.report_all = []
        self.vehicle_reports = []
        self.driver_reports = []
        self.all_vehicles = Report.ReportSummary()
        self.unique_riders = Report.UniqueRiderSummary()
        self.money_trips = []
        self.money_trips_summary = Report.ReportSummary()
        self.report_errors = Report.ReportErrors()

    def load(self, date_start, date_end):
        for day in range(date_start.day, date_end.day+1):
            # TODO what if end month/year is different than start?
            day_date = datetime.date(date_start.year, date_start.month, day)

            report_day = Report.ReportDay()
            report_day.date = day_date

            shifts = Shift.objects.filter(date=day_date)
            for i in shifts:
                if i.start_miles == '' or i.start_time == '' or i.end_miles == '' or i.end_time == '' or not i.driver or not i.vehicle:
                    # skip incomplete shift
                    if i.start_miles != '' or i.start_time != '' or i.end_miles != '' or i.end_time != '':
                        self.report_errors.add(day_date, self.report_errors.SHIFT_INCOMPLETE, error_shift=i)
                    continue

                report_shift = Report.ReportShift()
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
                report_trip.start_miles[T_STR] = shift.start_miles[T_STR][0:len(shift.start_miles[T_STR]) - len(i.start_miles)] + i.start_miles
                report_trip.start_miles[T_FLOAT] = float(report_trip.start_miles[T_STR])
                report_trip.start_time = datetime.datetime.strptime(i.start_time, '%I:%M %p')
                report_trip.end_miles[T_STR] = shift.start_miles[T_STR][0:len(shift.start_miles[T_STR]) - len(i.end_miles)] + i.end_miles
                report_trip.end_miles[T_FLOAT] = float(report_trip.end_miles[T_STR])
                report_trip.end_time = datetime.datetime.strptime(i.end_time, '%I:%M %p')

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
                    self.report_errors.add(day_date, self.report_errors.TRIP_MILES_OOB, error_trip=i)
                if report_trip.start_time < shift.start_time or report_trip.end_time > shift.end_time:
                    self.report_errors.add(day_date, self.report_errors.TRIP_TIME_OOB, error_trip=i)

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
                            self.unique_riders.names.append(Report.UniqueRiderSummary.Rider(i.name, elderly, ambulatory))
                    else:
                        self.unique_riders.names.append(Report.UniqueRiderSummary.Rider(i.name, i.elderly, i.ambulatory))
                    self.unique_riders.names = sorted(self.unique_riders.names)

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

            self.report_all.append(report_day)

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


def report(request, year, month):
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

    report = Report()
    report.load(date_start, date_end)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'month_prev': reverse('report', kwargs={'year':month_prev.year, 'month':month_prev.month}),
        'month_next': reverse('report', kwargs={'year':month_next.year, 'month':month_next.month}),
        'date_picker': date_picker,
        'vehicles': Vehicle.objects.filter(is_logged=True),
        'reports': report.report_all,
        'vehicle_reports': report.vehicle_reports,
        'all_vehicles': report.all_vehicles,
        'driver_reports': report.driver_reports,
        'unique_riders': report.unique_riders,
        'money_trips': report.money_trips,
        'money_trips_summary': report.money_trips_summary,
        'report_errors': report.report_errors,
    }
    return render(request, 'report/view.html', context)

def reportThisMonth(request):
    date = datetime.datetime.now().date()
    return report(request, date.year, date.month)

def reportLastMonth(request):
    date = (datetime.datetime.now().date()).replace(day=1) # first day of this month 
    date = date + datetime.timedelta(days=-1) # last day of the previous month
    return report(request, date.year, date.month)

def reportXLSX(request, year, month):
    date_start = datetime.date(year, month, 1)
    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

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

    ws_riders.cell(row_total, 1, 'TOTAL')
    ws_riders.cell(row_total, 2, report.unique_riders.elderly_ambulatory)
    ws_riders.cell(row_total, 3, report.unique_riders.elderly_nonambulatory)
    ws_riders.cell(row_total, 4, report.unique_riders.nonelderly_ambulatory)
    ws_riders.cell(row_total, 5, report.unique_riders.nonelderly_nonambulatory)
    ws_riders.cell(row_total, 6, report.unique_riders.unknown)

    row_header_riders = 4
    for i in range(row_header_riders, row_header_riders + len(report.unique_riders.names) + 1):
        ws_riders.merge_cells(start_row=i, start_column=1, end_row=i, end_column=2)
        if i > row_header_riders:
            ws_riders.cell(i, 3).number_format = 'BOOLEAN'
            ws_riders.cell(i, 4).number_format = 'BOOLEAN'

    ws_riders.cell(row_header_riders, 1, 'Name')
    ws_riders.cell(row_header_riders, 3, 'Elderly')
    ws_riders.cell(row_header_riders, 4, 'Ambulatory')

    for i in range(0, len(report.unique_riders.names)):
        ws_riders.cell(row_header_riders + i + 1, 1, report.unique_riders.names[i].name)
        ws_riders.cell(row_header_riders + i + 1, 3, report.unique_riders.names[i].elderly)
        ws_riders.cell(row_header_riders + i + 1, 4, report.unique_riders.names[i].ambulatory)

    # apply styles
    ws_riders.row_dimensions[row_header].height = style_rowheight_header
    ws_riders.row_dimensions[row_header_riders].height = style_rowheight_header
    for i in range(1, 7):
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
    for i in range(1, 5):
        for j in range(row_header_riders, row_header_riders + len(report.unique_riders.names) + 1):
            ws_riders.cell(j, i).border = style_border_normal
            if j == row_header_riders:
                ws_riders.cell(j, i).font = style_font_header
                ws_riders.cell(j, i).alignment = style_alignment_header
                ws_riders.cell(j, i).fill = style_fill_header
            else:
                ws_riders.cell(j, i).font = style_font_normal

    #####
    #### Money Collected
    #####
    ws_money = wb.create_sheet('Money Collected')
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

    return FileResponse(open(temp_file.name, 'rb'), filename='Transit_Report_' + date_start.strftime('%Y-%m') + '.xlsx', as_attachment=True)

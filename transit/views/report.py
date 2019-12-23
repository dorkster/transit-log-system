import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from transit.models import Driver, Vehicle, Trip, Shift, TripType, Client
from transit.forms import DatePickerForm

def report(request, year, month):
    class UniqueRider:
        def __init__(self, name, elderly=None, ambulatory=None):
            self.name = name
            self.elderly = elderly
            self.ambulatory = ambulatory

        def __lt__(self, other):
            return self.name < other.name

    class ReportVehicle():
        class Day():
            def __init__(self):
                self.date = None
                self.service_miles = ''
                self.service_hours = ''
                self.deadhead_miles = ''
                self.deadhead_hours = ''
                self.pmt = ''
                self.fuel = ''
                self.trip_types = {}

        def __init__(self):
            self.vehicle = Vehicle()
            self.days = []
            self.total = self.Day()
            self.errors = []
    
    class DriverSummary():
        def __init__(self):
            self.service_miles = 0
            self.service_hours = 0
            self.deadhead_miles = 0
            self.deadhead_hours = 0
            self.total_miles = 0
            self.total_hours = 0

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

    unique_riders = []

    triptypes = TripType.objects.all()

    vehicle_totals = ReportVehicle.Day()
    vehicle_total_service_miles = 0
    vehicle_total_service_hours = 0
    vehicle_total_deadhead_miles = 0
    vehicle_total_deadhead_hours = 0
    vehicle_total_pmt = 0
    vehicle_total_fuel = 0
    for i in triptypes:
        vehicle_totals.trip_types[str(i)] = 0

    driver_summaries = {}
    for driver in Driver.objects.filter(is_logged=True):
        driver_summaries[str(driver)] = DriverSummary()

    vehicles = Vehicle.objects.filter(is_logged=True)
    vehicle_list = []
    for vehicle in vehicles:
        rv = ReportVehicle()
        rv.vehicle = vehicle

        total_service_miles = 0
        total_service_hours = 0
        total_deadhead_miles = 0
        total_deadhead_hours = 0
        total_pmt = 0
        total_fuel = 0

        for i in triptypes:
            rv.total.trip_types[str(i)] = 0

        for day in range(date_start.day, date_end.day+1):
            day_date = datetime.date(year, month, day)
            day_shifts = Shift.objects.filter(date=day_date, vehicle=vehicle)
            day_trips = Trip.objects.filter(date=day_date, vehicle=vehicle, status=Trip.STATUS_NORMAL)

            rv_day = ReportVehicle.Day()
            rv_day.date = day_date
            for i in triptypes:
                rv_day.trip_types[str(i)] = 0

            shift_miles_start = 0
            shift_miles_end = 0
            shift_time_start = 0
            shift_time_end = 0
            shift_fuel = 0
            shift_data_list = []
            for shift in day_shifts:
                error_str = shift.get_error_str()
                if error_str != '':
                    rv.errors.append(error_str)

                shift_data = shift.get_parsed_log_data()
                if shift_data is not None:
                    shift_data_list.append(shift_data)

                    last_index = len(shift_data_list)-1
                    if shift_data.start_miles < shift_data_list[shift_miles_start].start_miles:
                        shift_miles_start = last_index
                    if shift_data.end_miles > shift_data_list[shift_miles_end].end_miles:
                        shift_miles_end = last_index
                    if shift_data.start_time < shift_data_list[shift_time_start].start_time:
                        shift_time_start = last_index
                    if shift_data.end_time > shift_data_list[shift_time_end].end_time:
                        shift_time_end = last_index

                    shift_fuel += shift_data.fuel

            trip_miles_start = 0
            trip_miles_end = 0
            trip_time_start = 0
            trip_time_end = 0
            trip_pmt = 0
            trip_data_list = []
            for trip in day_trips:
                error_str = trip.get_error_str()
                if error_str != '':
                    rv.errors.append(error_str)

                if not shift_data_list:
                    continue

                trip_data = trip.get_parsed_log_data(shift_data_list[shift_miles_start].start_miles_str)
                if trip_data is not None:
                    trip_data_list.append(trip_data)

                    last_index = len(trip_data_list)-1
                    if trip_data.start_miles < trip_data_list[trip_miles_start].start_miles:
                        trip_miles_start = last_index
                    if trip_data.end_miles > trip_data_list[trip_miles_end].end_miles:
                        trip_miles_end = last_index
                    if trip_data.start_time < trip_data_list[trip_time_start].start_time:
                        trip_time_start = last_index
                    if trip_data.end_time > trip_data_list[trip_time_end].end_time:
                        trip_time_end = last_index

                    trip_pmt += (trip_data.end_miles - trip_data.start_miles)
                    if trip.trip_type != None:
                        rv_day.trip_types[str(trip.trip_type)] += 1

                    ur_index = None
                    for i in range(len(unique_riders)):
                        if unique_riders[i].name == trip.name:
                            ur_index = i
                            if unique_riders[i].elderly is None:
                                unique_riders[i].elderly = trip.elderly
                            if unique_riders[i].ambulatory is None:
                                unique_riders[i].ambulatory = trip.ambulatory

                    if ur_index is None:
                        unique_riders.append(UniqueRider(trip.name, trip.elderly, trip.ambulatory))

            if not shift_data_list or not trip_data_list:
                continue

            service_miles = shift_data_list[shift_miles_end].end_miles - shift_data_list[shift_miles_start].start_miles
            service_hours = (shift_data_list[shift_time_end].end_time - shift_data_list[shift_time_start].start_time).seconds / 60 / 60
            deadhead_miles = (trip_data_list[trip_miles_start].start_miles - shift_data_list[shift_miles_start].start_miles) + (shift_data_list[shift_miles_end].end_miles - trip_data_list[trip_miles_end].end_miles)
            deadhead_hours = ((trip_data_list[trip_time_start].start_time - shift_data_list[shift_time_start].start_time).seconds + (shift_data_list[shift_time_end].end_time - trip_data_list[trip_time_end].end_time).seconds) / 60 / 60

            rv_day.service_miles = '{:.1f}'.format(service_miles)
            rv_day.service_hours = '{:.2f}'.format(service_hours).rstrip('0').rstrip('.')
            rv_day.deadhead_miles = '{:.1f}'.format(deadhead_miles)
            rv_day.deadhead_hours = '{:.2f}'.format(deadhead_hours).rstrip('0').rstrip('.')
            rv_day.pmt = '{:.1f}'.format(trip_pmt)
            rv_day.fuel = '{:.1f}'.format(shift_fuel).rstrip('0').rstrip('.')

            total_service_miles += service_miles
            total_service_hours += service_hours
            total_deadhead_miles += deadhead_miles
            total_deadhead_hours += deadhead_hours
            total_pmt += trip_pmt
            total_fuel += shift_fuel
            for i in triptypes:
                rv.total.trip_types[str(i)] += rv_day.trip_types[str(i)]
                vehicle_totals.trip_types[str(i)] += rv_day.trip_types[str(i)]

            vehicle_total_service_miles += service_miles
            vehicle_total_service_hours += service_hours
            vehicle_total_deadhead_miles += deadhead_miles
            vehicle_total_deadhead_hours += deadhead_hours
            vehicle_total_pmt += trip_pmt
            vehicle_total_fuel += shift_fuel

            for shift in day_shifts:
                shift_data = shift.get_parsed_log_data()
                if shift_data:
                    driver_summaries[str(shift.driver)].service_miles += (shift_data.end_miles - shift_data.start_miles)
                    driver_summaries[str(shift.driver)].service_hours += ((shift_data.end_time - shift_data.start_time).seconds / 60 / 60)
                    shift_trips = shift.get_start_end_trips()
                    if shift_trips is not None:
                        driver_summaries[str(shift.driver)].deadhead_miles += (shift_trips[0].start_miles - shift_data.start_miles) + (shift_data.end_miles - shift_trips[2].end_miles)
                        driver_summaries[str(shift.driver)].deadhead_hours += ((shift_trips[1].start_time - shift_data.start_time) + (shift_data.end_time - shift_trips[3].end_time)).seconds / 60 / 60

            for i in driver_summaries:
                driver_summaries[i].total_miles = driver_summaries[i].service_miles + driver_summaries[i].deadhead_miles
                driver_summaries[i].total_hours = driver_summaries[i].service_hours + driver_summaries[i].deadhead_hours

            rv.days.append(rv_day)

        rv.total.service_miles = '{:.1f}'.format(total_service_miles)
        rv.total.service_hours = '{:.2f}'.format(total_service_hours).rstrip('0').rstrip('.')
        rv.total.deadhead_miles = '{:.1f}'.format(total_deadhead_miles)
        rv.total.deadhead_hours = '{:.2f}'.format(total_deadhead_hours).rstrip('0').rstrip('.')
        rv.total.pmt = '{:.1f}'.format(total_pmt)
        rv.total.fuel = '{:.1f}'.format(total_fuel).rstrip('0').rstrip('.')
        vehicle_list.append(rv)

    vehicle_totals.service_miles = '{:.1f}'.format(vehicle_total_service_miles)
    vehicle_totals.service_hours = '{:.2f}'.format(vehicle_total_service_hours).rstrip('0').rstrip('.')
    vehicle_totals.deadhead_miles = '{:.1f}'.format(vehicle_total_deadhead_miles)
    vehicle_totals.deadhead_hours = '{:.2f}'.format(vehicle_total_deadhead_hours).rstrip('0').rstrip('.')
    vehicle_totals.pmt = '{:.1f}'.format(vehicle_total_pmt)
    vehicle_totals.fuel = '{:.1f}'.format(vehicle_total_fuel).rstrip('0').rstrip('.')

    no_vehicle_errors = []
    for day in range(date_start.day, date_end.day+1):
        day_date = datetime.date(year, month, day)
        no_vehicle_trips = Trip.objects.filter(date=day_date, vehicle=None, status=Trip.STATUS_NORMAL)
        for trip in no_vehicle_trips:
            error_str = trip.get_error_str()
            if error_str != '':
                no_vehicle_errors.append(error_str)

    unique_riders.sort()

    # try to fetch missing unique rider data from list of clients
    for i in unique_riders:
        if i.elderly == None or i.ambulatory == None:
            client_query = Client.objects.filter(name=i.name)
            if len(client_query) > 0:
                client = client_query[0]
                if i.elderly == None and client.elderly != None:
                    i.elderly = client.elderly
                if i.ambulatory == None and client.ambulatory != None:
                    i.ambulatory = client.ambulatory

    ur_elderly_ambulatory = 0
    ur_elderly_nonambulatory = 0
    ur_nonelderly_ambulatory = 0
    ur_nonelderly_nonambulatory = 0
    ur_unknown = 0

    for i in unique_riders:
        if i.elderly and i.ambulatory:
            ur_elderly_ambulatory += 1
        elif i.elderly and i.ambulatory == False:
            ur_elderly_nonambulatory +=1
        elif i.elderly == False and i.ambulatory:
            ur_nonelderly_ambulatory +=1
        elif i.elderly == False and i.ambulatory == False:
            ur_nonelderly_nonambulatory +=1
        else:
            ur_unknown +=1

    money_trips = []

    for day in range(date_start.day, date_end.day+1):
        day_date = datetime.date(year, month, day)
        day_trips = Trip.objects.filter(date=day_date)
        for trip in day_trips:
            if trip.collected_cash > 0 or trip.collected_check > 0:
                money_trips.append(trip)

    total_collected_cash = 0
    total_collected_check = 0
    total_collected_cash_str = '0.00'
    total_collected_check_str = '0.00'

    for i in money_trips:
        total_collected_cash += i.collected_cash
        total_collected_check += i.collected_check

    if total_collected_cash > 0:
        s = str(total_collected_cash)
        total_collected_cash_str = s[:len(s)-2] + '.' + s[len(s)-2:]

    if total_collected_check > 0:
        s = str(total_collected_check)
        total_collected_check_str = s[:len(s)-2] + '.' + s[len(s)-2:]

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'month_prev': reverse('report', kwargs={'year':month_prev.year, 'month':month_prev.month}),
        'month_next': reverse('report', kwargs={'year':month_next.year, 'month':month_next.month}),
        'date_picker': date_picker,
        'vehicles': vehicle_list,
        'no_vehicle_errors': no_vehicle_errors,
        'triptypes': triptypes,
        'unique_riders': unique_riders,
        'ur_elderly_ambulatory': ur_elderly_ambulatory,
        'ur_elderly_nonambulatory': ur_elderly_nonambulatory,
        'ur_nonelderly_ambulatory': ur_nonelderly_ambulatory,
        'ur_nonelderly_nonambulatory': ur_nonelderly_nonambulatory,
        'ur_unknown': ur_unknown,
        'money_trips': money_trips,
        'total_collected_cash': total_collected_cash_str,
        'total_collected_check': total_collected_check_str,
        'driver_summaries': driver_summaries,
        'vehicle_combined_totals': vehicle_totals,
    }
    return render(request, 'report/view.html', context)

def reportThisMonth(request):
    date = datetime.datetime.now().date()
    return report(request, date.year, date.month)

def reportLastMonth(request):
    date = (datetime.datetime.now().date()).replace(day=1) # first day of this month 
    date = date + datetime.timedelta(days=-1) # last day of the previous month
    return report(request, date.year, date.month)


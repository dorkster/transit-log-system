import datetime

from django.shortcuts import render
from django.urls import reverse

from transit.models import Driver, Vehicle, Trip, Shift, TripType

def report(request, year, month):
    class ReportVehicle():
        class Day():
            def __init__(self):
                self.date = None
                self.service_miles = ""
                self.service_hours = ""
                self.deadhead_miles = ""
                self.deadhead_hours = ""
                self.pmt = ""
                self.fuel = ""
                self.trip_types = {}

        def __init__(self):
            self.vehicle = Vehicle()
            self.days = []
            self.total = self.Day()
            self.errors = []

    date_start = datetime.date(year, month, 1)
    date_end = date_start
    if date_end.month == 12:
        date_end = date_end.replace(day=31)
    else:
        date_end = datetime.date(year, month+1, 1) + datetime.timedelta(days=-1)

    month_prev = date_start + datetime.timedelta(days=-1)
    month_prev.replace(day=1)
    month_next = date_end + datetime.timedelta(days=1)

    triptypes = TripType.objects.all()

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
            # day_shifts = Shift.objects.filter(date=day_date, vehicle=vehicle).exclude(start_miles="").exclude(end_miles="").exclude(start_time="").exclude(end_time="")
            day_shifts = Shift.objects.filter(date=day_date, vehicle=vehicle)
            day_trips = Trip.objects.filter(date=day_date, vehicle=vehicle, is_canceled=False)

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
                if error_str != "":
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
                if error_str != "":
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
                        rv_day.trip_types[str(trip.trip_type)] = 1

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

            rv.days.append(rv_day)

        rv.total.service_miles = '{:.1f}'.format(total_service_miles)
        rv.total.service_hours = '{:.2f}'.format(total_service_hours).rstrip('0').rstrip('.')
        rv.total.deadhead_miles = '{:.1f}'.format(total_deadhead_miles)
        rv.total.deadhead_hours = '{:.2f}'.format(total_deadhead_hours).rstrip('0').rstrip('.')
        rv.total.pmt = '{:.1f}'.format(total_pmt)
        rv.total.fuel = '{:.1f}'.format(total_fuel).rstrip('0').rstrip('.')
        vehicle_list.append(rv)

    no_vehicle_errors = []
    for day in range(date_start.day, date_end.day+1):
        day_date = datetime.date(year, month, day)
        no_vehicle_trips = Trip.objects.filter(date=day_date, vehicle=None, is_canceled=False)
        for trip in no_vehicle_trips:
            error_str = trip.get_error_str()
            if error_str != "":
                no_vehicle_errors.append(error_str)

    context = {
        'date_start': date_start,
        'date_end': date_end,
        'month_prev': reverse('report', kwargs={'year':month_prev.year, 'month':month_prev.month}),
        'month_next': reverse('report', kwargs={'year':month_next.year, 'month':month_next.month}),
        'vehicles': vehicle_list,
        'no_vehicle_errors': no_vehicle_errors,
        'triptypes': triptypes,
    }
    return render(request, 'report/view.html', context)

def reportThisMonth(request):
    date = datetime.datetime.now().date()
    return report(request, date.year, date.month)

def reportLastMonth(request):
    date = (datetime.datetime.now().date()).replace(day=1) # first day of this month 
    date = date + datetime.timedelta(days=-1) # last day of the previous month
    return report(request, date.year, date.month)


# Copyright © 2019-2021 Justin Jacobs
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

import datetime, uuid
import tempfile

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import FileResponse
from django.urls import reverse
from django.core.paginator import Paginator

from transit.models import Trip, Driver, Vehicle, TripType
from transit.forms import SearchTripsForm

from django.contrib.auth.decorators import permission_required

from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter

from transit.common.util import *

@permission_required(['transit.view_trip'])
def searchGetTrips(request):
    name = request.GET.get('name')
    address = request.GET.get('address')
    destination = request.GET.get('destination')
    driver = request.GET.get('driver')
    vehicle = request.GET.get('vehicle')
    start_year = request.GET.get('start_date_year')
    start_month = request.GET.get('start_date_month')
    start_day = request.GET.get('start_date_day')
    end_year = request.GET.get('end_date_year')
    end_month = request.GET.get('end_date_month')
    end_day = request.GET.get('end_date_day')
    notes = request.GET.get('notes')
    elderly = request.GET.get('elderly')
    ambulatory = request.GET.get('ambulatory')
    trip_type = request.GET.get('trip_type')
    tags = request.GET.get('tags')
    status = request.GET.get('status')

    trips = Trip.objects.all()
    searched = False

    if name:
        searched = True
        trips = trips.filter(name__icontains=name)

    if address:
        searched = True
        trips = trips.filter(address__icontains=address)

    if destination:
        searched = True
        trips = trips.filter(destination__icontains=destination)

    if driver:
        try:
            driver_obj = Driver.objects.get(id=uuid.UUID(driver))
        except:
            driver_obj = None

        if driver_obj:
            searched = True
            trips = trips.filter(driver=driver_obj)

    if vehicle:
        try:
            vehicle_obj = Vehicle.objects.get(id=uuid.UUID(vehicle))
        except:
            vehicle_obj = None

        if vehicle_obj:
            searched = True
            trips = trips.filter(vehicle=vehicle_obj)

    today = datetime.datetime.today()

    start_date = None
    if start_year:
        start_date = datetime.date(year=int(start_year), month=1, day=1)
        if start_month:
            start_date = start_date.replace(month=int(start_month))
        if start_day:
            day = int(start_day)
            if day <= 28:
                start_date = start_date.replace(day=int(start_day))
            else:
                for i in range(28, day+1):
                    try:
                        start_date = start_date.replace(day=i)
                    except:
                        pass
    elif start_month or start_day:
        start_date = datetime.date(year=today.year, month=1, day=1)
        if start_month:
            start_date = start_date.replace(month=int(start_month))
        if start_day:
            day = int(start_day)
            if day <= 28:
                start_date = start_date.replace(day=int(start_day))
            else:
                for i in range(28, day+1):
                    try:
                        start_date = start_date.replace(day=i)
                    except:
                        pass

    if start_date:
        searched = True
        trips = trips.filter(date__gte=start_date)

    end_date = None
    if end_year:
        end_date = datetime.date(year=int(end_year), month=1, day=1)
        if end_month:
            end_date = end_date.replace(month=int(end_month))
        if end_day:
            day = int(end_day)
            if day <= 28:
                end_date = end_date.replace(day=int(end_day))
            else:
                for i in range(28, day+1):
                    try:
                        end_date = end_date.replace(day=i)
                    except:
                        pass
    elif end_month or end_day:
        end_date = datetime.date(year=today.year, month=1, day=1)
        if end_month:
            end_date = end_date.replace(month=int(end_month))
        if end_day:
            day = int(end_day)
            if day <= 28:
                end_date = end_date.replace(day=int(end_day))
            else:
                for i in range(28, day+1):
                    try:
                        end_date = end_date.replace(day=i)
                    except:
                        pass

    if end_date:
        searched = True
        trips = trips.filter(date__lte=end_date)

    if notes:
        searched = True
        trips = trips.filter(note__icontains=notes)

    if elderly:
        searched = True
        if elderly == '0':
            trips = trips.filter(elderly=None)
        elif elderly == '1':
            trips = trips.filter(elderly=True)
        elif elderly == '2':
            trips = trips.filter(elderly=False)

    if ambulatory:
        searched = True
        if ambulatory == '0':
            trips = trips.filter(ambulatory=None)
        elif ambulatory == '1':
            trips = trips.filter(ambulatory=True)
        elif ambulatory == '2':
            trips = trips.filter(ambulatory=False)

    if trip_type:
        try:
            trip_type_obj = TripType.objects.get(id=uuid.UUID(trip_type))
        except:
            trip_type_obj = None

        if trip_type_obj:
            searched = True
            trips = trips.filter(trip_type=trip_type_obj)

    if tags:
        searched = True
        trips = trips.filter(tags__icontains=tags)

    if status:
        searched = True
        if status == '0':
            trips = trips.filter(status=Trip.STATUS_NORMAL)
        elif status == '1':
            trips = trips.filter(status=Trip.STATUS_CANCELED)
        elif status == '2':
            trips = trips.filter(status=Trip.STATUS_NO_SHOW)

    return (searched, trips.order_by('-date', '-sort_index'))

@permission_required(['transit.view_trip'])
def search(request):
    results = searchGetTrips(request)
    searched = results[0]
    trips = results[1]

    results_per_page = 25

    result_pages = Paginator(trips, results_per_page)
    results_paginated = result_pages.get_page(request.GET.get('page'))

    page_ranges = get_paginated_ranges(page=results_paginated, page_range=5, items_per_page=results_per_page)

    form = SearchTripsForm(request.GET)
    context = {
        'form': form,
        'searched': searched,
        'results': results_paginated if searched else Trip.objects.none(),
        'page_ranges': page_ranges,
        'query_string': request.GET.urlencode(),
    }
    return render(request, 'search.html', context=context)

@permission_required(['transit.view_trip'])
def searchExportXLSX(request):
    results = searchGetTrips(request)
    searched = results[0]
    trips = results[1]

    temp_file = tempfile.NamedTemporaryFile()

    wb = Workbook()

    style_font_normal = Font(name='Arial', size=10)
    style_border_normal_side = Side(border_style='thin', color='FF000000')
    style_border_normal = Border(left=style_border_normal_side, right=style_border_normal_side, top=style_border_normal_side, bottom=style_border_normal_side)
    style_colwidth_normal = 13
    style_colwidth_large = style_colwidth_normal * 2
    style_colwidth_xlarge = style_colwidth_normal * 3

    style_font_header = Font(name='Arial', size=10, bold=True)
    style_alignment_header = Alignment(horizontal='center', vertical='center', wrap_text=True)
    style_fill_header = PatternFill(fill_type='solid', fgColor='DFE0E1')
    style_rowheight_header = 25

    style_alignment_date = Alignment(horizontal='left')

    ws_results = wb.active
    ws_results.title = 'Search Results'

    row_header = 1
    trip_count = len(trips)

    ws_results.cell(row_header, 1, 'Date')
    ws_results.cell(row_header, 2, 'Pick up')
    ws_results.cell(row_header, 3, 'Appt. Time')
    ws_results.cell(row_header, 4, 'Name')
    ws_results.cell(row_header, 5, 'Address')
    ws_results.cell(row_header, 6, 'Destination')
    ws_results.cell(row_header, 7, 'Driver')
    ws_results.cell(row_header, 8, 'Vehicle')
    ws_results.cell(row_header, 9, 'Start Miles')
    ws_results.cell(row_header, 10, 'Start Time')
    ws_results.cell(row_header, 11, 'End Miles')
    ws_results.cell(row_header, 12, 'End Time')
    ws_results.cell(row_header, 13, 'Notes')
    ws_results.cell(row_header, 14, 'Trip Type / Tags')
    ws_results.cell(row_header, 15, 'Fare')
    ws_results.cell(row_header, 16, 'Money Collected')
    ws_results.cell(row_header, 17, 'Elderly?')
    ws_results.cell(row_header, 18, 'Ambulatory?')

    for i in range(0, trip_count):
        ws_results.cell(row_header + i + 1, 1, trips[i].date)
        ws_results.cell(row_header + i + 1, 2, trips[i].pick_up_time)
        ws_results.cell(row_header + i + 1, 3, trips[i].appointment_time)
        ws_results.cell(row_header + i + 1, 4, trips[i].name)
        ws_results.cell(row_header + i + 1, 5, trips[i].address)
        ws_results.cell(row_header + i + 1, 6, trips[i].destination)
        if trips[i].driver:
            ws_results.cell(row_header + i + 1, 7, str(trips[i].driver))
        if trips[i].vehicle:
            ws_results.cell(row_header + i + 1, 8, str(trips[i].vehicle))
        ws_results.cell(row_header + i + 1, 9, trips[i].start_miles)
        ws_results.cell(row_header + i + 1, 10, trips[i].start_time)
        ws_results.cell(row_header + i + 1, 11, trips[i].end_miles)
        ws_results.cell(row_header + i + 1, 12, trips[i].end_time)
        ws_results.cell(row_header + i + 1, 13, trips[i].note)
        tags_string = ''
        if trips[i].trip_type:
            tags_string += str(trips[i].trip_type)
            if trips[i].tags:
                tags_string += ' / '
        if trips[i].tags:
            tags_string += trips[i].tags
        ws_results.cell(row_header + i + 1, 14, tags_string)
        ws_results.cell(row_header + i + 1, 15, trips[i].fare / 100)
        ws_results.cell(row_header + i + 1, 16, (trips[i].collected_cash + trips[i].collected_check) / 100)
        ws_results.cell(row_header + i + 1, 17, trips[i].elderly)
        ws_results.cell(row_header + i + 1, 18, trips[i].ambulatory)

    # number formats
    for i in range(row_header + 1, row_header + trip_count + 1):
        ws_results.cell(i, 1).number_format = 'MMM DD, YYYY'
        ws_results.cell(i, 15).number_format = '$0.00'
        ws_results.cell(i, 16).number_format = '$0.00'
        ws_results.cell(i, 17).number_format = 'BOOLEAN'
        ws_results.cell(i, 18).number_format = 'BOOLEAN'

    # apply styles
    ws_results.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, 19):
        if i == 4 or i == 13 or i == 14:
            ws_results.column_dimensions[get_column_letter(i)].width = style_colwidth_large
        elif i == 5 or i == 6:
            ws_results.column_dimensions[get_column_letter(i)].width = style_colwidth_xlarge
        else:
            ws_results.column_dimensions[get_column_letter(i)].width = style_colwidth_normal

        for j in range(row_header, row_header + trip_count + 1):
            trip_index = j - row_header - 1

            ws_results.cell(j, i).border = style_border_normal
            if j == row_header:
                ws_results.cell(j, i).font = style_font_header
                ws_results.cell(j, i).alignment = style_alignment_header
                ws_results.cell(j, i).fill = style_fill_header
            else:
                if i == 1:
                    ws_results.cell(j, i).alignment = style_alignment_date

                ws_results.cell(j, i).font = style_font_normal
                ws_results.cell(j, i).fill = PatternFill(fill_type='solid', fgColor=trips[trip_index].get_driver_color()[0:6])

    wb.save(filename=temp_file.name)

    return FileResponse(open(temp_file.name, 'rb'), filename='Transit_Search.xlsx', as_attachment=True)

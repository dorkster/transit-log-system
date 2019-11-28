import datetime, uuid

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator

from transit.models import Trip, Driver, Vehicle
from transit.forms import SearchTripsForm

def search(request):
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

    result_pages = Paginator(trips, 25)
    result_page = request.GET.get('page')
    if result_page is None:
        result_page = 1
    results_paginated = result_pages.get_page(result_page)

    page_range = 5

    form = SearchTripsForm(request.GET)
    context = {
        'form': form,
        'searched': searched,
        'results': results_paginated if searched else Trip.objects.none(),
        'page_range_start': results_paginated.number - page_range - 1,
        'page_range_end': results_paginated.number + page_range,
        'result_start': ((results_paginated.number - 1) * 25) + 1,
        'result_end': results_paginated.number * 25 if results_paginated.number * 25 < results_paginated.paginator.count else results_paginated.paginator.count,
    }
    return render(request, 'search.html', context=context)

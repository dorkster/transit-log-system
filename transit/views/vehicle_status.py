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

import uuid

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import VehicleIssue, Vehicle, PreTrip, Driver

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import *

@permission_required(['transit.view_vehicle', 'transit.view_vehicleissue', 'transit.view_pretrip'])
def vehicleStatus(request):
    return render(request, 'vehicle/status/view.html', context={})

def ajaxVehicleStatus(request):
    if not request.user.has_perms(['transit.view_vehicle', 'transit.view_vehicleissue', 'transit.view_pretrip']):
        return HttpResponseRedirect(reverse('login_redirect'))

    logged_vehicles = Vehicle.objects.filter(is_logged=True, is_active=True)

    vehicle_data = []
    for vehicle in logged_vehicles:
        issues = VehicleIssue.objects.filter(vehicle=vehicle, status=VehicleIssue.STATUS_OPEN)
        pretrips = list(PreTrip.objects.filter(vehicle=vehicle).order_by('-date', '-inspect_type'))[:10]
        vehicle_data.append({'id': vehicle.id, 'issues': issues, 'pretrips': pretrips})

    context = {
        'logged_vehicles': logged_vehicles,
        'drivers': Driver.objects.filter(is_logged=True, is_active=True),
        'vehicles': logged_vehicles,
        'categories': VehicleIssue.ISSUE_CATEGORIES,
        'priorities': VehicleIssue.PRIORITY_LEVELS,
        'vehicle_data': vehicle_data,
    }
    return render(request, 'vehicle/status/ajax_view.html', context=context)

@permission_required(['transit.view_vehicle', 'transit.view_vehicleissue'])
def vehicleIssueTracker(request):
    return render(request, 'vehicle/issues/view.html', context={})

def ajaxVehicleIssueTracker(request):
    if not request.user.has_perms(['transit.view_vehicle', 'transit.view_vehicleissue']):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_vehicleissue'):
        if request_action == 'toggle_resolved':
            issue = get_object_or_404(VehicleIssue, id=request_id)
            # we can only unset the resolve state here. For setting the resolve state, we redirect to the edit page
            if issue.status == VehicleIssue.STATUS_RESOLVED:
                issue.status = VehicleIssue.STATUS_OPEN
                issue.resolution_notes = ''
                issue.save()
                log_event(request, LoggedEventAction.STATUS, LoggedEventModel.VEHICLE_ISSUE, str(issue))
        elif request_action == 'priority_up':
            issue = get_object_or_404(VehicleIssue, id=request_id)
            if issue.priority < VehicleIssue.PRIORITY_HIGH:
                issue.priority += 1
            issue.save()
            log_event(request, LoggedEventAction.EDIT, LoggedEventModel.VEHICLE_ISSUE, str(issue))
        elif request_action == 'priority_down':
            issue = get_object_or_404(VehicleIssue, id=request_id)
            if issue.priority > VehicleIssue.PRIORITY_LOW:
                issue.priority -= 1
            issue.save()
            log_event(request, LoggedEventAction.EDIT, LoggedEventModel.VEHICLE_ISSUE, str(issue))
    if request_action == 'filter_status':
        request.session['vehicle_status_filter_status'] = request_data
    elif request_action == 'filter_driver':
        request.session['vehicle_status_filter_driver'] = request_data
    elif request_action == 'filter_vehicle':
        request.session['vehicle_status_filter_vehicle'] = request_data
    elif request_action == 'filter_category':
        request.session['vehicle_status_filter_category'] = request_data
    elif request_action == 'filter_priority':
        request.session['vehicle_status_filter_priority'] = request_data
    elif request_action == 'filter_reset':
        request.session['vehicle_status_filter_driver'] = ''
        request.session['vehicle_status_filter_vehicle'] = ''
        request.session['vehicle_status_filter_category'] = ''
        request.session['vehicle_status_filter_priority'] = ''

    filter_status = request.session.get('vehicle_status_filter_status', '')
    filter_driver = request.session.get('vehicle_status_filter_driver', '')
    filter_vehicle = request.session.get('vehicle_status_filter_vehicle', '')
    filter_category = request.session.get('vehicle_status_filter_category', '')
    filter_priority = request.session.get('vehicle_status_filter_priority', '')

    vehicle_issues = VehicleIssue.objects.all()

    issue_counts = []
    for status_level in VehicleIssue.STATUS_LEVELS:
        issue_counts.append(vehicle_issues.filter(status=status_level[0]).count())

    filter_status_level = VehicleIssue.STATUS_OPEN
    if filter_status != '':
        filter_status_level = int(filter_status)
        vehicle_issues = vehicle_issues.filter(status=filter_status_level)

    # don't count resolved issues towards filter count
    issue_unfiltered_count = vehicle_issues.count()

    if filter_driver != '':
        vehicle_issues = vehicle_issues.filter(driver__id=filter_driver)
    if filter_vehicle != '':
        vehicle_issues = vehicle_issues.filter(vehicle__id=filter_vehicle)
    if filter_category != '':
        vehicle_issues = vehicle_issues.filter(category=int(filter_category))
    if filter_priority != '':
        vehicle_issues = vehicle_issues.filter(priority=int(filter_priority))

    if filter_status_level == VehicleIssue.STATUS_RESOLVED:
        vehicle_issues = vehicle_issues.order_by('-date')
    else:
        vehicle_issues = vehicle_issues.order_by('-priority', '-date')

    issue_filtered_count = vehicle_issues.count()

    issues_per_page = 25
    issue_pages = Paginator(vehicle_issues, issues_per_page)
    issues_paginated = issue_pages.get_page(request.GET.get('issue_page'))
    issue_page_ranges = get_paginated_ranges(page=issues_paginated, page_range=5, items_per_page=issues_per_page)

    logged_vehicles = Vehicle.objects.filter(is_logged=True, is_active=True)

    context = {
        'vehicle_issues': issues_paginated,
        'issue_page_ranges': issue_page_ranges,
        'filter_status': VehicleIssue.STATUS_OPEN if filter_status == '' else int(filter_status),
        'filter_driver': None if filter_driver == '' else Driver.objects.get(id=filter_driver),
        'filter_vehicle': None if filter_vehicle == '' else Vehicle.objects.get(id=filter_vehicle),
        'filter_category': None if filter_category == '' else int(filter_category),
        'filter_priority': None if filter_priority == '' else int(filter_priority),
        'is_filtered': (filter_driver != '' or filter_vehicle != '' or filter_category != '' or filter_priority != ''),
        'issue_filtered_count': issue_filtered_count,
        'issue_unfiltered_count': issue_unfiltered_count,
        'drivers': Driver.objects.filter(is_logged=True, is_active=True),
        'vehicles': logged_vehicles,
        'categories': VehicleIssue.ISSUE_CATEGORIES,
        'priorities': VehicleIssue.PRIORITY_LEVELS,
        'issue_counts': issue_counts,
    }
    return render(request, 'vehicle/issues/ajax_view.html', context=context)

@permission_required(['transit.view_vehicle', 'transit.view_pretrip'])
def vehiclePreTripLog(request):
    return render(request, 'vehicle/pretrip_log/view.html', context={})

def ajaxVehiclePreTripLog(request):
    if not request.user.has_perms(['transit.view_vehicle', 'transit.view_pretrip']):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    pretrips_per_page = 50
    pretrip_pages = Paginator(list(PreTrip.objects.all().order_by('-date', '-inspect_type')), pretrips_per_page)
    pretrips_paginated = pretrip_pages.get_page(request.GET.get('pretrip_page'))
    pretrip_page_ranges = get_paginated_ranges(page=pretrips_paginated, page_range=5, items_per_page=pretrips_per_page)

    logged_vehicles = Vehicle.objects.filter(is_logged=True, is_active=True)

    context = {
        'pretrips': pretrips_paginated,
        'pretrip_page_ranges': pretrip_page_ranges,
        'drivers': Driver.objects.filter(is_logged=True, is_active=True),
        'vehicles': logged_vehicles,
    }
    return render(request, 'vehicle/pretrip_log/ajax_view.html', context=context)


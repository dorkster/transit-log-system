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

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q

from transit.models import VehicleIssue
from transit.forms import EditVehicleIssueForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel, Driver

def vehicleIssueCreate(request):
    vehicle_issue = VehicleIssue()
    return vehicleIssueCreateEditCommon(request, vehicle_issue, is_new=True)

def vehicleIssueEdit(request, id):
    vehicle_issue = get_object_or_404(VehicleIssue, id=id)
    return vehicleIssueCreateEditCommon(request, vehicle_issue, is_new=False)

@permission_required(['transit.change_vehicleissue'])
def vehicleIssueCreateEditCommon(request, vehicle_issue, is_new):
    if request.method == 'POST':
        form = EditVehicleIssueForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-status'))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-issue-delete', kwargs={'id':vehicle_issue.id}))

        if vehicle_issue.driver:
            form.fields['driver'].queryset = Driver.objects.filter(Q(is_active=True, is_logged=True) | Q(id=vehicle_issue.driver.id))

        if form.is_valid():
            if is_new:
                vehicle_issue.date = datetime.datetime.now().date()

            vehicle_issue.driver = form.cleaned_data['driver']
            vehicle_issue.vehicle = form.cleaned_data['vehicle']
            vehicle_issue.description = form.cleaned_data['description']
            vehicle_issue.priority = form.cleaned_data['priority']
            vehicle_issue.category = form.cleaned_data['category']
            if not is_new:
                vehicle_issue.is_resolved = form.cleaned_data['is_resolved']
            vehicle_issue.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.VEHICLE_ISSUE, str(vehicle_issue))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.VEHICLE_ISSUE, str(vehicle_issue))

            return HttpResponseRedirect(reverse('vehicle-status'))
    else:
        initial = {
            'driver': vehicle_issue.driver,
            'vehicle': vehicle_issue.vehicle,
            'description': vehicle_issue.description,
            'priority': vehicle_issue.priority,
            'category': vehicle_issue.category,
            'is_resolved': vehicle_issue.is_resolved,
        }
        form = EditVehicleIssueForm(initial=initial)
        if vehicle_issue.driver:
            form.fields['driver'].queryset = Driver.objects.filter(Q(is_active=True, is_logged=True) | Q(id=vehicle_issue.driver.id))

    context = {
        'form': form,
        'vehicle_issue': vehicle_issue,
        'is_new': is_new,
    }

    return render(request, 'vehicle/issues/edit.html', context)

@permission_required('transit.delete_vehicleissue')
def vehicleIssueDelete(request, id):
    vehicle_issue = get_object_or_404(VehicleIssue, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-issue-edit', kwargs={'id':id}))

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.VEHICLE_ISSUE, str(vehicle_issue))

        vehicle_issue.delete()
        return HttpResponseRedirect(reverse('vehicle-status'))

    context = {
        'model': vehicle_issue,
    }

    return render(request, 'model_delete.html', context)


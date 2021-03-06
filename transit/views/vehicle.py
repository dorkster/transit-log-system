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

import uuid
import json

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Vehicle, Shift, PreTrip, VehicleIssue
from transit.forms import EditVehicleForm, vehicleMaintainForm, vehiclePreTripForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_vehicle'])
def vehicleList(request):
    context = {
        'vehicle': Vehicle.objects.all(),
    }
    return render(request, 'vehicle/list.html', context=context)

def vehicleCreate(request):
    vehicle = Vehicle()
    return vehicleCreateEditCommon(request, vehicle, is_new=True)

def vehicleEdit(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)
    return vehicleCreateEditCommon(request, vehicle, is_new=False)

@permission_required(['transit.change_vehicle'])
def vehicleCreateEditCommon(request, vehicle, is_new):
    if is_new == True:
        query = Vehicle.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_vehicle = query[0]
            vehicle.sort_index = last_vehicle.sort_index + 1
        else:
            vehicle.sort_index = 0

    if request.method == 'POST':
        form = EditVehicleForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#vehicle_' + str(vehicle.id)
            return HttpResponseRedirect(reverse('vehicles') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-delete', kwargs={'id':vehicle.id}))

        if form.is_valid():
            vehicle.name = form.cleaned_data['name']
            vehicle.is_logged = form.cleaned_data['is_logged']
            vehicle.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.VEHICLE, str(vehicle))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.VEHICLE, str(vehicle))

            return HttpResponseRedirect(reverse('vehicles') + '#vehicle_' + str(vehicle.id))
    else:
        initial = {
            'name': vehicle.name,
            'is_logged': vehicle.is_logged,
        }
        form = EditVehicleForm(initial=initial)

    context = {
        'form': form,
        'vehicle': vehicle,
        'is_new': is_new,
    }

    return render(request, 'vehicle/edit.html', context)

@permission_required('transit.delete_vehicle')
def vehicleDelete(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-edit', kwargs={'id':id}))

        query = Vehicle.objects.all()
        for i in query:
            if i.sort_index > vehicle.sort_index:
                i.sort_index -= 1;
                i.save()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.VEHICLE, str(vehicle))

        vehicle.delete()
        return HttpResponseRedirect(reverse('vehicles'))

    context = {
        'model': vehicle,
    }

    return render(request, 'model_delete.html', context)

def ajaxVehicleList(request):
    if not request.user.has_perm('transit.view_vehicle'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_vehicle'):
        if request_action == 'mv':
            vehicle = get_object_or_404(Vehicle, id=request_id)
            original_index = vehicle.sort_index
            vehicle.sort_index = -1

            # "remove" the selected item by shifting everything below it up by 1
            below_items = Vehicle.objects.filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(Vehicle, id=request_data)
                if vehicle.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the item at the new index by shifting everything below it down by 1
            below_items = Vehicle.objects.filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            vehicle.sort_index = new_index
            vehicle.save()

    vehicles = Vehicle.objects.all()
    return render(request, 'vehicle/ajax_list.html', {'vehicles': vehicles})

@permission_required(['transit.change_vehicle'])
def vehicleMaintainEdit(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)

    if request.method == 'POST':
        form = vehicleMaintainForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-status'))

        if form.is_valid():
            vehicle.oil_change_miles = form.cleaned_data['oil_change_miles']
            vehicle.inspection_date = form.cleaned_data['inspection_date']
            vehicle.save()

            log_event(request, LoggedEventAction.EDIT, LoggedEventModel.VEHICLE_MAINTAIN, str(vehicle))

            return HttpResponseRedirect(reverse('vehicle-status'))
    else:
        initial = {
            'oil_change_miles': vehicle.oil_change_miles,
            'inspection_date': vehicle.inspection_date,
        }
        form = vehicleMaintainForm(initial=initial)

    context = {
        'form': form,
        'vehicle': vehicle,
    }

    return render(request, 'vehicle/maintain.html', context)

@permission_required(['transit.add_pretrip'])
def vehiclePreTripCreate(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)

    # Pretrip was already logged, return to the schedule
    if len(PreTrip.objects.filter(shift_id=shift_id)) > 0:
        return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

    if request.method == 'POST':
        form = vehiclePreTripForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

        if form.is_valid():
            pretrip = PreTrip()
            pretrip.date = shift.date
            pretrip.driver = shift.driver
            pretrip.vehicle = shift.vehicle
            pretrip.shift_id = shift_id

            if form.cleaned_data['checklist'] != '':
                cl = json.loads(form.cleaned_data['checklist'])
                pretrip.cl_fluids = cl['cl_fluids']['status']
                pretrip.cl_engine = cl['cl_engine']['status']
                pretrip.cl_headlights = cl['cl_headlights']['status']
                pretrip.cl_hazards = cl['cl_hazards']['status']
                pretrip.cl_directional = cl['cl_directional']['status']
                pretrip.cl_markers = cl['cl_markers']['status']
                pretrip.cl_windshield = cl['cl_windshield']['status']
                pretrip.cl_glass = cl['cl_glass']['status']
                pretrip.cl_mirrors = cl['cl_mirrors']['status']
                pretrip.cl_doors = cl['cl_doors']['status']
                pretrip.cl_tires = cl['cl_tires']['status']
                pretrip.cl_leaks = cl['cl_leaks']['status']
                pretrip.cl_body = cl['cl_body']['status']
                pretrip.cl_registration = cl['cl_registration']['status']
                pretrip.cl_wheelchair = cl['cl_wheelchair']['status']
                pretrip.cl_mechanical = cl['cl_mechanical']['status']
                pretrip.cl_interior = cl['cl_interior']['status']

                pretrip.save()
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.PRETRIP, str(pretrip))

                # open vehicle issues as needed
                for key in cl:
                    if cl[key]['status'] == 1 and cl[key]['issue'] != "":
                        issue = VehicleIssue()
                        issue.date = shift.date
                        issue.driver = shift.driver
                        issue.vehicle = shift.vehicle
                        issue.description = cl[key]['issue']
                        issue.priority = cl[key]['issue_prio']
                        issue.category = issue.get_category_from_checklist(key)
                        issue.pretrip = pretrip
                        issue.pretrip_field = key
                        issue.save()
                        log_event(request, LoggedEventAction.CREATE, LoggedEventModel.VEHICLE_ISSUE, str(issue))

                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
    else:
        form = vehiclePreTripForm()

    context = {
        'form': form,
        'shift': shift,
        'checklist': PreTrip.CHECKLIST,
    }
    return render(request, 'vehicle/pretrip.html', context=context)

@permission_required('transit.delete_pretrip')
def vehiclePreTripDelete(request, id):
    pretrip = get_object_or_404(PreTrip, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-status'))

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.PRETRIP, str(pretrip))

        pretrip.delete()
        return HttpResponseRedirect(reverse('vehicle-status'))

    context = {
        'model': pretrip,
    }

    return render(request, 'model_delete.html', context)


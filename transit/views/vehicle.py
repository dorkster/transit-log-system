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
import json

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Vehicle, Shift, PreTrip, VehicleIssue
from transit.forms import EditVehicleForm, vehicleMaintainForm, vehiclePreTripForm, vehiclePreTripDeleteForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import move_item_in_queryset

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
        if query.count() > 0:
            vehicle.sort_index = query[0].sort_index + 1
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
            vehicle.is_active = form.cleaned_data['is_active']
            vehicle.notif_level = form.cleaned_data['notif_level']
            vehicle.description = form.cleaned_data['description']
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
            'is_active': vehicle.is_active,
            'notif_level': vehicle.notif_level,
            'description': vehicle.description,
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
            move_item_in_queryset(request_id, request_data, Vehicle.objects.all())

    vehicles = Vehicle.objects.all()
    return render(request, 'vehicle/ajax_list.html', {'vehicles': vehicles})

@permission_required(['transit.change_vehicle'])
def vehicleMaintainEdit(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)

    anchor = "#vehicle_" + str(vehicle.id)

    if request.method == 'POST':
        form = vehicleMaintainForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-status') + anchor)

        if form.is_valid():
            vehicle.oil_change_miles = form.cleaned_data['oil_change_miles']
            vehicle.inspection_date = form.cleaned_data['inspection_date']
            vehicle.maintainence_notes = form.cleaned_data['maintainence_notes']
            vehicle.save()

            log_event(request, LoggedEventAction.EDIT, LoggedEventModel.VEHICLE_MAINTAIN, str(vehicle))

            return HttpResponseRedirect(reverse('vehicle-status') + anchor)
    else:
        initial = {
            'oil_change_miles': vehicle.oil_change_miles,
            'inspection_date': vehicle.inspection_date,
            'maintainence_notes': vehicle.maintainence_notes,
        }
        form = vehicleMaintainForm(initial=initial)

    context = {
        'form': form,
        'vehicle': vehicle,
    }

    return render(request, 'vehicle/maintain.html', context)

@permission_required(['transit.add_pretrip'])
def vehiclePreTripCreate(request, shift_id):
    return vehiclePreTripCreateCommon(request, inspect_type=PreTrip.TYPE_PRE, shift_id=shift_id, vehicle_id=None)

@permission_required(['transit.add_pretrip'])
def vehiclePreTripCreatePost(request, shift_id):
    return vehiclePreTripCreateCommon(request, inspect_type=PreTrip.TYPE_POST, shift_id=shift_id, vehicle_id=None)

@permission_required(['transit.add_pretrip'])
def vehiclePreTripCreateNoShift(request, vehicle_id):
    return vehiclePreTripCreateCommon(request, inspect_type=PreTrip.TYPE_NO_SHIFT, shift_id=None, vehicle_id=vehicle_id)

@permission_required(['transit.add_pretrip'])
def vehiclePreTripCreateCommon(request, inspect_type, shift_id, vehicle_id):
    anchor = ''

    if shift_id:
        shift = get_object_or_404(Shift, id=shift_id)
        pretrip_date = shift.date
        pretrip_driver = shift.driver
        pretrip_vehicle = shift.vehicle

        # Pretrip was already logged, return to the schedule
        if inspect_type != PreTrip.TYPE_NO_SHIFT and PreTrip.objects.filter(shift_id=shift_id, inspect_type=inspect_type).count() > 0:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
    elif vehicle_id:
        shift = None
        pretrip_date = datetime.date.today()
        pretrip_driver = None
        pretrip_vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        if pretrip_vehicle:
            anchor = "#vehicle_" + str(pretrip_vehicle.id)
    else:
        return HttpResponseRedirect(reverse('vehicle-status'))

    if request.method == 'POST':
        form = vehiclePreTripForm(request.POST)

        if 'cancel' in request.POST:
            if shift_id:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':pretrip_date.year, 'month':pretrip_date.month, 'day':pretrip_date.day}))
            else:
                return HttpResponseRedirect(reverse('vehicle-status') + anchor)

        if form.is_valid():
            pretrip = PreTrip()
            pretrip.date = pretrip_date
            pretrip.vehicle = pretrip_vehicle

            if pretrip.vehicle:
                anchor = "#vehicle_" + str(pretrip.vehicle)

            pretrip.inspect_type = inspect_type

            if pretrip_driver:
                pretrip.driver = pretrip_driver
            else:
                pretrip.driver = form.cleaned_data['driver']

            if shift_id:
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
                        issue.date = pretrip.date
                        issue.driver = pretrip.driver
                        issue.vehicle = pretrip.vehicle
                        issue.description = cl[key]['issue']
                        issue.priority = cl[key]['issue_prio']
                        issue.category = issue.get_category_from_checklist(key)
                        issue.pretrip = pretrip
                        issue.pretrip_field = key
                        issue.save()
                        log_event(request, LoggedEventAction.CREATE, LoggedEventModel.VEHICLE_ISSUE, str(issue))

                if shift_id:
                    return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':pretrip_date.year, 'month':pretrip_date.month, 'day':pretrip_date.day}))
                else:
                    return HttpResponseRedirect(reverse('vehicle-status') + anchor)
    else:
        form = vehiclePreTripForm()

    if not shift:
        form.fields['driver'].required = True

    context = {
        'form': form,
        'pretrip_date': pretrip_date,
        'pretrip_driver': pretrip_driver,
        'pretrip_vehicle': pretrip_vehicle,
        'shift': shift,
        'checklist': PreTrip.CHECKLIST,
        'inspect_type': inspect_type,
    }
    return render(request, 'vehicle/pretrip.html', context=context)

@permission_required('transit.add_pretrip')
def vehiclePreTripDelete(request, id):
    pretrip = get_object_or_404(PreTrip, id=id)

    user_has_perm = request.user.has_perm('transit.delete_pretrip')
    can_delete = pretrip.can_delete() or user_has_perm

    if request.method == 'POST':
        if not can_delete or 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-pretrip-log'))

        if not user_has_perm:
            form = vehiclePreTripDeleteForm(request.POST)
            if form.is_valid():
                issue = VehicleIssue()
                issue.date = datetime.date.today()
                issue.vehicle = pretrip.vehicle
                issue.priority = VehicleIssue.PRIORITY_LOW
                issue.status = VehicleIssue.STATUS_TRIAGED

                issue.driver = form.cleaned_data['driver']
                issue.description = '[DELETED PRETRIP]\n' + str(pretrip) + '\n\n' + form.cleaned_data['deletion_reason']
                issue.save()

                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.VEHICLE_ISSUE, str(issue))

                log_event(request, LoggedEventAction.DELETE, LoggedEventModel.PRETRIP, str(pretrip))
                pretrip.delete()
                return HttpResponseRedirect(reverse('vehicle-pretrip-log'))
        else:
            log_event(request, LoggedEventAction.DELETE, LoggedEventModel.PRETRIP, str(pretrip))
            pretrip.delete()
            return HttpResponseRedirect(reverse('vehicle-pretrip-log'))

    context = {
        'model': pretrip,
        'can_delete': can_delete,
        'user_has_perm': user_has_perm,
        'form': vehiclePreTripDeleteForm(),
    }

    return render(request, 'vehicle/pretrip_delete.html', context)


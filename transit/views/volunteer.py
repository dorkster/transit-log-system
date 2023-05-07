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
import re

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Volunteer
from transit.forms import EditVolunteerForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import move_item_in_queryset

@permission_required(['transit.view_volunteer'])
def volunteerList(request):
    context = {
        'volunteers': Volunteer.objects.all(),
    }
    return render(request, 'volunteer/list.html', context=context)

def volunteerCreate(request):
    volunteer = Volunteer()
    return volunteerCreateEditCommonn(request, volunteer, is_new=True)

def volunteerEdit(request, id):
    volunteer = get_object_or_404(Volunteer, id=id)
    return volunteerCreateEditCommonn(request, volunteer, is_new=False)

@permission_required(['transit.change_volunteer'])
def volunteerCreateEditCommonn(request, volunteer, is_new):
    if is_new == True:
        query = Volunteer.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_volunteer = query[0]
            volunteer.sort_index = last_volunteer.sort_index + 1
        else:
            volunteer.sort_index = 0

    if request.method == 'POST':
        form = EditVolunteerForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#volunteer_' + str(volunteer.id)
            return HttpResponseRedirect(reverse('volunteers') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('volunteer-delete', kwargs={'id':volunteer.id}))

        if form.is_valid():
            volunteer.name = form.cleaned_data['name']
            volunteer.vehicle = form.cleaned_data['vehicle']
            volunteer.vehicle_color = form.cleaned_data['vehicle_color']
            volunteer.vehicle_plate = form.cleaned_data['vehicle_plate']
            volunteer.is_active = form.cleaned_data['is_active']
            volunteer.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.VOLUNTEER, str(volunteer))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.VOLUNTEER, str(volunteer))

            return HttpResponseRedirect(reverse('volunteers') + '#volunteer_' + str(volunteer.id))
    else:
        initial = {
            'name': volunteer.name,
            'vehicle': volunteer.vehicle,
            'vehicle_color': volunteer.vehicle_color,
            'vehicle_plate': volunteer.vehicle_plate,
            'is_active': volunteer.is_active,
        }
        form = EditVolunteerForm(initial=initial)

    context = {
        'form': form,
        'volunteer': volunteer,
        'is_new': is_new,
    }

    return render(request, 'volunteer/edit.html', context)

@permission_required(['transit.delete_volunteer'])
def volunteerDelete(request, id):
    volunteer = get_object_or_404(Volunteer, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('volunteer-edit', kwargs={'id':id}))

        query = Volunteer.objects.all()
        for i in query:
            if i.sort_index > volunteer.sort_index:
                i.sort_index -= 1;
                i.save()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.VOLUNTEER, str(volunteer))

        volunteer.delete()
        return HttpResponseRedirect(reverse('volunteers'))

    context = {
        'model': volunteer,
    }

    return render(request, 'model_delete.html', context)

def ajaxVolunteerList(request):
    if not request.user.has_perm('transit.view_volunteer'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'mv':
        if request.user.has_perm('transit.change_volunteer'):
            move_item_in_queryset(request_id, request_data, Volunteer.objects.all())

    context = {
        'volunteers': Volunteer.objects.all(),
    }
    return render(request, 'volunteer/ajax_list.html', context=context)


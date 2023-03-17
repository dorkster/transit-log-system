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

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Fare
from transit.forms import EditFareForm

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import move_item_in_queryset

@permission_required(['transit.view_fare'])
def fareList(request):
    context = {
        'fare': Fare.objects.all(),
    }
    return render(request, 'fare/list.html', context=context)

def fareCreate(request):
    fare = Fare()
    return fareCreateEditCommon(request, fare, is_new=True)

def fareEdit(request, id):
    fare = get_object_or_404(Fare, id=id)
    return fareCreateEditCommon(request, fare, is_new=False)

@permission_required(['transit.change_fare'])
def fareCreateEditCommon(request, fare, is_new):
    if is_new == True:
        query = Fare.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_fare = query[0]
            fare.sort_index = last_fare.sort_index + 1
        else:
            fare.sort_index = 0

    if request.method == 'POST':
        form = EditFareForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#fare_' + str(fare.id)
            return HttpResponseRedirect(reverse('fares') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('fare-delete', kwargs={'id':fare.id}))

        if form.is_valid():
            fare.name = form.cleaned_data['name']
            fare.fare = money_string_to_int(form.cleaned_data['fare'])
            fare.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.FARE, str(fare))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.FARE, str(fare))

            return HttpResponseRedirect(reverse('fares') + '#fare_' + str(fare.id))
    else:
        initial = {
            'name': fare.name,
            'fare': int_to_money_string(fare.fare, blank_zero=True),
        }
        form = EditFareForm(initial=initial)

    context = {
        'form': form,
        'fare': fare,
        'is_new': is_new,
    }

    return render(request, 'fare/edit.html', context)

@permission_required('transit.delete_fare')
def fareDelete(request, id):
    fare = get_object_or_404(Fare, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('fare-edit', kwargs={'id':id}))

        query = Fare.objects.all()
        for i in query:
            if i.sort_index > fare.sort_index:
                i.sort_index -= 1;
                i.save()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.FARE, str(fare))

        fare.delete()
        return HttpResponseRedirect(reverse('fares'))

    context = {
        'model': fare,
    }

    return render(request, 'model_delete.html', context)

def ajaxFareList(request):
    if not request.user.has_perm('transit.view_fare'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_fare'):
        if request_action == 'mv':
            move_item_in_queryset(request_id, request_data, Fare.objects.all())

    fares = Fare.objects.all()
    return render(request, 'fare/ajax_list.html', {'fares': fares})


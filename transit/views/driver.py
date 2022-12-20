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

from transit.models import Driver
from transit.forms import EditDriverForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_driver'])
def driverList(request):
    context = {
        'driver': Driver.objects.all(),
    }
    return render(request, 'driver/list.html', context=context)

def driverCreate(request):
    driver = Driver()
    return driverCreateEditCommon(request, driver, is_new=True)

def driverEdit(request, id):
    driver = get_object_or_404(Driver, id=id)
    return driverCreateEditCommon(request, driver, is_new=False)

@permission_required(['transit.change_driver'])
def driverCreateEditCommon(request, driver, is_new):
    if is_new == True:
        query = Driver.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_driver = query[0]
            driver.sort_index = last_driver.sort_index + 1
        else:
            driver.sort_index = 0

    if request.method == 'POST':
        form = EditDriverForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#driver_' + str(driver.id)
            return HttpResponseRedirect(reverse('drivers') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('driver-delete', kwargs={'id':driver.id}))

        if form.is_valid():
            driver.name = form.cleaned_data['name']
            driver.color = form.cleaned_data['color'][1:]
            driver.is_logged = form.cleaned_data['is_logged']
            driver.is_active = form.cleaned_data['is_active']
            driver.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.DRIVER, str(driver))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.DRIVER, str(driver))

            return HttpResponseRedirect(reverse('drivers') + '#driver_' + str(driver.id))
    else:
        initial = {
            'name': driver.name,
            'color': '#' + driver.color,
            'is_logged': driver.is_logged,
            'is_active': driver.is_active,
        }
        form = EditDriverForm(initial=initial)

    context = {
        'form': form,
        'driver': driver,
        'is_new': is_new,
    }

    return render(request, 'driver/edit.html', context)

@permission_required('transit.delete_driver')
def driverDelete(request, id):
    driver = get_object_or_404(Driver, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('driver-edit', kwargs={'id':id}))

        query = Driver.objects.all()
        for i in query:
            if i.sort_index > driver.sort_index:
                i.sort_index -= 1;
                i.save()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.DRIVER, str(driver))

        driver.delete()
        return HttpResponseRedirect(reverse('drivers'))

    context = {
        'model': driver,
    }

    return render(request, 'model_delete.html', context)

def ajaxDriverList(request):
    if not request.user.has_perm('transit.view_driver'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_driver'):
        if request_action == 'mv':
            driver = get_object_or_404(Driver, id=request_id)
            original_index = driver.sort_index
            driver.sort_index = -1

            # "remove" the selected item by shifting everything below it up by 1
            below_items = Driver.objects.filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(Driver, id=request_data)
                if driver.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the item at the new index by shifting everything below it down by 1
            below_items = Driver.objects.filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            driver.sort_index = new_index
            driver.save()

    drivers = Driver.objects.all()
    return render(request, 'driver/ajax_list.html', {'drivers': drivers})


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

from transit.models import ActivityColor
from transit.forms import EditActivityColorForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_activitycolor'])
def activityColorList(request):
    context = {
        'activity_colors': ActivityColor.objects.all(),
    }
    return render(request, 'activitycolor/list.html', context=context)

def activityColorCreate(request):
    activity_color = ActivityColor()
    return activityColorCreateEditCommon(request, activity_color, is_new=True)

def activityColorEdit(request, id):
    activity_color = get_object_or_404(ActivityColor, id=id)
    return activityColorCreateEditCommon(request, activity_color, is_new=False)

@permission_required(['transit.change_activitycolor'])
def activityColorCreateEditCommon(request, activity_color, is_new):
    if is_new == True:
        query = ActivityColor.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_activity_color = query[0]
            activity_color.sort_index = last_activity_color.sort_index + 1
        else:
            activity_color.sort_index = 0

    if request.method == 'POST':
        form = EditActivityColorForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#activity_color' + str(activity_color.id)
            return HttpResponseRedirect(reverse('activity-colors') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('activity-color-delete', kwargs={'id':activity_color.id}))

        if form.is_valid():
            activity_color.name = form.cleaned_data['name']
            activity_color.color = form.cleaned_data['color'][1:]
            activity_color.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.ACTIVITY_COLOR, str(activity_color))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.ACTIVITY_COLOR, str(activity_color))

            return HttpResponseRedirect(reverse('activity-colors') + '#activity_color_' + str(activity_color.id))
    else:
        initial = {
            'name': activity_color.name,
            'color': '#' + activity_color.color,
        }
        form = EditActivityColorForm(initial=initial)

    context = {
        'form': form,
        'activity_color': activity_color,
        'is_new': is_new,
    }

    return render(request, 'activitycolor/edit.html', context)

@permission_required('transit.delete_activitycolor')
def activityColorDelete(request, id):
    activity_color = get_object_or_404(ActivityColor, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('activity-color-edit', kwargs={'id':id}))

        query = ActivityColor.objects.all()
        for i in query:
            if i.sort_index > activity_color.sort_index:
                i.sort_index -= 1;
                i.save()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.ACTIVITY_COLOR, str(driver))

        activity_color.delete()
        return HttpResponseRedirect(reverse('activity-colors'))

    context = {
        'model': activity_color,
    }

    return render(request, 'model_delete.html', context)

def ajaxActivityColorList(request):
    if not request.user.has_perm('transit.view_activitycolor'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_activitycolor'):
        if request_action == 'mv':
            activity_color = get_object_or_404(ActivityColor, id=request_id)
            original_index = activity_color.sort_index
            activity_color.sort_index = -1

            # "remove" the selected item by shifting everything below it up by 1
            below_items = ActivityColor.objects.filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(ActivityColor, id=request_data)
                if activity_color.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the item at the new index by shifting everything below it down by 1
            below_items = ActivityColor.objects.filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            activity_color.sort_index = new_index
            activity_color.save()

    activity_colors = ActivityColor.objects.all()
    return render(request, 'activitycolor/ajax_list.html', {'activity_colors': activity_colors})


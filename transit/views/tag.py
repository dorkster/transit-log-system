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

from transit.models import Tag
from transit.forms import EditTagForm

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import move_item_in_queryset

@permission_required(['transit.view_tag'])
def tagList(request):
    context = {
        'tag': Tag.objects.all(),
    }
    return render(request, 'tag/list.html', context=context)

def tagCreate(request):
    tag = Tag()
    return tagCreateEditCommon(request, tag, is_new=True)

def tagEdit(request, id):
    tag = get_object_or_404(Tag, id=id)
    return tagCreateEditCommon(request, tag, is_new=False)

@permission_required(['transit.change_tag'])
def tagCreateEditCommon(request, tag, is_new):
    if is_new == True:
        query = Tag.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_tag = query[0]
            tag.sort_index = last_tag.sort_index + 1
        else:
            tag.sort_index = 0

    if request.method == 'POST':
        form = EditTagForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#tag_' + str(tag.id)
            return HttpResponseRedirect(reverse('tags') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('tag-delete', kwargs={'id':tag.id}))

        if form.is_valid():
            tag.name = form.cleaned_data['name']
            tag.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.TAG, str(tag))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.TAG, str(tag))

            return HttpResponseRedirect(reverse('tags') + '#tag_' + str(tag.id))
    else:
        initial = {
            'name': tag.name,
        }
        form = EditTagForm(initial=initial)

    context = {
        'form': form,
        'tag': tag,
        'is_new': is_new,
    }

    return render(request, 'tag/edit.html', context)

@permission_required('transit.delete_tag')
def tagDelete(request, id):
    tag = get_object_or_404(Tag, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('tag-edit', kwargs={'id':id}))

        query = Tag.objects.all()
        for i in query:
            if i.sort_index > tag.sort_index:
                i.sort_index -= 1;
                i.save()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.TAG, str(tag))

        tag.delete()
        return HttpResponseRedirect(reverse('tags'))

    context = {
        'model': tag,
    }

    return render(request, 'model_delete.html', context)

def ajaxTagList(request):
    if not request.user.has_perm('transit.view_tag'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_tag'):
        if request_action == 'mv':
            move_item_in_queryset(request_id, request_data, Tag.objects.all())

    tags = Tag.objects.all()
    return render(request, 'tag/ajax_list.html', {'tags': tags})


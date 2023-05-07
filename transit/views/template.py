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
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Template, TemplateTrip
from transit.forms import EditTemplateForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from transit.common.util import move_item_in_queryset

@permission_required(['transit.view_template'])
def templateList(request):
    context = {
        'template': Template.objects.all(),
    }
    return render(request, 'template/list.html', context=context)

def templateCreate(request):
    template = Template()
    return templateCreateEditCommon(request, template, is_new=True)

def templateEdit(request, id):
    template = get_object_or_404(Template, id=id)
    return templateCreateEditCommon(request, template, is_new=False)

@permission_required(['transit.change_template'])
def templateCreateEditCommon(request, template, is_new):
    if is_new == True:
        query = Template.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_template = query[0]
            template.sort_index = last_template.sort_index + 1
        else:
            template.sort_index = 0

    if request.method == 'POST':
        form = EditTemplateForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#template_' + str(template.id)
            return HttpResponseRedirect(reverse('templates') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('template-delete', kwargs={'id':template.id}))

        if form.is_valid():
            template.name = form.cleaned_data['name']
            template.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.TEMPLATE, str(template))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.TEMPLATE, str(template))

            return HttpResponseRedirect(reverse('templates') + '#template_' + str(template.id))
    else:
        initial = {
            'name': template.name,
        }
        form = EditTemplateForm(initial=initial)

    context = {
        'form': form,
        'template': template,
        'is_new': is_new,
    }

    return render(request, 'template/edit.html', context)

@permission_required(['transit.delete_template'])
def templateDelete(request, id):
    template = get_object_or_404(Template, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('template-edit', kwargs={'id':id}))

        query = Template.objects.all()
        for i in query:
            if i.sort_index > template.sort_index:
                i.sort_index -= 1;
                i.save()

        trip_query = TemplateTrip.objects.filter(parent=id)
        for i in trip_query:
            i.delete()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.TEMPLATE, str(template))

        template.delete()
        return HttpResponseRedirect(reverse('templates'))

    context = {
        'model': template,
    }

    return render(request, 'model_delete.html', context)

def ajaxTemplateList(request):
    if not request.user.has_perm('transit.view_template'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_template'):
        if request_action == 'mv':
            move_item_in_queryset(request_id, request_data, Template.objects.all())

    templates = Template.objects.all()
    return render(request, 'template/ajax_list.html', {'templates': templates})


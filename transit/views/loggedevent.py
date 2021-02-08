import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator

from transit.models import LoggedEvent

from django.contrib.auth.decorators import permission_required

@permission_required(['transit.view_loggedevent'])
def loggedEventList(request):
    context = {
        'logged_events': LoggedEvent.objects.all(),
    }
    return render(request, 'loggedevent/list.html', context=context)

def ajaxLoggedEventList(request):
    if not request.user.has_perm('transit.view_loggedevent'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'filter_action':
        request.session['eventlog_filter_action'] = request_data
    elif request_action == 'filter_reset':
        request.session['eventlog_filter_action'] = ''

    filter_action = request.session.get('eventlog_filter_action', '')

    # TODO filtering
    logged_events = LoggedEvent.objects.all()

    unfiltered_count = len(logged_events)

    if filter_action != '':
        logged_events = logged_events.filter(event_action=filter_action)

    filtered_count = len(logged_events)

    logged_events = logged_events.order_by('-timestamp')

    logged_event_pages = Paginator(logged_events, 25)
    logged_events_paginated = logged_event_pages.get_page(request.GET.get('page'))

    actions = [
        { 'id': 1, 'name': 'Create' },
        { 'id': 2, 'name': 'Edit' },
        { 'id': 3, 'name': 'Delete' },
        { 'id': 4, 'name': 'Start Log' },
        { 'id': 5, 'name': 'End Log' },
        { 'id': 6, 'name': 'Log Fuel' },
        { 'id': 7, 'name': 'Set Status'},
    ]

    context = {
        'logged_events': logged_events_paginated,
        'filter_action': None if filter_action == '' else int(filter_action),
        'is_filtered': (filter_action != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'actions': actions,
    }
    return render(request, 'loggedevent/ajax_list.html', context=context)


import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator

from django.contrib.auth.models import User
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *

@permission_required(['transit.view_loggedevent'])
def loggedEventList(request):
    context = {
        'logged_events': LoggedEvent.objects.all(),
    }
    return render(request, 'loggedevent/list.html', context=context)

def ajaxLoggedEventList(request):
    if not request.user.has_perm('transit.view_loggedevent'):
        return HttpResponseRedirect(reverse('login_redirect'))

    SORT_TIMESTAMP = 0
    SORT_USERNAME = 1
    SORT_IP_ADDRESS = 2
    SORT_ACTION = 3
    SORT_TARGET = 4
    SORT_DESCRIPTION = 5

    sort_mode = request.session.get('eventlog_sort', SORT_TIMESTAMP)
    sort_mode_dir = request.session.get('eventlog_sort_dir', 0)

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'filter_action':
        request.session['eventlog_filter_action'] = request_data
    elif request_action == 'filter_target':
        request.session['eventlog_filter_target'] = request_data
    elif request_action == 'filter_username':
        request.session['eventlog_filter_username'] = request_data
    elif request_action == 'filter_search':
        request.session['eventlog_filter_search'] = request_data
    elif request_action == 'filter_reset':
        request.session['eventlog_filter_action'] = ''
        request.session['eventlog_filter_target'] = ''
        request.session['eventlog_filter_username'] = ''
        request.session['eventlog_filter_search'] = ''
    elif request_action == 'clear_log':
        for i in LoggedEvent.objects.all():
            i.delete()
        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.UNKNOWN, 'Cleared Event Log')
    elif request_action == 'sort':
        new_sort_mode = int(request_data)
        if sort_mode == new_sort_mode:
            sort_mode_dir = 1 if sort_mode_dir == 0 else 0
        else:
            sort_mode_dir = 0
        sort_mode = new_sort_mode
        request.session['eventlog_sort'] = new_sort_mode
        request.session['eventlog_sort_dir'] = sort_mode_dir

    filter_action = request.session.get('eventlog_filter_action', '')
    filter_target = request.session.get('eventlog_filter_target', '')
    filter_username = request.session.get('eventlog_filter_username', '')
    filter_search = request.session.get('eventlog_filter_search', '')

    # TODO filter by date?
    logged_events = LoggedEvent.objects.all()

    unfiltered_count = len(logged_events)

    if filter_action != '':
        logged_events = logged_events.filter(event_action=filter_action)

    if filter_target != '':
        logged_events = logged_events.filter(event_model=filter_target)

    if filter_username != '':
        logged_events = logged_events.filter(username=filter_username)

    if filter_search != '':
        logged_events = logged_events.filter(event_desc__icontains=filter_search)

    filtered_count = len(logged_events)

    logged_events = logged_events.order_by('-timestamp')

    if sort_mode == SORT_TIMESTAMP:
        logged_events = logged_events.order_by('-timestamp')
    elif sort_mode == SORT_USERNAME:
        logged_events = logged_events.order_by('username', '-timestamp')
    elif sort_mode == SORT_IP_ADDRESS:
        logged_events = logged_events.order_by('ip_address', '-timestamp')
    elif sort_mode == SORT_ACTION:
        logged_events = logged_events.order_by('event_action', '-timestamp')
    elif sort_mode == SORT_TARGET:
        logged_events = logged_events.order_by('event_model', '-timestamp')
    elif sort_mode == SORT_DESCRIPTION:
        logged_events = logged_events.order_by('event_desc', '-timestamp')

    if sort_mode_dir == 1:
        logged_events = logged_events.reverse()

    logged_event_pages = Paginator(logged_events, 25)
    logged_events_paginated = logged_event_pages.get_page(request.GET.get('page'))

    actions = []
    for i in range(LoggedEventAction.CREATE, LoggedEventAction.STATUS + 1):
        actions.append( { 'id': i, 'name': LoggedEventAction.get_str(i) })

    targets = []
    for i in range(LoggedEventModel.CLIENT, LoggedEventModel.PRETRIP + 1):
        targets.append( { 'id': i, 'name': LoggedEventModel.get_str(i) })

    context = {
        'logged_events': logged_events_paginated,
        'filter_action': None if filter_action == '' else int(filter_action),
        'filter_target': None if filter_target == '' else int(filter_target),
        'filter_username': None if filter_username == '' else filter_username,
        'filter_search': filter_search,
        'is_filtered': (filter_action != '' or filter_target != '' or filter_username != '' or filter_search != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'users': User.objects.all(),
        'actions': actions,
        'targets': targets,
        'current_ip': request.META['REMOTE_ADDR'],
        'sort_mode': sort_mode,
        'sort_mode_dir': sort_mode_dir,
    }
    return render(request, 'loggedevent/ajax_list.html', context=context)


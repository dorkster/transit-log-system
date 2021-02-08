import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator

from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

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
    elif request_action == 'filter_target':
        request.session['eventlog_filter_target'] = request_data
    elif request_action == 'filter_reset':
        request.session['eventlog_filter_action'] = ''
        request.session['eventlog_filter_target'] = ''
    elif request_action == 'clear_log':
        for i in LoggedEvent.objects.all():
            i.delete()

    filter_action = request.session.get('eventlog_filter_action', '')
    filter_target = request.session.get('eventlog_filter_target', '')

    # TODO filtering
    logged_events = LoggedEvent.objects.all()

    unfiltered_count = len(logged_events)

    if filter_action != '':
        logged_events = logged_events.filter(event_action=filter_action)

    if filter_target != '':
        logged_events = logged_events.filter(event_model=filter_target)

    filtered_count = len(logged_events)

    logged_events = logged_events.order_by('-timestamp')

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
        'is_filtered': (filter_action != '' or filter_target != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'actions': actions,
        'targets': targets,
        'current_ip': request.META['REMOTE_ADDR'],
    }
    return render(request, 'loggedevent/ajax_list.html', context=context)


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

import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator

from django.contrib.auth.models import User
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.common.util import *

@permission_required(['transit.view_loggedevent'])
def loggedEventList(request):
    context = {
        'logged_events': LoggedEvent.objects.all(),
    }
    return render(request, 'loggedevent/list.html', context=context)

def ajaxLoggedEventList(request):
    if not request.user.has_perm('transit.view_loggedevent'):
        return HttpResponseRedirect(reverse('login_redirect'))

    date_months = [
        { 'id': 1, 'name': 'January' },
        { 'id': 2, 'name': 'February' },
        { 'id': 3, 'name': 'March' },
        { 'id': 4, 'name': 'April' },
        { 'id': 5, 'name': 'May' },
        { 'id': 6, 'name': 'June' },
        { 'id': 7, 'name': 'July' },
        { 'id': 8, 'name': 'August' },
        { 'id': 9, 'name': 'September' },
        { 'id': 10, 'name': 'October' },
        { 'id': 11, 'name': 'November' },
        { 'id': 12, 'name': 'December' },
    ]

    date_days = []
    for i in range(1,32):
        date_days.append(i)

    date_years = []
    for i in range(2019, datetime.date.today().year + 2):
        date_years.append(i)

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

    reset_current_page = False

    if request_action == 'filter_action':
        reset_current_page = True
        request.session['eventlog_filter_action'] = request_data
    elif request_action == 'filter_target':
        reset_current_page = True
        request.session['eventlog_filter_target'] = request_data
    elif request_action == 'filter_username':
        reset_current_page = True
        request.session['eventlog_filter_username'] = request_data
    elif request_action == 'filter_search':
        reset_current_page = True
        request.session['eventlog_filter_search'] = request_data
    elif request_action == 'filter_date_start_month':
        reset_current_page = True
        request.session['eventlog_filter_date_start_month'] = int(request_data)
    elif request_action == 'filter_date_start_day':
        reset_current_page = True
        request.session['eventlog_filter_date_start_day'] = int(request_data)
    elif request_action == 'filter_date_start_year':
        reset_current_page = True
        request.session['eventlog_filter_date_start_year'] = int(request_data)
    elif request_action == 'filter_date_end_month':
        reset_current_page = True
        request.session['eventlog_filter_date_end_month'] = int(request_data)
    elif request_action == 'filter_date_end_day':
        reset_current_page = True
        request.session['eventlog_filter_date_end_day'] = int(request_data)
    elif request_action == 'filter_date_end_year':
        reset_current_page = True
        request.session['eventlog_filter_date_end_year'] = int(request_data)
    elif request_action == 'filter_date_single_day':
        reset_current_page = True
        single_day = datetime.datetime.strptime(request_data, '%Y-%m-%d')
        request.session['eventlog_filter_date_start_year'] = single_day.year
        request.session['eventlog_filter_date_start_month'] = single_day.month
        request.session['eventlog_filter_date_start_day'] = single_day.day
        request.session['eventlog_filter_date_end_year'] = single_day.year
        request.session['eventlog_filter_date_end_month'] = single_day.month
        request.session['eventlog_filter_date_end_day'] = single_day.day
    elif request_action == 'filter_reset':
        reset_current_page = True
        request.session['eventlog_filter_action'] = ''
        request.session['eventlog_filter_target'] = ''
        request.session['eventlog_filter_username'] = ''
        request.session['eventlog_filter_search'] = ''
        request.session['eventlog_filter_date_start_month'] = 0
        request.session['eventlog_filter_date_start_day'] = 0
        request.session['eventlog_filter_date_start_year'] = 0
        request.session['eventlog_filter_date_end_month'] = 0
        request.session['eventlog_filter_date_end_day'] = 0
        request.session['eventlog_filter_date_end_year'] = 0
    elif request_action == 'clear_log':
        reset_current_page = True
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

    if reset_current_page:
        return render(request, 'loggedevent/ajax_reset.html', context={})

    filter_action = request.session.get('eventlog_filter_action', '')
    filter_target = request.session.get('eventlog_filter_target', '')
    filter_username = request.session.get('eventlog_filter_username', '')
    filter_search = request.session.get('eventlog_filter_search', '')
    filter_date_start_month = request.session.get('eventlog_filter_date_start_month', 0)
    filter_date_start_day = request.session.get('eventlog_filter_date_start_day', 0)
    filter_date_start_year = request.session.get('eventlog_filter_date_start_year', 0)
    filter_date_end_month = request.session.get('eventlog_filter_date_end_month', 0)
    filter_date_end_day = request.session.get('eventlog_filter_date_end_day', 0)
    filter_date_end_year = request.session.get('eventlog_filter_date_end_year', 0)

    # TODO filter by date?
    logged_events = LoggedEvent.objects.all()

    unfiltered_count = len(logged_events)
    is_filtered = False

    if filter_action != '':
        logged_events = logged_events.filter(event_action=filter_action)
        is_filtered = True

    if filter_target != '':
        logged_events = logged_events.filter(event_model=filter_target)
        is_filtered = True

    if filter_username != '':
        logged_events = logged_events.filter(username=filter_username)
        is_filtered = True

    if filter_search != '':
        logged_events = logged_events.filter(event_desc__icontains=filter_search)
        is_filtered = True

    if filter_date_start_month != 0 and filter_date_start_day != 0 and filter_date_start_year != 0:
        try:
            logged_events = logged_events.filter(timestamp__gte=datetime.datetime(year=filter_date_start_year, month=filter_date_start_month, day=filter_date_start_day))
            is_filtered = True
        except:
            pass

    if filter_date_end_month != 0 and filter_date_end_day != 0 and filter_date_end_year != 0:
        try:
            logged_events = logged_events.filter(timestamp__lt=datetime.datetime(year=filter_date_end_year, month=filter_date_end_month, day=filter_date_end_day) + datetime.timedelta(days=1))
            is_filtered = True
        except:
            pass

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

    results_per_page = 25

    logged_event_pages = Paginator(logged_events, results_per_page)
    logged_events_paginated = logged_event_pages.get_page(request.GET.get('page'))

    page_ranges = get_paginated_ranges(page=logged_events_paginated, page_range=10, items_per_page=results_per_page)

    actions = []
    for i in range(LoggedEventAction.CREATE, LoggedEventAction.STATUS + 1):
        actions.append( { 'id': i, 'name': LoggedEventAction.get_str(i) })

    targets = []
    for i in range(LoggedEventModel.CLIENT, LoggedEventModel.TEMPLATE_DRIVER_STATUS + 1):
        targets.append( { 'id': i, 'name': LoggedEventModel.get_str(i) })

    context = {
        'logged_events': logged_events_paginated,
        'page_ranges': page_ranges,
        'filter_action': None if filter_action == '' else int(filter_action),
        'filter_target': None if filter_target == '' else int(filter_target),
        'filter_username': None if filter_username == '' else filter_username,
        'filter_search': filter_search,
        'filter_date_start_month': filter_date_start_month,
        'filter_date_start_day': filter_date_start_day,
        'filter_date_start_year': filter_date_start_year,
        'filter_date_end_month': filter_date_end_month,
        'filter_date_end_day': filter_date_end_day,
        'filter_date_end_year': filter_date_end_year,
        'is_filtered': is_filtered,
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'users': User.objects.all(),
        'actions': actions,
        'targets': targets,
        'current_ip': request.META['REMOTE_ADDR'],
        'sort_mode': sort_mode,
        'sort_mode_dir': sort_mode_dir,
        'date_months': date_months,
        'date_days': date_days,
        'date_years': date_years,
    }
    return render(request, 'loggedevent/ajax_list.html', context=context)


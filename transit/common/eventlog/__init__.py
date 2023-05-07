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

import datetime

from transit.models import LoggedEvent

def log_event(request, event_action, event_model, event_desc):
    logged_events = LoggedEvent.objects.all()

    while logged_events.count() >= 10000:
        logged_events[0].delete()

    event = LoggedEvent()
    event.username = request.user.get_username()

    # TODO use django-ipware?
    if request.META['REMOTE_ADDR']:
        event.ip_address = request.META['REMOTE_ADDR']

    event.event_action = event_action
    event.event_model = event_model
    event.event_desc = event_desc

    event.save()


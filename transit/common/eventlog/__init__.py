import datetime

from transit.models import LoggedEvent

def log_event(request, event_type, event_desc):
    logged_events = LoggedEvent.objects.all()

    if logged_events.count() >= 10:
        logged_events[0].delete()

    event = LoggedEvent()
    event.username = request.user.get_username()

    #TODO ip address

    event.event_type = event_type
    event.event_desc = event_desc

    event.save()


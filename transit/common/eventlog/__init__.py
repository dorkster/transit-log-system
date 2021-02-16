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


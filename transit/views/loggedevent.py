import datetime

from django.shortcuts import render
# from django.http import HttpResponseRedirect
# from django.urls import reverse

from transit.models import LoggedEvent

# from django.contrib.auth.decorators import permission_required

# @permission_required(['transit.view_loggedevent'])
def loggedEventList(request):
    context = {
        'logged_events': LoggedEvent.objects.all(),
    }
    return render(request, 'loggedevent/list.html', context=context)

def ajaxLoggedEventList(request):
    # if not request.user.has_perm('transit.view_loggedevent'):
    #     return HttpResponseRedirect(reverse('login_redirect'))

    # request_id = ''
    # if request.GET['target_id'] != '':
    #     request_id = uuid.UUID(request.GET['target_id'])
    #
    # request_action = request.GET['target_action']
    # request_data = request.GET['target_data']

    # TODO filtering
    logged_events = LoggedEvent.objects.all()
    logged_events = logged_events.order_by('-timestamp')

    context = {
        'logged_events': logged_events,
    }
    return render(request, 'loggedevent/ajax_list.html', context=context)


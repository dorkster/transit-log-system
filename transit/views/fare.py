import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Fare
from transit.forms import EditFareForm

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_fare'])
def fareList(request):
    context = {
        'fare': Fare.objects.all(),
    }
    return render(request, 'fare/list.html', context=context)

def fareCreate(request):
    fare = Fare()
    return fareCreateEditCommon(request, fare, is_new=True)

def fareEdit(request, id):
    fare = get_object_or_404(Fare, id=id)
    return fareCreateEditCommon(request, fare, is_new=False)

@permission_required(['transit.change_fare'])
def fareCreateEditCommon(request, fare, is_new):
    if is_new == True:
        query = Fare.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_fare = query[0]
            fare.sort_index = last_fare.sort_index + 1
        else:
            fare.sort_index = 0

    if request.method == 'POST':
        form = EditFareForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#fare_' + str(fare.id)
            return HttpResponseRedirect(reverse('fares') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('fare-delete', kwargs={'id':fare.id}))

        if form.is_valid():
            fare.name = form.cleaned_data['name']
            fare.fare = money_string_to_int(form.cleaned_data['fare'])
            fare.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.FARE, str(fare))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.FARE, str(fare))

            return HttpResponseRedirect(reverse('fares') + '#fare_' + str(fare.id))
    else:
        initial = {
            'name': fare.name,
            'fare': int_to_money_string(fare.fare, blank_zero=True),
        }
        form = EditFareForm(initial=initial)

    context = {
        'form': form,
        'fare': fare,
        'is_new': is_new,
    }

    return render(request, 'fare/edit.html', context)

@permission_required('transit.delete_fare')
def fareDelete(request, id):
    fare = get_object_or_404(Fare, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('fare-edit', kwargs={'id':id}))

        query = Fare.objects.all()
        for i in query:
            if i.sort_index > fare.sort_index:
                i.sort_index -= 1;
                i.save()

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.FARE, str(fare))

        fare.delete()
        return HttpResponseRedirect(reverse('fares'))

    context = {
        'model': fare,
    }

    return render(request, 'model_delete.html', context)

def ajaxFareList(request):
    if not request.user.has_perm('transit.view_fare'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_fare'):
        if request_action == 'mv':
            fare = get_object_or_404(Fare, id=request_id)
            original_index = fare.sort_index
            fare.sort_index = -1

            # "remove" the selected item by shifting everything below it up by 1
            below_items = Fare.objects.filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(Fare, id=request_data)
                if fare.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the item at the new index by shifting everything below it down by 1
            below_items = Fare.objects.filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            fare.sort_index = new_index
            fare.save()

    fares = Fare.objects.all()
    return render(request, 'fare/ajax_list.html', {'fares': fares})


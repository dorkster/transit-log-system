import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers

from transit.models import Template, TemplateTrip, Client
from transit.forms import EditTemplateTripForm

def templateTripList(request, parent):
    context = {
        'parent':parent,
        'template_trips': TemplateTrip.objects.filter(parent=parent),
    }
    return render(request, 'schedule/template/trip/list.html', context=context)

def templateTripCreate(request, parent):
    trip = TemplateTrip()
    trip.parent = Template.objects.get(id=parent)
    return templateTripCreateEditCommon(request, trip, is_new=True)

def templateTripEdit(request, parent, id):
    trip = get_object_or_404(TemplateTrip, id=id)
    return templateTripCreateEditCommon(request, trip, is_new=False)

def templateTripCreateEditCommon(request, trip, is_new):
    if is_new == True:
        query = TemplateTrip.objects.filter(parent=trip.parent).order_by('-sort_index')
        if len(query) > 0:
            last_trip = query[0]
            trip.sort_index = last_trip.sort_index + 1
        else:
            trip.sort_index = 0

    if request.method == 'POST':
        form = EditTemplateTripForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#trip_' + str(trip.id)
            return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':trip.parent.id}) + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('template-trip-delete', kwargs={'parent':trip.parent.id, 'id':trip.id}))

        if form.is_valid():
            trip.name = form.cleaned_data['name']
            trip.address = form.cleaned_data['address']
            trip.phone = form.cleaned_data['phone']
            trip.destination = form.cleaned_data['destination']
            trip.pick_up_time = form.cleaned_data['pick_up_time']
            trip.appointment_time = form.cleaned_data['appointment_time']
            trip.trip_type = form.cleaned_data['trip_type']
            trip.elderly = form.cleaned_data['elderly']
            trip.ambulatory = form.cleaned_data['ambulatory']
            trip.note = form.cleaned_data['notes']
            trip.save()

            return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':trip.parent.id}) + '#trip_' + str(trip.id))
    else:
        initial = {
            'name': trip.name,
            'address': trip.address,
            'phone': trip.phone,
            'destination': trip.destination,
            'pick_up_time': trip.pick_up_time,
            'appointment_time': trip.appointment_time,
            'trip_type': trip.trip_type,
            'elderly': trip.elderly,
            'ambulatory': trip.ambulatory,
            'notes': trip.note,
        }
        form = EditTemplateTripForm(initial=initial)

    context = {
        'form': form,
        'trip': trip,
        'clients': Client.objects.all(),
        'clients_json': serializers.serialize('json', Client.objects.all()),
        'is_new': is_new,
    }

    return render(request, 'schedule/template/trip/edit.html', context)

def templateTripDelete(request, parent, id):
    trip = get_object_or_404(TemplateTrip, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('template-trip-edit', kwargs={'parent':trip.parent.id, 'id':id}))

        query = TemplateTrip.objects.filter(parent=trip.parent)
        for i in query:
            if i.sort_index > trip.sort_index:
                i.sort_index -= 1;
                i.save()

        trip.delete()
        return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':parent}))

    context = {
        'model': trip,
    }

    return render(request, 'model_delete.html', context)

def ajaxTemplateTripList(request, parent):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'mv':
        trip = get_object_or_404(TemplateTrip, id=request_id)

        do_sort = False
        if request_data == 'u':
            query = TemplateTrip.objects.filter(parent=trip.parent, sort_index=trip.sort_index-1)
            do_sort = True
        elif request_data == 'd':
            query = TemplateTrip.objects.filter(parent=trip.parent, sort_index=trip.sort_index+1)
            do_sort = True

        if do_sort and len(query) > 0:
            swap_index = query[0].sort_index
            query[0].sort_index = trip.sort_index
            trip.sort_index = swap_index
            query[0].save()
            trip.save()

    trips = TemplateTrip.objects.filter(parent=parent)

    context = {
        'parent': parent,
        'trips': trips,
        'template': Template.objects.get(id=parent),
    }
    return render(request, 'schedule/template/trip/ajax_list.html', context=context)


import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers

from transit.models import Template, TemplateTrip, Client, FrequentTag, Trip
from transit.forms import EditTemplateTripForm, EditTemplateActivityForm

def templateTripList(request, parent):
    context = {
        'parent':parent,
        'template_trips': TemplateTrip.objects.filter(parent=parent),
    }
    return render(request, 'template/trip/list.html', context=context)

def templateTripCreate(request, parent):
    trip = TemplateTrip()
    trip.parent = Template.objects.get(id=parent)
    return templateTripCreateEditCommon(request, trip, is_new=True)

def templateTripCreateActivity(request, parent):
    trip = TemplateTrip()
    trip.parent = Template.objects.get(id=parent)
    trip.is_activity = True
    return templateTripCreateEditCommon(request, trip, is_new=True)

def templateTripCreateReturn(request, parent, id):
    origin_trip = get_object_or_404(TemplateTrip, id=id)
    trip = TemplateTrip()
    trip.parent = origin_trip.parent
    trip.name = origin_trip.name
    trip.address = origin_trip.destination
    trip.phone_home = origin_trip.phone_home
    trip.phone_cell = origin_trip.phone_cell
    trip.phone_address = origin_trip.phone_destination
    trip.phone_destination = origin_trip.phone_address
    trip.destination = origin_trip.address
    trip.trip_type = origin_trip.trip_type
    trip.tags = origin_trip.tags
    trip.elderly = origin_trip.elderly
    trip.ambulatory = origin_trip.ambulatory

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
        if trip.is_activity:
            form = EditTemplateActivityForm(request.POST)
        else:
            form = EditTemplateTripForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#trip_' + str(trip.id)
            return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':trip.parent.id}) + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('template-trip-delete', kwargs={'parent':trip.parent.id, 'id':trip.id}))

        if form.is_valid():
            if trip.is_activity:
                trip.pick_up_time = form.cleaned_data['start_time']
                trip.appointment_time = form.cleaned_data['end_time']
                trip.note = form.cleaned_data['description']
            else:
                FrequentTag.removeTags(trip.get_tag_list())

                trip.name = form.cleaned_data['name']
                trip.address = form.cleaned_data['address']
                trip.phone_home = form.cleaned_data['phone_home']
                trip.phone_cell = form.cleaned_data['phone_cell']
                trip.phone_address = form.cleaned_data['phone_address']
                trip.phone_destination = form.cleaned_data['phone_destination']
                trip.destination = form.cleaned_data['destination']
                trip.pick_up_time = form.cleaned_data['pick_up_time']
                trip.appointment_time = form.cleaned_data['appointment_time']
                trip.trip_type = form.cleaned_data['trip_type']
                trip.tags = form.cleaned_data['tags']
                trip.elderly = form.cleaned_data['elderly']
                trip.ambulatory = form.cleaned_data['ambulatory']
                trip.note = form.cleaned_data['notes']

            if not trip.is_activity:
                FrequentTag.addTags(trip.get_tag_list())

            trip.save()

            return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':trip.parent.id}) + '#trip_' + str(trip.id))
    else:
        if trip.is_activity:
            initial = {
                'start_time': trip.pick_up_time,
                'end_time': trip.appointment_time,
                'description': trip.note,
            }
            form = EditTemplateActivityForm(initial=initial)
        else:
            initial = {
                'name': trip.name,
                'address': trip.address,
                'phone_home': trip.phone_home,
                'phone_cell': trip.phone_cell,
                'phone_address': trip.phone_address,
                'phone_destination': trip.phone_destination,
                'destination': trip.destination,
                'pick_up_time': trip.pick_up_time,
                'appointment_time': trip.appointment_time,
                'trip_type': trip.trip_type,
                'tags': trip.tags,
                'elderly': trip.elderly,
                'ambulatory': trip.ambulatory,
                'notes': trip.note,
            }
            form = EditTemplateTripForm(initial=initial)

    addresses = set()
    for i in Trip.objects.filter(date__gte=(datetime.date.today() - datetime.timedelta(days=30))):
        if i.address:
            addresses.add(str(i.address))
        if i.destination:
            addresses.add(str(i.destination))

    context = {
        'form': form,
        'trip': trip,
        'clients': Client.objects.all(),
        'clients_json': serializers.serialize('json', Client.objects.all()),
        'is_new': is_new,
        'frequent_tags': FrequentTag.objects.all()[:10],
        'addresses': sorted(addresses),
    }

    return render(request, 'template/trip/edit.html', context)

def templateTripDelete(request, parent, id):
    trip = get_object_or_404(TemplateTrip, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('template-trip-edit', kwargs={'parent':trip.parent.id, 'id':id}))

        FrequentTag.removeTags(trip.get_tag_list())

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
        template_trip = get_object_or_404(TemplateTrip, id=request_id)
        original_index = template_trip.sort_index
        template_trip.sort_index = -1

        # "remove" the selected item by shifting everything below it up by 1
        below_items = TemplateTrip.objects.filter(parent=template_trip.parent, sort_index__gt=original_index)
        for i in below_items:
            i.sort_index -= 1;
            i.save()

        if request_data == '':
            new_index = 0
        else:
            target_item = get_object_or_404(TemplateTrip, id=request_data)
            if template_trip.id != target_item.id:
                new_index = target_item.sort_index + 1
            else:
                new_index = original_index

        # prepare to insert the item at the new index by shifting everything below it down by 1
        below_items = TemplateTrip.objects.filter(parent=template_trip.parent, sort_index__gte=new_index)
        for i in below_items:
            i.sort_index += 1
            i.save()

        template_trip.sort_index = new_index
        template_trip.save()
    elif request_action == 'toggle_extra_columns':
        request.session['template_extra_columns'] = not request.session.get('template_extra_columns', False)

    trips = TemplateTrip.objects.filter(parent=parent)

    context = {
        'parent': parent,
        'trips': trips,
        'template': Template.objects.get(id=parent),
        'show_extra_columns': request.session.get('template_extra_columns', False),
    }
    return render(request, 'template/trip/ajax_list.html', context=context)


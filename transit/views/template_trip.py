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

import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers

from transit.models import Template, TemplateTrip, Client, Tag, Trip, SiteSettings, Destination, Fare
from transit.forms import EditTemplateTripForm, EditTemplateActivityForm, EditTemplateDriverStatusForm

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_templatetrip'])
def templateTripList(request, parent):
    context = {
        'parent':parent,
        'template': Template.objects.get(id=parent),
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
    trip.format = Trip.FORMAT_ACTIVITY
    return templateTripCreateEditCommon(request, trip, is_new=True)

def templateTripCreateDriverStatus(request, parent):
    trip = TemplateTrip()
    trip.parent = Template.objects.get(id=parent)
    trip.format = Trip.FORMAT_DRIVER_STATUS
    return templateTripCreateEditCommon(request, trip, is_new=True)

def templateTripCreateReturn(request, parent, id):
    origin_trip = get_object_or_404(TemplateTrip, id=id)
    trip = TemplateTrip()
    trip.parent = origin_trip.parent
    trip.driver = origin_trip.driver
    trip.vehicle = origin_trip.vehicle
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
    trip.passenger = origin_trip.passenger

    return templateTripCreateEditCommon(request, trip, is_new=True, is_return_trip=True)

def templateTripCopy(request, parent, id):
    origin_trip = get_object_or_404(TemplateTrip, id=id)
    trip = TemplateTrip()
    trip_id = trip.id
    trip = origin_trip
    trip.id = trip_id
    return templateTripCreateEditCommon(request, trip, is_new=True)

def templateTripEdit(request, parent, id):
    trip = get_object_or_404(TemplateTrip, id=id)
    return templateTripCreateEditCommon(request, trip, is_new=False)

@permission_required(['transit.change_templatetrip'])
def templateTripCreateEditCommon(request, trip, is_new, is_return_trip=False):
    if is_new == True:
        query = TemplateTrip.objects.filter(parent=trip.parent).order_by('-sort_index')
        if len(query) > 0:
            last_trip = query[0]
            trip.sort_index = last_trip.sort_index + 1
        else:
            trip.sort_index = 0

    if request.method == 'POST':
        if trip.format == Trip.FORMAT_ACTIVITY:
            form = EditTemplateActivityForm(request.POST)
        elif trip.format == Trip.FORMAT_DRIVER_STATUS:
            form = EditTemplateDriverStatusForm(request.POST)
        else:
            form = EditTemplateTripForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#trip_' + str(trip.id)
            return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':trip.parent.id}) + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('template-trip-delete', kwargs={'parent':trip.parent.id, 'id':trip.id}))

        if form.is_valid():
            old_parent = trip.parent
            trip.parent = form.cleaned_data['parent']

            if trip.format == Trip.FORMAT_ACTIVITY:
                trip.status = form.cleaned_data['status']
                trip.pick_up_time = form.cleaned_data['start_time']
                trip.appointment_time = form.cleaned_data['end_time']
                trip.note = form.cleaned_data['description']

                if trip.pick_up_time == trip.appointment_time:
                    trip.appointment_time = ''
            elif trip.format == Trip.FORMAT_DRIVER_STATUS:
                trip.driver = form.cleaned_data['driver']
                trip.pick_up_time = form.cleaned_data['start_time']
                trip.appointment_time = form.cleaned_data['end_time']
                trip.note = form.cleaned_data['notes']
                trip.passenger = form.cleaned_data['is_available']

                if trip.pick_up_time == trip.appointment_time:
                    trip.appointment_time = ''
            else:
                trip.status = form.cleaned_data['status']
                trip.driver = form.cleaned_data['driver']
                trip.vehicle = form.cleaned_data['vehicle']
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
                trip.fare = money_string_to_int(form.cleaned_data['fare'])
                trip.passenger = form.cleaned_data['passenger']

            # trip date changed, which means sort indexes need to be updated
            if old_parent != trip.parent:
                # decrease sort indexes on the old parent to fill in the gap
                if not is_new:
                    trips_below = TemplateTrip.objects.filter(parent=old_parent, sort_index__gt=trip.sort_index)
                    for i in trips_below:
                        i.sort_index -= 1
                        i.save()
                # set the sort index on the new parent
                query = TemplateTrip.objects.filter(parent=trip.parent).order_by('-sort_index')
                if len(query) > 0:
                    trip.sort_index = query[0].sort_index + 1
                else:
                    trip.sort_index = 0

            trip.save()

            if trip.format == Trip.FORMAT_ACTIVITY:
                log_model = LoggedEventModel.TEMPLATE_TRIP_ACTIVITY
            elif trip.format == Trip.FORMAT_DRIVER_STATUS:
                log_model = LoggedEventModel.TEMPLATE_DRIVER_STATUS
            else:
                log_model = LoggedEventModel.TEMPLATE_TRIP

            if is_new:
                log_event(request, LoggedEventAction.CREATE, log_model, str(trip))
            else:
                log_event(request, LoggedEventAction.EDIT, log_model, str(trip))

            if is_new and not is_return_trip and trip.format == Trip.FORMAT_NORMAL:
                if form.cleaned_data['add_client'] == True:
                    client = Client()
                    client.name = form.cleaned_data['name']
                    client.address = form.cleaned_data['address']
                    client.phone_home = form.cleaned_data['phone_home']
                    client.phone_cell = form.cleaned_data['phone_cell']
                    client.elderly = form.cleaned_data['elderly']
                    client.ambulatory = form.cleaned_data['ambulatory']
                    client.save()
                    log_event(request, LoggedEventAction.CREATE, LoggedEventModel.CLIENT, str(client))
                if form.cleaned_data['add_dest1'] == True:
                    destination = Destination()
                    destination.address = form.cleaned_data['address']
                    destination.phone = form.cleaned_data['phone_address']
                    destination.save()
                if form.cleaned_data['add_dest2'] == True:
                    destination = Destination()
                    destination.address = form.cleaned_data['destination']
                    destination.phone = form.cleaned_data['phone_destination']
                    destination.save()

                if form.cleaned_data['create_return_trip'] == True:
                    return HttpResponseRedirect(reverse('template-trip-create-return', kwargs={'parent':trip.parent.id, 'id':trip.id}))

            return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':trip.parent.id}) + '#trip_' + str(trip.id))
    else:
        if trip.format == Trip.FORMAT_ACTIVITY:
            initial = {
                'parent': trip.parent,
                'start_time': trip.pick_up_time,
                'end_time': trip.appointment_time,
                'description': trip.note,
                'status': trip.status,
            }
            form = EditTemplateActivityForm(initial=initial)
        elif trip.format == Trip.FORMAT_DRIVER_STATUS:
            initial = {
                'parent': trip.parent,
                'driver': trip.driver,
                'start_time': trip.pick_up_time,
                'end_time': trip.appointment_time,
                'notes': trip.note,
                'is_available': False if is_new else trip.passenger,
            }
            form = EditTemplateDriverStatusForm(initial=initial)
        else:
            initial = {
                'parent': trip.parent,
                'driver': trip.driver,
                'vehicle': trip.vehicle,
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
                'status': trip.status,
                'fare': int_to_money_string(trip.fare, blank_zero=True),
                'passenger': trip.passenger,
            }
            form = EditTemplateTripForm(initial=initial)

    addresses = set()
    destinations = Destination.objects.filter(is_active=True)

    if len(destinations) == 0:
        site_settings = SiteSettings.load()
        if site_settings.autocomplete_history_days > 0:
            for i in Trip.objects.filter(date__gte=(datetime.date.today() - datetime.timedelta(days=site_settings.autocomplete_history_days-1))):
                if i.address:
                    addresses.add(str(i.address))
                if i.destination:
                    addresses.add(str(i.destination))

    clients = Client.objects.filter(is_active=True)

    context = {
        'form': form,
        'trip': trip,
        'clients': clients,
        'clients_json': serializers.serialize('json', clients),
        'addresses': sorted(addresses),
        'destinations': destinations,
        'destinations_json': serializers.serialize('json', destinations),
        'is_new': is_new,
        'is_return_trip': is_return_trip,
        'tags': Tag.objects.all(),
        'fares': Fare.objects.all(),
        'Trip': Trip,
    }

    return render(request, 'template/trip/edit.html', context)

@permission_required(['transit.delete_templatetrip'])
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

        log_model = LoggedEventModel.TEMPLATE_TRIP_ACTIVITY if trip.format == Trip.FORMAT_ACTIVITY else LoggedEventModel.TEMPLATE_TRIP
        log_event(request, LoggedEventAction.DELETE, log_model, str(trip))

        trip.delete()
        return HttpResponseRedirect(reverse('template-trips', kwargs={'parent':parent}))

    context = {
        'model': trip,
    }

    return render(request, 'model_delete.html', context)

def ajaxTemplateTripList(request, parent):
    if not request.user.has_perm('transit.view_templatetrip'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_templatetrip'):
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
        elif request_action == 'toggle_canceled':
            trip = get_object_or_404(TemplateTrip, id=request_id)
            if request_data == '0':
                trip.status = Trip.STATUS_NORMAL
            elif request_data == '1':
                trip.status = Trip.STATUS_CANCELED
            trip.save()
            log_model = LoggedEventModel.TEMPLATE_TRIP_ACTIVITY if trip.format == Trip.FORMAT_ACTIVITY else LoggedEventModel.TEMPLATE_TRIP
            log_event(request, LoggedEventAction.STATUS, log_model, str(trip))

    if request_action == 'toggle_extra_columns':
        request.session['template_extra_columns'] = not request.session.get('template_extra_columns', False)

    trips = TemplateTrip.objects.filter(parent=parent)

    context = {
        'parent': parent,
        'trips': trips,
        'template': Template.objects.get(id=parent),
        'show_extra_columns': request.session.get('template_extra_columns', False),
        'Trip': Trip,
    }
    return render(request, 'template/trip/ajax_list.html', context=context)


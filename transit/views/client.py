import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q

from transit.models import Client, Trip, FrequentTag, TemplateTrip, SiteSettings
from transit.forms import EditClientForm

def clientList(request):
    context = {
        'clients': Client.objects.all(),
    }
    return render(request, 'client/list.html', context=context)

def clientCreate(request):
    client = Client()
    return clientCreateEditCommon(request, client, is_new=True)

def clientEdit(request, id):
    client = get_object_or_404(Client, id=id)
    return clientCreateEditCommon(request, client, is_new=False)

def clientCreateEditCommon(request, client, is_new, is_dupe=False, src_trip=None, src_template_trip=None):
    if request.method == 'POST':
        form = EditClientForm(request.POST)

        if 'cancel' in request.POST:
            if src_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_trip.date.year, 'month':src_trip.date.month, 'day':src_trip.date.day}) + '#trip_' + str(src_trip.id))
            elif src_template_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_template_trip.date.year, 'month':src_template_trip.date.month, 'day':src_template_trip.date.day}) + '#trip_' + str(src_template_trip.id))
            else:
                url_hash = '' if is_new else '#client_' + str(client.id)
                return HttpResponseRedirect(reverse('clients') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('client-delete', kwargs={'id':client.id}))

        if form.is_valid():
            existing_clients = Client.objects.filter(name=form.cleaned_data['name'])
            if len(existing_clients) > 0:
                unique_client = existing_clients[0]
            else:
                unique_client = client

            FrequentTag.removeTags(unique_client.get_tag_list())

            unique_client.name = form.cleaned_data['name']
            unique_client.address = form.cleaned_data['address']
            unique_client.phone_home = form.cleaned_data['phone_home']
            unique_client.phone_cell = form.cleaned_data['phone_cell']
            unique_client.elderly = form.cleaned_data['elderly']
            unique_client.ambulatory = form.cleaned_data['ambulatory']
            unique_client.tags = form.cleaned_data['tags']

            FrequentTag.addTags(unique_client.get_tag_list())

            unique_client.save()

            if src_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_trip.date.year, 'month':src_trip.date.month, 'day':src_trip.date.day}) + '#trip_' + str(src_trip.id))
            elif src_template_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_template_trip.date.year, 'month':src_template_trip.date.month, 'day':src_template_trip.date.day}) + '#trip_' + str(src_template_trip.id))
            else:
                return HttpResponseRedirect(reverse('clients') + '#client_' + str(unique_client.id))
    else:
        initial = {
            'name': client.name,
            'address': client.address,
            'phone_home': client.phone_home,
            'phone_cell': client.phone_cell,
            'elderly': client.elderly,
            'ambulatory': client.ambulatory,
            'tags': client.tags,
        }
        form = EditClientForm(initial=initial)

    site_settings = SiteSettings.load()

    names = set()
    addresses = set()
    if site_settings.autocomplete_history_days > 0:
        for i in Trip.objects.filter(date__gte=(datetime.date.today() - datetime.timedelta(days=site_settings.autocomplete_history_days-1))):
            if i.name:
                names.add(str(i.name))
            if i.address:
                addresses.add(str(i.address))
            if i.destination:
                addresses.add(str(i.destination))

    context = {
        'form': form,
        'client': client,
        'is_new': is_new,
        'frequent_tags': FrequentTag.objects.all()[:10],
        'names': sorted(names),
        'addresses': sorted(addresses),
        'is_dupe': is_dupe,
    }

    return render(request, 'client/edit.html', context)

def clientDelete(request, id):
    client = get_object_or_404(Client, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('client-edit', kwargs={'id':id}))

        client.delete()
        return HttpResponseRedirect(reverse('clients'))

    context = {
        'model': client,
    }

    return render(request, 'model_delete.html', context)

def clientCreateFromTrip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    existing_clients = Client.objects.filter(name=trip.name)
    if len(existing_clients) > 0:
        return clientCreateEditCommon(request, existing_clients[0], is_new=False, is_dupe=True, src_trip=trip)

    client = Client()
    client.name = trip.name
    client.address = trip.address
    client.phone_home = trip.phone_home
    client.phone_cell = trip.phone_cell
    client.elderly = trip.elderly
    client.ambulatory = trip.ambulatory
    return clientCreateEditCommon(request, client, is_new=True)

def clientCreateFromTemplateTrip(request, trip_id):
    trip = get_object_or_404(TemplateTrip, id=trip_id)

    existing_clients = Client.objects.filter(name=trip.name)
    if len(existing_clients) > 0:
        return clientCreateEditCommon(request, existing_clients[0], is_new=False, is_dupe=True, src_template_trip=trip)

    client = Client()
    client.name = trip.name
    client.address = trip.address
    client.phone_home = trip.phone_home
    client.phone_cell = trip.phone_cell
    client.elderly = trip.elderly
    client.ambulatory = trip.ambulatory
    return clientCreateEditCommon(request, client, is_new=True)

def ajaxClientList(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'filter_elderly':
        request.session['clients_elderly'] = int(request_data)
    elif request_action == 'filter_ambulatory':
        request.session['clients_ambulatory'] = int(request_data)
    elif request_action == 'filter_search':
        request.session['clients_search'] = request_data
    elif request_action == 'filter_reset':
        request.session['clients_elderly'] = 0
        request.session['clients_ambulatory'] = 0
        request.session['clients_search'] = ''
    elif request_action == 'toggle_extra_columns':
        request.session['clients_extra_columns'] = not request.session.get('clients_extra_columns', False)

    filter_elderly = request.session.get('clients_elderly', 0)
    filter_ambulatory = request.session.get('clients_ambulatory', 0)
    filter_search = request.session.get('clients_search', '')

    clients = Client.objects.all()
    unfiltered_count = len(clients)

    if filter_elderly == 1:
        clients = clients.filter(elderly=True)
    elif filter_elderly == 2:
        clients = clients.filter(elderly=False)

    if filter_ambulatory == 1:
        clients = clients.filter(ambulatory=True)
    elif filter_ambulatory == 2:
        clients = clients.filter(ambulatory=False)

    if filter_search != '':
        clients = clients.filter(Q(name__icontains=filter_search) | Q(address__icontains=filter_search))

    filtered_count = len(clients)

    context = {
        'clients': clients,
        'filter_elderly': filter_elderly,
        'filter_ambulatory': filter_ambulatory,
        'filter_search': filter_search,
        'is_filtered': (filter_elderly > 0 or filter_ambulatory > 0 or filter_search != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'show_extra_columns': request.session.get('clients_extra_columns', False),
    }
    return render(request, 'client/ajax_list.html', context=context)


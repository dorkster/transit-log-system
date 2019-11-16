import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q

from transit.models import Client, Trip, FrequentTag
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

def clientCreateEditCommon(request, client, is_new):
    if request.method == 'POST':
        form = EditClientForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#client_' + str(client.id)
            return HttpResponseRedirect(reverse('clients') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('client-delete', kwargs={'id':client.id}))

        if form.is_valid():
            FrequentTag.removeTags(client.get_tag_list())

            client.name = form.cleaned_data['name']
            client.address = form.cleaned_data['address']
            client.phone_home = form.cleaned_data['phone_home']
            client.phone_cell = form.cleaned_data['phone_cell']
            client.elderly = form.cleaned_data['elderly']
            client.ambulatory = form.cleaned_data['ambulatory']
            client.tags = form.cleaned_data['tags']

            FrequentTag.addTags(client.get_tag_list())

            client.save()

            return HttpResponseRedirect(reverse('clients') + '#client_' + str(client.id))
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

    context = {
        'form': form,
        'client': client,
        'is_new': is_new,
        'frequent_tags': FrequentTag.objects.all()[:10]
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

    # TODO search for existing client?
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
    }
    return render(request, 'client/ajax_list.html', context=context)


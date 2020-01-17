import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Destination, Trip, SiteSettings
from transit.forms import EditDestinationForm

def destinationList(request):
    context = {
        'destination': Destination.objects.all(),
    }
    return render(request, 'destination/list.html', context=context)

def destinationCreate(request):
    destination = Destination()
    return destinationCreateEditCommon(request, destination, is_new=True)

def destinationEdit(request, id):
    destination = get_object_or_404(Destination, id=id)
    return destinationCreateEditCommon(request, destination, is_new=False)

def destinationCreateEditCommon(request, destination, is_new):
    if request.method == 'POST':
        form = EditDestinationForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#destination_' + str(destination.id)
            return HttpResponseRedirect(reverse('destinations') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('destination-delete', kwargs={'id':destination.id}))

        if form.is_valid():
            existing_destinations = Destination.objects.filter(address=form.cleaned_data['address'])
            if len(existing_destinations) > 0:
                unique_destination = existing_destinations[0]
            else:
                unique_destination = destination

            unique_destination.address = form.cleaned_data['address']
            unique_destination.phone = form.cleaned_data['phone']
            unique_destination.save()

            return HttpResponseRedirect(reverse('destinations') + '#destination_' + str(unique_destination.id))
    else:
        initial = {
            'address': destination.address,
            'phone': destination.phone,
        }
        form = EditDestinationForm(initial=initial)

    site_settings = SiteSettings.load()

    addresses = set()
    if site_settings.autocomplete_history_days > 0:
        for i in Trip.objects.filter(date__gte=(datetime.date.today() - datetime.timedelta(days=site_settings.autocomplete_history_days-1))):
            if i.address:
                addresses.add(str(i.address))
            if i.destination:
                addresses.add(str(i.destination))

    context = {
        'form': form,
        'destination': destination,
        'is_new': is_new,
        'addresses': sorted(addresses),
    }

    return render(request, 'destination/edit.html', context)

def destinationDelete(request, id):
    destination = get_object_or_404(Destination, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('destination-edit', kwargs={'id':id}))

        destination.delete()
        return HttpResponseRedirect(reverse('destinations'))

    context = {
        'model': destination,
    }

    return render(request, 'model_delete.html', context)

def ajaxDestinationList(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    destination = Destination.objects.all()
    return render(request, 'destination/ajax_list.html', {'destinations': destination})


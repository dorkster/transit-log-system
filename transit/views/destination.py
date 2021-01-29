import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Destination, Trip, SiteSettings, TemplateTrip
from transit.forms import EditDestinationForm

from django.contrib.auth.decorators import permission_required

@permission_required(['transit.view_destination'])
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

@permission_required(['transit.change_destination'])
def destinationCreateEditCommon(request, destination, is_new, is_dupe=False, src_trip=None, src_template_trip=None):
    if request.method == 'POST':
        form = EditDestinationForm(request.POST)

        if 'cancel' in request.POST:
            if src_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_trip.date.year, 'month':src_trip.date.month, 'day':src_trip.date.day}) + '#trip_' + str(src_trip.id))
            elif src_template_trip != None:
                return HttpResponseRedirect(reverse('template-trips', kwargs={'parent': src_template_trip.parent.id}) + '#trip_' + str(src_template_trip.id))
            else:
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

            if src_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_trip.date.year, 'month':src_trip.date.month, 'day':src_trip.date.day}) + '#trip_' + str(src_trip.id))
            elif src_template_trip != None:
                return HttpResponseRedirect(reverse('template-trips', kwargs={'parent': src_template_trip.parent.id}) + '#trip_' + str(src_template_trip.id))
            else:
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
        'is_dupe': is_dupe,
    }

    return render(request, 'destination/edit.html', context)

@permission_required(['transit.delete_destination'])
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

@permission_required(['transit.change_destination'])
def destinationCreateFromTrip(request, trip_id, use_address):
    trip = get_object_or_404(Trip, id=trip_id)

    if use_address == 1:
        target_address = trip.address
        target_phone = trip.phone_address
    else:
        # 'destination' is the default
        target_address = trip.destination
        target_phone = trip.phone_destination

    existing_destinations = Destination.objects.filter(address=target_address)
    if len(existing_destinations) > 0:
        return destinationCreateEditCommon(request, existing_destinations[0], is_new=False, is_dupe=True, src_trip=trip)

    destination = Destination()
    destination.address = target_address
    destination.phone = target_phone
    return destinationCreateEditCommon(request, destination, is_new=True, src_trip=trip)

@permission_required(['transit.change_destination'])
def destinationCreateFromTemplateTrip(request, trip_id, use_address):
    trip = get_object_or_404(TemplateTrip, id=trip_id)

    if use_address == 1:
        target_address = trip.address
        target_phone = trip.phone_address
    else:
        # 'destination' is the default
        target_address = trip.destination
        target_phone = trip.phone_destination

    existing_destinations = Destination.objects.filter(address=target_address)
    if len(existing_destinations) > 0:
        return destinationCreateEditCommon(request, existing_destinations[0], is_new=False, is_dupe=True, src_template_trip=trip)

    destination = Destination()
    destination.address = target_address
    destination.phone = target_phone
    return destinationCreateEditCommon(request, destination, is_new=True, src_template_trip=trip)

def ajaxDestinationList(request):
    if not request.user.has_perm('transit.view_destination'):
        return HttpResponseRedirect(reverse('login_redirect'))

    SORT_ADDRESS = 0
    SORT_PHONE = 1

    sort_mode = request.session.get('destinations_sort', SORT_ADDRESS)
    sort_mode_dir = request.session.get('destinations_sort_dir', 0)

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'filter_search':
        request.session['destinations_search'] = request_data
    elif request_action == 'filter_reset':
        request.session['destinations_search'] = ''
    elif request_action == 'sort':
        new_sort_mode = int(request_data)
        if sort_mode == new_sort_mode:
            sort_mode_dir = 1 if sort_mode_dir == 0 else 0
        else:
            sort_mode_dir = 0
        sort_mode = new_sort_mode
        request.session['destinations_sort'] = new_sort_mode
        request.session['destinations_sort_dir'] = sort_mode_dir

    filter_search = request.session.get('destinations_search', '')

    destinations = Destination.objects.all()
    unfiltered_count = len(destinations)

    if filter_search != '':
        destinations = destinations.filter(address__icontains=filter_search)

    filtered_count = len(destinations)

    if sort_mode == SORT_ADDRESS:
        destinations = destinations.order_by('address')
    elif sort_mode == SORT_PHONE:
        destinations = destinations.order_by('phone', 'address')

    if sort_mode_dir == 1:
        destinations = destinations.reverse()

    context = {
        'destinations': destinations,
        'filter_search': filter_search,
        'is_filtered': (filter_search != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'sort_mode': sort_mode,
        'sort_mode_dir': sort_mode_dir,
    }
    return render(request, 'destination/ajax_list.html', context=context)


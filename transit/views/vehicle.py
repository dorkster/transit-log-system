import uuid
import json

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Vehicle, Shift, PreTrip
from transit.forms import EditVehicleForm, vehicleMaintainForm, vehiclePreTripForm

from django.contrib.auth.decorators import permission_required

def vehicleList(request):
    context = {
        'vehicle': Vehicle.objects.all(),
    }
    return render(request, 'vehicle/list.html', context=context)

def vehicleCreate(request):
    vehicle = Vehicle()
    return vehicleCreateEditCommon(request, vehicle, is_new=True)

def vehicleEdit(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)
    return vehicleCreateEditCommon(request, vehicle, is_new=False)

def vehicleCreateEditCommon(request, vehicle, is_new):
    if is_new == True:
        query = Vehicle.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_vehicle = query[0]
            vehicle.sort_index = last_vehicle.sort_index + 1
        else:
            vehicle.sort_index = 0

    if request.method == 'POST':
        form = EditVehicleForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#vehicle_' + str(vehicle.id)
            return HttpResponseRedirect(reverse('vehicles') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-delete', kwargs={'id':vehicle.id}))

        if form.is_valid():
            vehicle.name = form.cleaned_data['name']
            vehicle.is_logged = form.cleaned_data['is_logged']
            vehicle.save()

            return HttpResponseRedirect(reverse('vehicles') + '#vehicle' + str(vehicle.id))
    else:
        initial = {
            'name': vehicle.name,
            'is_logged': vehicle.is_logged,
        }
        form = EditVehicleForm(initial=initial)

    context = {
        'form': form,
        'vehicle': vehicle,
        'is_new': is_new,
    }

    return render(request, 'vehicle/edit.html', context)

@permission_required('transit.can_delete_vehicle')
def vehicleDelete(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-edit', kwargs={'id':id}))

        query = Vehicle.objects.all()
        for i in query:
            if i.sort_index > vehicle.sort_index:
                i.sort_index -= 1;
                i.save()

        vehicle.delete()
        return HttpResponseRedirect(reverse('vehicles'))

    context = {
        'model': vehicle,
    }

    return render(request, 'model_delete.html', context)

def ajaxVehicleList(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'mv':
        vehicle = get_object_or_404(Vehicle, id=request_id)

        do_sort = False
        if request_data == 'u':
            query = Vehicle.objects.filter(sort_index=vehicle.sort_index-1)
            do_sort = True
        elif request_data == 'd':
            query = Vehicle.objects.filter(sort_index=vehicle.sort_index+1)
            do_sort = True

        if do_sort and len(query) > 0:
            swap_index = query[0].sort_index
            query[0].sort_index = vehicle.sort_index
            vehicle.sort_index = swap_index
            query[0].save()
            vehicle.save()

    vehicles = Vehicle.objects.all()
    return render(request, 'vehicle/ajax_list.html', {'vehicles': vehicles})

def vehicleMaintainEdit(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)

    if request.method == 'POST':
        form = vehicleMaintainForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-status'))

        if form.is_valid():
            vehicle.oil_change_miles = form.cleaned_data['oil_change_miles']
            vehicle.inspection_date = form.cleaned_data['inspection_date']
            vehicle.save()

            return HttpResponseRedirect(reverse('vehicle-status'))
    else:
        initial = {
            'oil_change_miles': vehicle.oil_change_miles,
            'inspection_date': vehicle.inspection_date,
        }
        form = vehicleMaintainForm(initial=initial)

    context = {
        'form': form,
        'vehicle': vehicle,
    }

    return render(request, 'vehicle/maintain.html', context)

def vehiclePreTripCreate(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)

    if request.method == 'POST':
        form = vehiclePreTripForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))

        if form.is_valid():
            pretrip = PreTrip()
            pretrip.date = shift.date
            pretrip.driver = shift.driver
            pretrip.vehicle = shift.vehicle
            pretrip.shift_id = shift_id

            if form.cleaned_data['checklist'] != '':
                cl = json.loads(form.cleaned_data['checklist'])
                pretrip.cl_fluids = cl['cl_fluids']
                pretrip.cl_engine = cl['cl_engine']
                pretrip.cl_headlights = cl['cl_headlights']
                pretrip.cl_hazards = cl['cl_hazards']
                pretrip.cl_directional = cl['cl_directional']
                pretrip.cl_markers = cl['cl_markers']
                pretrip.cl_windshield = cl['cl_windshield']
                pretrip.cl_glass = cl['cl_glass']
                pretrip.cl_mirrors = cl['cl_mirrors']
                pretrip.cl_doors = cl['cl_doors']
                pretrip.cl_tires = cl['cl_tires']
                pretrip.cl_leaks = cl['cl_leaks']
                pretrip.cl_body = cl['cl_body']
                pretrip.cl_registration = cl['cl_registration']
                pretrip.cl_wheelchair = cl['cl_wheelchair']
                pretrip.cl_mechanical = cl['cl_mechanical']
                pretrip.cl_interior = cl['cl_interior']

                pretrip.save()

                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'view', 'year':shift.date.year, 'month':shift.date.month, 'day':shift.date.day}))
    else:
        form = vehiclePreTripForm()

    checklist = {
        'cl_fluids': {'label': 'All Fuel & Fluids', 'subitems': ('Gas', 'Oil', 'Anti-Freeze', 'Windshield Wash')},
        'cl_engine': {'label': 'Start Engine'},
        'cl_headlights': {'label': 'Head Lights / High Beams'},
        'cl_hazards': {'label': 'Hazards / Ambers'},
        'cl_directional': {'label': 'Directional'},
        'cl_markers': {'label': 'Markers / Reflectors'},
        'cl_windshield': {'label': 'Windshield'},
        'cl_glass': {'label': 'All Other Glass'},
        'cl_mirrors': {'label': 'All Mirrors'},
        'cl_doors': {'label': 'All Door Operation'},
        'cl_tires': {'label': 'Tires', 'subitems': ('Pressure', 'Condition')},
        'cl_leaks': {'label': 'Leaks of Any Kind'},
        'cl_body': {'label': 'Body Damage'},
        'cl_registration': {'label': 'Registration', 'subitems': ('Plate', 'Sticker')},
        'cl_wheelchair': {'label': 'Wheelchair Lift', 'subitems': ('Condition', 'Operation')},
        'cl_mechanical': {'label': 'Mechanical'},
        'cl_interior': {'label': 'Interior', 'subitems': ('Lights', 'Seats', 'Belts', 'Registration & Insurance Paperwork', 'Cleanliness', 'Horn', 'Fire Extinguisher', 'First Aid Kit', 'Entry Steps', 'Floor Covering', 'All wheelchair track and harnessing', 'All assigned van electronics (communication & navigational)', 'Personal belongings left behind')},
    }
    context = {
        'form': form,
        'shift': shift,
        'checklist': checklist,
    }
    return render(request, 'vehicle/pretrip.html', context=context)

@permission_required('transit.can_delete_pretrip')
def vehiclePreTripDelete(request, id):
    pretrip = get_object_or_404(PreTrip, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-status'))

        pretrip.delete()
        return HttpResponseRedirect(reverse('vehicle-status'))

    context = {
        'model': pretrip,
    }

    return render(request, 'model_delete.html', context)


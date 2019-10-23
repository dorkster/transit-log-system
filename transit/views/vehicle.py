import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Vehicle
from transit.forms import EditVehicleForm

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
            return HttpResponseRedirect(reverse('vehicles') + "#vehicle" + str(vehicle.id))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-delete', kwargs={'id':vehicle.id}))

        if form.is_valid():
            vehicle.name = form.cleaned_data['name']
            vehicle.is_logged = form.cleaned_data['is_logged']
            vehicle.save()

            return HttpResponseRedirect(reverse('vehicles') + "#vehicle" + str(vehicle.id))
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
    return render(request, 'vehicle/ajax/list.html', {'vehicles': vehicles})


import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Driver
from transit.forms import EditDriverForm

from django.contrib.auth.decorators import permission_required

def driverList(request):
    context = {
        'driver': Driver.objects.all(),
    }
    return render(request, 'driver/list.html', context=context)

def driverCreate(request):
    driver = Driver()
    return driverCreateEditCommon(request, driver, is_new=True)

def driverEdit(request, id):
    driver = get_object_or_404(Driver, id=id)
    return driverCreateEditCommon(request, driver, is_new=False)

def driverCreateEditCommon(request, driver, is_new):
    if is_new == True:
        query = Driver.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_driver = query[0]
            driver.sort_index = last_driver.sort_index + 1
        else:
            driver.sort_index = 0

    if request.method == 'POST':
        form = EditDriverForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#driver_' + str(driver.id)
            return HttpResponseRedirect(reverse('drivers') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('driver-delete', kwargs={'id':driver.id}))

        if form.is_valid():
            driver.name = form.cleaned_data['name']
            driver.color = form.cleaned_data['color']
            driver.is_logged = form.cleaned_data['is_logged']
            driver.save()

            return HttpResponseRedirect(reverse('drivers') + '#driver_' + str(driver.id))
    else:
        initial = {
            'name': driver.name,
            'color': driver.color,
            'is_logged': driver.is_logged,
        }
        form = EditDriverForm(initial=initial)

    context = {
        'form': form,
        'driver': driver,
        'is_new': is_new,
    }

    return render(request, 'driver/edit.html', context)

@permission_required('transit.can_delete_driver')
def driverDelete(request, id):
    driver = get_object_or_404(Driver, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('driver-edit', kwargs={'id':id}))

        query = Driver.objects.all()
        for i in query:
            if i.sort_index > driver.sort_index:
                i.sort_index -= 1;
                i.save()

        driver.delete()
        return HttpResponseRedirect(reverse('drivers'))

    context = {
        'model': driver,
    }

    return render(request, 'model_delete.html', context)

def ajaxDriverList(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'mv':
        driver = get_object_or_404(Driver, id=request_id)
        original_index = driver.sort_index
        driver.sort_index = -1

        # "remove" the selected item by shifting everything below it up by 1
        below_items = Driver.objects.filter(sort_index__gt=original_index)
        for i in below_items:
            i.sort_index -= 1;
            i.save()

        if request_data == '':
            new_index = 0
        else:
            target_item = get_object_or_404(Driver, id=request_data)
            if driver.id != target_item.id:
                new_index = target_item.sort_index + 1
            else:
                new_index = original_index

        # prepare to insert the item at the new index by shifting everything below it down by 1
        below_items = Driver.objects.filter(sort_index__gte=new_index)
        for i in below_items:
            i.sort_index += 1
            i.save()

        driver.sort_index = new_index
        driver.save()

    drivers = Driver.objects.all()
    return render(request, 'driver/ajax_list.html', {'drivers': drivers})


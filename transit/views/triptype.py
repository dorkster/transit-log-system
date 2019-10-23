import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import TripType
from transit.forms import EditTripTypeForm

def triptypeList(request):
    context = {
        'triptype': TripType.objects.all(),
    }
    return render(request, 'triptype/list.html', context=context)

def triptypeCreate(request):
    triptype = TripType()
    return triptypeCreateEditCommon(request, triptype, is_new=True)

def triptypeEdit(request, id):
    triptype = get_object_or_404(TripType, id=id)
    return triptypeCreateEditCommon(request, triptype, is_new=False)

def triptypeCreateEditCommon(request, triptype, is_new):
    if is_new == True:
        query = TripType.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_triptype = query[0]
            triptype.sort_index = last_triptype.sort_index + 1
        else:
            triptype.sort_index = 0

    if request.method == 'POST':
        form = EditTripTypeForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('triptypes') + "#triptype" + str(triptype.id))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('triptype-delete', kwargs={'id':triptype.id}))

        if form.is_valid():
            triptype.name = form.cleaned_data['name']
            triptype.save()

            return HttpResponseRedirect(reverse('triptypes') + "#triptype" + str(triptype.id))
    else:
        initial = {
            'name': triptype.name,
        }
        form = EditTripTypeForm(initial=initial)

    context = {
        'form': form,
        'triptype': triptype,
        'is_new': is_new,
    }

    return render(request, 'triptype/edit.html', context)

def triptypeDelete(request, id):
    triptype = get_object_or_404(TripType, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('triptype-edit', kwargs={'id':id}))

        query = TripType.objects.all()
        for i in query:
            if i.sort_index > triptype.sort_index:
                i.sort_index -= 1;
                i.save()

        triptype.delete()
        return HttpResponseRedirect(reverse('triptypes'))

    context = {
        'model': triptype,
    }

    return render(request, 'model_delete.html', context)

def ajaxTripTypeList(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'mv':
        triptype = get_object_or_404(TripType, id=request_id)

        do_sort = False
        if request_data == 'u':
            query = TripType.objects.filter(sort_index=triptype.sort_index-1)
            do_sort = True
        elif request_data == 'd':
            query = TripType.objects.filter(sort_index=triptype.sort_index+1)
            do_sort = True

        if do_sort and len(query) > 0:
            swap_index = query[0].sort_index
            query[0].sort_index = triptype.sort_index
            triptype.sort_index = swap_index
            query[0].save()
            triptype.save()

    triptypes = TripType.objects.all()
    return render(request, 'triptype/ajax/list.html', {'triptypes': triptypes})


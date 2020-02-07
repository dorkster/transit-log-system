import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import TripType
from transit.forms import EditTripTypeForm

from django.contrib.auth.decorators import permission_required

@permission_required(['transit.view_triptype'])
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

@permission_required(['transit.change_triptype'])
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
            url_hash = '' if is_new else '#triptype_' + str(triptype.id)
            return HttpResponseRedirect(reverse('triptypes') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('triptype-delete', kwargs={'id':triptype.id}))

        if form.is_valid():
            triptype.name = form.cleaned_data['name']
            triptype.save()

            return HttpResponseRedirect(reverse('triptypes') + '#triptype_' + str(triptype.id))
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

@permission_required('transit.delete_triptype')
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

@permission_required(['transit.view_triptype'])
def ajaxTripTypeList(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_triptype'):
        if request_action == 'mv':
            triptype = get_object_or_404(TripType, id=request_id)
            original_index = triptype.sort_index
            triptype.sort_index = -1

            # "remove" the selected item by shifting everything below it up by 1
            below_items = TripType.objects.filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(TripType, id=request_data)
                if triptype.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the item at the new index by shifting everything below it down by 1
            below_items = TripType.objects.filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            triptype.sort_index = new_index
            triptype.save()

    triptypes = TripType.objects.all()
    return render(request, 'triptype/ajax_list.html', {'triptypes': triptypes})


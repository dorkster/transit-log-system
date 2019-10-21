import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Client
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
            return HttpResponseRedirect(reverse('clients') + "#client_" + str(client.id))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('client-delete', kwargs={'id':client.id}))

        if form.is_valid():
            client.name = form.cleaned_data['name']
            client.address = form.cleaned_data['address']
            client.phone_home = form.cleaned_data['phone_home']
            client.phone_mobile = form.cleaned_data['phone_mobile']
            client.phone_default = form.cleaned_data['phone_default']
            client.elderly = form.cleaned_data['elderly']
            client.ambulatory = form.cleaned_data['ambulatory']
            client.save()

            return HttpResponseRedirect(reverse('clients') + "#client_" + str(client.id))
    else:
        initial = {
            'name': client.name,
            'address': client.address,
            'phone_home': client.phone_home,
            'phone_mobile': client.phone_mobile,
            'phone_default': client.phone_default,
            'elderly': client.elderly,
            'ambulatory': client.ambulatory,
        }
        form = EditClientForm(initial=initial)

    context = {
        'form': form,
        'client': client,
        'is_new': is_new,
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

def ajaxClientList(request):
    request_id = ''
    if request.GET['client_id'] != '':
        request_id = uuid.UUID(request.GET['trip_id'])

    request_action = request.GET['client_action']
    request_data = request.GET['client_data']

    clients = Client.objects.all()
    return render(request, 'client/ajax/list.html', {'clients': clients})


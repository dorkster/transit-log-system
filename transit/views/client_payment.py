import uuid
import datetime
import re

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Client, ClientPayment
from transit.forms import EditClientPaymentForm

from django.contrib.auth.decorators import permission_required

def moneyParse(value):
    num_only = ''
    matches = re.findall('\d*', value)
    for i in matches:
        num_only += i

    if num_only == '':
        return 0
    else:
        return int(num_only)

def moneyFormat(value):
    if value == 0:
        return ''

    s = str(value)
    return s[:len(s)-2] + '.' + s[len(s)-2:]

@permission_required(['transit.view_clientpayment'])
def clientPaymentList(request, parent):
    context = {
        'parent':parent,
        'client_payments': ClientPayment.objects.filter(parent=parent),
    }
    return render(request, 'client/payment/list.html', context=context)

def clientPaymentCreate(request, parent):
    client_payment = ClientPayment()
    client_payment.parent = Client.objects.get(id=parent)
    return clientPaymentCreateEditCommon(request, client_payment, is_new=True)

def clientPaymentEdit(request, parent, id):
    client_payment = get_object_or_404(ClientPayment, id=id)
    return clientPaymentCreateEditCommon(request, client_payment, is_new=False)

@permission_required(['transit.change_clientpayment'])
def clientPaymentCreateEditCommon(request, client_payment, is_new):
    if is_new:
        client_payment.date_paid = datetime.date.today()

    if request.method == 'POST':
        form = EditClientPaymentForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#payment_' + str(client_payment.id)
            return HttpResponseRedirect(reverse('client-payments', kwargs={'parent':client_payment.parent.id}) + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('client-payment-delete', kwargs={'parent':client_payment.parent.id, 'id':client_payment.id}))

        if form.is_valid():
            client_payment.date_paid = form.cleaned_data['date_paid']
            # TODO money format
            client_payment.cash = moneyParse(form.cleaned_data['cash'])
            client_payment.check = moneyParse(form.cleaned_data['check'])
            client_payment.save()

            return HttpResponseRedirect(reverse('client-payments', kwargs={'parent':client_payment.parent.id}) + '#payment_' + str(client_payment.id))
    else:
        initial = {
            'date_paid': client_payment.date_paid,
            'cash': moneyFormat(client_payment.cash),
            'check': moneyFormat(client_payment.check),
        }
        form = EditClientPaymentForm(initial=initial)

    context = {
        'form': form,
        'client_payment': client_payment,
        'is_new': is_new,
    }

    return render(request, 'client/payment/edit.html', context)

@permission_required(['transit.delete_clientpayment'])
def clientPaymentDelete(request, parent, id):
    client_payment = get_object_or_404(ClientPayment, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('client-payment-edit', kwargs={'parent':client_payment.parent.id, 'id':id}))

        client_payment.delete()
        return HttpResponseRedirect(reverse('client-payments', kwargs={'parent':parent}))

    context = {
        'model': client_payment,
    }

    return render(request, 'model_delete.html', context)

@permission_required(['transit.view_clientpayment'])
def ajaxClientPaymentList(request, parent):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    # TODO column sort?

    client_payments = ClientPayment.objects.filter(parent=parent)

    context = {
        'parent': parent,
        'client_payments': client_payments,
        'client': Client.objects.get(id=parent),
    }
    return render(request, 'client/payment/ajax_list.html', context=context)


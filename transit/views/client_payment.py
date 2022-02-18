# Copyright © 2019-2021 Justin Jacobs
#
# This file is part of the Transit Log System.
#
# The Transit Log System is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# The Transit Log System is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# The Transit Log System.  If not, see http://www.gnu.org/licenses/

import uuid
import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Client, ClientPayment
from transit.forms import EditClientPaymentForm
from transit.views.report import Report

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_clientpayment'])
def clientPaymentList(request, parent):
    # run report to get all fares/payments
    report_date_start = datetime.date(year=2019, month=1, day=1)
    report_date_end = datetime.date(year=datetime.date.today().year+2, month=1, day=1)
    report_client = Client.objects.get(id=parent)
    report = Report()
    report.load(report_date_start, report_date_end, client_name=report_client.name, filter_by_money=True)

    context = {
        'parent':parent,
        'client': Client.objects.get(id=parent),
        'client_payments': ClientPayment.objects.filter(parent=parent),
        'report': report,
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
            client_payment.money_cash = money_string_to_int(form.cleaned_data['cash'])
            client_payment.money_check = money_string_to_int(form.cleaned_data['check'])
            client_payment.save()

            if is_new:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.CLIENT_PAYMENT, str(client_payment))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.CLIENT_PAYMENT, str(client_payment))

            return HttpResponseRedirect(reverse('client-payments', kwargs={'parent':client_payment.parent.id}) + '#payment_' + str(client_payment.id))
    else:
        initial = {
            'date_paid': client_payment.date_paid,
            'cash': int_to_money_string(client_payment.money_cash, blank_zero=True),
            'check': int_to_money_string(client_payment.money_check, blank_zero=True),
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

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.CLIENT_PAYMENT, str(client_payment))

        client_payment.delete()
        return HttpResponseRedirect(reverse('client-payments', kwargs={'parent':parent}))

    context = {
        'model': client_payment,
    }

    return render(request, 'model_delete.html', context)

def ajaxClientPaymentList(request, parent):
    if not request.user.has_perm('transit.view_clientpayment'):
        return HttpResponseRedirect(reverse('login_redirect'))

    SORT_DATE_PAID = 0
    SORT_CASH = 1
    SORT_CHECK = 2

    sort_mode = request.session.get('client_payments_sort', SORT_DATE_PAID)
    sort_mode_dir = request.session.get('client_payments_sort_dir', 0)

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'sort':
        new_sort_mode = int(request_data)
        if sort_mode == new_sort_mode:
            sort_mode_dir = 1 if sort_mode_dir == 0 else 0
        else:
            sort_mode_dir = 0
        sort_mode = new_sort_mode
        request.session['client_payments_sort'] = new_sort_mode
        request.session['client_payments_sort_dir'] = sort_mode_dir

    client_payments = ClientPayment.objects.filter(parent=parent)

    if sort_mode == SORT_DATE_PAID:
        client_payments = client_payments.order_by('date_paid')
    elif sort_mode == SORT_CASH:
        client_payments = client_payments.order_by('cash', 'date_paid')
    elif sort_mode == SORT_CHECK:
        client_payments = client_payments.order_by('check', 'date_paid')

    if sort_mode_dir == 1:
        client_payments = client_payments.reverse()

    context = {
        'parent': parent,
        'client_payments': client_payments,
        'client': Client.objects.get(id=parent),
        'sort_mode': sort_mode,
        'sort_mode_dir': sort_mode_dir,
    }
    return render(request, 'client/payment/ajax_list.html', context=context)


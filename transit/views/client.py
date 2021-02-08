import uuid
import datetime
import tempfile

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.http import FileResponse
from django.urls import reverse
from django.db.models import Q

from transit.models import Client, Trip, Tag, TemplateTrip, SiteSettings
from transit.forms import EditClientForm

from django.contrib.auth.decorators import permission_required

from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.view_client'])
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

@permission_required(['transit.change_client'])
def clientCreateEditCommon(request, client, is_new, is_dupe=False, src_trip=None, src_template_trip=None):
    if request.method == 'POST':
        form = EditClientForm(request.POST)

        if 'cancel' in request.POST:
            if src_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_trip.date.year, 'month':src_trip.date.month, 'day':src_trip.date.day}) + '#trip_' + str(src_trip.id))
            elif src_template_trip != None:
                return HttpResponseRedirect(reverse('template-trips', kwargs={'parent': src_template_trip.parent.id}) + '#trip_' + str(src_template_trip.id))
            else:
                url_hash = '' if is_new else '#client_' + str(client.id)
                return HttpResponseRedirect(reverse('clients') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('client-delete', kwargs={'id':client.id}))

        if form.is_valid():
            is_existing_client = False
            existing_clients = Client.objects.filter(name=form.cleaned_data['name'])
            if len(existing_clients) > 0:
                unique_client = existing_clients[0]
                is_existing_client = True
            else:
                unique_client = client

            unique_client.name = form.cleaned_data['name']
            unique_client.address = form.cleaned_data['address']
            unique_client.phone_home = form.cleaned_data['phone_home']
            unique_client.phone_cell = form.cleaned_data['phone_cell']
            unique_client.elderly = form.cleaned_data['elderly']
            unique_client.ambulatory = form.cleaned_data['ambulatory']
            unique_client.tags = form.cleaned_data['tags']
            unique_client.staff = form.cleaned_data['staff']

            unique_client.save()

            if is_new and not is_existing_client:
                log_event(request, LoggedEventAction.CREATE, LoggedEventModel.CLIENT, str(unique_client))
            else:
                log_event(request, LoggedEventAction.EDIT, LoggedEventModel.CLIENT, str(unique_client))

            if src_trip != None:
                return HttpResponseRedirect(reverse('schedule', kwargs={'mode':'edit', 'year':src_trip.date.year, 'month':src_trip.date.month, 'day':src_trip.date.day}) + '#trip_' + str(src_trip.id))
            elif src_template_trip != None:
                return HttpResponseRedirect(reverse('template-trips', kwargs={'parent': src_template_trip.parent.id}) + '#trip_' + str(src_template_trip.id))
            else:
                return HttpResponseRedirect(reverse('clients') + '#client_' + str(unique_client.id))
    else:
        initial = {
            'name': client.name,
            'address': client.address,
            'phone_home': client.phone_home,
            'phone_cell': client.phone_cell,
            'elderly': client.elderly,
            'ambulatory': client.ambulatory,
            'tags': client.tags,
            'staff': client.staff,
        }
        form = EditClientForm(initial=initial)

    site_settings = SiteSettings.load()

    names = set()
    addresses = set()
    if site_settings.autocomplete_history_days > 0:
        for i in Trip.objects.filter(date__gte=(datetime.date.today() - datetime.timedelta(days=site_settings.autocomplete_history_days-1))):
            if i.name:
                names.add(str(i.name))
            if i.address:
                addresses.add(str(i.address))
            if i.destination:
                addresses.add(str(i.destination))

    context = {
        'form': form,
        'client': client,
        'is_new': is_new,
        'tags': Tag.objects.all(),
        'names': sorted(names),
        'addresses': sorted(addresses),
        'is_dupe': is_dupe,
    }

    return render(request, 'client/edit.html', context)

@permission_required(['transit.delete_client'])
def clientDelete(request, id):
    client = get_object_or_404(Client, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('client-edit', kwargs={'id':id}))

        log_event(request, LoggedEventAction.DELETE, LoggedEventModel.CLIENT, str(client))

        client.delete()
        return HttpResponseRedirect(reverse('clients'))

    context = {
        'model': client,
    }

    return render(request, 'model_delete.html', context)

@permission_required(['transit.change_client'])
def clientCreateFromTrip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    existing_clients = Client.objects.filter(name=trip.name)
    if len(existing_clients) > 0:
        return clientCreateEditCommon(request, existing_clients[0], is_new=False, is_dupe=True, src_trip=trip)

    client = Client()
    client.name = trip.name
    client.address = trip.address
    client.phone_home = trip.phone_home
    client.phone_cell = trip.phone_cell
    client.elderly = trip.elderly
    client.ambulatory = trip.ambulatory
    return clientCreateEditCommon(request, client, is_new=True, src_trip=trip)

@permission_required(['transit.change_client'])
def clientCreateFromTemplateTrip(request, trip_id):
    trip = get_object_or_404(TemplateTrip, id=trip_id)

    existing_clients = Client.objects.filter(name=trip.name)
    if len(existing_clients) > 0:
        return clientCreateEditCommon(request, existing_clients[0], is_new=False, is_dupe=True, src_template_trip=trip)

    client = Client()
    client.name = trip.name
    client.address = trip.address
    client.phone_home = trip.phone_home
    client.phone_cell = trip.phone_cell
    client.elderly = trip.elderly
    client.ambulatory = trip.ambulatory
    return clientCreateEditCommon(request, client, is_new=True, src_template_trip=trip)

def ajaxClientList(request):
    if not request.user.has_perm('transit.view_client'):
        return HttpResponseRedirect(reverse('login_redirect'))

    SORT_NAME = 0
    SORT_ADDRESS = 1
    SORT_PHONE_HOME = 2
    SORT_PHONE_CELL = 3
    SORT_ELDERLY = 4
    SORT_AMBULATORY = 5
    SORT_TAGS = 6

    sort_mode = request.session.get('clients_sort', SORT_NAME)
    sort_mode_dir = request.session.get('clients_sort_dir', 0)

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'filter_elderly':
        request.session['clients_elderly'] = int(request_data)
    elif request_action == 'filter_ambulatory':
        request.session['clients_ambulatory'] = int(request_data)
    elif request_action == 'filter_staff':
        request.session['clients_staff'] = int(request_data)
    elif request_action == 'filter_search':
        request.session['clients_search'] = request_data
    elif request_action == 'filter_reset':
        request.session['clients_elderly'] = 0
        request.session['clients_ambulatory'] = 0
        request.session['clients_staff'] = 0
        request.session['clients_search'] = ''
    elif request_action == 'toggle_extra_columns':
        request.session['clients_extra_columns'] = not request.session.get('clients_extra_columns', False)
    elif request_action == 'sort':
        new_sort_mode = int(request_data)
        if sort_mode == new_sort_mode:
            sort_mode_dir = 1 if sort_mode_dir == 0 else 0
        else:
            sort_mode_dir = 0
        sort_mode = new_sort_mode
        request.session['clients_sort'] = new_sort_mode
        request.session['clients_sort_dir'] = sort_mode_dir

    filter_elderly = request.session.get('clients_elderly', 0)
    filter_ambulatory = request.session.get('clients_ambulatory', 0)
    filter_staff = request.session.get('clients_staff', 0)
    filter_search = request.session.get('clients_search', '')

    clients = Client.objects.all()
    unfiltered_count = len(clients)

    if filter_elderly == 1:
        clients = clients.filter(elderly=True)
    elif filter_elderly == 2:
        clients = clients.filter(elderly=False)

    if filter_ambulatory == 1:
        clients = clients.filter(ambulatory=True)
    elif filter_ambulatory == 2:
        clients = clients.filter(ambulatory=False)

    if filter_staff == 1:
        clients = clients.filter(staff=True)
    elif filter_staff == 2:
        clients = clients.filter(staff=False)

    if filter_search != '':
        clients = clients.filter(Q(name__icontains=filter_search) | Q(address__icontains=filter_search) | Q(tags__icontains=filter_search))

    filtered_count = len(clients)

    if sort_mode == SORT_NAME:
        clients = clients.order_by('name')
    elif sort_mode == SORT_ADDRESS:
        clients = clients.order_by('address', 'name')
    elif sort_mode == SORT_PHONE_HOME:
        clients = clients.order_by('phone_home', 'name')
    elif sort_mode == SORT_PHONE_CELL:
        clients = clients.order_by('phone_cell', 'name')
    elif sort_mode == SORT_ELDERLY:
        clients = clients.order_by('elderly', 'name')
    elif sort_mode == SORT_AMBULATORY:
        clients = clients.order_by('ambulatory', 'name')
    elif sort_mode == SORT_TAGS:
        clients = clients.order_by('tags', 'name')

    if sort_mode_dir == 1:
        clients = clients.reverse()

    context = {
        'clients': clients,
        'filter_elderly': filter_elderly,
        'filter_ambulatory': filter_ambulatory,
        'filter_staff': filter_staff,
        'filter_search': filter_search,
        'is_filtered': (filter_elderly > 0 or filter_ambulatory > 0 or filter_staff > 0 or filter_search != ''),
        'filtered_count': filtered_count,
        'unfiltered_count': unfiltered_count,
        'show_extra_columns': request.session.get('clients_extra_columns', False),
        'sort_mode': sort_mode,
        'sort_mode_dir': sort_mode_dir,
    }
    return render(request, 'client/ajax_list.html', context=context)

@permission_required(['transit.view_client'])
def clientXLSX(request):
    SORT_NAME = 0
    SORT_ADDRESS = 1
    SORT_PHONE_HOME = 2
    SORT_PHONE_CELL = 3
    SORT_ELDERLY = 4
    SORT_AMBULATORY = 5
    SORT_TAGS = 6

    sort_mode = request.session.get('clients_sort', SORT_NAME)
    sort_mode_dir = request.session.get('clients_sort_dir', 0)

    filter_elderly = request.session.get('clients_elderly', 0)
    filter_ambulatory = request.session.get('clients_ambulatory', 0)
    filter_staff = request.session.get('clients_staff', 0)
    filter_search = request.session.get('clients_search', '')

    clients = Client.objects.all()

    if filter_elderly == 1:
        clients = clients.filter(elderly=True)
    elif filter_elderly == 2:
        clients = clients.filter(elderly=False)

    if filter_ambulatory == 1:
        clients = clients.filter(ambulatory=True)
    elif filter_ambulatory == 2:
        clients = clients.filter(ambulatory=False)

    if filter_staff == 1:
        clients = clients.filter(staff=True)
    elif filter_staff == 2:
        clients = clients.filter(staff=False)

    if filter_search != '':
        clients = clients.filter(Q(name__icontains=filter_search) | Q(address__icontains=filter_search) | Q(tags__icontains=filter_search))

    if sort_mode == SORT_NAME:
        clients = clients.order_by('name')
    elif sort_mode == SORT_ADDRESS:
        clients = clients.order_by('address', 'name')
    elif sort_mode == SORT_PHONE_HOME:
        clients = clients.order_by('phone_home', 'name')
    elif sort_mode == SORT_PHONE_CELL:
        clients = clients.order_by('phone_cell', 'name')
    elif sort_mode == SORT_ELDERLY:
        clients = clients.order_by('elderly', 'name')
    elif sort_mode == SORT_AMBULATORY:
        clients = clients.order_by('ambulatory', 'name')
    elif sort_mode == SORT_TAGS:
        clients = clients.order_by('tags', 'name')

    if sort_mode_dir == 1:
        clients = clients.reverse()

    temp_file = tempfile.NamedTemporaryFile()

    wb = Workbook()

    style_font_normal = Font(name='Arial', size=10)
    style_border_normal_side = Side(border_style='thin', color='FF000000')
    style_border_normal = Border(left=style_border_normal_side, right=style_border_normal_side, top=style_border_normal_side, bottom=style_border_normal_side)
    style_colwidth_normal = 13
    style_colwidth_large = 30

    style_font_header = Font(name='Arial', size=10, bold=True)
    style_alignment_header = Alignment(horizontal='center', vertical='center', wrap_text=True)
    style_fill_header = PatternFill(fill_type='solid', fgColor='DFE0E1')
    style_rowheight_header = 25

    ws = wb.active
    ws.title = 'Clients'

    row_header = 1

    ws.cell(row_header, 1, 'Name')
    ws.cell(row_header, 2, 'Address')
    ws.cell(row_header, 3, 'Phone (Home)')
    ws.cell(row_header, 4, 'Phone (Cell)')
    ws.cell(row_header, 5, 'Elderly?')
    ws.cell(row_header, 6, 'Ambulatory?')
    ws.cell(row_header, 7, 'Tags')

    for i in range(0, len(clients)):
        ws.cell(i+2, 1, clients[i].name)
        ws.cell(i+2, 2, clients[i].address)
        ws.cell(i+2, 3, clients[i].phone_home)
        ws.cell(i+2, 4, clients[i].phone_cell)
        ws.cell(i+2, 5, clients[i].elderly)
        ws.cell(i+2, 6, clients[i].ambulatory)
        ws.cell(i+2, 7, clients[i].tags)

        # display elderly/ambulatory as booleans
        ws.cell(i+2, 5).number_format = 'BOOLEAN'
        ws.cell(i+2, 6).number_format = 'BOOLEAN'

    # apply styles
    ws.row_dimensions[row_header].height = style_rowheight_header
    for i in range(1, 8):
        if i == 1 or i == 2 or i == 7:
            ws.column_dimensions[get_column_letter(i)].width = style_colwidth_large
        else:
            ws.column_dimensions[get_column_letter(i)].width = style_colwidth_normal
        for j in range(row_header, len(clients)+2):
            ws.cell(j, i).border = style_border_normal
            if j == row_header:
                ws.cell(j, i).font = style_font_header
                ws.cell(j, i).alignment = style_alignment_header
                ws.cell(j, i).fill = style_fill_header
            else:
                ws.cell(j, i).font = style_font_normal

    wb.save(filename=temp_file.name)

    return FileResponse(open(temp_file.name, 'rb'), filename='Transit_Clients.xlsx', as_attachment=True)

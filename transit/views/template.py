import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Template, TemplateTrip
from transit.forms import EditTemplateForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent

@permission_required(['transit.view_template'])
def templateList(request):
    context = {
        'template': Template.objects.all(),
    }
    return render(request, 'template/list.html', context=context)

def templateCreate(request):
    template = Template()
    return templateCreateEditCommon(request, template, is_new=True)

def templateEdit(request, id):
    template = get_object_or_404(Template, id=id)
    return templateCreateEditCommon(request, template, is_new=False)

@permission_required(['transit.change_template'])
def templateCreateEditCommon(request, template, is_new):
    if is_new == True:
        query = Template.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_template = query[0]
            template.sort_index = last_template.sort_index + 1
        else:
            template.sort_index = 0

    if request.method == 'POST':
        form = EditTemplateForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#template_' + str(template.id)
            return HttpResponseRedirect(reverse('templates') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('template-delete', kwargs={'id':template.id}))

        if form.is_valid():
            template.name = form.cleaned_data['name']
            template.save()

            if is_new:
                log_event(request, LoggedEvent.ACTION_CREATE, LoggedEvent.MODEL_TEMPLATE, str(template))
            else:
                log_event(request, LoggedEvent.ACTION_EDIT, LoggedEvent.MODEL_TEMPLATE, str(template))

            return HttpResponseRedirect(reverse('templates') + '#template_' + str(template.id))
    else:
        initial = {
            'name': template.name,
        }
        form = EditTemplateForm(initial=initial)

    context = {
        'form': form,
        'template': template,
        'is_new': is_new,
    }

    return render(request, 'template/edit.html', context)

@permission_required(['transit.delete_template'])
def templateDelete(request, id):
    template = get_object_or_404(Template, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('template-edit', kwargs={'id':id}))

        query = Template.objects.all()
        for i in query:
            if i.sort_index > template.sort_index:
                i.sort_index -= 1;
                i.save()

        trip_query = TemplateTrip.objects.filter(parent=id)
        for i in trip_query:
            i.delete()

        log_event(request, LoggedEvent.ACTION_DELETE, LoggedEvent.MODEL_TEMPLATE, str(template))

        template.delete()
        return HttpResponseRedirect(reverse('templates'))

    context = {
        'model': template,
    }

    return render(request, 'model_delete.html', context)

def ajaxTemplateList(request):
    if not request.user.has_perm('transit.view_template'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_template'):
        if request_action == 'mv':
            template = get_object_or_404(Template, id=request_id)
            original_index = template.sort_index
            template.sort_index = -1

            # "remove" the selected item by shifting everything below it up by 1
            below_items = Template.objects.filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(Template, id=request_data)
                if template.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the item at the new index by shifting everything below it down by 1
            below_items = Template.objects.filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            template.sort_index = new_index
            template.save()

    templates = Template.objects.all()
    return render(request, 'template/ajax_list.html', {'templates': templates})


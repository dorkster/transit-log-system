import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Template
from transit.forms import EditTemplateForm

def templateList(request):
    context = {
        'template': Template.objects.all(),
    }
    return render(request, 'schedule/template/list.html', context=context)

def templateCreate(request):
    template = Template()
    return templateCreateEditCommon(request, template, is_new=True)

def templateEdit(request, id):
    template = get_object_or_404(Template, id=id)
    return templateCreateEditCommon(request, template, is_new=False)

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
            return HttpResponseRedirect(reverse('templates') + "#template_" + str(template.id))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('template-delete', kwargs={'id':template.id}))

        if form.is_valid():
            template.name = form.cleaned_data['name']
            template.save()

            return HttpResponseRedirect(reverse('templates') + "#template_" + str(template.id))
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

    return render(request, 'schedule/template/edit.html', context)

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

        template.delete()
        return HttpResponseRedirect(reverse('templates'))

    context = {
        'model': template,
    }

    return render(request, 'model_delete.html', context)

def ajaxTemplateList(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'mv':
        template = get_object_or_404(Template, id=request_id)

        do_sort = False
        if request_data == 'u':
            query = Template.objects.filter(sort_index=template.sort_index-1)
            do_sort = True
        elif request_data == 'd':
            query = Template.objects.filter(sort_index=template.sort_index+1)
            do_sort = True

        if do_sort and len(query) > 0:
            swap_index = query[0].sort_index
            query[0].sort_index = template.sort_index
            template.sort_index = swap_index
            query[0].save()
            template.save()

    templates = Template.objects.all()
    return render(request, 'schedule/template/ajax_list.html', {'templates': templates})


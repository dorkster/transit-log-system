import uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import Tag
from transit.forms import EditTagForm

from django.contrib.auth.decorators import permission_required

from transit.common.util import *

@permission_required(['transit.view_tag'])
def tagList(request):
    context = {
        'tag': Tag.objects.all(),
    }
    return render(request, 'tag/list.html', context=context)

def tagCreate(request):
    tag = Tag()
    return tagCreateEditCommon(request, tag, is_new=True)

def tagEdit(request, id):
    tag = get_object_or_404(Tag, id=id)
    return tagCreateEditCommon(request, tag, is_new=False)

@permission_required(['transit.change_tag'])
def tagCreateEditCommon(request, tag, is_new):
    if is_new == True:
        query = Tag.objects.all().order_by('-sort_index')
        if len(query) > 0:
            last_tag = query[0]
            tag.sort_index = last_tag.sort_index + 1
        else:
            tag.sort_index = 0

    if request.method == 'POST':
        form = EditTagForm(request.POST)

        if 'cancel' in request.POST:
            url_hash = '' if is_new else '#tag_' + str(tag.id)
            return HttpResponseRedirect(reverse('tags') + url_hash)
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('tag-delete', kwargs={'id':tag.id}))

        if form.is_valid():
            tag.name = form.cleaned_data['name']
            tag.save()

            return HttpResponseRedirect(reverse('tags') + '#tag_' + str(tag.id))
    else:
        initial = {
            'name': tag.name,
        }
        form = EditTagForm(initial=initial)

    context = {
        'form': form,
        'tag': tag,
        'is_new': is_new,
    }

    return render(request, 'tag/edit.html', context)

@permission_required('transit.delete_tag')
def tagDelete(request, id):
    tag = get_object_or_404(Tag, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('tag-edit', kwargs={'id':id}))

        query = Tag.objects.all()
        for i in query:
            if i.sort_index > tag.sort_index:
                i.sort_index -= 1;
                i.save()

        tag.delete()
        return HttpResponseRedirect(reverse('tags'))

    context = {
        'model': tag,
    }

    return render(request, 'model_delete.html', context)

def ajaxTagList(request):
    if not request.user.has_perm('transit.view_tag'):
        return HttpResponseRedirect(reverse('login_redirect'))

    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request.user.has_perm('transit.change_tag'):
        if request_action == 'mv':
            tag = get_object_or_404(Tag, id=request_id)
            original_index = tag.sort_index
            tag.sort_index = -1

            # "remove" the selected item by shifting everything below it up by 1
            below_items = Tag.objects.filter(sort_index__gt=original_index)
            for i in below_items:
                i.sort_index -= 1;
                i.save()

            if request_data == '':
                new_index = 0
            else:
                target_item = get_object_or_404(Tag, id=request_data)
                if tag.id != target_item.id:
                    new_index = target_item.sort_index + 1
                else:
                    new_index = original_index

            # prepare to insert the item at the new index by shifting everything below it down by 1
            below_items = Tag.objects.filter(sort_index__gte=new_index)
            for i in below_items:
                i.sort_index += 1
                i.save()

            tag.sort_index = new_index
            tag.save()

    tags = Tag.objects.all()
    return render(request, 'tag/ajax_list.html', {'tags': tags})


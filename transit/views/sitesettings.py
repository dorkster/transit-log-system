from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import SiteSettings
from transit.forms import SiteSettingsForm

def sitesettingsEdit(request):
    settings = SiteSettings.load()
    updated = False

    if 'cancel' in request.POST:
        return HttpResponseRedirect(reverse('index'))

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST)
        if form.is_valid():
            settings.enable_quick_edit = form.cleaned_data['enable_quick_edit']
            settings.activity_color = form.cleaned_data['activity_color']
            settings.cancel_color = form.cleaned_data['cancel_color']
            settings.save()
            updated = True
    else:
        initial = {
            'enable_quick_edit': settings.enable_quick_edit,
            'activity_color': settings.activity_color,
            'cancel_color': settings.cancel_color,
        }
        form = SiteSettingsForm(initial=initial)

    context = {
        'form': form,
        'updated': updated,
    }

    return render(request, 'settings.html', context)


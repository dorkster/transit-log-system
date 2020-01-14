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
            settings.activity_color = form.cleaned_data['activity_color'][1:]
            settings.cancel_color = form.cleaned_data['cancel_color'][1:]
            settings.autocomplete_history_days = form.cleaned_data['autocomplete_history_days']
            settings.save()
            updated = True
    else:
        initial = {
            'activity_color': '#' + settings.activity_color,
            'cancel_color': '#' + settings.cancel_color,
            'autocomplete_history_days': settings.autocomplete_history_days,
        }
        form = SiteSettingsForm(initial=initial)

    context = {
        'form': form,
        'updated': updated,
    }

    return render(request, 'settings.html', context)


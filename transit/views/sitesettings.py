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

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import SiteSettings
from transit.forms import SiteSettingsForm

from django.contrib.auth.decorators import permission_required

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

@permission_required(['transit.change_sitesettings'])
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
            settings.reset_filter_on_shift_change = form.cleaned_data['reset_filter_on_shift_change']
            settings.skip_weekends = form.cleaned_data['skip_weekends']
            if request.user.is_superuser:
                settings.page_title = form.cleaned_data['page_title']
                settings.short_page_title = form.cleaned_data['short_page_title']
            settings.save()
            log_event(request, LoggedEventAction.EDIT, LoggedEventModel.UNKNOWN, 'Updated site settings')
            updated = True
    else:
        initial = {
            'activity_color': '#' + settings.activity_color,
            'cancel_color': '#' + settings.cancel_color,
            'autocomplete_history_days': settings.autocomplete_history_days,
            'reset_filter_on_shift_change': settings.reset_filter_on_shift_change,
            'skip_weekends': settings.skip_weekends,
            'page_title': settings.page_title,
            'short_page_title': settings.short_page_title,
        }
        form = SiteSettingsForm(initial=initial)

    context = {
        'form': form,
        'updated': updated,
    }

    return render(request, 'settings.html', context)


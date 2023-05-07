# Copyright © 2019-2023 Justin Jacobs
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

from transit.models import Driver, Vehicle, TripType
from transit.forms import EditUserForm

from django.contrib.auth.models import User
from django.contrib.auth import password_validation, authenticate, login

from transit.common.eventlog import *
from transit.models import LoggedEvent, LoggedEventAction, LoggedEventModel

def index(request):
    form = None
    users = User.objects.all()
    superusers = users.filter(is_superuser=True, is_staff=True)

    # get the totals for some models to display appropriate warnings
    drivers = Driver.objects.count()
    vehicles = Vehicle.objects.count()
    triptypes = TripType.objects.count()

    if superusers.count() == 0:
        user = User()
        user.is_superuser = True
        user.is_staff = True

        if request.method == 'POST':
            form = EditUserForm(request.POST)

            if form.is_valid():
                user.username = form.cleaned_data['username']
                user.set_password(form.cleaned_data['password'])
                if len(User.objects.filter(username=user.username)) > 0:
                    form.add_error('username', 'Username already exists')

                if form.cleaned_data['password'] != '':
                    password_validators = [
                        password_validation.MinimumLengthValidator(),
                        password_validation.UserAttributeSimilarityValidator(),
                        password_validation.CommonPasswordValidator(),
                        password_validation.NumericPasswordValidator(),
                    ]

                    try:
                        password_validation.validate_password(form.cleaned_data['password'], user=user, password_validators=password_validators)
                    except:
                        form.add_error('password', 'Password is not valid')

                if len(form.errors) == 0:
                    user.save()
                    log_event(request, LoggedEventAction.CREATE, LoggedEventModel.USER, str(user))
                    user_login = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
                    if user_login is not None:
                        login(request, user_login)
        else:
            initial = {
                'username': user.username,
            }
            form = EditUserForm(initial=initial)
            form.fields['username'].required = True
            form.fields['password'].required = True
            form.fields['password_confirm'].required = True

    context = {
        'form': form,
        'users': users.count(),
        'super_users': superusers.count(),
        'normal_users': users.count() - superusers.count(),
        'drivers': drivers,
        'vehicles': vehicles,
        'triptypes': triptypes,
    }
    return render(request, 'index.html', context=context)

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

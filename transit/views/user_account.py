from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.contrib.auth.models import User, Group, Permission
from transit.forms import EditUserForm

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import password_validation

def userGroupIntToStr(group):
    if group == 1:
        return 'Assistant'
    elif group == 2:
        return 'Basic'
    else:
        # default
        return 'Staff'

def userGetGroupInt(user):
    for i in user.groups.all():
        if i.name == 'Assistant':
            return 1
        elif i.name == 'Basic':
            return 2

    # Staff (default)
    return 0

def userGetGroup(group_name):
    query = Group.objects.filter(name=group_name)
    if len(query) > 0:
        group = query[0]
    else:
        group = Group()
        group.name = group_name
        group.save()

    permissions = []
    if group_name == 'Basic':
        permissions.append(Permission.objects.get(codename='view_schedulemessage'))
        permissions.append(Permission.objects.get(codename='view_shift'))
        permissions.append(Permission.objects.get(codename='view_trip'))
    elif group_name == 'Assistant':
        permissions.append(Permission.objects.get(codename='view_client'))
        permissions.append(Permission.objects.get(codename='view_destination'))
        permissions.append(Permission.objects.get(codename='add_frequenttag'))
        permissions.append(Permission.objects.get(codename='change_frequenttag'))
        permissions.append(Permission.objects.get(codename='delete_frequenttag'))
        permissions.append(Permission.objects.get(codename='view_frequenttag'))
        permissions.append(Permission.objects.get(codename='add_schedulemessage'))
        permissions.append(Permission.objects.get(codename='change_schedulemessage'))
        permissions.append(Permission.objects.get(codename='delete_schedulemessage'))
        permissions.append(Permission.objects.get(codename='view_schedulemessage'))
        permissions.append(Permission.objects.get(codename='add_shift'))
        permissions.append(Permission.objects.get(codename='change_shift'))
        permissions.append(Permission.objects.get(codename='delete_shift'))
        permissions.append(Permission.objects.get(codename='view_shift'))
        permissions.append(Permission.objects.get(codename='view_template'))
        permissions.append(Permission.objects.get(codename='view_templatetrip'))
        permissions.append(Permission.objects.get(codename='add_trip'))
        permissions.append(Permission.objects.get(codename='change_trip'))
        permissions.append(Permission.objects.get(codename='delete_trip'))
        permissions.append(Permission.objects.get(codename='view_trip'))
        permissions.append(Permission.objects.get(codename='view_fare'))
        permissions.append(Permission.objects.get(codename='view_tag'))
    elif group_name == 'Staff':
        permissions.append(Permission.objects.get(codename='add_group'))
        permissions.append(Permission.objects.get(codename='change_group'))
        permissions.append(Permission.objects.get(codename='view_group'))
        permissions.append(Permission.objects.get(codename='add_user'))
        permissions.append(Permission.objects.get(codename='change_user'))
        permissions.append(Permission.objects.get(codename='delete_user'))
        permissions.append(Permission.objects.get(codename='view_user'))
        permissions.append(Permission.objects.get(codename='add_client'))
        permissions.append(Permission.objects.get(codename='change_client'))
        permissions.append(Permission.objects.get(codename='delete_client'))
        permissions.append(Permission.objects.get(codename='view_client'))
        permissions.append(Permission.objects.get(codename='add_destination'))
        permissions.append(Permission.objects.get(codename='change_destination'))
        permissions.append(Permission.objects.get(codename='delete_destination'))
        permissions.append(Permission.objects.get(codename='view_destination'))
        permissions.append(Permission.objects.get(codename='add_driver'))
        permissions.append(Permission.objects.get(codename='change_driver'))
        permissions.append(Permission.objects.get(codename='view_driver'))
        permissions.append(Permission.objects.get(codename='add_frequenttag'))
        permissions.append(Permission.objects.get(codename='change_frequenttag'))
        permissions.append(Permission.objects.get(codename='delete_frequenttag'))
        permissions.append(Permission.objects.get(codename='view_frequenttag'))
        permissions.append(Permission.objects.get(codename='add_pretrip'))
        permissions.append(Permission.objects.get(codename='change_pretrip'))
        permissions.append(Permission.objects.get(codename='view_pretrip'))
        permissions.append(Permission.objects.get(codename='add_schedulemessage'))
        permissions.append(Permission.objects.get(codename='change_schedulemessage'))
        permissions.append(Permission.objects.get(codename='delete_schedulemessage'))
        permissions.append(Permission.objects.get(codename='view_schedulemessage'))
        permissions.append(Permission.objects.get(codename='add_shift'))
        permissions.append(Permission.objects.get(codename='change_shift'))
        permissions.append(Permission.objects.get(codename='delete_shift'))
        permissions.append(Permission.objects.get(codename='view_shift'))
        permissions.append(Permission.objects.get(codename='change_sitesettings'))
        permissions.append(Permission.objects.get(codename='view_sitesettings'))
        permissions.append(Permission.objects.get(codename='add_template'))
        permissions.append(Permission.objects.get(codename='change_template'))
        permissions.append(Permission.objects.get(codename='delete_template'))
        permissions.append(Permission.objects.get(codename='view_template'))
        permissions.append(Permission.objects.get(codename='add_templatetrip'))
        permissions.append(Permission.objects.get(codename='change_templatetrip'))
        permissions.append(Permission.objects.get(codename='delete_templatetrip'))
        permissions.append(Permission.objects.get(codename='view_templatetrip'))
        permissions.append(Permission.objects.get(codename='add_trip'))
        permissions.append(Permission.objects.get(codename='change_trip'))
        permissions.append(Permission.objects.get(codename='delete_trip'))
        permissions.append(Permission.objects.get(codename='view_trip'))
        permissions.append(Permission.objects.get(codename='add_triptype'))
        permissions.append(Permission.objects.get(codename='change_triptype'))
        permissions.append(Permission.objects.get(codename='view_triptype'))
        permissions.append(Permission.objects.get(codename='add_vehicle'))
        permissions.append(Permission.objects.get(codename='change_vehicle'))
        permissions.append(Permission.objects.get(codename='view_vehicle'))
        permissions.append(Permission.objects.get(codename='add_vehicleissue'))
        permissions.append(Permission.objects.get(codename='change_vehicleissue'))
        permissions.append(Permission.objects.get(codename='view_vehicleissue'))
        permissions.append(Permission.objects.get(codename='add_clientpayment'))
        permissions.append(Permission.objects.get(codename='change_clientpayment'))
        permissions.append(Permission.objects.get(codename='delete_clientpayment'))
        permissions.append(Permission.objects.get(codename='view_clientpayment'))
        permissions.append(Permission.objects.get(codename='add_fare'))
        permissions.append(Permission.objects.get(codename='change_fare'))
        permissions.append(Permission.objects.get(codename='delete_fare'))
        permissions.append(Permission.objects.get(codename='view_fare'))
        permissions.append(Permission.objects.get(codename='add_tag'))
        permissions.append(Permission.objects.get(codename='change_tag'))
        permissions.append(Permission.objects.get(codename='delete_tag'))
        permissions.append(Permission.objects.get(codename='view_tag'))

    group.permissions.set(permissions)
    group.save()

    return group

@permission_required(['auth.view_user'])
def userList(request):
    context = {
        'user_accounts': User.objects.filter(is_staff=False),
    }
    return render(request, 'user/list.html', context=context)

@user_passes_test(lambda u: u.is_superuser)
def userUpdatePermissions(request):
    users = User.objects.filter(is_staff=False)

    for user in users:
        group_id = userGetGroupInt(user)
        group = userGetGroup(userGroupIntToStr(group_id))
        user.groups.set([group])
        # permissions are handled by group, so clear user permissions
        user.user_permissions.set({})

    return render(request, 'user/update_permissions.html', context={})


def userCreate(request):
    user = User()
    return userCreateEdit(request, user, is_new=True)

def userEdit(request, username):
    user = get_object_or_404(User, username=username)
    return userCreateEdit(request, user, is_new=False)

@permission_required(['auth.change_user'])
def userCreateEdit(request, user, is_new):
    if request.method == 'POST':
        form = EditUserForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('users'))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('user-delete', kwargs={'username':user.username}))

        if form.is_valid():
            if is_new:
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

            if len(form.errors) > 0:
                context = {
                    'form': form,
                    'is_new': is_new,
                    'user_account': user,
                }
                return render(request, 'user/edit.html', context=context)

            if form.cleaned_data['password'] != '':
                user.set_password(form.cleaned_data['password'])

            if request.user.username != user.username:
                # user needs to be saved so Group setting can get an ID
                user.save()

                account_type = int(form.cleaned_data['account_type'])
                group = userGetGroup(userGroupIntToStr(account_type))

                user.groups.set([group])

                # permissions are handled by group, so clear user permissions
                user.user_permissions.set({})

            user.save()
            return HttpResponseRedirect(reverse('users'))

    else:
        account_type = 0

        if user.id:
            account_type = userGetGroupInt(user)

        initial = {
            'username': user.username,
            'account_type': account_type,
        }
        form = EditUserForm(initial=initial)

    if is_new:
        form.fields['username'].required = True
        form.fields['password'].required = True
        form.fields['password_confirm'].required = True

    context = {
        'form': form,
        'is_new': is_new,
        'user_account': user,
    }
    return render(request, 'user/edit.html', context=context)

@permission_required('auth.delete_user')
def userDelete(request, username):
    user = get_object_or_404(User, username=username)

    can_delete = True
    if request.user.username == user.username:
        can_delete = False

    staff_users = User.objects.filter(groups__name='Staff')
    if len(staff_users) == 1 and len(user.groups.all().filter(name='Staff')) != 0:
        can_delete = False

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('user-edit', kwargs={'username':user.username}))

        if can_delete:
            user.delete()
        return HttpResponseRedirect(reverse('users'))

    context = {
        'user_account': user,
        'can_delete': can_delete,
    }

    return render(request, 'user/delete.html', context)


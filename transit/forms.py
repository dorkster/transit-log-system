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

import datetime

from django import forms

from transit.models import Driver, Vehicle, TripType, Client, VehicleIssue, Trip, Template, TemplateTrip, ActivityColor

# from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _

BOOL_CHOICES = (
    (True, 'Yes'),
    (False, 'No')
)

NULL_BOOL_CHOICES = (
    (None, '---------'),
    (0, 'Unknown'),
    (1, 'Yes'),
    (2, 'No')
)

YEARS = []
for year in range(2019, datetime.date.today().year + 2):
    YEARS.append(year)

class formWidgetAttrs():
    default = {'class': 'form-control form-control-width-fix'}
    default['onfocus'] = 'inputScrollToView(this)'

    date = {'class': 'form-control form-control-width-fix snps-inline-select'}

    name = default.copy()
    name['list'] = 'client-names'

    address = default.copy()
    address['list'] = 'addresses'

    phone = default.copy()
    phone['onchange'] = 'validatePhone(this)'
    phone['inputmode'] = 'tel'
    phone['autocomplete'] = 'off'

    notes = default.copy()
    notes['rows'] = '3'
    notes['cols'] = '20'

    time = default.copy()
    time['onchange'] = 'validateTime(this)'
    time['autocomplete'] = 'off'

    mile = default.copy()
    mile['onchange'] = 'validateMiles(this, false)'
    mile['inputmode'] = 'decimal'
    mile['autocomplete'] = 'off'

    mile_shift = mile.copy()
    mile_shift['onchange'] = 'validateMiles(this, true)'

    big_mile = mile.copy()
    big_mile['class'] += ' form-control-lg'
    big_mile['size'] = '15'

    fuel = default.copy()
    fuel['onchange'] = 'validateFuel(this)'
    fuel['inputmode'] = 'decimal'
    fuel['autocomplete'] = 'off'

    text_area = default.copy()
    text_area['rows'] = '6'
    text_area['cols'] = '20'

    color = default.copy()
    color['class'] += ' form-control-color'
    color['type'] = 'color'

    money = default.copy()
    money['onchange'] = 'validateMoney(this)'
    money['inputmode'] = 'decimal'
    money['autocomplete'] = 'off'

    new_user = default.copy()
    new_user['autocomplete'] = 'off'

    new_password = default.copy()
    new_password['autocomplete'] = 'new-password'

class DatePickerForm(forms.Form):
    date = forms.DateField(label='', widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))

class DateRangePickerForm(forms.Form):
    date_start = forms.DateField(label='', widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    date_end = forms.DateField(label='', widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))

class EditTripForm(forms.Form):
    try:
        triptypes_exist = TripType.objects.count() > 0
    except:
        triptypes_exist = False

    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    name = forms.CharField(widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(label='Pick-Up Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_alt = forms.CharField(label='Phone (Alternate)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_address = forms.CharField(label='Phone (Pick-Up)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_destination = forms.CharField(label='Phone (Destination)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    destination = forms.CharField(label='Destination Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    pick_up_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    appointment_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))
    trip_type = forms.ModelChoiceField(TripType.objects, required=(triptypes_exist), widget=forms.Select(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.HiddenInput())
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    start_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    status = forms.ChoiceField(required=False, choices=Trip.STATUS_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))
    collected_cash = forms.CharField(label='Money Collected: Cash ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    collected_check = forms.CharField(label='Money Collected: Check ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    fare = forms.CharField(label='Fare ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    passenger = forms.BooleanField(label='Passenger on vehicle?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    cancel_date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    create_return_trip = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    add_client = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    add_dest1 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    add_dest2 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

class EditShiftForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.all(), widget=forms.Select(attrs=formWidgetAttrs.default))
    start_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile_shift))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile_shift))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    fuel = forms.CharField(label='Fuel (gal)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.fuel))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))

class shiftStartEndForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))

class shiftFuelForm(forms.Form):
    fuel = forms.CharField(label='Fuel (gal)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.fuel))

class tripStartForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.all(), required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    collected_cash = forms.CharField(label='Money Collected: Cash ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    collected_check = forms.CharField(label='Money Collected: Check ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    additional_pickups = forms.CharField(widget=forms.HiddenInput(), required=False)

class tripEndForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    collected_cash = forms.CharField(label='Money Collected: Cash ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    collected_check = forms.CharField(label='Money Collected: Check ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    additional_pickups = forms.CharField(widget=forms.HiddenInput(), required=False)

class EditClientForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_alt = forms.CharField(label='Phone (Alternate)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.HiddenInput())
    staff = forms.BooleanField(label='Is staff member?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    is_active = forms.BooleanField(label='Is active?', help_text='Inactive clients will not appear in autocomplete drop-downs.', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    is_transit_policy_acknowledged = forms.BooleanField(label='Transit Policy Acknowledged?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    update_trips = forms.BooleanField(label='Update existing trips and templates?', help_text='If "Yes" is selected, this will perform a search-and-replace on this client\'s trips.', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class EditClientPaymentForm(forms.Form):
    date_paid = forms.DateField(label='Date Paid', widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    cash = forms.CharField(label='Cash ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    check = forms.CharField(label='Check ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))

class EditDestinationForm(forms.Form):
    address = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    is_active = forms.BooleanField(label='Is active?', help_text='Inactive destinations will not appear in autocomplete drop-downs.', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    update_trips = forms.BooleanField(label='Update existing trips and templates?', help_text='If "Yes" is selected, this will perform a search-and-replace on trips that use this destination.', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class EditDriverForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))
    is_logged = forms.BooleanField(label='Is logged?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class EditVehicleForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    is_logged = forms.BooleanField(label='Is logged?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class EditTripTypeForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    is_trip_counted = forms.BooleanField(label='Include in report trip counts?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class UploadFileForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple':True, 'accept':'.xlsx'}))
    log_data_only = forms.BooleanField(label='Only include rows with full log data?', required=False, initial=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    dry_run = forms.BooleanField(label="Dry run? (i.e. don't write to database)", required=False, initial=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class EditVehicleIssueForm(forms.Form):
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    description = forms.CharField(widget=forms.Textarea(attrs=formWidgetAttrs.text_area))
    priority = forms.ChoiceField(choices=VehicleIssue.PRIORITY_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))
    is_resolved = forms.BooleanField(label='Is Resolved?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    category = forms.ChoiceField(choices=VehicleIssue.ISSUE_CATEGORIES, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditTemplateForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditTemplateTripForm(forms.Form):
    try:
        triptypes_exist = TripType.objects.count() > 0
    except:
        triptypes_exist = False

    parent = forms.ModelChoiceField(Template.objects.all(), label='Template', empty_label=None, required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    name = forms.CharField(widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(label='Pick-Up Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_alt = forms.CharField(label='Phone (Alternate)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_address = forms.CharField(label='Phone (Pick-Up)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_destination = forms.CharField(label='Phone (Destination)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    destination = forms.CharField(label='Destination Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    pick_up_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    appointment_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))
    trip_type = forms.ModelChoiceField(TripType.objects, required=(triptypes_exist), widget=forms.Select(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.HiddenInput())
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    status = forms.ChoiceField(required=False, choices=TemplateTrip.STATUS_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))
    fare = forms.CharField(label='Fare ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    passenger = forms.BooleanField(label='Passenger on vehicle?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    create_return_trip = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    add_client = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    add_dest1 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    add_dest2 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

class EditTemplateActivityForm(forms.Form):
    parent = forms.ModelChoiceField(Template.objects.all(), label='Template', empty_label=None, required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    description = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    status = forms.ChoiceField(required=False, choices=TemplateTrip.STATUS_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))
    activity_color = forms.ModelChoiceField(ActivityColor.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    driver_is_available = forms.BooleanField(label='Driver is available?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class EditScheduleMessageForm(forms.Form):
    message = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditActivityForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    description = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    status = forms.ChoiceField(required=False, choices=Trip.STATUS_LEVELS_ACTIVITY, widget=forms.Select(attrs=formWidgetAttrs.default))
    cancel_date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    activity_color = forms.ModelChoiceField(ActivityColor.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    driver_is_available = forms.BooleanField(label='Driver is available?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))

class vehicleMaintainForm(forms.Form):
    MONTHS = {}
    for i in range(1,13):
        MONTHS[i] = str(i) + ' - ' + datetime.date(1900, i, 1).strftime('%B')

    oil_change_miles = forms.CharField(label='Next Oil Change (miles)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile))
    inspection_date = forms.DateField(label='Inspection Sticker', required=False, widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, empty_label=('-- Year--', '-- Month --', '-- Day --'), months=MONTHS, years=YEARS))

class vehiclePreTripForm(forms.Form):
    checklist = forms.CharField(widget=forms.HiddenInput(), required=False)
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditFareForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    fare = forms.CharField(label='Fare ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))

class EditTagForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditActivityColorForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))

class SearchTripsForm(forms.Form):
    TRIP_STATUS_LEVELS = (
        (None, '---------'),
        (0, 'Normal'),
        (1, 'Canceled'),
        (2, 'No Show')
    )

    name = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    destination = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    start_date = forms.DateField(required=False, widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS, empty_label=('-- Year--', '-- Month --', '-- Day --')))
    end_date = forms.DateField(required=False, widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS, empty_label=('-- Year--', '-- Month --', '-- Day --')))
    notes = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    trip_type = forms.ModelChoiceField(TripType.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    elderly = forms.ChoiceField(choices=NULL_BOOL_CHOICES, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    ambulatory = forms.ChoiceField(choices=NULL_BOOL_CHOICES, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    status = forms.ChoiceField(required=False, choices=TRIP_STATUS_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))

class SiteSettingsForm(forms.Form):
    activity_color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))
    cancel_color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))
    no_show_color = forms.CharField(label='No-show color', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))
    autocomplete_history_days = forms.IntegerField(min_value=0, label='Address autocomplete history days', help_text='If no Destinations have been defined, address fields will use the past X days of Trips to generate suggestions.', widget=forms.NumberInput(attrs=formWidgetAttrs.default))
    reset_filter_on_shift_change = forms.BooleanField(label='Reset Schedule filter when starting/ending Shift', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    skip_weekends = forms.BooleanField(label='Skip weekends in the Schedule date picker', required=False, widget=forms.Select(attrs=formWidgetAttrs.default, choices=BOOL_CHOICES))
    pretrip_warning_threshold = forms.IntegerField(min_value=0, label='Pre-Trip Warning Threshold', help_text='If a vehicle has gone X days without a pre-trip inspection, a warning notification will be displayed. Set it to 0 to disable the warning altogether.', widget=forms.NumberInput(attrs=formWidgetAttrs.default))
    page_title = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    short_page_title = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditUserForm(forms.Form):
    USER_ACCOUNT_TYPES = [
        (0, 'Staff'),
        (1, 'Assistant'),
        (2, 'Basic')
    ]

    username = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.new_user))
    account_type = forms.ChoiceField(choices=USER_ACCOUNT_TYPES, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs=formWidgetAttrs.new_password))
    password_confirm = forms.CharField(required=False, widget=forms.PasswordInput(attrs=formWidgetAttrs.new_password))

    def clean(self):
        cleaned_data = super(EditUserForm, self).clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            self.add_error('password_confirm', 'Password does not match')

        return cleaned_data


import datetime

from django import forms

from transit.models import Driver, Vehicle, TripType, Client, VehicleIssue, Trip, Template, TemplateTrip

# from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _

BOOL_CHOICES = (
    (True, 'Yes'),
    (False, 'No')
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

    notes = default.copy()
    notes['rows'] = '3'
    notes['cols'] = '20'

    time = default.copy()
    time['onchange'] = 'validateTime(this)'

    mile = default.copy()
    mile['onchange'] = 'validateMiles(this, false)'
    mile['inputmode'] = 'decimal'

    mile_shift = mile.copy()
    mile_shift['onchange'] = 'validateMiles(this, true)'

    big_mile = mile.copy()
    big_mile['class'] += ' form-control-lg'
    big_mile['size'] = '15'

    big_mile_trip = big_mile.copy()
    big_mile_trip['oninput'] = 'showFullMiles(this)'

    big_mile_shift = big_mile.copy()
    big_mile_shift['onchange'] = mile_shift['onchange']
    big_mile_shift['oninput'] = 'showFullMiles(this)'

    fuel = default.copy()
    fuel['onchange'] = 'validateFuel(this)'
    fuel['inputmode'] = 'decimal'

    text_area = default.copy()
    text_area['rows'] = '6'
    text_area['cols'] = '20'

    color = default.copy()
    color['class'] += ' form-control-color'
    color['type'] = 'color'

    money = default.copy()
    money['onchange'] = 'validateMoney(this)'
    money['inputmode'] = 'decimal'

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
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    name = forms.CharField(widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(label='Pick-Up Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_address = forms.CharField(label='Phone (Pick-Up)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_destination = forms.CharField(label='Phone (Destination)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    destination = forms.CharField(label='Destination Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    pick_up_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    appointment_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))
    trip_type = forms.ModelChoiceField(TripType.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
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
    create_return_trip = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

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
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_shift))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))

class shiftFuelForm(forms.Form):
    fuel = forms.CharField(label='Fuel (gal)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.fuel))

class tripStartForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_trip))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.all(), required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    collected_cash = forms.CharField(label='Money Collected: Cash ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    collected_check = forms.CharField(label='Money Collected: Check ($)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.money))
    additional_pickups = forms.CharField(widget=forms.HiddenInput(), required=False)

class tripEndForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_trip))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    additional_pickups = forms.CharField(widget=forms.HiddenInput(), required=False)

class EditClientForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditDestinationForm(forms.Form):
    address = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))

class EditDriverForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))
    is_logged = forms.ChoiceField(choices=BOOL_CHOICES, label='Is logged?', required=True, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditVehicleForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    is_logged = forms.ChoiceField(choices=BOOL_CHOICES, label='Is logged?', required=True, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditTripTypeForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class UploadFileForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple':True, 'accept':'.xlsx'}))
    log_data_only = forms.ChoiceField(choices=BOOL_CHOICES, label='Only include rows with full log data?', required=True, initial=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    dry_run = forms.ChoiceField(choices=BOOL_CHOICES, label="Dry run? (i.e. don't write to database)", required=True, initial=False, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditVehicleIssueForm(forms.Form):
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    description = forms.CharField(widget=forms.Textarea(attrs=formWidgetAttrs.text_area))
    priority = forms.ChoiceField(choices=VehicleIssue.PRIORITY_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))
    is_resolved = forms.ChoiceField(choices=BOOL_CHOICES, label='Is Resolved?', required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    category = forms.ChoiceField(choices=VehicleIssue.ISSUE_CATEGORIES, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditTemplateForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditTemplateTripForm(forms.Form):
    parent = forms.ModelChoiceField(Template.objects.all(), label='Template', empty_label=None, required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    name = forms.CharField(widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(label='Pick-Up Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_address = forms.CharField(label='Phone (Pick-Up)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_destination = forms.CharField(label='Phone (Destination)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    destination = forms.CharField(label='Destination Address', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.address))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    pick_up_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    appointment_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))
    trip_type = forms.ModelChoiceField(TripType.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    status = forms.ChoiceField(required=False, choices=TemplateTrip.STATUS_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))
    create_return_trip = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

class EditTemplateActivityForm(forms.Form):
    parent = forms.ModelChoiceField(Template.objects.all(), label='Template', empty_label=None, required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    description = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    status = forms.ChoiceField(required=False, choices=TemplateTrip.STATUS_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditScheduleMessageForm(forms.Form):
    message = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditActivityForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    description = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    status = forms.ChoiceField(required=False, choices=Trip.STATUS_LEVELS_ACTIVITY, widget=forms.Select(attrs=formWidgetAttrs.default))

class vehicleMaintainForm(forms.Form):
    MONTHS = {}
    for i in range(1,13):
        MONTHS[i] = str(i) + ' - ' + datetime.date(1900, i, 1).strftime('%B')

    oil_change_miles = forms.CharField(label='Next Oil Change (miles)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile))
    inspection_date = forms.DateField(label='Inspection Sticker', required=False, widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, empty_label=('-- Year--', '-- Month --', '-- Day --'), months=MONTHS, years=YEARS))

class vehiclePreTripForm(forms.Form):
    checklist = forms.CharField(widget=forms.HiddenInput(), required=False)

class SearchTripsForm(forms.Form):
    name = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    destination = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    start_date = forms.DateField(required=False, widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS, empty_label=('-- Year--', '-- Month --', '-- Day --')))
    end_date = forms.DateField(required=False, widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date, years=YEARS, empty_label=('-- Year--', '-- Month --', '-- Day --')))

class SiteSettingsForm(forms.Form):
    activity_color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))
    cancel_color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.color))
    autocomplete_history_days = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs=formWidgetAttrs.default))
    reset_filter_on_shift_change = forms.ChoiceField(choices=BOOL_CHOICES, label='Reset Schedule filter when starting/ending Shift', widget=forms.Select(attrs=formWidgetAttrs.default))
    skip_weekends = forms.ChoiceField(choices=BOOL_CHOICES, label='Skip weekends in the Schedule date picker', widget=forms.Select(attrs=formWidgetAttrs.default))

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

class SchedulePrintFilterForm(forms.Form):
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.HiddenInput())
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=False, widget=forms.HiddenInput())
    search = forms.CharField(required=False, widget=forms.HiddenInput())
    hide_canceled = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())
    hide_completed = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())
    hide_nolog = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())

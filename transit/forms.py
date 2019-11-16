from django import forms

from transit.models import Driver, Vehicle, TripType, Client, VehicleIssue, Trip

# from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _

BOOL_CHOICES = (
    (True, 'Yes'),
    (False, 'No')
)

class formWidgetAttrs():
    default = {'class': 'form-control form-control-width-fix'}
    default['onfocus'] = 'inputScrollToView(this)'

    date = {'class': 'form-control form-control-width-fix snps-inline-select'}

    name = default.copy()
    name['list'] = 'client-names'

    phone = default.copy()
    phone['onchange'] = 'validatePhone(this)'
    phone['inputmode'] = 'numeric'
    # phone['pattern'] = '[0-9]*-*[0-9]*-*[0-9]*-*[0-9]*'

    notes = default.copy()
    notes['rows'] = '3'
    notes['cols'] = '20'

    time = default.copy()
    time['onchange'] = 'validateTime(this)'

    mile = default.copy()
    mile['onchange'] = 'validateMiles(this, false)'
    mile['inputmode'] = 'numeric'
    mile['pattern'] = '[0-9]*\.[0-9]*'

    mile_shift = mile.copy()
    mile_shift['onchange'] = 'validateMiles(this, true)'

    big_mile = mile.copy()
    big_mile['class'] += ' form-control-lg'
    big_mile['size'] = '15'

    big_mile_trip = big_mile.copy()
    big_mile_trip['oninput'] = 'showFullMiles(this)'

    big_mile_shift = big_mile.copy()
    big_mile_shift['onchange'] = mile_shift['onchange']

    fuel = default.copy()
    fuel['onchange'] = 'validateFuel(this)'
    fuel['inputmode'] = 'numeric'
    fuel['pattern'] = '[0-9]*\.[0-9]*'

    text_area = default.copy()
    text_area['rows'] = '6'
    text_area['cols'] = '20'

    color = default.copy()
    color['onchange'] = 'validateColor(this)'

class DatePickerForm(forms.Form):
    date = forms.DateField(label='', widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date))

class EditTripForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date))
    name = forms.CharField(widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    destination = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
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

class EditShiftForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date))
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    start_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile_shift))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile_shift))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    fuel = forms.CharField(label='Fuel (gal)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.fuel))

class shiftStartEndForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_shift))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))

class shiftFuelForm(forms.Form):
    fuel = forms.CharField(label='Fuel (gal)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.fuel))

class tripStartForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_trip))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.filter(is_logged=True), required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    adjacent_trips = forms.CharField(widget=forms.HiddenInput(), required=False)

class tripEndForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_trip))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    adjacent_trips = forms.CharField(widget=forms.HiddenInput(), required=False)

class EditClientForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))

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
    # date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date))
    driver = forms.ModelChoiceField(Driver.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects.filter(is_logged=True), widget=forms.Select(attrs=formWidgetAttrs.default))
    description = forms.CharField(widget=forms.Textarea(attrs=formWidgetAttrs.text_area))
    priority = forms.ChoiceField(choices=VehicleIssue.PRIORITY_LEVELS, widget=forms.Select(attrs=formWidgetAttrs.default))
    is_resolved = forms.ChoiceField(choices=BOOL_CHOICES, label='Is Resolved?', required=True, widget=forms.Select(attrs=formWidgetAttrs.default))

class EditTemplateForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class EditTemplateTripForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    phone_home = forms.CharField(label='Phone (Home)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_cell = forms.CharField(label='Phone (Cell)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    destination = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    pick_up_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    appointment_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))
    trip_type = forms.ModelChoiceField(TripType.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))

class EditScheduleMessageForm(forms.Form):
    message = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))


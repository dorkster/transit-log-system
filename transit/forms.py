from django import forms

from transit.models import Driver, Vehicle, TripType, Client

# from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _

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
    big_mile['class'] += " form-control-lg"
    big_mile['size'] = '15'

    big_mile_trip = big_mile.copy()
    big_mile_trip['oninput'] = 'showFullMiles(this)'

    big_mile_shift = big_mile.copy()
    big_mile_shift['onchange'] = mile_shift['onchange']

    fuel = default.copy()
    fuel['onchange'] = 'validateFuel(this)'
    fuel['inputmode'] = 'numeric'
    fuel['pattern'] = '[0-9]*\.[0-9]*'

class DatePickerForm(forms.Form):
    date = forms.DateField(label='', widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date))

class EditTripForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date))
    name = forms.CharField(widget=forms.TextInput(attrs=formWidgetAttrs.name))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    destination = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    pick_up_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    appointment_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs=formWidgetAttrs.notes))
    trip_type = forms.ModelChoiceField(TripType.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    driver = forms.ModelChoiceField(Driver.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=False, widget=forms.Select(attrs=formWidgetAttrs.default))
    start_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    is_canceled = forms.BooleanField(label='Canceled', required=False, widget=forms.CheckboxInput())

class EditShiftForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(attrs=formWidgetAttrs.date))
    driver = forms.ModelChoiceField(Driver.objects, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, widget=forms.Select(attrs=formWidgetAttrs.default))
    start_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile_shift))
    start_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    end_miles = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.mile_shift))
    end_time = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    fuel = forms.CharField(label='Fuel (gal)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))

class shiftStartEndForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_shift))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))

class shiftFuelForm(forms.Form):
    fuel = forms.CharField(label='Fuel (gal)', required=False, widget=forms.TextInput(attrs=formWidgetAttrs.fuel))

class tripStartForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_trip))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))
    driver = forms.ModelChoiceField(Driver.objects, required=True, widget=forms.Select(attrs=formWidgetAttrs.default))
    vehicle = forms.ModelChoiceField(Vehicle.objects, required=True, widget=forms.Select(attrs=formWidgetAttrs.default))

class tripEndForm(forms.Form):
    miles = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.big_mile_trip))
    time = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.time))

class EditClientForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    phone_home = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_mobile = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.phone))
    phone_default = forms.ChoiceField(label='Default Phone Number', choices=Client.DEFAULT_PHONE, widget=forms.Select(attrs=formWidgetAttrs.default))
    elderly = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))
    ambulatory = forms.NullBooleanField(required=False, widget=forms.NullBooleanSelect(attrs=formWidgetAttrs.default))

class EditDriverForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    color = forms.CharField(required=False, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    is_logged = forms.BooleanField(label='Is logged?', required=False, widget=forms.CheckboxInput())

class EditVehicleForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs=formWidgetAttrs.default))
    is_logged = forms.BooleanField(label='Is logged?', required=False, widget=forms.CheckboxInput())

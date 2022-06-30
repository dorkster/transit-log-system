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

import uuid, re, datetime
from django.db import models
from django.urls import reverse

from transit.common.util import *

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class FieldSizes():
    # generic sizes
    SM = 64
    MD = 128
    LG = 256
    XL = 512

    PHONE = 16
    MILES = 8
    TIME = 8
    FUEL = 4
    COLOR = 8

class LoggedEventAction():
    UNKNOWN = 0
    CREATE = 1
    EDIT = 2
    DELETE = 3
    LOG_START = 4
    LOG_END = 5
    LOG_FUEL = 6
    STATUS = 7

    def get_str(val):
        if val == LoggedEventAction.CREATE:
            return "Create"
        elif val == LoggedEventAction.EDIT:
            return "Edit"
        elif val == LoggedEventAction.DELETE:
            return "Delete"
        elif val == LoggedEventAction.LOG_START:
            return "Start Log"
        elif val == LoggedEventAction.LOG_END:
            return "End Log"
        elif val == LoggedEventAction.LOG_FUEL:
            return "Log Fuel"
        elif val == LoggedEventAction.STATUS:
            return "Set Status"
        else: # UNKNOWN
            return "Unknown"

class LoggedEventModel():
    UNKNOWN = 0
    CLIENT = 1
    CLIENT_PAYMENT = 2
    DESTINATION = 3
    DRIVER = 4
    FARE = 5
    SHIFT = 6
    TAG = 7
    TEMPLATE = 8
    TEMPLATE_TRIP = 9
    TEMPLATE_TRIP_ACTIVITY = 10
    TRIP = 11
    TRIP_ACTIVITY = 12
    TRIPTYPE = 13
    USER = 14
    VEHICLE = 15
    VEHICLE_MAINTAIN = 16
    VEHICLE_ISSUE = 17
    PRETRIP = 18

    def get_str(val):
        if val == LoggedEventModel.CLIENT:
            return "Client"
        elif val == LoggedEventModel.CLIENT_PAYMENT:
            return "Client Payment"
        elif val == LoggedEventModel.DESTINATION:
            return "Destination"
        elif val == LoggedEventModel.DRIVER:
            return "Driver"
        elif val == LoggedEventModel.FARE:
            return "Fare"
        elif val == LoggedEventModel.SHIFT:
            return "Shift"
        elif val == LoggedEventModel.TAG:
            return "Tag"
        elif val == LoggedEventModel.TEMPLATE:
            return "Template"
        elif val == LoggedEventModel.TEMPLATE_TRIP:
            return "Template Trip"
        elif val == LoggedEventModel.TEMPLATE_TRIP_ACTIVITY:
            return "Template Activity"
        elif val == LoggedEventModel.TRIP:
            return "Trip"
        elif val == LoggedEventModel.TRIP_ACTIVITY:
            return "Activity"
        elif val == LoggedEventModel.TRIPTYPE:
            return "Trip Type"
        elif val == LoggedEventModel.USER:
            return "User"
        elif val == LoggedEventModel.VEHICLE:
            return "Vehicle"
        elif val == LoggedEventModel.VEHICLE_MAINTAIN:
            return "Vehicle Maintainence"
        elif val == LoggedEventModel.VEHICLE_ISSUE:
            return "Vehicle Issue"
        elif val == LoggedEventModel.PRETRIP:
            return "Pre-Trip"
        else: # UNKNOWN
            return "Unknown"

class Trip(models.Model):
    STATUS_NORMAL = 0
    STATUS_CANCELED = 1
    STATUS_NO_SHOW = 2

    STATUS_LEVELS = [
        (STATUS_NORMAL, '---------'),
        (STATUS_CANCELED, 'Canceled'),
        (STATUS_NO_SHOW, 'No Show'),
    ]
    STATUS_LEVELS_ACTIVITY = [
        (STATUS_NORMAL, '---------'),
        (STATUS_CANCELED, 'Canceled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    date = models.DateField()
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=FieldSizes.MD)
    address = models.CharField(max_length=FieldSizes.MD, blank=True)
    phone_home = models.CharField(verbose_name='Phone (Home)', max_length=FieldSizes.PHONE, blank=True)
    phone_cell = models.CharField(verbose_name='Phone (Cell)', max_length=FieldSizes.PHONE, blank=True)
    phone_address = models.CharField(verbose_name='Phone (Address)', max_length=FieldSizes.PHONE, blank=True)
    phone_destination = models.CharField(verbose_name='Phone (Destination)', max_length=FieldSizes.PHONE, blank=True)
    destination = models.CharField(max_length=FieldSizes.MD, blank=True)
    pick_up_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    appointment_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    trip_type = models.ForeignKey('TripType', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=FieldSizes.XL, blank=True)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)
    note = models.TextField(max_length=FieldSizes.LG, blank=True)
    start_miles = models.CharField(max_length=FieldSizes.MILES, blank=True)
    start_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    end_miles = models.CharField(max_length=FieldSizes.MILES, blank=True)
    end_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    status = models.IntegerField(choices=STATUS_LEVELS, default=STATUS_NORMAL)
    is_activity = models.BooleanField(default=False, editable=False)
    collected_cash = models.IntegerField(default=0)
    collected_check = models.IntegerField(default=0)
    fare = models.IntegerField(default=0)
    passenger = models.BooleanField(verbose_name='Passenger on vehicle?', default=True)
    cancel_date = models.DateField(default=None, null=True, blank=False)

    class Meta:
        ordering = ['-date', 'sort_index']

    def __str__(self):
        if self.is_activity:
            output = '[' + str(self.date) + ']'

            if self.pick_up_time and self.appointment_time:
                output += ' - ' + str(self.pick_up_time) + ' to ' + str(self.appointment_time)
            elif self.pick_up_time:
                output += ' - ' + str(self.pick_up_time)
            elif self.appointment_time:
                output += ' - ' + str(self.appointment_time)

            output += ' - ' + self.note
            return output

        output = '[' + str(self.date) + '] - ' + self.name
        if self.address is not None and self.address != '':
            output += ' from ' + self.address
            if self.destination is not None and self.destination != '':
                output += ' to ' + self.destination
        return output

    def str_pretty(self):
        output = self.date.strftime('%b %d, %Y') + ' | ' + self.name
        if self.address is not None and self.address != '':
            output += ' from ' + self.address
            if self.destination is not None and self.destination != '':
                output += ' to ' + self.destination
        return output

    def get_driver_color(self):
        site_settings = SiteSettings.load()
        if self.status == Trip.STATUS_CANCELED:
            return site_settings.get_color(SiteSettings.COLOR_CANCEL)
        elif self.status == Trip.STATUS_NO_SHOW:
            return site_settings.get_color(SiteSettings.COLOR_NO_SHOW)
        elif self.is_activity:
            return site_settings.get_color(SiteSettings.COLOR_ACTIVITY)
        else:
            return Driver.get_color(self.driver)

    def get_driver_style(self):
        output = "background: #" + self.get_driver_color() + ";"
        if self.status == Trip.STATUS_CANCELED or self.status == Trip.STATUS_NO_SHOW:
            output += "text-decoration: line-through;"
        return output

    def get_phone_number(self, phone_type):
        num_only = ''
        num_regex = '\d*'
        if phone_type == 'cell':
            matches = re.findall(num_regex, self.phone_cell)
        elif phone_type == 'address':
            matches = re.findall(num_regex, self.phone_address)
        elif phone_type == 'destination':
            matches = re.findall(num_regex, self.phone_destination)
        else:
            matches = re.findall(num_regex, self.phone_home)
        for i in matches:
            num_only += i
        return num_only

    def get_phone_number_list(self):
        phone_numbers = []
        if self.phone_home:
            phone_numbers.append({'label': 'Home Phone', 'value': self.phone_home, 'tel':self.get_phone_number('')})
        if self.phone_cell:
            phone_numbers.append({'label': 'Cell Phone', 'value': self.phone_cell, 'tel':self.get_phone_number('cell')})
        if self.address and self.phone_address:
            phone_numbers.append({'label': self.address, 'value': self.phone_address, 'tel':self.get_phone_number('address')})
        if self.destination and self.phone_destination:
            phone_numbers.append({'label': self.destination, 'value': self.phone_destination, 'tel':self.get_phone_number('destination')})
        return phone_numbers

    def get_phone_number_count(self):
        count = 0
        if self.phone_home:
            count += 1
        if self.phone_cell:
            count += 1
        if self.address and self.phone_address:
            count += 1
        if self.destination and self.phone_destination:
            count += 1
        return count

    def get_class_name(self):
        if self.is_activity:
            return 'Activity'
        else:
            return 'Trip'

    def check_blank(self, field):
        if field != '':
            return True
        elif self.start_miles == '' and self.start_time == '' and self.end_miles == '' and self.end_time == '':
            return True
        else:
            return False

    def check_start_miles(self):
        return self.check_blank(self.start_miles)

    def check_start_time(self):
        return self.check_blank(self.start_time)

    def check_end_miles(self):
        return self.check_blank(self.end_miles)

    def check_end_time(self):
        return self.check_blank(self.end_time)

    def get_tag_list(self):
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            tags[i] = tags[i].strip()
        return tags

    def get_styled_tag_list(self):
        tag_list = []
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            tag_str = tags[i].strip()
            # TODO don't hard-code this
            if tag_str == 'Wheelchair':
                tag_list.append((tag_str, 'badge-warning'))
            else:
                tag_list.append((tag_str, 'badge-info'))
        return tag_list

    def get_collected_cash_str(self):
        return int_to_money_string(self.collected_cash)

    def get_collected_check_str(self):
        return int_to_money_string(self.collected_check)

    def get_fare_str(self):
        return int_to_money_string(self.fare)

    def is_medical(self):
        if self.trip_type is None:
            return False
        return self.trip_type.name == 'Medical'

    def check_tag(self, tag_str):
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            if tags[i].strip() == tag_str:
                return True
        return False

    def get_driver_str(self):
        if self.driver:
            return self.driver.name
        else:
            return '---------'

    def get_vehicle_str(self):
        if self.vehicle:
            return self.vehicle.name
        else:
            return '---------'

    def get_status_str(self):
        if self.is_activity:
            return self.STATUS_LEVELS_ACTIVITY[self.status][1]
        else:
            return self.STATUS_LEVELS[self.status][1]

class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=FieldSizes.SM)
    color = models.CharField(default='FFFFFF', max_length=FieldSizes.COLOR, blank=True)
    is_logged = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Driver'

    def get_color(self):
        if self and self.color != '':
            color = self.color
        else:
            color = 'FFFFFF00'
        
        return color


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=FieldSizes.SM)
    is_logged = models.BooleanField(default=True)
    oil_change_miles = models.CharField(max_length=FieldSizes.MILES, blank=True)
    inspection_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Vehicle'

class TripType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=FieldSizes.SM)
    is_trip_counted = models.BooleanField('Included in report trip counts?', default=True)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Trip Type'

class Shift(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True)
    start_miles = models.CharField(max_length=FieldSizes.MILES, blank=True)
    start_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    end_miles = models.CharField(max_length=FieldSizes.MILES, blank=True)
    end_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    fuel = models.CharField('Fuel (gallons)', max_length=FieldSizes.FUEL, blank=True)
    note = models.TextField(max_length=FieldSizes.LG, blank=True)

    def __str__(self):
        return '[' + str(self.date) + '] - ' + str(self.driver) + ' / ' + str(self.vehicle)

    def get_driver_color(self):
        return Driver.get_color(self.driver)

    def get_class_name(self):
        return 'Shift'

    def check_blank(self, field):
        if field != '':
            return True
        elif self.start_miles == '' and self.start_time == '' and self.end_miles == '' and self.end_time == '':
            return True
        else:
            return False

    def check_start_miles(self):
        return self.check_blank(self.start_miles)

    def check_start_time(self):
        return self.check_blank(self.start_time)

    def check_end_miles(self):
        return self.check_blank(self.end_miles)

    def check_end_time(self):
        return self.check_blank(self.end_time)

    def check_pretrip(self):
        return (len(PreTrip.objects.filter(shift_id=self.id)) > 0)


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=FieldSizes.MD)
    address = models.CharField(max_length=FieldSizes.MD, blank=True)
    phone_home = models.CharField('Phone (Home)', max_length=FieldSizes.PHONE, blank=True)
    phone_cell = models.CharField('Phone (Cell)', max_length=FieldSizes.PHONE, blank=True)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)
    tags = models.CharField(max_length=FieldSizes.XL, blank=True)
    staff = models.BooleanField(verbose_name='Is staff member?', default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Client'

    def get_tag_list(self):
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            tags[i] = tags[i].strip()
        return tags

    def get_styled_tag_list(self):
        tag_list = []
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            tag_str = tags[i].strip()
            # TODO don't hard-code this
            if tag_str == 'Wheelchair':
                tag_list.append((tag_str, 'badge-warning'))
            else:
                tag_list.append((tag_str, 'badge-info'))
        return tag_list

class ClientPayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey('Client', on_delete=models.CASCADE)
    date_paid = models.DateField()
    money_cash = models.IntegerField(default=0)
    money_check = models.IntegerField(default=0)
    notes = models.TextField(max_length=FieldSizes.LG, blank=True)

    class Meta:
        ordering = ['date_paid']

    def get_class_name(self):
        return 'Payment'

    def __str__(self):
        if self.parent:
            return '[' + str(self.date_paid) + '] ' + str(self.parent.name) + ': Cash = $' + self.get_cash_str() + ' | Check = $' + self.get_check_str()
        else:
            return '[' + str(self.date_paid) + '] <None>'

    def get_cash_str(self):
        return int_to_money_string(self.money_cash)

    def get_check_str(self):
        return int_to_money_string(self.money_check)

class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=FieldSizes.MD)
    phone = models.CharField(max_length=FieldSizes.PHONE, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['address']

    def __str__(self):
        output = self.address
        if self.phone:
            output += ' (' + self.phone + ')'
        return output

    def get_class_name(self):
        return 'Destination'

class VehicleIssue(models.Model):
    PRIORITY_HIGH = 2
    PRIORITY_MEDIUM = 1
    PRIORITY_LOW = 0

    PRIORITY_LEVELS = [
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_LOW, 'Low'),
    ]

    ISSUE_NONE = 0
    ISSUE_FLUIDS = 1
    ISSUE_ENGINE = 2
    ISSUE_HEADLIGHTS = 3
    ISSUE_HAZARDS = 4
    ISSUE_DIRECTIONAL = 5
    ISSUE_MARKERS = 6
    ISSUE_WINDSHIELD = 7
    ISSUE_GLASS = 8
    ISSUE_MIRRORS = 9
    ISSUE_DOORS = 10
    ISSUE_TIRES = 11
    ISSUE_LEAKS = 12
    ISSUE_BODY = 13
    ISSUE_REGISTRATION = 14
    ISSUE_WHEELCHAIR = 15
    ISSUE_MECHANICAL = 16
    ISSUE_INTERIOR = 17

    ISSUE_CATEGORIES = [
        (ISSUE_NONE, '---------'),
        (ISSUE_FLUIDS, 'Fuel & Fluids'),
        (ISSUE_ENGINE, 'Engine'),
        (ISSUE_HEADLIGHTS, 'Headlights / High Beams'),
        (ISSUE_HAZARDS, 'Hazards / Ambers'),
        (ISSUE_DIRECTIONAL, 'Directional'),
        (ISSUE_MARKERS, 'Markers / Reflectors'),
        (ISSUE_WINDSHIELD, 'Windshield'),
        (ISSUE_GLASS, 'Other Glass'),
        (ISSUE_MIRRORS, 'Mirrors'),
        (ISSUE_DOORS, 'Doors'),
        (ISSUE_TIRES, 'Tires'),
        (ISSUE_LEAKS, 'Leaks'),
        (ISSUE_BODY, 'Body Damage'),
        (ISSUE_REGISTRATION, 'Registration'),
        (ISSUE_WHEELCHAIR, 'Wheelchair Lift'),
        (ISSUE_MECHANICAL, 'Mechanical'),
        (ISSUE_INTERIOR, 'Interior'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(max_length=FieldSizes.XL, blank=True)
    priority = models.IntegerField(choices=PRIORITY_LEVELS, default=PRIORITY_MEDIUM)
    is_resolved = models.BooleanField(default=False)
    pretrip = models.ForeignKey('PreTrip', on_delete=models.SET_NULL, null=True, blank=True, editable=False)
    pretrip_field = models.CharField(max_length=FieldSizes.SM, default=False, editable=False)
    category = models.IntegerField(choices=ISSUE_CATEGORIES, default=ISSUE_NONE)

    class Meta:
        ordering = ['is_resolved', '-priority', '-date']

    def __str__(self):
        return '[' + str(self.date) + '] ' + str(self.vehicle) + ': ' + self.description

    def get_class_name(self):
        return 'Vehicle Issue'

    def get_category_str(self):
        for i in self.ISSUE_CATEGORIES:
            if i[0] == self.category:
                return i[1]

    def get_category_from_checklist(self, cl_key):
        if cl_key == 'cl_fluids':
            return self.ISSUE_FLUIDS
        elif cl_key == 'cl_engine':
            return self.ISSUE_ENGINE
        elif cl_key == 'cl_headlights':
            return self.ISSUE_HEADLIGHTS
        elif cl_key == 'cl_hazards':
            return self.ISSUE_HAZARDS
        elif cl_key == 'cl_directional':
            return self.ISSUE_DIRECTIONAL
        elif cl_key == 'cl_markers':
            return self.ISSUE_MARKERS
        elif cl_key == 'cl_windshield':
            return self.ISSUE_WINDSHIELD
        elif cl_key == 'cl_glass':
            return self.ISSUE_GLASS
        elif cl_key == 'cl_mirrors':
            return self.ISSUE_MIRRORS
        elif cl_key == 'cl_doors':
            return self.ISSUE_DOORS
        elif cl_key == 'cl_tires':
            return self.ISSUE_TIRES
        elif cl_key == 'cl_leaks':
            return self.ISSUE_LEAKS
        elif cl_key == 'cl_body':
            return self.ISSUE_BODY
        elif cl_key == 'cl_registration':
            return self.ISSUE_REGISTRATION
        elif cl_key == 'cl_wheelchair':
            return self.ISSUE_WHEELCHAIR
        elif cl_key == 'cl_mechanical':
            return self.ISSUE_MECHANICAL
        elif cl_key == 'cl_interior':
            return self.ISSUE_INTERIOR
        else:
            return self.ISSUE_NONE

class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=128)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Template'

class TemplateTrip(models.Model):
    STATUS_NORMAL = 0
    STATUS_CANCELED = 1

    STATUS_LEVELS = [
        (STATUS_NORMAL, '---------'),
        (STATUS_CANCELED, 'Canceled'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey('Template', on_delete=models.CASCADE)
    sort_index = models.IntegerField(default=0, editable=False)
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=FieldSizes.MD)
    address = models.CharField(max_length=FieldSizes.MD, blank=True)
    phone_home = models.CharField(verbose_name='Phone (Home)', max_length=FieldSizes.PHONE, blank=True)
    phone_cell = models.CharField(verbose_name='Phone (Cell)', max_length=FieldSizes.PHONE, blank=True)
    phone_address = models.CharField(verbose_name='Phone (Address)', max_length=FieldSizes.PHONE, blank=True)
    phone_destination = models.CharField(verbose_name='Phone (Destination)', max_length=FieldSizes.PHONE, blank=True)
    destination = models.CharField(max_length=FieldSizes.MD, blank=True)
    pick_up_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    appointment_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    trip_type = models.ForeignKey('TripType', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=FieldSizes.XL, blank=True)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)
    note = models.TextField(max_length=FieldSizes.LG, blank=True)
    is_activity = models.BooleanField(default=False, editable=False)
    status = models.IntegerField(choices=STATUS_LEVELS, default=STATUS_NORMAL)
    fare = models.IntegerField(default=0)
    passenger = models.BooleanField(verbose_name='Passenger on vehicle?', default=True)

    class Meta:
        ordering = ['parent', 'sort_index']

    def __str__(self):
        if self.is_activity:
            output = ''
            if self.pick_up_time:
                output += str(self.pick_up_time) + ' - '
            if self.appointment_time: 
                output += str(self.appointment_time) + ' - '
            output += self.note
            return output

        output = '[' + self.parent.name + '] - ' + self.name
        if self.address is not None and self.address != '':
            output += ' from ' + self.address
            if self.destination is not None and self.destination != '':
                output += ' to ' + self.destination
        return output

    def get_class_name(self):
        if self.is_activity:
            return 'Activity Template'
        else:
            return 'Trip Template'

    def get_tag_list(self):
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            tags[i] = tags[i].strip()
        return tags

    def get_styled_tag_list(self):
        tag_list = []
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            tag_str = tags[i].strip()
            # TODO don't hard-code this
            if tag_str == 'Wheelchair':
                tag_list.append((tag_str, 'badge-warning'))
            else:
                tag_list.append((tag_str, 'badge-info'))
        return tag_list

    def is_medical(self):
        if self.trip_type is None:
            return False
        return self.trip_type.name == 'Medical'

    def get_driver_color(self):
        site_settings = SiteSettings.load()
        if self.status > 0:
            return site_settings.get_color(SiteSettings.COLOR_CANCEL)
        elif self.is_activity:
            return site_settings.get_color(SiteSettings.COLOR_ACTIVITY)
        else:
            return Driver.get_color(self.driver)

    def get_driver_style(self):
        output = "background: #" + self.get_driver_color() + ";"
        if self.status == Trip.STATUS_CANCELED or self.status == Trip.STATUS_NO_SHOW:
            output += "text-decoration: line-through;"
        return output

    def get_fare_str(self):
        return int_to_money_string(self.fare)


class ScheduleMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    message = models.CharField(max_length=FieldSizes.LG, blank=True)

class PreTrip(models.Model):
    CHECKLIST = {
        'cl_fluids': {'label': 'All Fuel & Fluids', 'subitems': ('Gas', 'Oil', 'Anti-Freeze', 'Windshield Wash')},
        'cl_engine': {'label': 'Start Engine'},
        'cl_headlights': {'label': 'Head Lights / High Beams'},
        'cl_hazards': {'label': 'Hazards / Ambers'},
        'cl_directional': {'label': 'Directional'},
        'cl_markers': {'label': 'Markers / Reflectors'},
        'cl_windshield': {'label': 'Windshield'},
        'cl_glass': {'label': 'All Other Glass'},
        'cl_mirrors': {'label': 'All Mirrors'},
        'cl_doors': {'label': 'All Door Operation'},
        'cl_tires': {'label': 'Tires', 'subitems': ('Pressure', 'Condition')},
        'cl_leaks': {'label': 'Leaks of Any Kind'},
        'cl_body': {'label': 'Body Damage'},
        'cl_registration': {'label': 'Registration', 'subitems': ('Plate', 'Sticker')},
        'cl_wheelchair': {'label': 'Wheelchair Lift', 'subitems': ('Condition', 'Operation')},
        'cl_mechanical': {'label': 'Mechanical'},
        'cl_interior': {'label': 'Interior', 'subitems': ('Lights', 'Seats', 'Belts', 'Registration & Insurance Paperwork', 'Cleanliness', 'Horn', 'Fire Extinguisher', 'First Aid Kit', 'Entry Steps', 'Floor Covering', 'All wheelchair track and harnessing', 'All assigned van electronics (communication & navigational)', 'Personal belongings left behind')},
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(editable=False)
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True, editable=False)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True, editable=False)
    shift_id = models.UUIDField(editable=False, null=True)
    cl_fluids = models.IntegerField(default=0)
    cl_engine = models.IntegerField(default=0)
    cl_headlights = models.IntegerField(default=0)
    cl_hazards = models.IntegerField(default=0)
    cl_directional = models.IntegerField(default=0)
    cl_markers = models.IntegerField(default=0)
    cl_windshield = models.IntegerField(default=0)
    cl_glass = models.IntegerField(default=0)
    cl_mirrors = models.IntegerField(default=0)
    cl_doors = models.IntegerField(default=0)
    cl_tires = models.IntegerField(default=0)
    cl_leaks = models.IntegerField(default=0)
    cl_body = models.IntegerField(default=0)
    cl_registration = models.IntegerField(default=0)
    cl_wheelchair = models.IntegerField(default=0)
    cl_mechanical = models.IntegerField(default=0)
    cl_interior = models.IntegerField(default=0)

    def __str__(self):
        output = str(self.date) + ' - ' + str(self.driver) + ' - ' + str(self.vehicle)
        if (self.status() == 2):
            output += ' - Passed'
        elif self.status() == 1:
            output += ' - Failed'
        
        return output

    def status(self):
        if self.cl_fluids == 2 and self.cl_engine == 2 and self.cl_headlights == 2 and self.cl_hazards == 2 and self.cl_directional == 2 and self.cl_markers == 2 and self.cl_windshield == 2 and self.cl_glass == 2 and self.cl_mirrors == 2 and self.cl_doors == 2 and self.cl_tires == 2 and self.cl_leaks == 2 and self.cl_body == 2 and self.cl_registration == 2 and self.cl_wheelchair == 2 and self.cl_interior == 2:
            return 2
        else:
            return 1

    def failure_list(self):
        output = []

        issues = VehicleIssue.objects.filter(pretrip=self)

        for i in self.CHECKLIST:
            if getattr(self, i) == 1:
                fail = { 'label': self.CHECKLIST[i]['label'], 'issue_id': None }
                for issue in issues:
                    if issue.pretrip_field == i:
                        fail['issue_id'] = issue.id
                        break
                output.append(fail)

        return output

    def get_class_name(self):
        return 'Pre-Trip'

class Fare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=FieldSizes.MD)
    fare = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name + ": $" + self.get_fare_str()

    def get_class_name(self):
        return 'Fare'

    def get_fare_str(self):
        return int_to_money_string(self.fare)

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=FieldSizes.SM)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Tag'

    def get_button_style(self):
        # TODO don't hard-code this
        if self.name == 'Wheelchair':
            return 'btn-warning'
        else:
            return 'btn-info'

class LoggedEvent(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    username = models.CharField(default='{unknown user}', max_length=FieldSizes.MD, blank=False)
    ip_address = models.GenericIPAddressField(default=None, blank=True, null=True)
    event_action = models.IntegerField(default=LoggedEventAction.UNKNOWN)
    event_model = models.IntegerField(default=LoggedEventModel.UNKNOWN)
    event_desc = models.CharField(default='', max_length=FieldSizes.XL, blank=True)

    def get_model_str(self):
        return LoggedEventModel.get_str(self.event_model)

    def get_action_str(self):
        return LoggedEventAction.get_str(self.event_action)

class SiteSettings(SingletonModel):
    COLOR_ACTIVITY = 0
    COLOR_CANCEL = 1
    COLOR_NO_SHOW = 2

    id = models.AutoField(primary_key=True)
    activity_color = models.CharField(default='DDD9C3', max_length=FieldSizes.COLOR, blank=True)
    cancel_color = models.CharField(default='BBBBBB', max_length=FieldSizes.COLOR, blank=True)
    no_show_color = models.CharField(default='888888', max_length=FieldSizes.COLOR, blank=True)
    autocomplete_history_days = models.IntegerField(default=30)
    reset_filter_on_shift_change = models.BooleanField(verbose_name='Reset Schedule filter when starting/ending Shift', default=False)
    skip_weekends = models.BooleanField(verbose_name='Skip weekends in Schedule date picker', default=False)
    pretrip_warning_threshold = models.IntegerField(default=14)
    page_title = models.CharField(max_length=FieldSizes.LG, blank=True)
    short_page_title = models.CharField(max_length=FieldSizes.MD, blank=True)

    def get_color(self, context):
        if context == self.COLOR_ACTIVITY:
            if self.activity_color != '':
                color = self.activity_color
        elif context == self.COLOR_CANCEL:
            if self.cancel_color != '':
                color = self.cancel_color
        elif context == self.COLOR_NO_SHOW:
            if self.no_show_color != '':
                color = self.no_show_color
        else:
            color = '00000000'

        return color


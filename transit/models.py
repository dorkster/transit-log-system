import uuid, re, datetime
from django.db import models
from django.urls import reverse

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

    # TODO event? (i.e. Mealsite)
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
        if self.status > 0:
            return site_settings.get_color('cancel')
        elif self.is_activity:
            return site_settings.get_color('activity')
        else:
            return Driver.get_color(self.driver)

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

    class LogData():
        def __init__(self):
            self.start_miles = None
            self.start_time = None
            self.end_miles = None
            self.end_time = None

    def get_parsed_log_data(self, shift_miles):
        if self.start_miles == '' or self.start_time == '' or self.end_miles == '' or self.end_time == '' or self.is_activity:
            return None

        data = self.LogData()
        data.start_miles = float(shift_miles[0:len(shift_miles)-len(self.start_miles)] + self.start_miles)
        data.start_time = datetime.datetime.strptime(self.start_time, '%I:%M %p')
        data.end_miles = float(shift_miles[0:len(shift_miles)-len(self.end_miles)] + self.end_miles)
        data.end_time = datetime.datetime.strptime(self.end_time, '%I:%M %p')

        return data

    def get_error_str(self):
        if (self.start_miles == '' and self.start_time == '' and self.end_miles == '' and self.end_time == '') or self.is_activity:
            return '' # Empty; can be safely ignored
        if self.start_miles == '' or self.start_time == '' or self.end_miles == '' or self.end_time == '':
            error_msg = ''

            if self.vehicle == None:
                error_msg = '<strong class="text-danger">Error</strong><span class="text-muted">: Trip contains log data, but has no vehicle assigned.</span><br/>'
            else:
                error_msg = '<strong class="text-danger">Error</strong><span class="text-muted">: Trip contains partial log data.</span><br/>'

            if error_msg != '':
                error_ref = str(self) + '<br/><a href="' + reverse('schedule', kwargs={'mode':'edit', 'year':self.date.year, 'month':self.date.month, 'day':self.date.day}) + '#trip_' + str(self.id) + '">View Schedule</a> | <a href="' + reverse('trip-edit', kwargs={'mode':'edit', 'id':self.id}) + '">Edit</a>'
                return error_msg + error_ref
        else:
            return ''

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
        if self.collected_cash == 0:
            return '0.00'
        s = str(self.collected_cash)
        return s[:len(s)-2] + '.' + s[len(s)-2:]

    def get_collected_check_str(self):
        if self.collected_check == 0:
            return '0.00'
        s = str(self.collected_check)
        return s[:len(s)-2] + '.' + s[len(s)-2:]

    def is_medical(self):
        if self.trip_type is None:
            return False
        return self.trip_type.name == 'Medical'

class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=FieldSizes.SM)
    color = models.CharField(max_length=FieldSizes.COLOR, blank=True)
    is_logged = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Driver'

    def get_color(self):
        color = '00000000'
        if self and self.color != '':
            color = self.color
        
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

    class LogData():
        def __init__(self):
            self.start_miles = None
            self.start_time = None
            self.end_miles = None
            self.end_time = None
            self.fuel = 0

            # string used for parsing Trip log data
            self.start_miles_str = None

    def get_parsed_log_data(self):
        if self.start_miles == '' or self.start_time == '' or self.end_miles == '' or self.end_time == '':
            return None

        data = self.LogData()
        data.driver = self.driver
        data.start_miles = float(self.start_miles)
        data.start_time = datetime.datetime.strptime(self.start_time, '%I:%M %p')
        data.end_miles = float(self.end_miles)
        data.end_time = datetime.datetime.strptime(self.end_time, '%I:%M %p')
        if self.fuel != '':
            data.fuel = float(self.fuel)

        data.start_miles_str = self.start_miles

        return data

    def get_error_str(self):
        if self.start_miles == '' and self.start_time == '' and self.end_miles == '' and self.end_time == '':
            return '' # Empty; can be safely ignored
        if self.start_miles == '' or self.start_time == '' or self.end_miles == '' or self.end_time == '':
            # vehicle can not be None due to form validation, so no need to check for it here
            error_msg = '<strong class="text-danger">Error</strong><span class="text-muted">: Shift contains partial log data.</span><br/>'
            error_ref = str(self) + '<br/><a href="' + reverse('schedule', kwargs={'mode':'edit', 'year':self.date.year, 'month':self.date.month, 'day':self.date.day}) + '">View Schedule</a> | <a href="' + reverse('shift-edit', kwargs={'mode':'edit', 'id':self.id}) + '">Edit</a>'
            return error_msg + error_ref
        else:
            return ''

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

    def get_start_end_trips(self):
        trip_miles_start = 0
        trip_miles_end = 0
        trip_time_start = 0
        trip_time_end = 0
        trip_data_list = []
        shift_data = self.get_parsed_log_data()

        for trip in Trip.objects.filter(date=self.date, vehicle=self.vehicle, status=Trip.STATUS_NORMAL):
            trip_data = trip.get_parsed_log_data(self.start_miles)

            if trip_data is None:
                continue

            # TODO also check time?
            if trip_data.start_miles < shift_data.start_miles or trip_data.end_miles > shift_data.end_miles:
                continue

            trip_data_list.append(trip_data)
            last_index = len(trip_data_list)-1
            if trip_data.start_miles < trip_data_list[trip_miles_start].start_miles:
                trip_miles_start = last_index
            if trip_data.end_miles > trip_data_list[trip_miles_end].end_miles:
                trip_miles_end = last_index
            if trip_data.start_time < trip_data_list[trip_time_start].start_time:
                trip_time_start = last_index
            if trip_data.end_time > trip_data_list[trip_time_end].end_time:
                trip_time_end = last_index

        if len(trip_data_list) > 0:
            return (trip_data_list[trip_miles_start], trip_data_list[trip_time_start], trip_data_list[trip_miles_end], trip_data_list[trip_time_end])
        else:
            return None


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=FieldSizes.MD)
    address = models.CharField(max_length=FieldSizes.MD, blank=True)
    phone_home = models.CharField('Phone (Home)', max_length=FieldSizes.PHONE, blank=True)
    phone_cell = models.CharField('Phone (Cell)', max_length=FieldSizes.PHONE, blank=True)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)
    tags = models.CharField(max_length=FieldSizes.XL, blank=True)

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

class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=FieldSizes.MD)
    phone = models.CharField(max_length=FieldSizes.PHONE, blank=True)

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
            return ISSUE_NONE

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

    class Meta:
        ordering = ['parent', 'sort_index']

    def __str__(self):
        if self.is_activity:
            output = ''
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
        if self.is_activity:
            return site_settings.get_color('activity')
        else:
            return Driver.get_color(self.driver)

class ScheduleMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    message = models.CharField(max_length=FieldSizes.LG, blank=True)

class FrequentTag(models.Model):
    tag = models.CharField(primary_key=True, max_length=FieldSizes.SM)
    count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-count']

    def addTags(tag_list):
        for i in tag_list:
            i_tag = i.strip()
            if i_tag == '':
                continue

            try:
                f_tag = FrequentTag.objects.get(tag=i_tag)
                f_tag.count += 1
                f_tag.save()
            except:
                f_tag = FrequentTag()
                f_tag.tag = i_tag
                f_tag.count = 1
                f_tag.save()

    def removeTags(tag_list):
        for i in tag_list:
            i_tag = i.strip()
            if i_tag == '':
                continue

            try:
                f_tag = FrequentTag.objects.get(tag=i_tag)
                f_tag.count -= 1
                if f_tag.count <= 0:
                    f_tag.delete()
                else:
                    f_tag.save()
            except:
                pass

    def getStyle(self):
        # TODO don't hard-code this
        if self.tag == 'Wheelchair':
            return 'badge-warning'
        else:
            return 'badge-info'

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
    shift_id = models.UUIDField(editable=False)
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

class SiteSettings(SingletonModel):
    activity_color = models.CharField(default='DDD9C3', max_length=FieldSizes.COLOR, blank=True)
    cancel_color = models.CharField(default='BBBBBB', max_length=FieldSizes.COLOR, blank=True)
    autocomplete_history_days = models.IntegerField(default=30)
    reset_filter_on_shift_change = models.BooleanField(verbose_name='Reset Schedule filter when starting/ending Shift', default=False)

    def get_color(self, context):
        color = '00000000'
        if context == 'activity':
            if self.activity_color != '':
                color = self.activity_color
        elif context == 'cancel':
            if self.cancel_color != '':
                color = self.cancel_color

        return color

class HelpPage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0)
    slug = models.CharField(max_length=FieldSizes.MD, unique=True)
    title = models.CharField(max_length=FieldSizes.XL)
    body = models.TextField(max_length=8192, blank=True)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.title

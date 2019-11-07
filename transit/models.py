import uuid, re, datetime
from django.db import models
from django.urls import reverse

# Create your models here.

class Trip(models.Model):
    # TODO event? (i.e. Mealsite)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    date = models.DateField()
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=256)
    address = models.CharField(max_length=256, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    destination = models.CharField(max_length=256, blank=True)
    pick_up_time = models.CharField(max_length=16, blank=True)
    appointment_time = models.CharField(max_length=16, blank=True)
    trip_type = models.ForeignKey('TripType', on_delete=models.SET_NULL, null=True, blank=True)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)
    note = models.TextField(max_length=1024, blank=True)
    start_miles = models.CharField(max_length=32, blank=True)
    start_time = models.CharField(max_length=16, blank=True)
    end_miles = models.CharField(max_length=32, blank=True)
    end_time = models.CharField(max_length=16, blank=True)
    is_canceled = models.BooleanField(verbose_name='Canceled', default=False)

    class Meta:
        ordering = ['-date', 'sort_index']

    def __str__(self):
        output = '[' + str(self.date) + '] - ' + self.name
        if self.address is not None and self.address is not '':
            output += ' from ' + self.address
            if self.destination is not None and self.destination is not '':
                output += ' to ' + self.destination
        return output

    def str_pretty(self):
        output = self.date.strftime('%b %d, %Y') + ' | ' + self.name
        if self.address is not None and self.address is not '':
            output += ' from ' + self.address
            if self.destination is not None and self.destination is not '':
                output += ' to ' + self.destination
        return output

    def get_driver_color(self):
        if self.is_canceled:
            return '#BBBBBB'
        else:
            return Driver.get_color(self.driver)

    def get_phone_number(self):
        num_only = ''
        matches = re.findall('\d*', self.phone)
        for i in matches:
            num_only += i
        return num_only

    def get_class_name(self):
        return 'Trip'

    class LogData():
        def __init__(self):
            self.start_miles = None
            self.start_time = None
            self.end_miles = None
            self.end_time = None

    def get_parsed_log_data(self, shift_miles):
        if self.start_miles == '' or self.start_time == '' or self.end_miles == '' or self.end_time == '':
            return None

        data = self.LogData()
        data.start_miles = float(shift_miles[0:len(shift_miles)-len(self.start_miles)] + self.start_miles)
        data.start_time = datetime.datetime.strptime(self.start_time, '%I:%M %p')
        data.end_miles = float(shift_miles[0:len(shift_miles)-len(self.end_miles)] + self.end_miles)
        data.end_time = datetime.datetime.strptime(self.end_time, '%I:%M %p')

        return data

    def get_error_str(self):
        if self.start_miles == '' and self.start_time == '' and self.end_miles == '' and self.end_time == '':
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

class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=32)
    color = models.CharField(max_length=9, blank=True)
    is_logged = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Driver'

    def get_color(self):
        color = 'none'
        if self and self.color != '':
            color = self.color
        
        return color


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=32)
    is_logged = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_index']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Vehicle'

class TripType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sort_index = models.IntegerField(default=0, editable=False)
    name = models.CharField(max_length=32)

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
    start_miles = models.CharField(max_length=32, blank=True)
    start_time = models.CharField(max_length=16, blank=True)
    end_miles = models.CharField(max_length=32, blank=True)
    end_time = models.CharField(max_length=16, blank=True)
    fuel = models.CharField('Fuel (gallons)', max_length=16, blank=True)

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


class Client(models.Model):
    PHONE_HOME = 'home'
    PHONE_MOBILE = 'mobi'

    DEFAULT_PHONE = [
        (PHONE_HOME, 'Home'),
        (PHONE_MOBILE, 'Mobile'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    address = models.CharField(max_length=256, blank=True)
    phone_home = models.CharField('Phone (Home)', max_length=32, blank=True)
    phone_mobile = models.CharField('Phone (Mobile)', max_length=32, blank=True)
    phone_default = models.CharField('Default Phone Number', max_length=4, choices=DEFAULT_PHONE, default=PHONE_HOME)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_class_name(self):
        return 'Client'

class VehicleIssue(models.Model):
    PRIORITY_HIGH = 2
    PRIORITY_MEDIUM = 1
    PRIORITY_LOW = 0

    PRIORITY_LEVELS = [
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_LOW, 'Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(max_length=4096, blank=True)
    priority = models.IntegerField(choices=PRIORITY_LEVELS, default=PRIORITY_MEDIUM)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['is_resolved', '-priority', '-date']

    def __str__(self):
        return '[' + str(self.date) + '] ' + str(self.vehicle) + ': ' + self.description

    def get_class_name(self):
        return 'Vehicle Issue'

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
    name = models.CharField(max_length=256)
    address = models.CharField(max_length=256, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    destination = models.CharField(max_length=256, blank=True)
    pick_up_time = models.CharField(max_length=16, blank=True)
    appointment_time = models.CharField(max_length=16, blank=True)
    trip_type = models.ForeignKey('TripType', on_delete=models.SET_NULL, null=True, blank=True)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)
    note = models.TextField(max_length=1024, blank=True)

    class Meta:
        ordering = ['parent', 'sort_index']

    def __str__(self):
        output = '[' + self.parent.name + '] - ' + self.name
        if self.address is not None and self.address is not '':
            output += ' from ' + self.address
            if self.destination is not None and self.destination is not '':
                output += ' to ' + self.destination
        return output

    def get_class_name(self):
        return 'Trip Template'

class ScheduleMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    message = models.CharField(max_length=1024, blank=True)

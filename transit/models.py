import uuid, re, datetime
from django.db import models
from django.urls import reverse

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
            output = '[' + str(self.date) + '] - '
            if self.appointment_time: 
                output += str(self.appointment_time) + ' - '
            output += self.note
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
        if self.status > 0:
            return 'BBBBBB'
        elif self.is_activity:
            return 'DDD9C3'
        else:
            return Driver.get_color(self.driver)

    def get_phone_number(self, phone_type):
        num_only = ''
        num_regex = '\d*'
        if phone_type == 'cell':
            matches = re.findall(num_regex, self.phone_cell)
        else:
            matches = re.findall(num_regex, self.phone_home)
        for i in matches:
            num_only += i
        return num_only

    def get_phone_home_number(self):
        return self.get_phone_number('') # default is home number

    def get_phone_cell_number(self):
        return self.get_phone_number('cell')

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
        print(tags)
        return tags

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
    description = models.TextField(max_length=FieldSizes.XL, blank=True)
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
    name = models.CharField(max_length=FieldSizes.MD)
    address = models.CharField(max_length=FieldSizes.MD, blank=True)
    phone_home = models.CharField(verbose_name='Phone (Home)', max_length=FieldSizes.PHONE, blank=True)
    phone_cell = models.CharField(verbose_name='Phone (Cell)', max_length=FieldSizes.PHONE, blank=True)
    destination = models.CharField(max_length=FieldSizes.MD, blank=True)
    pick_up_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    appointment_time = models.CharField(max_length=FieldSizes.TIME, blank=True)
    trip_type = models.ForeignKey('TripType', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=FieldSizes.XL, blank=True)
    elderly = models.BooleanField(verbose_name='Elderly?', null=True, blank=True)
    ambulatory = models.BooleanField(verbose_name='Ambulatory?', null=True, blank=True)
    note = models.TextField(max_length=FieldSizes.LG, blank=True)

    class Meta:
        ordering = ['parent', 'sort_index']

    def __str__(self):
        output = '[' + self.parent.name + '] - ' + self.name
        if self.address is not None and self.address != '':
            output += ' from ' + self.address
            if self.destination is not None and self.destination != '':
                output += ' to ' + self.destination
        return output

    def get_class_name(self):
        return 'Trip Template'

    def get_tag_list(self):
        tags = self.tags.split(',')
        for i in range(0, len(tags)):
            tags[i] = tags[i].strip()
        return tags

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

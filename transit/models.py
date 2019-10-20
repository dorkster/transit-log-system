import uuid, re
from django.db import models

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

    def get_absolute_url(self):
        return reverse('model-detail-view', args=[str(self.id)])

    def __str__(self):
        output = '[' + str(self.date) + '] - ' + self.name
        if self.address is not None and self.address is not "":
            output += ' from ' + self.address
            if self.destination is not None and self.destination is not "":
                output += ' to ' + self.destination
        return output

    def str_pretty(self):
        output = self.date.strftime("%b %d, %Y") + ' | ' + self.name
        if self.address is not None and self.address is not "":
            output += ' from ' + self.address
            if self.destination is not None and self.destination is not "":
                output += ' to ' + self.destination
        return output

    def get_driver_color(self):
        if self.is_canceled:
            return "#BBBBBB"
        else:
            return Driver.get_color(self.driver)

    def get_phone_number(self):
        num_only = ''
        matches = re.findall("\d*", self.phone)
        for i in matches:
            num_only += i
        return num_only

    def get_class_name(self):
        return 'Trip'

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
        if self and self.color != "":
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
    name = models.CharField(max_length=32)
    def __str__(self):
        return self.name

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


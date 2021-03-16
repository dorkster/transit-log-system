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
import subprocess

from transit.models import SiteSettings, VehicleIssue, Vehicle, Shift

def sitesettings(request):
    return {
        'settings': SiteSettings.load(),
    }

def notifications(request):
    vehicle_inspections = []
    vehicle_oil_changes = []

    today = datetime.date.today()
    for v in Vehicle.objects.filter(is_logged=True):
        if v.inspection_date is not None:
            due_date = v.inspection_date
            if today >= due_date:
                vehicle_inspections.append(v)

        if v.oil_change_miles != '':
            latest_shift = Shift.objects.filter(vehicle=v.id).order_by('date').exclude(end_miles='').last()
            if latest_shift is not None and latest_shift.end_miles != '':
                # NOTE considering that a bug with the string formatting can wreck the site here, we check exceptions
                # TODO validate string before passing to float()?
                try:
                    shift_miles = float(latest_shift.end_miles);
                except:
                    shift_miles = 0
                try:
                    oil_change_miles = float(v.oil_change_miles);
                except:
                    oil_change_miles = 0
                if shift_miles >= oil_change_miles:
                    vehicle_oil_changes.append(v)


    vehicle_issues = VehicleIssue.objects.filter(priority__gt=VehicleIssue.PRIORITY_LOW, is_resolved=False)
    vehicle_issues_low = VehicleIssue.objects.filter(priority=VehicleIssue.PRIORITY_LOW, is_resolved=False)
    return {
        'notifications': (len(vehicle_issues) > 0 or len(vehicle_issues_low) > 0 or len(vehicle_inspections) > 0 or len(vehicle_oil_changes) > 0),
        'notify_vehicle_issues': vehicle_issues,
        'notify_vehicle_issues_low': vehicle_issues_low,
        'notify_vehicle_inspections': vehicle_inspections,
        'notify_vehicle_oil_changes': vehicle_oil_changes,
    }

def version(request):
    version_str = subprocess.run(['git', 'describe', '--tags'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    return {
        'version': version_str,
    }


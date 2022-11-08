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

from transit.models import SiteSettings, VehicleIssue, Vehicle, Shift, PreTrip

class VersionInfo():
    version_str = subprocess.run(['git', 'describe', '--tags'], stdout=subprocess.PIPE).stdout.decode('utf-8')

def globals(request):
    site_settings = SiteSettings.load()

    vehicle_inspections = []
    vehicle_oil_changes = []
    vehicle_pretrips = []

    today = datetime.date.today()

    if site_settings.pretrip_warning_threshold > 0:
        pretrip_threshold = today - datetime.timedelta(days=site_settings.pretrip_warning_threshold)
        pretrips = PreTrip.objects.filter(date__gte=pretrip_threshold)

    for v in Vehicle.objects.filter(is_logged=True, is_shown_in_notifications=True):
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

        if site_settings.pretrip_warning_threshold > 0 and len(pretrips.filter(vehicle=v.id)) == 0:
            vehicle_pretrips.append(v)


    vehicle_issues_low = VehicleIssue.objects.filter(priority=VehicleIssue.PRIORITY_LOW, is_resolved=False)
    vehicle_issues_medium = VehicleIssue.objects.filter(priority=VehicleIssue.PRIORITY_MEDIUM, is_resolved=False)
    vehicle_issues_high = VehicleIssue.objects.filter(priority=VehicleIssue.PRIORITY_HIGH, is_resolved=False)

    vehicle_issues_featured_medium = vehicle_issues_medium.filter(vehicle__is_shown_in_notifications=True)
    vehicle_issues_featured_high = vehicle_issues_high.filter(vehicle__is_shown_in_notifications=True)

    return {
        'notifications': (len(vehicle_issues_low) > 0 or len(vehicle_issues_medium) > 0 or len(vehicle_issues_high) > 0 or len(vehicle_inspections) > 0 or len(vehicle_oil_changes) > 0 or len(vehicle_pretrips) > 0),
        'notify_vehicle_issues_low': vehicle_issues_low,
        'notify_vehicle_issues_medium': vehicle_issues_medium,
        'notify_vehicle_issues_high': vehicle_issues_high,
        'notify_vehicle_issues_featured_medium': vehicle_issues_featured_medium,
        'notify_vehicle_issues_featured_high': vehicle_issues_featured_high,
        'notify_vehicle_inspections': vehicle_inspections,
        'notify_vehicle_oil_changes': vehicle_oil_changes,
        'notify_vehicle_pretrips': vehicle_pretrips,
        'settings': site_settings,
        'version': VersionInfo.version_str,
    }


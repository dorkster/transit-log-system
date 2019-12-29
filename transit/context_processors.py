import datetime

from transit.models import SiteSettings, VehicleIssue, Vehicle, Shift

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
                shift_miles = float(latest_shift.end_miles);
                oil_change_miles = float(v.oil_change_miles);
                if shift_miles >= oil_change_miles:
                    vehicle_oil_changes.append(v)


    vehicle_issues = VehicleIssue.objects.filter(priority__gt=VehicleIssue.PRIORITY_LOW, is_resolved=False)
    return {
        'settings': SiteSettings.load(),
        'notifications': (len(vehicle_issues) > 0 or len(vehicle_inspections) > 0 or len(vehicle_oil_changes) > 0),
        'notify_vehicle_issues': vehicle_issues,
        'notify_vehicle_inspections': vehicle_inspections,
        'notify_vehicle_oil_changes': vehicle_oil_changes,
    }

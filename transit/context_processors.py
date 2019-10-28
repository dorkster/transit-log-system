from transit.models import VehicleIssue

def notifications(request):
    vehicle_issues = VehicleIssue.objects.filter(priority__gt=VehicleIssue.PRIORITY_LOW, is_resolved=False)
    return {
        'notify_vehicle_issues': vehicle_issues,
    }

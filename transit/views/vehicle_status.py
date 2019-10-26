from django.shortcuts import render

from transit.models import VehicleIssue

def vehicleStatus(request):
    # context = {
    #     'vehicle_issues': VehicleIssue.objects.all(),
    # }
    return render(request, 'vehicle/status/view.html', context={})

def ajaxVehicleStatus(request):
    vehicle_issues = VehicleIssue.objects.all()
    return render(request, 'vehicle/status/ajax_view.html', {'vehicle_issues': vehicle_issues})


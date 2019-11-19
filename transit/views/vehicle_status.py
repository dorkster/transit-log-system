import uuid

from django.shortcuts import render, get_object_or_404

from transit.models import VehicleIssue, Vehicle

def vehicleStatus(request):
    return render(request, 'vehicle/status/view.html', context={})

def ajaxVehicleStatus(request):
    request_id = ''
    if request.GET['target_id'] != '':
        request_id = uuid.UUID(request.GET['target_id'])

    request_action = request.GET['target_action']
    request_data = request.GET['target_data']

    if request_action == 'toggle_resolved':
        issue = get_object_or_404(VehicleIssue, id=request_id)
        issue.is_resolved = not issue.is_resolved
        issue.save()
    elif request_action == 'filter_toggle_resolved':
        request.session['vehicle_status_filter_show_resolved'] = not request.session.get('vehicle_status_filter_show_resolved', False)
    elif request_action == 'filter_reset':
        request.session['vehicle_status_filter_show_resolved'] = False;

    filter_show_resolved = request.session.get('vehicle_status_filter_show_resolved', False)

    if not filter_show_resolved:
        vehicle_issues = VehicleIssue.objects.filter(is_resolved=False)
    else:
        vehicle_issues = VehicleIssue.objects.all()

    context = {
        'vehicle_issues': vehicle_issues,
        'filter_show_resolved': filter_show_resolved,
        'is_filtered': (filter_show_resolved),
        'logged_vehicles': Vehicle.objects.filter(is_logged=True)
    }
    return render(request, 'vehicle/status/ajax_view.html', context=context)


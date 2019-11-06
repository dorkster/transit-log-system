import uuid

from django.shortcuts import render, get_object_or_404

from transit.models import VehicleIssue

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

    filter_show_resolved_str = request.GET.get('filter_show_resolved', None)

    if filter_show_resolved_str is not None:
        filter_show_resolved_str = filter_show_resolved_str.lower()
        request.session['vehicle_status_filter_show_resolved'] = True if filter_show_resolved_str == 'true' else False

    filter_show_resolved = request.session.get('vehicle_status_filter_show_resolved', False)

    if not filter_show_resolved:
        vehicle_issues = VehicleIssue.objects.filter(is_resolved=False)
    else:
        vehicle_issues = VehicleIssue.objects.all()

    context = {
        'vehicle_issues': vehicle_issues,
        'filter_show_resolved': filter_show_resolved
    }
    return render(request, 'vehicle/status/ajax_view.html', context=context)


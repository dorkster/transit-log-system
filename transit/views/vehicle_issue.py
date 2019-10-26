import datetime, uuid

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from transit.models import VehicleIssue
from transit.forms import EditVehicleIssueForm

def vehicleIssueCreate(request):
    vehicle_issue = VehicleIssue()
    return vehicleIssueCreateEditCommon(request, vehicle_issue, is_new=True)

def vehicleIssueEdit(request, id):
    vehicle_issue = get_object_or_404(VehicleIssue, id=id)
    return vehicleIssueCreateEditCommon(request, vehicle_issue, is_new=False)

def vehicleIssueCreateEditCommon(request, vehicle_issue, is_new):
    if request.method == 'POST':
        form = EditVehicleIssueForm(request.POST)

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-status'))
        elif 'delete' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-issue-delete', kwargs={'id':vehicle_issue.id}))

        if form.is_valid():
            if is_new:
                vehicle_issue.date = datetime.datetime.now().date()

            vehicle_issue.driver = form.cleaned_data['driver']
            vehicle_issue.vehicle = form.cleaned_data['vehicle']
            vehicle_issue.description = form.cleaned_data['description']
            vehicle_issue.priority = form.cleaned_data['priority']
            if not is_new:
                vehicle_issue.is_resolved = form.cleaned_data['is_resolved']
            vehicle_issue.save()

            return HttpResponseRedirect(reverse('vehicle-status'))
    else:
        initial = {
            'driver': vehicle_issue.driver,
            'vehicle': vehicle_issue.vehicle,
            'description': vehicle_issue.description,
            'priority': vehicle_issue.priority,
            'is_resolved': vehicle_issue.is_resolved,
        }
        form = EditVehicleIssueForm(initial=initial)

    context = {
        'form': form,
        'vehicle_issue': vehicle_issue,
        'is_new': is_new,
    }

    return render(request, 'vehicle/issues/edit.html', context)

def vehicleIssueDelete(request, id):
    vehicle_issue = get_object_or_404(VehicleIssue, id=id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('vehicle-issue-edit', kwargs={'id':id}))

        vehicle_issue.delete()
        return HttpResponseRedirect(reverse('vehicle-status'))

    context = {
        'model': vehicle_issue,
    }

    return render(request, 'model_delete.html', context)


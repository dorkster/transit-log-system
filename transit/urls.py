from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('schedule/<slug:mode>/<int:year>/<int:month>/<int:day>', views.schedule, name='schedule'),
    path('schedule/<slug:mode>/today', views.scheduleToday, name='schedule-today'),
    path('schedule/<slug:mode>/tomorrow', views.scheduleTomorrow, name='schedule-tomorrow'),
    path('schedule/edit/print/<int:year>/<int:month>/<int:day>', views.schedulePrint, name='schedule-print'),

    path('schedule/<slug:mode>/trips/create/<int:year>/<int:month>/<int:day>', views.tripCreate, name='trip-create'),
    path('schedule/<slug:mode>/trips/create/today', views.tripCreateToday, name='trip-create-today'),
    path('schedule/<slug:mode>/trips/create/tomorrow', views.tripCreateTomorrow, name='trip-create-tomorrow'),
    path('schedule/<slug:mode>/trips/<uuid:id>/edit/', views.tripEdit, name='trip-edit'),
    path('schedule/<slug:mode>/trips/<uuid:id>/delete/', views.tripDelete, name='trip-delete'),

    path('schedule/<slug:mode>/shifts/create/<int:year>/<int:month>/<int:day>', views.shiftCreate, name='shift-create'),
    path('schedule/<slug:mode>/shifts/create/today', views.shiftCreateToday, name='shift-create-today'),
    path('schedule/<slug:mode>/shifts/create/tomorrow', views.shiftCreateTomorrow, name='shift-create-tomorrow'),
    path('schedule/<slug:mode>/shifts/<uuid:id>/edit/', views.shiftEdit, name='shift-edit'),
    path('schedule/<slug:mode>/shifts/<uuid:id>/delete/', views.shiftDelete, name='shift-delete'),

    path('schedule/view/shifts/<uuid:id>/start/', views.shiftStart, name='shift-start'),
    path('schedule/view/shifts/<uuid:id>/end/', views.shiftEnd, name='shift-end'),
    path('schedule/view/shifts/<uuid:id>/fuel/', views.shiftFuel, name='shift-fuel'),

    path('schedule/view/trips/<uuid:id>/start/', views.tripStart, name='trip-start'),
    path('schedule/view/trips/<uuid:id>/end/', views.tripEnd, name='trip-end'),

    path('clients/', views.clientList, name='clients'),
    path('clients/create', views.clientCreate, name='client-create'),
    path('clients/<uuid:id>/edit', views.clientEdit, name='client-edit'),
    path('clients/<uuid:id>/delete', views.clientDelete, name='client-delete'),

    path('drivers/', views.driverList, name='drivers'),
    path('drivers/create', views.driverCreate, name='driver-create'),
    path('drivers/<uuid:id>/edit', views.driverEdit, name='driver-edit'),
    path('drivers/<uuid:id>/delete', views.driverDelete, name='driver-delete'),

    path('vehicles/', views.vehicleList, name='vehicles'),
    path('vehicles/create', views.vehicleCreate, name='vehicle-create'),
    path('vehicles/<uuid:id>/edit', views.vehicleEdit, name='vehicle-edit'),
    path('vehicles/<uuid:id>/delete', views.vehicleDelete, name='vehicle-delete'),

    path('triptypes/', views.triptypeList, name='triptypes'),
    path('triptypes/create', views.triptypeCreate, name='triptype-create'),
    path('triptypes/<uuid:id>/edit', views.triptypeEdit, name='triptype-edit'),
    path('triptypes/<uuid:id>/delete', views.triptypeDelete, name='triptype-delete'),

    path('templates/', views.templateList, name='templates'),
    path('templates/create', views.templateCreate, name='template-create'),
    path('templates/<uuid:id>/edit', views.templateEdit, name='template-edit'),
    path('templates/<uuid:id>/delete', views.templateDelete, name='template-delete'),

    path('templates/<uuid:parent>/trips/', views.templateTripList, name='template-trips'),
    path('templates/<uuid:parent>/trips/create', views.templateTripCreate, name='template-trip-create'),
    path('templates/<uuid:parent>/trips/<uuid:id>/edit', views.templateTripEdit, name='template-trip-edit'),
    path('templates/<uuid:parent>/trips/<uuid:id>/delete', views.templateTripDelete, name='template-trip-delete'),

    path('report/<int:year>/<int:month>', views.report, name='report'),
    path('report/this-month', views.reportThisMonth, name='report-this-month'),
    path('report/last-month', views.reportLastMonth, name='report-last-month'),

    path('vehicle-status/', views.vehicleStatus, name='vehicle-status'),
    path('vehicle-status/issues/create', views.vehicleIssueCreate, name='vehicle-issue-create'),
    path('vehicle-status/issues/<uuid:id>/edit', views.vehicleIssueEdit, name='vehicle-issue-edit'),
    path('vehicle-status/issues/<uuid:id>/delete', views.vehicleIssueDelete, name='vehicle-issue-delete'),

    path('import/', views.excelImport, name='excel-import'),

    path('ajax/schedule-edit/', views.ajaxScheduleEdit, name='ajax-schedule-edit'),
    path('ajax/schedule-view/', views.ajaxScheduleView, name='ajax-schedule-view'),
    path('ajax/set-vehicle-from-driver/', views.ajaxSetVehicleFromDriver, name='ajax-set-vehicle-from-driver'),
    path('ajax/client-list/', views.ajaxClientList, name='ajax-client-list'),
    path('ajax/driver-list/', views.ajaxDriverList, name='ajax-driver-list'),
    path('ajax/vehicle-list/', views.ajaxVehicleList, name='ajax-vehicle-list'),
    path('ajax/triptype-list/', views.ajaxTripTypeList, name='ajax-triptype-list'),
    path('ajax/vehicle-status/', views.ajaxVehicleStatus, name='ajax-vehicle-status'),
    path('ajax/template-list/', views.ajaxTemplateList, name='ajax-template-list'),
    path('ajax/template-trip-list/<uuid:parent>/', views.ajaxTemplateTripList, name='ajax-template-trip-list'),
]

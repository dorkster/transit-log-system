# Copyright © 2019-2023 Justin Jacobs
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

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('accounts/login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='user/logged_out.html'), name='logout'),
    path('accounts/password-change/', auth_views.PasswordChangeView.as_view(template_name='user/password_change.html'), name='password_change'),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(template_name='user/password_change_done.html'), name='password_change_done'),
    path('accounts/login-redirect/', auth_views.LoginView.as_view(template_name='user/login_redirect.html'), name='login_redirect'),

    path('accounts/', views.userList, name='users'),
    path('accounts/update-permissions', views.userUpdatePermissions, name='users-update-permissions'),
    path('accounts/create', views.userCreate, name='user-create'),
    path('accounts/<str:username>/edit', views.userEdit, name='user-edit'),
    path('accounts/<str:username>/delete', views.userDelete, name='user-delete'),

    path('settings/', views.sitesettingsEdit, name='settings'),

    path('help/', views.helpMain, name='help'),
    path('help/<slug:slug>/', views.helpPage, name='help-topic'),

    path('schedule/<slug:mode>/<int:year>/<int:month>/<int:day>', views.schedule, name='schedule'),
    path('schedule/<slug:mode>/today', views.scheduleToday, name='schedule-today'),
    path('schedule/<slug:mode>/tomorrow', views.scheduleTomorrow, name='schedule-tomorrow'),
    path('schedule/edit/print/<int:year>/<int:month>/<int:day>', views.schedulePrint, name='schedule-print'),
    path('schedule/edit/print-simple/<int:year>/<int:month>/<int:day>', views.schedulePrintSimple, name='schedule-print-simple'),
    path('schedule/edit/message/<int:year>/<int:month>/<int:day>', views.scheduleMessage, name='schedule-message'),
    path('schedule/edit/print-daily-log/<int:year>/<int:month>/<int:day>', views.schedulePrintDailyLog, name='schedule-print-daily-log'),

    path('schedule/<slug:mode>/trips/create/<int:year>/<int:month>/<int:day>', views.tripCreate, name='trip-create'),
    path('schedule/<slug:mode>/trips/create/today', views.tripCreateToday, name='trip-create-today'),
    path('schedule/<slug:mode>/trips/create/tomorrow', views.tripCreateTomorrow, name='trip-create-tomorrow'),
    path('schedule/<slug:mode>/trips/<uuid:id>/edit/', views.tripEdit, name='trip-edit'),
    path('schedule/<slug:mode>/trips/<uuid:id>/delete/', views.tripDelete, name='trip-delete'),
    path('schedule/<slug:mode>/trips/create-return/<uuid:id>', views.tripCreateReturn, name='trip-create-return'),
    path('schedule/<slug:mode>/trips/copy/<uuid:id>', views.tripCopy, name='trip-copy'),
    path('schedule/<slug:mode>/trips/create-from-client/<uuid:id>', views.tripCreateFromClient, name='trip-create-from-client'),

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

    path('schedule/<slug:mode>/activities/create/<int:year>/<int:month>/<int:day>', views.tripCreateActivity, name='trip-create-activity'),
    path('schedule/<slug:mode>/activities/<uuid:id>/edit/', views.tripEdit, name='trip-edit-activity'),
    path('schedule/<slug:mode>/activities/<uuid:id>/delete/', views.tripDelete, name='trip-delete-activity'),

    path('clients/', views.clientList, name='clients'),
    path('clients/create', views.clientCreate, name='client-create'),
    path('clients/<uuid:id>/edit', views.clientEdit, name='client-edit'),
    path('clients/<uuid:id>/delete', views.clientDelete, name='client-delete'),
    path('clients/create-from-trip/<uuid:trip_id>', views.clientCreateFromTrip, name='client-create-from-trip'),
    path('clients/create-from-template-trip/<uuid:trip_id>', views.clientCreateFromTemplateTrip, name='client-create-from-template-trip'),
    path('clients/xlsx', views.clientXLSX, name='client-xlsx'),
    path('clients/<uuid:id>/update-trips', views.clientUpdateTrips, name='client-update-trips'),
    path('clients/<uuid:id>/fix-dupes', views.clientFixDupes, name='client-fix-dupes'),

    path('clients/<uuid:parent>/payments/', views.clientPaymentList, name='client-payments'),
    path('clients/<uuid:parent>/payments/create', views.clientPaymentCreate, name='client-payment-create'),
    path('clients/<uuid:parent>/payments/<uuid:id>/edit', views.clientPaymentEdit, name='client-payment-edit'),
    path('clients/<uuid:parent>/payments/<uuid:id>/delete', views.clientPaymentDelete, name='client-payment-delete'),

    path('clients/<uuid:parent>/report/<int:start_year>/<int:start_month>/<int:start_day>/<int:end_year>/<int:end_month>/<int:end_day>/', views.clientReport, name='client-report'),
    path('clients/<uuid:parent>/report/<int:year>/<int:month>/', views.clientReportMonth, name='client-report-month'),
    path('clients/<uuid:parent>/report/this-month/', views.clientReportThisMonth, name='client-report-this-month'),
    path('clients/<uuid:parent>/report/by-driver/<uuid:driver_id>/<int:start_year>/<int:start_month>/<int:start_day>/<int:end_year>/<int:end_month>/<int:end_day>/', views.clientReportByDriver, name='client-report-by-driver'),
    path('clients/<uuid:parent>/report/by-driver/<uuid:driver_id>/<int:year>/<int:month>/', views.clientReportByDriverMonth, name='client-report-by-driver-month'),
    path('clients/<uuid:parent>/report/by-driver/<uuid:driver_id>/this-month/', views.clientReportByDriverThisMonth, name='client-report-by-driver-this-month'),

    path('destinations/', views.destinationList, name='destinations'),
    path('destinations/create', views.destinationCreate, name='destination-create'),
    path('destinations/<uuid:id>/edit', views.destinationEdit, name='destination-edit'),
    path('destinations/<uuid:id>/delete', views.destinationDelete, name='destination-delete'),
    path('destinations/create-from-trip/<uuid:trip_id>/<int:use_address>', views.destinationCreateFromTrip, name='destination-create-from-trip'),
    path('destinations/create-from-template-trip/<uuid:trip_id>/<int:use_address>', views.destinationCreateFromTemplateTrip, name='destination-create-from-template-trip'),
    path('destinations/<uuid:id>/update-trips', views.destinationUpdateTrips, name='destination-update-trips'),
    path('destinations/<uuid:id>/fix-dupes', views.destinationFixDupes, name='destination-fix-dupes'),
    path('destination/xlsx', views.destinationXLSX, name='destination-xlsx'),

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

    path('fares/', views.fareList, name='fares'),
    path('fares/create', views.fareCreate, name='fare-create'),
    path('fares/<uuid:id>/edit', views.fareEdit, name='fare-edit'),
    path('fares/<uuid:id>/delete', views.fareDelete, name='fare-delete'),

    path('tags/', views.tagList, name='tags'),
    path('tags/create', views.tagCreate, name='tag-create'),
    path('tags/<uuid:id>/edit', views.tagEdit, name='tag-edit'),
    path('tags/<uuid:id>/delete', views.tagDelete, name='tag-delete'),

    path('activty-colors/', views.activityColorList, name='activity-colors'),
    path('activty-colors/create', views.activityColorCreate, name='activity-color-create'),
    path('activty-colors/<uuid:id>/edit', views.activityColorEdit, name='activity-color-edit'),
    path('activty-colors/<uuid:id>/delete', views.activityColorDelete, name='activity-color-delete'),

    path('volunteers/', views.volunteerList, name='volunteers'),
    path('volunteers/create', views.volunteerCreate, name='volunteer-create'),
    path('volunteers/<uuid:id>/edit', views.volunteerEdit, name='volunteer-edit'),
    path('volunteers/<uuid:id>/delete', views.volunteerDelete, name='volunteer-delete'),

    path('templates/', views.templateList, name='templates'),
    path('templates/create', views.templateCreate, name='template-create'),
    path('templates/<uuid:id>/edit', views.templateEdit, name='template-edit'),
    path('templates/<uuid:id>/delete', views.templateDelete, name='template-delete'),

    path('templates/<uuid:parent>/trips/', views.templateTripList, name='template-trips'),
    path('templates/<uuid:parent>/trips/create', views.templateTripCreate, name='template-trip-create'),
    path('templates/<uuid:parent>/trips/<uuid:id>/edit', views.templateTripEdit, name='template-trip-edit'),
    path('templates/<uuid:parent>/trips/<uuid:id>/delete', views.templateTripDelete, name='template-trip-delete'),
    path('templates/<slug:parent>/trips/copy/<uuid:id>', views.templateTripCopy, name='template-trip-copy'),
    path('templates/<uuid:parent>/trips/create-return/<uuid:id>', views.templateTripCreateReturn, name='template-trip-create-return'),

    path('templates/<uuid:parent>/activities/create', views.templateTripCreateActivity, name='template-trip-create-activity'),
    path('templates/<uuid:parent>/activities/<uuid:id>/edit', views.templateTripEdit, name='template-trip-edit-activity'),
    path('templates/<uuid:parent>/activities/<uuid:id>/delete', views.templateTripDelete, name='template-trip-delete-activity'),

    path('report/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>', views.report, name='report'),
    path('report/<int:year>/<int:month>', views.reportMonth, name='report-month'),
    path('report/<int:year>', views.reportYear, name='report-year'),
    path('report/this-month', views.reportThisMonth, name='report-this-month'),
    path('report/last-month', views.reportLastMonth, name='report-last-month'),
    path('report/xlsx/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>', views.reportXLSX, name='report-xlsx'),
    path('report/print/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>', views.reportPrint, name='report-print'),
    path('report/print-mileage-summary/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>', views.reportPrintMileageSummary, name='report-print-mileage-summary'),

    path('report/by-driver/<uuid:driver_id>/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>', views.reportDriver, name='report-driver'),
    path('report/by-driver/<uuid:driver_id>/<int:year>/<int:month>', views.reportMonthDriver, name='report-month-driver'),
    path('report/by-driver/<uuid:driver_id>/this-month', views.reportThisMonthDriver, name='report-this-month-driver'),
    path('report/by-driver/<uuid:driver_id>/last-month', views.reportLastMonthDriver, name='report-last-month-driver'),
    path('report/by-driver/<uuid:driver_id>/xlsx/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>', views.reportXLSXDriver, name='report-xlsx-driver'),
    path('report/by-driver/<uuid:driver_id>/print/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>', views.reportPrintDriver, name='report-print-driver'),

    path('report/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>/edit-trip/<uuid:id>', views.tripEditFromReport, name='report-trip-edit'),
    path('report/<int:start_year>/<int:start_month>/<int:start_day>/to/<int:end_year>/<int:end_month>/<int:end_day>/edit-shift/<uuid:id>', views.shiftEditFromReport, name='report-shift-edit'),

    path('report/fare-check-oneway/<int:start_year>/<int:start_month>/<int:start_day>/<int:end_year>/<int:end_month>/<int:end_day>/', views.fareCheckOneWay, name='report-fare-check-oneway'),
    path('report/fare-check-oneway/<int:year>/<int:month>/', views.fareCheckOneWayMonth, name='report-fare-check-oneway-month'),
    path('report/fare-check-oneway/this-month/', views.fareCheckOneWayThisMonth, name='report-fare-check-oneway-this-month'),

    path('vehicle-status/', views.vehicleStatus, name='vehicle-status'),
    path('vehicle-status/issues/create', views.vehicleIssueCreate, name='vehicle-issue-create'),
    path('vehicle-status/issues/<uuid:id>/edit', views.vehicleIssueEdit, name='vehicle-issue-edit'),
    path('vehicle-status/issues/<uuid:id>/delete', views.vehicleIssueDelete, name='vehicle-issue-delete'),
    path('vehicle-status/maintainence/<uuid:id>/edit', views.vehicleMaintainEdit, name='vehicle-maintain-edit'),

    path('vehicle-pretrip/create/<uuid:shift_id>', views.vehiclePreTripCreate, name='vehicle-pretrip-create'),
    path('vehicle-pretrip/create-no-shift/<uuid:vehicle_id>', views.vehiclePreTripCreateNoShift, name='vehicle-pretrip-create-no-shift'),
    path('vehicle-pretrip/<uuid:id>/delete', views.vehiclePreTripDelete, name='vehicle-pretrip-delete'),

    path('import/', views.excelImport, name='excel-import'),
    path('search/', views.search, name='search'),
    path('search-xlsx/', views.searchExportXLSX, name='search-xlsx'),

    path('event-log/', views.loggedEventList, name='loggedevent-list'),

    path('ajax/schedule-edit/', views.ajaxScheduleEdit, name='ajax-schedule-edit'),
    path('ajax/schedule-view/', views.ajaxScheduleView, name='ajax-schedule-view'),
    path('ajax/schedule-read-only/', views.ajaxScheduleReadOnly, name='ajax-schedule-read-only'),
    path('ajax/schedule-print/<int:year>/<int:month>/<int:day>', views.ajaxSchedulePrint, name='ajax-schedule-print'),
    path('ajax/schedule-print-daily-log/<int:year>/<int:month>/<int:day>', views.ajaxSchedulePrintDailyLog, name='ajax-schedule-print-daily-log'),
    path('ajax/client-list/', views.ajaxClientList, name='ajax-client-list'),
    path('ajax/client-payment-list/<uuid:parent>/', views.ajaxClientPaymentList, name='ajax-client-payment-list'),
    path('ajax/destination-list/', views.ajaxDestinationList, name='ajax-destination-list'),
    path('ajax/driver-list/', views.ajaxDriverList, name='ajax-driver-list'),
    path('ajax/vehicle-list/', views.ajaxVehicleList, name='ajax-vehicle-list'),
    path('ajax/triptype-list/', views.ajaxTripTypeList, name='ajax-triptype-list'),
    path('ajax/fare-list/', views.ajaxFareList, name='ajax-fare-list'),
    path('ajax/tag-list/', views.ajaxTagList, name='ajax-tag-list'),
    path('ajax/activity-color-list/', views.ajaxActivityColorList, name='ajax-activity-color-list'),
    path('ajax/volunteer-list/', views.ajaxVolunteerList, name='ajax-volunteer-list'),
    path('ajax/vehicle-status/', views.ajaxVehicleStatus, name='ajax-vehicle-status'),
    path('ajax/template-list/', views.ajaxTemplateList, name='ajax-template-list'),
    path('ajax/template-trip-list/<uuid:parent>/', views.ajaxTemplateTripList, name='ajax-template-trip-list'),
    path('ajax/loggedevent-list/', views.ajaxLoggedEventList, name='ajax-loggedevent-list'),
]

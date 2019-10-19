from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('schedule/<slug:mode>/<int:year>/<int:month>/<int:day>', views.schedule, name='schedule'),
    path('schedule/<slug:mode>/today', views.scheduleToday, name='schedule-today'),
    path('schedule/<slug:mode>/tomorrow', views.scheduleTomorrow, name='schedule-tomorrow'),

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

    path('ajax/schedule-edit/', views.ajaxScheduleEdit, name='ajax-schedule-edit'),
    path('ajax/schedule-view/', views.ajaxScheduleView, name='ajax-schedule-view'),
    path('ajax/set-vehicle-from-driver/', views.ajaxSetVehicleFromDriver, name='ajax-set-vehicle-from-driver'),
    path('ajax/client-list/', views.ajaxClientList, name='ajax-client-list'),
]

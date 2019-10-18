from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('<slug:mode>/<int:year>/<int:month>/<int:day>', views.schedule, name='schedule'),
    path('<slug:mode>/today', views.scheduleToday, name='schedule-today'),
    path('<slug:mode>/tomorrow', views.scheduleTomorrow, name='schedule-tomorrow'),

    path('<slug:mode>/trips/create/<int:year>/<int:month>/<int:day>', views.tripCreate, name='trip-create'),
    path('<slug:mode>/trips/create/today', views.tripCreateToday, name='trip-create-today'),
    path('<slug:mode>/trips/create/tomorrow', views.tripCreateTomorrow, name='trip-create-tomorrow'),
    path('<slug:mode>/trips/<uuid:id>/edit/', views.tripEdit, name='trip-edit'),
    path('<slug:mode>/trips/<uuid:id>/delete/', views.tripDelete, name='trip-delete'),

    path('<slug:mode>/shifts/create/<int:year>/<int:month>/<int:day>', views.shiftCreate, name='shift-create'),
    path('<slug:mode>/shifts/create/today', views.shiftCreateToday, name='shift-create-today'),
    path('<slug:mode>/shifts/create/tomorrow', views.shiftCreateTomorrow, name='shift-create-tomorrow'),
    path('<slug:mode>/shifts/<uuid:id>/edit/', views.shiftEdit, name='shift-edit'),
    path('<slug:mode>/shifts/<uuid:id>/delete/', views.shiftDelete, name='shift-delete'),

    path('view/shifts/<uuid:id>/start/', views.shiftStart, name='shift-start'),
    path('view/shifts/<uuid:id>/end/', views.shiftEnd, name='shift-end'),
    path('view/shifts/<uuid:id>/fuel/', views.shiftFuel, name='shift-fuel'),

    path('view/trips/<uuid:id>/start/', views.tripStart, name='trip-start'),
    path('view/trips/<uuid:id>/end/', views.tripEnd, name='trip-end'),

    path('clients/', views.clientList, name='clients'),
    path('clients/create', views.clientCreate, name='client-create'),
    path('clients/<uuid:id>/edit', views.clientEdit, name='client-edit'),
    path('clients/<uuid:id>/delete', views.clientDelete, name='client-delete'),

    path('ajax/schedule-edit/', views.ajaxScheduleEdit, name='ajax-schedule-edit'),
    path('ajax/schedule-view/', views.ajaxScheduleView, name='ajax-schedule-view'),
    path('ajax/set-vehicle-from-driver/', views.ajaxSetVehicleFromDriver, name='ajax-set-vehicle-from-driver'),
    path('ajax/client-list/', views.ajaxClientList, name='ajax-client-list'),
]

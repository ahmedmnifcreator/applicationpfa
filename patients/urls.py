from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.patient_list, name='list'),
    path('add/', views.patient_add, name='add'),
    path('<int:pk>/', views.patient_detail, name='detail'),
    path('<int:pk>/edit/', views.patient_edit, name='edit'),
    path('<int:pk>/delete/', views.patient_delete, name='delete'),
    path('appointment/add/', views.appointment_add, name='appointment_add'),
    path('appointment/<int:pk>/delete/', views.appointment_delete, name='appointment_delete'),
]

from django.urls import path
from . import views

app_name = 'biomarkers'

urlpatterns = [
    path('', views.biomarker_list, name='list'),
    path('export/', views.export_csv, name='export_csv'),
]

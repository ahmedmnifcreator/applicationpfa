from django.urls import path
from . import views

app_name = 'visits'

urlpatterns = [
    path('list/', views.mri_list, name='list'),
    path('upload/', views.mri_upload, name='upload'),
    path('status/<int:visit_id>/', views.mri_status, name='status'),
]

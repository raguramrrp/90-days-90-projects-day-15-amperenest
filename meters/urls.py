from django.urls import path
from . import views

app_name = 'meters'

urlpatterns = [
    path('', views.meter_list, name='list'),
    path('add/', views.meter_create, name='create'),
    path('<int:pk>/', views.meter_detail, name='detail'),
    path('<int:pk>/edit/', views.meter_edit, name='edit'),
    path('<int:pk>/archive/', views.meter_archive, name='archive'),
]

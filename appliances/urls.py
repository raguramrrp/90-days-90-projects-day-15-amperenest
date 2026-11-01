from django.urls import path
from . import views

app_name = 'appliances'

urlpatterns = [
    path('', views.appliance_list, name='list'),
    path('add/', views.appliance_create, name='create'),
    path('insights/', views.appliance_insights, name='insights'),
    path('<int:pk>/edit/', views.appliance_edit, name='edit'),
    path('<int:pk>/delete/', views.appliance_delete, name='delete'),
]

from django.urls import path
from . import views

app_name = 'households'

urlpatterns = [
    path('', views.household_list, name='list'),
    path('add/', views.household_create, name='create'),
    path('<int:pk>/', views.household_detail, name='detail'),
    path('<int:pk>/edit/', views.household_edit, name='edit'),
    path('<int:pk>/switch/', views.household_switch, name='switch'),
    path('<int:pk>/members/add/', views.member_add, name='member_add'),
    path('<int:pk>/members/<int:member_id>/remove/', views.member_remove, name='member_remove'),
]

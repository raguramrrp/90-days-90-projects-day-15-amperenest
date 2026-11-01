from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.bill_list, name='list'),
    path('add/', views.bill_create, name='create'),
    path('calculator/', views.bill_calculator, name='calculator'),
    path('<int:pk>/', views.bill_detail, name='detail'),
    path('<int:pk>/edit/', views.bill_edit, name='edit'),
    path('<int:pk>/mark-paid/', views.bill_mark_paid, name='mark_paid'),
]

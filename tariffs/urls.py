from django.urls import path
from . import views

app_name = 'tariffs'

urlpatterns = [
    path('', views.tariff_list, name='list'),
    path('add/', views.tariff_create, name='create'),
    path('<int:pk>/', views.tariff_detail, name='detail'),
    path('<int:pk>/edit/', views.tariff_edit, name='edit'),
    path('<int:pk>/slabs/add/', views.tariff_slab_add, name='slab_add'),
    path('<int:pk>/slabs/<int:slab_id>/delete/', views.tariff_slab_delete, name='slab_delete'),
    path('<int:pk>/charges/add/', views.tariff_charge_add, name='charge_add'),
]

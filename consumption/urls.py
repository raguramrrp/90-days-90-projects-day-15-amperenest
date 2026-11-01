from django.urls import path
from . import views

app_name = 'consumption'

urlpatterns = [
    path('readings/', views.readings_list, name='list'),
    path('readings/add/', views.reading_create, name='create'),
    path('readings/<int:pk>/edit/', views.reading_edit, name='edit'),
    path('readings/<int:pk>/delete/', views.reading_delete, name='delete'),
    path('history/', views.consumption_history, name='history'),
    path('import/', views.readings_import, name='import'),
]

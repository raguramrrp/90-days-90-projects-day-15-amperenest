from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.alert_list, name='list'),
    path('<int:pk>/read/', views.alert_mark_read, name='mark_read'),
    path('<int:pk>/dismiss/', views.alert_dismiss, name='dismiss'),
    path('dismiss-all/', views.alert_dismiss_all, name='dismiss_all'),
    path('rules/<int:pk>/toggle/', views.alert_rule_toggle, name='rule_toggle'),
]
